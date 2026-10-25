import json
from ai_review.agents import ReviewSession
from ai_review.model import ModelResult
from ai_review.config import Settings
from ai_review.tools import SnapshotTools
from ai_review.schemas import ReviewSnapshot, ReviewRequest, FileSnapshot


class ScriptedModel:
    def __init__(self,responses): self.responses=iter(responses)
    def invoke(self,*args,**kwargs):
        response=next(self.responses)
        if isinstance(response,Exception): raise response
        return response


def text(value): return ModelResult({'role':'model','parts':[{'text':value}]},value)


def tool():
    call={'name':'inspect_python','args':{'path':'app.py'}}
    return ModelResult({'role':'model','parts':[{'functionCall':call}]},tool_calls=[call])


def session(responses):
    s=ReviewSnapshot(ReviewRequest('me','demo',1),'b'*40,'a'*40, {'app.py':FileSnapshot('app.py','x=1\n','@@ -0,0 +1 @@\n+x=1',[1])})
    return ReviewSession(s,ScriptedModel(responses),SnapshotTools(s,None,Settings()),Settings(),{})


def test_specialist_uses_tool_and_records_outcome():
    s=session([tool(),text('{"findings":[]}')])
    s.review('correctness')
    assert s.checks['correctness']['status']=='complete'
    assert s.tools.events[0]['tool']=='inspect_python'


def test_malformed_output_repairs_once_and_preserves_partial():
    s=session([tool(),text('bad'),text('still bad')])
    s.review('correctness')
    assert s.checks['correctness']['status']=='partial'
    assert s.errors


def test_failure_does_not_erase_other_reviewer_results():
    s=session([RuntimeError('model failure'),tool(),text('{"findings":[]}')])
    s.review('correctness')
    s.review('tests')
    assert s.checks['correctness']['status']=='partial'
    assert s.checks['tests']['status']=='complete'
    assert s.finish().status=='partial'


def test_unapproved_tool_is_rejected():
    s=session([])
    assert not s.tools.dispatch('run_shell', {'cmd':'anything'}).ok


def test_no_findings_without_tool_is_not_clean():
    s=session([text('{"findings":[]}')]*3)
    s.review('correctness')
    assert s.checks['correctness']['status']=='partial'


def test_early_empty_answer_gets_an_investigation_chance_before_finishing():
    s = session([text('{"findings":[]}'), tool(), text('{"findings":[]}')])
    s.review('correctness')
    assert s.checks['correctness']['status'] == 'complete'
    assert s.tools.events[0]['tool'] == 'inspect_python'


def test_installed_langgraph_runs_the_full_node_sequence():
    import pytest
    pytest.importorskip('langgraph',reason='Install project dependencies to verify the real LangGraph adapter')
    from ai_review.graph import build_review_graph
    from ai_review.schemas import ToolResult
    s=session([tool(),text('{"findings":[]}')]*3)
    s.tools.scan_security=lambda paths:ToolResult(True,[])
    result=build_review_graph(s.model,s.tools,s.settings).invoke({'completed':[]})
    assert result['completed']==['static_analysis','correctness','security','tests','validate','verify']
    assert result['report'].status=='complete'


def test_model_failure_reason_is_visible_without_raw_response():
    from ai_review.model import ModelError
    s=session([ModelError('Model request failed (HTTP 400)')])
    s.review('correctness')
    assert 'HTTP 400' in s.errors[0]


def test_final_output_schema_is_bound_to_each_reviewers_category():
    s=session([tool(),tool(),text('{"findings":[]}')])
    original=s.model.invoke
    schemas=[]
    def invoke(*args,**kwargs):
        if kwargs.get('response_schema'):
            schemas.append(kwargs['response_schema'])
        return original(*args,**kwargs)
    s.model.invoke=invoke
    s.review('tests')
    assert schemas[0]['properties']['findings']['items']['properties']['category']['enum']==['tests']


def test_verifier_corrects_category_and_updates_publication_identity():
    from test_validation import finding, snapshot
    from ai_review.validation import validate_findings
    issue = validate_findings(snapshot(), [finding()]).retained[0]
    old_id = issue.id
    s = session([text(json.dumps({'decisions': [{'id': old_id, 'status': 'supported',
        'category': 'security', 'reason': 'Unauthorized access is a security impact'}]}))])
    s.snapshot = snapshot()
    s.findings = [issue]
    s.verify()
    assert issue.category == 'security'
    assert issue.id != old_id
    assert issue.verification_status == 'supported'
    assert s.checks['verifier']['status'] == 'complete'


def test_invalid_verifier_category_cannot_make_a_candidate_publishable():
    from test_validation import finding, snapshot
    from ai_review.validation import validate_findings
    issue = validate_findings(snapshot(), [finding()]).retained[0]
    s = session([text(json.dumps({'decisions': [{'id': issue.id, 'status': 'supported',
        'category': 'made-up', 'reason': 'Claimed support'}]}))])
    s.findings = [issue]
    s.verify()
    assert issue.verification_status == 'unverified'
    assert s.checks['verifier']['status'] == 'partial'


def test_category_correction_merges_duplicate_findings_without_breaking_report():
    from test_validation import finding, snapshot
    from ai_review.validation import validate_findings
    issues = validate_findings(snapshot(), [finding(), finding(category='security')]).retained
    decisions = [{'id': f.id, 'status': 'supported', 'category': 'security',
        'reason': 'Same source issue'} for f in issues]
    s = session([text(json.dumps({'decisions': decisions}))])
    s.snapshot = snapshot()
    s.findings = issues
    s.verify()
    report = s.finish()
    assert len(report.findings) == 1
    assert report.findings[0].verification_status == 'supported'


def test_prompt_context_truncation_is_visible_in_final_report():
    s = session([])
    s.snapshot.files['app.py'].content = 'x = 1\n' * 6000
    s.context()
    s.context()
    for name in ('correctness', 'security', 'tests', 'verifier', 'static_analysis'):
        s.checks[name] = {'status': 'complete'}
    report = s.finish()
    assert report.status == 'partial'
    assert report.scope_notes == ['Prompt source context truncated: app.py']


def test_verifier_category_promotion_restores_valid_inline_anchor():
    from test_validation import finding, snapshot
    from ai_review.validation import validate_findings
    issue = validate_findings(snapshot(), [finding(category='tests')]).retained[0]
    s = session([text(json.dumps({'decisions': [{'id': issue.id, 'status': 'supported',
        'category': 'correctness', 'reason': 'Functional defect rather than missing coverage'}]}))])
    s.snapshot = snapshot()
    s.findings = [issue]
    s.verify()
    assert issue.category == 'correctness'
    assert issue.inline_eligible
