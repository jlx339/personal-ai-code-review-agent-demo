import json
from ai_review.context import build_context
from ai_review.evidence import EvidenceCatalog
from ai_review.schemas import FileSnapshot, ReviewRequest, ReviewSnapshot


def snapshot(source,added):
    return ReviewSnapshot(ReviewRequest('me','repo',1),'a'*40,'b'*40,
        {'app.py':FileSnapshot('app.py',source,added_lines=added)})


def test_context_contains_complete_changed_function_and_issued_reference():
    s=snapshot('import json\n\ndef changed():\n    return 1\n\n'+('\n'*100)+'def unrelated():\n    pass\n',[4])
    c=EvidenceCatalog(s);data=json.loads(build_context(s,c))
    blocks=data['files'][0]['head_source']
    assert any('def changed()' in b['content'] and 'return 1' in b['content'] for b in blocks)
    assert not any('unrelated' in b['content'] for b in blocks)
    assert all(b['ref'] for b in blocks)


def test_context_truncation_never_exposes_a_partial_line_as_evidence():
    s=snapshot('x = 123456789\n'*100,list(range(1,101))); c=EvidenceCatalog(s)
    data=json.loads(build_context(s,c,limit=90))
    assert s.scope_notes
    for b in data['files'][0]['head_source']:
        assert b['content'].splitlines()[-1].endswith('123456789')
        assert b['end_line']-b['start_line']+1==len(b['content'].splitlines())


def test_unicode_separator_inside_a_secret_does_not_change_physical_source_lines():
    source='password="a\u2028b"\nx = 1\n'
    compile(source,'app.py','exec')
    s=snapshot(source,[1,2]);c=EvidenceCatalog(s)
    data=json.loads(build_context(s,c))
    block=data['files'][0]['head_source'][0]
    assert block['end_line']==2
    assert '2: x = 1' in block['content']
    assert 'a\u2028b' not in block['content']


def test_changed_function_context_includes_local_callers_and_callback_wiring():
    source='def changed(items):\n    return items[0]\n'+('\n'*40)+'def caller():\n    return changed([1])\n'+('\n'*40)+'graph.add_conditional_edges("source", changed)\n'
    s=snapshot(source,[2]);c=EvidenceCatalog(s)
    data=json.loads(build_context(s,c));text='\n'.join(b['content'] for b in data['files'][0]['head_source'])
    assert 'def caller()' in text
    assert 'graph.add_conditional_edges' in text
