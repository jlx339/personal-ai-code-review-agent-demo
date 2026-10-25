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


def test_diagnostics_are_single_line_sanitized_json():
    import json
    from ai_review.report import diagnostic_summary
    r=ReviewReport('me/demo',1,'a'*40,'b'*40,errors=['API_KEY="private-literal"'])
    line=diagnostic_summary(r)
    assert '\n' not in line and 'private-literal' not in line
    assert json.loads(line)['status']=='partial'


def test_quoted_code_remains_readable_while_html_and_mentions_are_escaped():
    from ai_review.report import safe_text
    assert safe_text('`response["answer"]` and `state[\'notes\']`') == '`response["answer"]` and `state[\'notes\']`'
    assert safe_text('<script>@owner</script>') == '&lt;script&gt;＠owner&lt;/script&gt;'


def test_diagnostic_finding_contains_sanitized_evidence_for_remote_evaluation():
    import json
    from test_publish import report
    from ai_review.report import diagnostic_summary
    r = report()
    r.findings[0].impact = 'API_KEY="private-literal"'
    result = diagnostic_summary(r)
    payload = json.loads(result)['findings'][0]
    assert payload['evidence'][0]['excerpt'] == r.findings[0].evidence[0].excerpt
    assert payload['explanation'] == r.findings[0].explanation
    assert 'private-literal' not in result
