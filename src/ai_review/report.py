"""Human-readable report plus sanitized structured artifacts."""
from dataclasses import asdict
from pathlib import Path
import html
import json
from ai_review.redaction import redact_source
from ai_review.schemas import SEVERITIES


def safe_text(text):
    return html.escape(redact_source(str(text)),quote=False).replace('@','＠')


def render_markdown(report):
    lines=[f'# AI review: {safe_text(report.repository)} PR {report.pr_number}',
        f'**Status: {report.status.upper()}**', f'Reviewed commit: `{report.head_sha}`',
        'AI-generated suggestions require human verification. No reviewed code was executed.',
        f'Model requests: {report.usage.get("requests", "unknown")}', '## Checks']
    for name,check in report.checks.items():
        lines.append(f'- {safe_text(name)}: {safe_text(check.get("status"))} — {safe_text(check.get("detail",""))}')
    if report.scope_notes or report.errors:
        lines.append('## Incomplete checks and scope notes')
        lines.extend('- '+safe_text(x) for x in report.scope_notes+report.errors)
    lines.append('## Prioritized findings')
    findings=sorted(report.findings,key=lambda f:(SEVERITIES.index(f.severity),f.path,f.start_line,f.id))
    for f in findings:
        lines.extend([f'### {f.severity.upper()} · {safe_text(f.title)}',
            f'ID `{f.id}` · {f.category} · {f.verification_status} · {safe_text(f.path)}:{f.start_line} ({f.source})',
            safe_text(f.explanation),f'Impact: {safe_text(f.impact)}',
            f'Preconditions: {safe_text(f.preconditions or "Not established")}',
            f'Suggested fix or test: {safe_text(f.suggestion or "Inspect the affected behavior")}',
            'Evidence:'])
        lines.extend(f'- {safe_text(e.path)}:{e.start_line}–{e.end_line} ({e.source}): {safe_text(e.excerpt)}' for e in f.evidence)
    if not findings:
        lines.append('No actionable findings reported.' if report.status=='complete' else 'No findings available; analysis is incomplete.')
    return '\n\n'.join(lines)+'\n'


def sanitize(value):
    if isinstance(value,str):
        return redact_source(value)
    if isinstance(value,dict):
        return {k:sanitize(v) for k,v in value.items()}
    if isinstance(value,list):
        return [sanitize(x) for x in value]
    return value


def save_report(report,output_dir:Path):
    output_dir.mkdir(parents=True,exist_ok=True)
    payload=sanitize(asdict(report))
    (output_dir/'report.json').write_text(json.dumps(payload,indent=2)+'\n')
    (output_dir/'report.md').write_text(render_markdown(report))
    (output_dir/'trace.json').write_text(json.dumps(sanitize(report.trace),indent=2)+'\n')


def diagnostic_summary(report):
    """One-line sanitized status for remote troubleshooting without raw messages."""
    return json.dumps(sanitize(dict(status=report.status,checks=report.checks,errors=report.errors,
        scope_notes=report.scope_notes,usage=report.usage,findings=[dict(id=f.id,
        title=f.title,category=f.category,severity=f.severity,source=f.source,path=f.path,
        line=f.start_line,verification=f.verification_status) for f in report.findings])))
