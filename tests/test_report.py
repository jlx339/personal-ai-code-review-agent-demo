from ai_review.report import render_markdown, save_report
from ai_review.schemas import ReviewReport


def test_partial_report_does_not_claim_clean_and_masks_secrets(tmp_path):
    r=ReviewReport('me/demo',1,'a'*40,'b'*40,scope_notes=['Bandit unavailable'], errors=['API_KEY="private-literal"'])
    save_report(r,tmp_path)
    assert 'private-literal' not in (tmp_path/'report.json').read_text()
    md=render_markdown(r)
    assert 'PARTIAL' in md and 'No issues found' not in md
    assert 'Bandit unavailable' in md
    assert (tmp_path/'trace.json').is_file()
