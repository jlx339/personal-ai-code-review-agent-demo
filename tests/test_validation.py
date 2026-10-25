from ai_review.validation import validate_findings
from ai_review.schemas import Finding, Evidence, FileSnapshot, ReviewSnapshot, ReviewRequest


def snapshot():
    return ReviewSnapshot(ReviewRequest('me','demo',1),'b'*40,'a'*40,
        {'app.py':FileSnapshot('app.py','x=1\nx=1\n','',[2])})


def finding(line=2,category='correctness'):
    return Finding(category,'high','Bad arithmetic','app.py',line,line,
        [Evidence('app.py',line,line,'x=1')],impact='Wrong result',explanation='Concrete bug')


def test_exact_line_identity_and_added_anchor():
    out=validate_findings(snapshot(),[finding()])
    assert len(out.retained)==1 and out.retained[0].inline_eligible
    assert not out.retained[0].verification_status=='supported'
    assert validate_findings(snapshot(),[finding(1)]).rejected


def test_invalid_evidence_and_unknown_path_rejected():
    f=finding();f.evidence[0].excerpt='invented'
    assert not validate_findings(snapshot(),[f]).retained
    f=finding();f.path='missing.py'
    assert not validate_findings(snapshot(),[f]).retained


def test_same_line_distinct_issues_retained_and_duplicates_removed():
    f=finding(); g=finding();g.title='Different failure'
    out=validate_findings(snapshot(),[f,finding(),g])
    assert len(out.retained)==2
    assert len(set(x.id for x in out.retained))==2


def test_test_gap_is_report_only():
    f=finding(category='tests')
    out=validate_findings(snapshot(),[f])
    assert not out.retained[0].inline_eligible


def test_deleted_authorization_guard_survives_as_base_side_report_finding():
    s=snapshot()
    f=s.files['app.py']
    f.content='def f(user):\n    return secret\n'
    f.added_lines=[]
    f.base_content='def f(user):\n    authorize(user)\n    return secret\n'
    f.removed_lines=[2]
    issue=Finding('security','high','Authorization removed','app.py',2,2,
        [Evidence('app.py',2,2,'    authorize(user)',source='base')],
        impact='Unauthorized data access',explanation='Guard was removed',source='base')
    out=validate_findings(s,[issue])
    assert len(out.retained)==1
    assert not out.retained[0].inline_eligible


def test_rejected_evidence_identifies_the_source_range_and_reason():
    f=finding();f.evidence[0].excerpt='invented'
    reason=validate_findings(snapshot(),[f]).rejected[0]
    assert 'app.py:2' in reason and 'excerpt' in reason.lower()
