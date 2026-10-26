"""Development startup must load schema changes; tests never launch a server."""
import sys
from pathlib import Path
import pytest
from scripts import start_resume_inspector_local as launcher


@pytest.mark.parametrize('development', [False, True])
def test_development_watches_application_code_without_starting_provider(monkeypatch, development):
    import uvicorn
    from local_api.core import provider_env
    from local_api.services import llm_section_review
    monkeypatch.setattr(provider_env, 'load_provider_env', lambda *_: None)
    monkeypatch.setattr(llm_section_review, 'review_status', lambda: {'enabled': False, 'configured': False})
    captured = []
    monkeypatch.setattr(uvicorn, 'run', lambda *a, **kw: captured.append((a, kw)))
    monkeypatch.setattr(sys, 'argv', ['start_resume_inspector_local.py'] + (['--development'] if development else []))
    launcher.main()
    args, options = captured[0]
    assert args == ('local_api.app:app',)
    assert options['port'] == 8012
    assert options.get('reload', False) is development
    if development:
        assert options['reload_dirs'] == [str(launcher.ROOT / 'local_api')]
    else:
        assert 'reload_dirs' not in options
