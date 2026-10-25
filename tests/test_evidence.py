import pytest
from ai_review.evidence import EvidenceCatalog
from ai_review.schemas import FileSnapshot, ReviewRequest, ReviewSnapshot


def catalog():
    snap=ReviewSnapshot(ReviewRequest('me','repo',1),'a'*40,'b'*40,
        {'app.py':FileSnapshot('app.py','def f():\n    return 1\nAPI_KEY="private-value"\n',added_lines=[2])})
    return EvidenceCatalog(snap)


def candidate(ref):
    return dict(category='correctness',severity='high',title='Wrong result',
        evidence=[dict(ref=ref,start_line=2,end_line=2)],impact='Wrong answer',
        preconditions='Function called',explanation='Returns the wrong value',suggestion='Return the intended result')


def test_references_build_exact_source_without_model_quotations():
    c=catalog(); block=c.register('app.py','head',1,3)
    f=c.resolve(candidate(block['ref']))
    assert f.path=='app.py' and f.start_line==2
    assert f.evidence[0].excerpt=='    return 1'
    assert 'private-value' not in block['content']


def test_unknown_and_outside_delivered_reference_ranges_are_rejected():
    c=catalog()
    with pytest.raises(ValueError,match='Unknown source reference'): c.resolve(candidate('invented'))
    block=c.register('app.py','head',1,1)
    with pytest.raises(ValueError,match='outside delivered'): c.resolve(candidate(block['ref']))


def test_model_cannot_supply_its_own_quote_or_publication_flags():
    c=catalog(); raw=candidate(c.register('app.py','head',1,3)['ref'])
    raw['evidence'][0]['excerpt']='invented'
    with pytest.raises(ValueError): c.resolve(raw)
    raw=candidate(c.register('app.py','head',1,3)['ref']);raw['verification_status']='supported'
    with pytest.raises(ValueError): c.resolve(raw)


def test_evidence_ending_in_a_blank_line_preserves_that_line():
    c=catalog();c.snapshot.files['app.py'].content='def f():\n    return 1\n\nnext_value=2\n'
    raw=candidate(c.register('app.py','head',1,3)['ref'])
    raw['evidence'][0]['end_line']=3
    assert c.resolve(raw).evidence[0].excerpt=='    return 1\n'


def test_unicode_separator_in_a_string_keeps_github_line_numbers():
    c=catalog();c.snapshot.files['app.py'].content='text="a\u2028b"\nx=1\n'
    ref=c.register('app.py','head',1,2)['ref']
    assert c.resolve(candidate(ref)).evidence[0].excerpt=='x=1'
