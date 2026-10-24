import json
import pytest

from scripts.run_chunked_schema_pilot import load_scope, verify_scope_sources, ensure_new_output


def manifest(tmp_path, selected, **extra):
    path = tmp_path / 'selection.json'
    path.write_text(json.dumps({'selected': selected, 'disjoint_confirmed': True, **extra}))
    return path


def row(index):
    return {'file': f'resume-{index}.pdf', 'sha256': f'{index:064x}'}


def test_scope_requires_hash_bound_disjoint_five_to_ten_documents(tmp_path):
    selected = [row(index) for index in range(1, 6)]
    assert load_scope(manifest(tmp_path, selected)) == selected
    with pytest.raises(ValueError, match='5--10'):
        load_scope(manifest(tmp_path, selected[:4]))
    with pytest.raises(ValueError, match='disjoint'):
        path = tmp_path / 'not-disjoint.json'
        path.write_text(json.dumps({'selected': selected, 'disjoint_confirmed': False}))
        load_scope(path)


def test_scope_rejects_duplicate_filename_or_hash(tmp_path):
    selected = [row(index) for index in range(1, 6)]
    selected[-1]['sha256'] = selected[0]['sha256']
    with pytest.raises(ValueError, match='unique'):
        load_scope(manifest(tmp_path, selected))


def test_single_file_selects_exactly_one_frozen_manifest_entry(tmp_path):
    selected = [row(index) for index in range(1, 6)]
    assert load_scope(manifest(tmp_path, selected), single_file='resume-3.pdf') == [selected[2]]


def test_single_file_rejects_missing_or_duplicate_match(tmp_path):
    selected = [row(index) for index in range(1, 6)]
    path = manifest(tmp_path, selected)
    with pytest.raises(ValueError, match='not found'):
        load_scope(path, single_file='not-in-manifest.pdf')
    selected[-1] = {'file': 'resume-3.pdf', 'sha256': 'f' * 64}
    with pytest.raises(ValueError, match='multiple'):
        load_scope(manifest(tmp_path, selected), single_file='resume-3.pdf')


def test_hash_mismatch_is_rejected_before_provider_setup(tmp_path):
    selected = [row(index) for index in range(1, 6)]
    source = tmp_path / 'pdfs'; source.mkdir()
    (source / 'resume-1.pdf').write_bytes(b'changed bytes')
    scope = load_scope(manifest(tmp_path, selected), single_file='resume-1.pdf')
    with pytest.raises(ValueError, match='Missing or changed'):
        verify_scope_sources(scope, source)


def test_existing_output_directory_is_refused(tmp_path):
    output = tmp_path / 'existing-output'; output.mkdir()
    with pytest.raises(ValueError, match='new output'):
        ensure_new_output(output)
