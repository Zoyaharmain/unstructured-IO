"""Offline structural/source-presence audit. This does not create semantic gold labels."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import unicodedata
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from local_api.schemas.sections import SectionResponse
from local_api.services.subschema_validation import validate_hierarchy
from local_api.services.schema_diagnostics import diagnose
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.export import standardized_export


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def normalized(value):return ''.join(c for c in unicodedata.normalize('NFKC',str(value)).casefold() if c.isalnum())


def original_text(path):
    if path.suffix.lower()=='.pdf':
        return subprocess.run(['pdftotext','-layout',str(path),'-'],capture_output=True,text=True,check=True,timeout=60).stdout
    if path.suffix.lower()=='.docx':
        w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        with ZipFile(path) as z:
            root=ET.fromstring(z.read('word/document.xml'))
        mc='{http://schemas.openxmlformats.org/markup-compatibility/2006}'
        for alternate in list(root.iter(mc+'AlternateContent')):
            branches=list(alternate)
            chosen=next((b for b in branches if b.tag==mc+'Choice'),branches[0] if branches else None)
            for branch in branches:
                if branch is not chosen:alternate.remove(branch)
        return '\n'.join(''.join(t.text or '' for t in p.iter(w+'t'))
                         for p in root.iter(w+'p') if not any(q is not p for q in p.iter(w+'p')))
    raise ValueError('Unsupported source format')


def literals(data):
    for field,value in data.get('contact',{}).items():
        if value:yield 'contact.'+field,str(value)
    for category in ('experience','education','projects','certifications'):
        for i,record in enumerate(data.get(category,[])):
            for name,value in record.items():
                if isinstance(value,str) and value.strip():yield f'{category}[{i}].{name}',value
    for i,value in enumerate(data.get('skills',{}).get('all_skills',[])):
        if value:yield f'skills.all_skills[{i}]',value


def audit_one(mapping,source):
    text=original_text(source);nt=normalized(text)
    if source.suffix.lower()=='.pdf':
        raw=subprocess.run(['pdftotext','-raw',str(source),'-'],capture_output=True,text=True,check=True,timeout=60).stdout
        nt += '\0' + normalized(raw)
    meta=mapping.get('meta',{});data=mapping['data']
    checks=list(literals(data))
    for parent in mapping.get('section_schemas',[]):
        if parent['category']!='awards':continue
        for ri,record in enumerate(parent['records']):
            for attribute in record['attributes']:
                for vi,item in enumerate(attribute['items']):
                    if isinstance(item['value'],str):
                        checks.append((f'awards[{ri}].{attribute["name"]}[{vi}]',item['value']))
    unmatched=[{'path':path,'value_length':len(value),'reason':'not_confirmed_in_independent_text; layout/normalization may differ'}
               for path,value in checks if normalized(value) not in nt]
    issues=[]
    inventory_available=bool(meta.get('reviewed_sections'))
    if inventory_available:
        try:validate_hierarchy(mapping['section_schemas'],SectionResponse.model_validate(meta['reviewed_sections']))
        except Exception as exc:issues.append(diagnose(exc,'subschema_validation'))
    if data.get('contact',{}).get('full_name') and '@' in data['contact']['full_name']:
        issues.append({'code':'email_used_as_candidate_name','path':'data.contact.full_name'})
    seen=set()
    for i,job in enumerate(data.get('experience',[])):
        if not job.get('company') and not job.get('role'):
            issues.append({'code':'identityless_experience_record','path':f'data.experience[{i}]'})
        key=tuple(normalized(job.get(k,'')) for k in ('company','role','start_date','end_date'))
        if all(key):
            if key in seen:issues.append({'code':'duplicate_job_identity_and_dates','path':f'data.experience[{i}]'})
            seen.add(key)
    std,metadata,status,warnings=standardize_resume_data(data,reference_date=datetime(2026,10,29,tzinfo=timezone.utc))
    return {'source_sha256':sha(source),'source_text_characters':len(text),'source_reader':'pdftotext_layout' if source.suffix.lower()=='.pdf' else 'original_docx_xml',
        'mapping_status':meta.get('mapping_result',{}).get('status'),
        'field_review_status':meta.get('field_review',{}).get('status'),
        'section_review_status':meta.get('section_review',{}).get('status'),
        'document_scope':meta.get('document_scope',{}).get('kind'),
        'candidate_resume':meta.get('document_scope',{}).get('candidate_resume'),
        'counts':{k:len(data.get(k,[])) for k in ('experience','education','projects','certifications')},
        'literal_checks':len(checks),'source_presence_not_confirmed':unmatched,
        'structural_issues':issues,'citation_inventory_available':inventory_available,'missing_required_fields':meta.get('missing_required_fields',[]),
        'unassigned_source_spans':meta.get('source_accounting',{}).get('unresolved_meaningful_spans'),
        'active_field_failures':[d for d in meta.get('field_review',{}).get('diagnostics',[]) if not d.get('recovered')],
        'standardization_warning_counts':dict(Counter(w.warning_type for w in warnings)),
        'duration_statuses':dict(Counter(e.duration_status for e in std.experience)),
        'human_verified':False,'semantic_accuracy_percent':None}, std,metadata,status,warnings,text


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True);parser.add_argument('--sources',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('Output must be new; prior reports are immutable')
    summary=json.loads((args.run/'summary_report.json').read_text())
    before={str(p):sha(p) for p in args.run.rglob('*') if p.is_file()}
    sources={r['filename']:args.sources/r['filename'] for r in summary}
    if any(not p.is_file() for p in sources.values()):parser.error('Original source file missing')
    original_hashes={name:sha(p) for name,p in sources.items()}
    def blocked(*a,**k):raise RuntimeError('Network forbidden by offline audit')
    socket.socket.connect=blocked;socket.create_connection=blocked
    args.output.mkdir(parents=True,mode=0o700)
    for folder in ('documents','standardized','private-source-text'):(args.output/folder).mkdir(mode=0o700)
    rows=[]
    for n,record in enumerate(summary,1):
        name=record['filename'];artifact=args.run/(Path(name).stem+'_schema.json')
        mapping=json.loads(artifact.read_text())
        result,std,metadata,status,warnings,text=audit_one(mapping,sources[name])
        result.update(file=name,saved_output_sha256=sha(artifact))
        (args.output/'documents'/f'{n:02d}.json').write_text(json.dumps(result,indent=2)+'\n')
        metadata.source_evidence=mapping.get('meta',{}).get('field_evidence',{})
        wrapped={**mapping,'standardized_data':std.model_dump(),'standardization_metadata':metadata.model_dump(),'validation_status':status.model_dump(),'warnings':[w.model_dump() for w in warnings]}
        (args.output/'standardized'/f'{n:02d}.json').write_text(json.dumps(standardized_export(wrapped),indent=2)+'\n')
        (args.output/'private-source-text'/f'{n:02d}.txt').write_text(text)
        rows.append(result)
        print(f'{n}/{len(summary)} audited',flush=True)
    assert all(sha(Path(p))==h for p,h in before.items()),'Saved run changed during audit'
    assert all(sha(sources[n])==h for n,h in original_hashes.items()),'Original source changed during audit'
    result={'documents':len(rows),'mapping_statuses':dict(Counter(r['mapping_status'] for r in rows)),
        'field_review_statuses':dict(Counter(r['field_review_status'] for r in rows)),
        'section_review_statuses':dict(Counter(r['section_review_status'] for r in rows)),
        'scope_counts':dict(Counter(r['document_scope'] for r in rows)),
        'citation_inventory_unavailable':sum(not r['citation_inventory_available'] for r in rows),
        'structure_issue_documents':sum(bool(r['structural_issues']) for r in rows),
        'literal_checks':sum(r['literal_checks'] for r in rows),
        'literal_presence_not_confirmed':sum(len(r['source_presence_not_confirmed']) for r in rows),
        'duration_statuses':dict(sum((Counter(r['duration_statuses']) for r in rows),Counter())),
        'standardization_warning_counts':dict(sum((Counter(r['standardization_warning_counts']) for r in rows),Counter())),
        'semantic_accuracy_percent':None,'human_verified':False,'network_calls':0,
        'original_sources_unchanged':True,'saved_outputs_unchanged':True,
        'limitations':'Literal presence and citation validation are not entity precision, recall, extraction recall or semantic accuracy. Automated findings need independent review.'}
    (args.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    (args.output/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    (args.output/'expected.review-template.json').write_text(json.dumps([{'file':r['file'],'source_sha256':r['source_sha256'],'human_verified':False,'expected':{'contact':None,'experience':None,'education':None,'skills':None,'projects':None,'achievements':None},'review_notes':[]} for r in rows],indent=2)+'\n')

if __name__=='__main__':main()
