import json
from pathlib import Path

ROOT=Path(__file__).parents[1]


def workflow(name): return json.loads((ROOT/'.github/workflows'/name).read_text())


def test_analysis_workflow_has_trusted_trigger_and_no_publish_permission():
    w=workflow('analyze.yml')
    assert 'pull_request_target' in w['on'] and 'pull_request' not in w['on']
    assert w['permissions']=={'contents':'read','pull-requests':'read'}
    j=w['jobs']['review']
    assert 'head.repo.full_name == github.repository' in j['if']
    assert "user.type != 'Bot'" in j['if']
    assert 'default_branch' in j['if']
    assert w['concurrency']['cancel-in-progress'] is True
    assert j['uses']=='./.github/workflows/review-job.yml'


def test_worker_checkout_is_pinned_and_serialized():
    w=workflow('review-job.yml');j=w['jobs']['analyze']
    assert j['timeout-minutes']==15
    assert j['concurrency']['group']=='ai-review-model-${{ github.repository }}'
    assert j['concurrency']['cancel-in-progress'] is False
    checkout=j['steps'][0]
    assert checkout['with']['ref']=='${{ github.sha }}'
    assert checkout['with']['persist-credentials'] is False
    upload=j['steps'][-1]
    assert upload['with']['retention-days']==7
    for step in j['steps']:
        if 'uses' in step: assert len(step['uses'].split('@')[1])==40
        if 'run' in step: assert '${{' not in step['run']


def test_publisher_is_manual_and_has_no_model_key():
    w=workflow('publish.yml')
    assert set(w['on'])=={'workflow_dispatch'}
    j=w['jobs']['publish']
    assert 'default_branch' in j['if']
    assert w['permissions']=={'actions':'read','contents':'read','pull-requests':'write'}
    assert j['concurrency']['cancel-in-progress'] is False
    assert 'GEMINI_API_KEY' not in json.dumps(w)
    for step in j['steps']:
        if 'run' in step: assert '${{' not in step['run']
