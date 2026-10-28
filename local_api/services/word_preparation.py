"""Prepare Word input in memory without modifying the uploaded document."""
from io import BytesIO
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import posixpath

from local_api.utils.file_validation import ExtractionError


def convert_legacy_word(payload):
    """Isolated LibreOffice profiles avoid unwritable/shared user configuration."""
    with TemporaryDirectory(prefix='resume-word-') as directory:
        root = Path(directory)
        source = root / 'document.doc'
        source.write_bytes(payload)
        profile = (root / 'profile').as_uri()
        try:
            completed = subprocess.run(
                ['soffice', f'-env:UserInstallation={profile}', '--headless',
                 '--convert-to', 'docx', '--outdir', directory, str(source)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60,
                check=False)
        except subprocess.TimeoutExpired:
            raise ExtractionError(422, 'Legacy Word conversion timed out') from None
        target = root / 'document.docx'
        if completed.returncode or not target.is_file():
            raise ExtractionError(422, 'Legacy Word document could not be converted')
        return target.read_bytes()


def repair_null_image_relationships(payload):
    """Remove only missing image links to NULL; never remove text-bearing parts.

    Some Word writers leave an image relationship to ../NULL. python-docx refuses
    the entire archive, although document.xml and its text are intact. Missing
    real image paths, non-image relationships and other corruption are untouched.
    """
    changes = {}
    count = 0
    with ZipFile(BytesIO(payload)) as archive:
        names = set(archive.namelist())
        for name in names:
            if not name.endswith('.rels'):
                continue
            root = ET.fromstring(archive.read(name))
            removed = 0
            for relation in list(root):
                target = relation.get('Target', '')
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(posixpath.dirname(name)), target)).lstrip('/')
                if (relation.get('Type', '').endswith('/image') and
                        relation.get('TargetMode') != 'External' and
                        posixpath.basename(target).upper() == 'NULL' and resolved not in names):
                    root.remove(relation)
                    removed += 1
            if removed:
                changes[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
                count += removed
        if not changes:
            return payload, 0
        output = BytesIO()
        with ZipFile(output, 'w') as repaired:
            for item in archive.infolist():
                repaired.writestr(item, changes.get(item.filename, archive.read(item.filename)))
        return output.getvalue(), count


def materialize_textboxes(payload):
    """Expose Word text boxes to paragraph-only partitioners in reading order.

    Transform a private copy, retain paragraph/table XML and choose one branch
    of Word's alternate shape representations. Original upload bytes stay intact.
    """
    import copy
    w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    mc='{http://schemas.openxmlformats.org/markup-compatibility/2006}'
    with ZipFile(BytesIO(payload)) as archive:
        root=ET.fromstring(archive.read('word/document.xml'))
        # Choice and Fallback describe the same displayed shape, not two boxes.
        for alternate in list(root.iter(mc+'AlternateContent')):
            branches=list(alternate)
            eligible=[branch for branch in branches if list(branch.iter(w+'txbxContent'))]
            if eligible:
                selected=next((branch for branch in eligible if branch.tag==mc+'Choice'),eligible[0])
                for branch in branches:
                    if branch is not selected:alternate.remove(branch)
        count=0; tails={}
        # Repeat because copied nested boxes need materialization too.
        while True:
            parents={child:parent for parent in root.iter() for child in parent}
            boxes=list(root.iter(w+'txbxContent'))
            if not boxes:break
            box=boxes[0]
            anchor=parents.get(box)
            while anchor is not None and anchor.tag!=w+'p':anchor=parents.get(anchor)
            if anchor is None or anchor not in parents:
                raise ExtractionError(422,'Word text box has no supported paragraph anchor')
            contents=[copy.deepcopy(child) for child in box if child.tag in {w+'p',w+'tbl'}]
            parent=parents[anchor];offset=list(parent).index(tails.get(anchor,anchor))+1
            for child in contents:
                parent.insert(offset,child);offset+=1
                tails[anchor]=child
            parents[box].remove(box)
            count+=1
        if not count:return payload,0
        prepared=BytesIO()
        with ZipFile(prepared,'w') as output:
            for item in archive.infolist():
                output.writestr(item,ET.tostring(root,encoding='utf-8',xml_declaration=True)
                                if item.filename=='word/document.xml' else archive.read(item.filename))
        return prepared.getvalue(),count


def annotate_table_paragraphs(payload, elements):
    """Recover paragraph boundaries only for exactly matching flattened tables.

    Text and source element indices remain unchanged. No fuzzy alignment or
    inserted source words: ambiguous/unmatched tables retain upstream output.
    """
    import re
    w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    with ZipFile(BytesIO(payload)) as archive:
        root=ET.fromstring(archive.read('word/document.xml'))
    used=set()
    for table in root.iter(w+'tbl'):
        paragraphs=[''.join(t.text or '' for t in p.iter(w+'t')).strip() for p in table.iter(w+'p')]
        paragraphs=[p for p in paragraphs if p]
        normalized=' '.join(' '.join(paragraphs).split())
        matches=[i for i,e in enumerate(elements) if i not in used and e.get('type')=='Table'
                 and ' '.join(e.get('text','').split())==normalized]
        if len(matches)!=1:continue
        index=matches[0];text=elements[index]['text'];cursor=0;spans=[]
        for paragraph in paragraphs:
            match=re.compile(r'\s+'.join(re.escape(word) for word in paragraph.split())).search(text,cursor)
            if not match or text[cursor:match.start()].strip():break
            spans.append({'start':match.start(),'end':match.end()});cursor=match.end()
        else:
            if text[cursor:].strip():continue
            metadata=elements[index].setdefault('metadata',{})
            metadata['word_source_paragraphs']=spans
            metadata['recovery_cuts']=sorted(set(metadata.get('recovery_cuts',[]))|{x for span in spans for x in span.values()})
            used.add(index)
