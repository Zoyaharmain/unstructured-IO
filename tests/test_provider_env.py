"""The local launcher reads provider settings without executing .env content."""
from local_api.core.provider_env import load_provider_env


def test_private_settings_and_process_precedence(tmp_path, monkeypatch):
    monkeypatch.setenv('DEEPSEEK_MODEL', 'process-model')
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    monkeypatch.delenv('DEEPSEEK_REVIEW_ENABLED', raising=False)
    monkeypatch.delenv('OTHER_SETTING', raising=False)
    path = tmp_path / '.env'
    path.write_text('export DEEPSEEK_API_KEY="private-test-value"\nDEEPSEEK_MODEL=file-model\nDEEPSEEK_REVIEW_ENABLED=true # enabled\nOTHER_SETTING=ignored\n')
    load_provider_env(path)
    import os
    assert os.environ['DEEPSEEK_API_KEY'] == 'private-test-value'
    assert os.environ['DEEPSEEK_MODEL'] == 'process-model'
    assert os.environ['DEEPSEEK_REVIEW_ENABLED'] == 'true'
    assert 'OTHER_SETTING' not in os.environ
    # The loader itself does not print private configuration.
    monkeypatch.delenv('DEEPSEEK_API_KEY')
    monkeypatch.delenv('DEEPSEEK_REVIEW_ENABLED')


def test_env_content_is_not_executed(tmp_path, monkeypatch):
    marker = tmp_path / 'must-not-exist'
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    path = tmp_path / '.env'
    path.write_text(f'DEEPSEEK_API_KEY=$(touch {marker})\n')
    load_provider_env(path)
    assert not marker.exists()
    monkeypatch.delenv('DEEPSEEK_API_KEY')


def test_absent_env_is_allowed(tmp_path):
    load_provider_env(tmp_path / 'missing.env')
