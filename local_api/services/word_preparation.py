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
