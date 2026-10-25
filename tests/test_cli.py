import json
import pytest
from ai_review.cli import main


def test_cli_help_requires_no_api_keys(capsys):
    with pytest.raises(SystemExit) as exc: main(['--help'])
    assert exc.value.code==0
    assert 'analyze' in capsys.readouterr().out


def test_publish_rejects_empty_selection_without_network(capsys,monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN','fake')
    assert main(['publish','--repository','me/demo','--run-id','42','--approved-ids',''])==1
    assert 'Select' in capsys.readouterr().err
