import json
from unittest.mock import patch
from ai_review.tools import SnapshotTools
from ai_review.redaction import redact_source
from ai_review.schemas import ReviewSnapshot, ReviewRequest, FileSnapshot
from ai_review.config import Settings


def tools(content='x = 1\nprint(x)\n'):
    s = ReviewSnapshot(ReviewRequest('me','demo',1),'b'*40,'a'*40, {'app.py':FileSnapshot('app.py',content)})
    return SnapshotTools(s, None, Settings())


def test_read_and_search_are_bounded_and_reject_traversal():
    t=tools()
    assert t.read_source('app.py',2,2).data['content'] == 'print(x)'
    assert not t.read_source('../secret',1,2).ok
    assert t.search_source('print', ['app.py']).data[0]['line'] == 2
    assert not t.read_source('app.py',0,9).ok


def test_redaction_preserves_lines_and_masks_secret():
    value='API_KEY = "sk-prod-test-secret-12345678"\nprint("safe")\n'
    redacted=redact_source(value)
    assert 'sk-prod' not in redacted
    assert redacted.count('\n') == 2
    assert 'print("safe")' in redacted


def test_syntax_inspection_does_not_execute_code():
    result=tools('raise RuntimeError("never execute")\n').inspect_python('app.py')
    assert result.ok
    assert not tools('def broken(').inspect_python('app.py').ok


def test_scanner_is_fixed_command_and_missing_tool_is_partial():
    with patch('ai_review.tools.subprocess.run', side_effect=FileNotFoundError):
        result=tools().scan_security(['app.py'])
    assert not result.ok and 'unavailable' in result.error
    with patch('ai_review.tools.subprocess.run') as run:
        run.return_value.returncode=0
        def execute(*args, **kwargs):
            kwargs['stdout'].write(json.dumps({'results':[], 'errors':[]}))
            return run.return_value
        run.side_effect=execute
        run.return_value.stderr=''
        result=tools().scan_security(['app.py'])
        assert result.ok and result.data == []
        assert run.call_args.kwargs['shell'] is False
        assert run.call_args.kwargs['timeout'] == 30
        assert isinstance(run.call_args.args[0], list)


def test_partial_reads_and_search_do_not_leak_private_key_interior():
    t=tools('KEY = """-----BEGIN PRIVATE KEY-----\nTOP_SECRET_BASE64_MATERIAL\n-----END PRIVATE KEY-----"""\n')
    assert 'TOP_SECRET' not in str(t.read_source('app.py',2,2).data)
    assert 'TOP_SECRET' not in str(t.search_source('TOP_SECRET',['app.py']).data)


def test_large_syntax_inventory_marks_incomplete_output():
    t=tools('\n'.join(f'def f{i}(): pass' for i in range(101)))
    assert t.inspect_python('app.py').truncated


def test_read_source_can_request_a_window_larger_than_short_file():
    result=tools('x=1\n').read_source('app.py',1,100)
    assert result.ok
    assert result.data['content']=='x=1'
    assert result.data['end_line']==1


def test_search_accepts_a_bounded_test_directory():
    t=tools()
    t.snapshot.files['tests/test_app.py']=FileSnapshot('tests/test_app.py','def test_parse_answer(): pass\n',changed=False)
    result=t.search_source('parse_answer',['tests/'])
    assert result.ok
    assert result.data==[{'path':'tests/test_app.py','line':1,'content':'def test_parse_answer(): pass'}]


def test_static_scan_limit_marks_report_scope_incomplete():
    from types import SimpleNamespace
    def execute(command, **kwargs):
        kwargs['stdout'].write(json.dumps({'errors': [], 'results': [
            {'filename': command[-1], 'line_number': 1, 'test_id': 'B101',
             'issue_severity': 'LOW', 'issue_text': 'assert used'} for _ in range(51)]}))
        return SimpleNamespace(returncode=1)
    t = tools()
    with patch('ai_review.tools.subprocess.run', side_effect=execute):
        result = t.dispatch('scan_security', {'paths': ['app.py']})
    assert len(result.data) == 50
    assert result.truncated
    assert t.failures == ['scan_security: output truncated']


def test_source_reads_issue_references_bound_to_the_delivered_window():
    t=tools();result=t.read_source('app.py',2,2)
    from test_evidence import candidate
    f=t.evidence.resolve(candidate(result.data['ref']))
    assert f.evidence[0].excerpt=='print(x)'
