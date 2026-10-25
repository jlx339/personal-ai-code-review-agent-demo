import pytest
from ai_review.schemas import Finding, ReviewRequest, ReviewReport
from ai_review.config import Settings


def test_invalid_finding_rejected():
    with pytest.raises(ValueError):
        Finding(category='style', severity='high', title='x', path='x.py', start_line=0, end_line=1)


def test_repository_input_cannot_be_url_or_path():
    for owner in ['../evil', 'https://evil', 'x y']:
        with pytest.raises(ValueError):
            ReviewRequest(owner=owner, repo='demo', pr_number=1)


def test_report_round_trip():
    report = ReviewReport(repository='me/demo', pr_number=1, head_sha='a'*40, base_sha='b'*40)
    assert ReviewReport.from_json(report.to_json()).head_sha == 'a'*40
    assert report.status == 'partial'


def test_settings_prohibit_paid_model_and_invalid_budget():
    with pytest.raises(ValueError):
        Settings(model='other')
    with pytest.raises(ValueError):
        Settings(max_requests=0)
