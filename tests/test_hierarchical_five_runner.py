"""Paid-run scope and integrity guards; all tests are offline."""
import hashlib
import json
import sys
from pathlib import Path
from copy import deepcopy
import pytest
from scripts.run_hierarchical_five import verify, main
from local_api.services import llm_section_review as llm


@pytest.fixture
def manifest(tmp_path):
    selected = []
    for i in range(5):
        source = tmp_path / f'{i}.pdf'
        source.write_bytes(f'fixture {i}'.encode())
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        baseline = tmp_path / f'{i}.json'
        baseline.write_text('{}')
        selected.append({'file': source.name, 'document_id': digest[:20], 'sha256': digest,
            'source_path': str(source), 'baseline_source': str(baseline), 'baseline_mapping': str(baseline),
            'baseline_source_sha256': hashlib.sha256(baseline.read_bytes()).hexdigest(),
            'baseline_mapping_sha256': hashlib.sha256(baseline.read_bytes()).hexdigest(),
            'prior_llm_selection_name_match': False, 'prior_llm_selection_hash_match': False})
    prior = tmp_path / 'preserved.json'
    prior.write_text('{}')
    return {'selected': selected, 'document_count': 5, 'history_sources': [], 'code_sha256': {},
            'prior350_preservation_file': str(prior)}


def test_valid_frozen_selection(manifest):
    assert len(verify(manifest)) == 5


@pytest.mark.parametrize('mutation', ['count', 'duplicate', 'changed_source', 'changed_baseline', 'prior_overlap'])
def test_invalid_selection_fails_before_paid_stage(manifest, mutation):
    if mutation == 'count':manifest['selected'].pop()
    if mutation == 'duplicate':manifest['selected'][1] = deepcopy(manifest['selected'][0])
    if mutation == 'changed_source':Path(manifest['selected'][0]['source_path']).write_bytes(b'changed')
    if mutation == 'changed_baseline':Path(manifest['selected'][0]['baseline_mapping']).write_text('changed')
    if mutation == 'prior_overlap':manifest['selected'][0]['prior_llm_selection_hash_match'] = True
    with pytest.raises(ValueError):verify(manifest)


def test_default_cli_is_offline_and_cannot_make_paid_calls(manifest, tmp_path, monkeypatch):
    config = llm.ReviewSettings(enabled=True, api_key='test-only')
    manifest['provider'] = {name: getattr(config, name) for name in
        ('model', 'base_url', 'thinking', 'max_tokens', 'max_units', 'max_input_chars')}
    path = tmp_path / 'selection.json'
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(llm.ReviewSettings, 'from_env', classmethod(lambda cls: config))
    monkeypatch.setattr(llm, 'provider_json', lambda *a, **k: pytest.fail('Dry run made a provider request'))
    monkeypatch.setattr(sys, 'argv', ['run_hierarchical_five.py', '--manifest', str(path)])
    main()
