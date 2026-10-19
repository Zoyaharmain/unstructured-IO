"""Corpus audit checks catch corruption rather than equating coverage with accuracy."""
import importlib.util
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as NS

spec = importlib.util.spec_from_file_location('batch_audit', Path(__file__).parents[1]/'scripts/batch_check_resumes.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def fixture():
    block = NS(source_element_index=0,start=0,end=5,text='Alpha')
    section = NS(category='skills',blocks=[block],text='Alpha',
                 highlights=[NS(start=0,end=5)],entries=[NS(block_indices=[0])])
    return [NS(text='Alpha')], NS(sections=[section],needs_review=[])


def test_valid_source_and_highlights():
    elements,result=fixture()
    assert audit.validate_result(elements,result)==[]


def test_audit_catches_lost_text_and_invalid_highlight():
    elements,result=fixture()
    result.sections[0].blocks[0].start=1
    result.sections[0].highlights[0].end=6
    errors=audit.validate_result(elements,result)
    assert 'source_range_or_text_mismatch' in errors
    assert 'invalid_highlight_offsets' in errors


def test_audit_catches_duplicate_sections_and_bad_entry_reference():
    elements,result=fixture()
    result.sections.append(result.sections[0])
    result.sections[0].entries[0].block_indices=[99]
    errors=audit.validate_result(elements,result)
    assert 'duplicate_categories' in errors
    assert 'invalid_entry_reference' in errors


def test_offline_guard_blocks_sockets_and_removes_provider_key():
    code=f'''import importlib.util, os, socket
spec=importlib.util.spec_from_file_location('audit',{str(Path(audit.__file__))!r})
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
os.environ['DEEPSEEK_API_KEY']='dummy'
m.offline_environment()
assert 'DEEPSEEK_API_KEY' not in os.environ
assert os.environ['HF_HUB_OFFLINE']=='1'
try: socket.create_connection(('127.0.0.1',8011))
except RuntimeError: pass
else: raise AssertionError('Network guard failed')
'''
    subprocess.run([sys.executable,'-c',code],check=True)


def test_deadline_cannot_be_swallowed_by_parser_exception_handler():
    caught=False
    try:
        try:audit.timeout_handler()
        except Exception:raise AssertionError('Deadline was swallowed')
    except audit.DocumentDeadline:caught=True
    assert caught
