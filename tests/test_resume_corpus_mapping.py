"""Bulk mapping must reuse matching saved sources and resume without duplication."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from scripts.map_resume_corpus import fresh_worker


def test_corpus_reuses_saved_blocks_and_resume_is_idempotent(tmp_path):
    spec=importlib.util.spec_from_file_location('corpus_sample',Path(__file__).with_name('test_schema_mapping.py'))
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    request=helper.sample()
    source=tmp_path/'resumes';source.mkdir();file=source/'sample.pdf';file.write_bytes(b'saved fixture source')
    saved=tmp_path/'saved';saved.mkdir()
    artifact={'file':'sample.pdf','extraction':{'elements':[e.model_dump() for e in request.elements]},'sections':request.sections.model_dump()}
    (saved/'fixture.json').write_text(json.dumps(artifact))
    (saved/'current-results.json').write_text(json.dumps([{'file':'sample.pdf','sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'artifact':'fixture.json'}]))
    output=tmp_path/'output'
    cmd=[sys.executable,'scripts/map_resume_corpus.py',str(source),'--output',str(output),'--saved-audit',str(saved)]
    for _ in range(2):
        completed=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
        assert completed.returncode==0,completed.stderr
    summary=json.loads((output/'summary.json').read_text())
    assert summary['files_completed']==1 and summary['complete']
    assert summary['provider_calls']==0
    assert summary['input_modes']=={'reused_saved_blocks':1}
    assert len((output/'results.jsonl').read_text().splitlines())==1
    row=json.loads((output/'per-resume.json').read_text())[0]
    mapping=json.loads((output/row['mapping_artifact']).read_text())
    assert mapping['section_schemas'] and row['citation_validation_passed']


def test_changed_source_is_rejected_before_extracting(tmp_path):
    source=tmp_path/'changed.pdf';source.write_bytes(b'changed')
    row=fresh_worker({'source':str(source),'file':source.name,'sha256':'old'},str(tmp_path/'output'),30,'code')
    assert row['error_type']=='SourceChanged' and row['status']=='failed'
    assert row['provider_calls']==0
