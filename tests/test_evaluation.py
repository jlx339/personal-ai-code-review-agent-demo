from ai_review.evaluation import evaluate
from ai_review.schemas import ReviewReport
from test_publish import report


def test_scoring_records_human_labels_and_unmatched_misses():
    r=report()
    expected=[{'id':'known-bug','severity':'high'},{'id':'second-bug','severity':'critical'}]
    labels={'aabbccddeeff':{'expected_id':'known-bug','actionable':True}}
    metrics=evaluate(r,expected,labels)
    assert metrics['actionable_precision']==1.0
    assert metrics['high_critical_recall']==0.5
    assert metrics['missed_issue_ids']==['second-bug']


def test_undefined_metrics_and_missing_labels_are_explicit():
    r=ReviewReport('me/demo',1,'a'*40,'b'*40)
    metrics=evaluate(r,[],{})
    assert metrics['actionable_precision'] is None
    assert metrics['high_critical_recall'] is None
    metrics=evaluate(report(),[],{})
    assert metrics['unlabeled_finding_ids']==['aabbccddeeff']
    assert metrics['actionable_precision'] is None
