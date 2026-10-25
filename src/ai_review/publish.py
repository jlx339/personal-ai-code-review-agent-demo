"""Deterministic manual publication of specific verified report findings."""
import io
import re
import zipfile
from ai_review.config import Settings
from ai_review.github import ApiError
from ai_review.report import safe_text
from ai_review.schemas import ReviewReport, ReviewRequest, PublishResult, safe_path
from ai_review.snapshot import parse_diff, read_file
from ai_review.redaction import redact_source


def load_verified_report(client,repository,run_id,expected_workflow):
    owner,repo=repository.split('/')
    ReviewRequest(owner,repo,1)
    if not str(run_id).isdigit():
        raise ValueError('Invalid run ID')
    prefix=f'/repos/{repository}'
    metadata=client.get(prefix)
    run=client.get(f'{prefix}/actions/runs/{run_id}')
    if (str(run['id'])!=str(run_id) or run.get('repository',{}).get('full_name')!=repository
            or run.get('event') not in ('pull_request_target','workflow_dispatch')
            or run.get('status')!='completed' or run.get('conclusion')!='success'
            or run.get('path','').split('@')[0]!=expected_workflow):
        raise ValueError('Untrusted analysis workflow run')
    artifacts=client.get(f'{prefix}/actions/runs/{run_id}/artifacts')['artifacts']
    matches=[a for a in artifacts if a['name']==f'ai-review-{run_id}']
    if len(matches)!=1 or matches[0].get('expired') or matches[0].get('size_in_bytes',2_000_001)>2_000_000:
        raise ValueError('Review artifact missing, expired, or oversized')
    raw=client.download_artifact(f"{prefix}/actions/artifacts/{int(matches[0]['id'])}/zip")
    if len(raw)>2_000_000:
        raise ValueError('Artifact archive exceeds limit')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries=archive.infolist()
        if len(entries)>10 or sum(x.file_size for x in entries)>2_000_000:
            raise ValueError('Artifact contents exceed limit')
        for entry in entries:
            safe_path(entry.filename)
            if entry.is_dir() or entry.flag_bits & 1:
                raise ValueError('Unsupported artifact entry')
        if [x.filename for x in entries].count('report.json')!=1:
            raise ValueError('Report file missing or duplicated')
        report=ReviewReport.from_json(archive.read('report.json').decode('utf-8'))
    if report.repository!=repository or report.run_id!=str(run_id):
        raise ValueError('Report identity does not match trusted run')
    default=metadata['default_branch']
    worker_path=f'{repository}/.github/workflows/review-job.yml@{report.reviewer_sha}'
    trusted_workers=[w for w in run.get('referenced_workflows',[])
        if w.get('path')==worker_path and w.get('sha')==report.reviewer_sha
        and w.get('ref')==f'refs/heads/{default}']
    if len(trusted_workers)!=1:
        raise ValueError('Trusted reviewer workflow revision not established')
    if run['event']=='pull_request_target':
        prs=[pr for pr in run.get('pull_requests',[]) if pr.get('number')==report.pr_number]
        if (len(prs)!=1 or prs[0].get('base',{}).get('ref')!=default
                or prs[0].get('head',{}).get('sha')!=report.head_sha
                or run.get('head_sha')!=report.head_sha):
            raise ValueError('PR report does not match trusted base and reviewed head')
    elif run.get('head_branch')!=default or run.get('head_sha')!=report.reviewer_sha:
        raise ValueError('Manual analysis did not run from the default branch')
    if not re.fullmatch('[a-f0-9]{20}',report.report_id):
        raise ValueError('Invalid report identifier')
    return report


def _markers(report,ids):
    return {i:f'<!-- ai-review:{report.report_id}:{i} -->' for i in ids}


def publish_selected(client,report,approved_ids):
    if not approved_ids or len(set(approved_ids))!=len(approved_ids):
        raise ValueError('Select explicit unique finding IDs')
    selected=[f for f in report.findings if f.id in approved_ids]
    if len(selected)!=len(approved_ids) or any(f.verification_status!='supported' for f in selected):
        raise ValueError('Selection includes unknown or unverified findings')
    if not re.fullmatch('[a-f0-9]{20}',report.report_id) or any(not re.fullmatch('[a-f0-9]{12}',f.id) for f in selected):
        raise ValueError('Invalid report/finding identity')
    prefix=f'/repos/{report.repository}/pulls/{report.pr_number}'
    pr=client.get(prefix)
    if (pr['head']['sha']!=report.head_sha or pr.get('state')!='open'
            or pr['head']['repo']['full_name']!=report.repository or pr['user']['type']=='Bot'):
        raise ValueError('PR changed or is outside supported scope; rerun analysis')
    markers=_markers(report,approved_ids)
    reviews=client.pages(prefix+'/reviews')
    def trusted_review(r):
        return (r.get('user',{}).get('login')=='github-actions[bot]'
            and r.get('user',{}).get('type')=='Bot' and r.get('commit_id')==report.head_sha)
    bodies='\n'.join(r.get('body') or '' for r in reviews if trusted_review(r))
    remaining=[f for f in selected if markers[f.id] not in bodies]
    if not remaining:
        return PublishResult('skipped',reason='Selected findings already published')
    files=client.pages(prefix+'/files')
    patches={f['filename']:f.get('patch') for f in files}
    previous_paths={f['filename']:f.get('previous_filename') or f['filename'] for f in files}
    comments=[]
    summaries=[]
    source_cache={}
    for f in remaining:
        if f.path not in patches or not patches[f.path]:
            raise ValueError('Selected finding has no complete patch')
        added,removed,anchors=parse_diff(patches[f.path])
        relevant=removed if f.source=='base' else added+anchors
        if not any(f.start_line<=n<=f.end_line for n in relevant):
            raise ValueError('Selected finding is unrelated to changed source')
        if not f.evidence:
            raise ValueError('Selected finding lacks evidence')
        for e in f.evidence:
            cache_key=(e.path,e.source)
            if cache_key not in source_cache:
                path=previous_paths.get(e.path,e.path) if e.source=='base' else e.path
                ref=report.base_sha if e.source=='base' else report.head_sha
                source_cache[cache_key]=redact_source(read_file(client,report.repository,path,ref,Settings())).splitlines()
            lines=source_cache[cache_key]
            if e.end_line>len(lines) or '\n'.join(lines[e.start_line-1:e.end_line])!=redact_source(e.excerpt):
                raise ValueError('Selected finding evidence no longer matches')
        if not any(e.path==f.path and (e.source=='base')==(f.source=='base') and e.start_line<=f.start_line<=f.end_line<=e.end_line for e in f.evidence):
            raise ValueError('Selected finding lacks anchor evidence')
        body=f'**[AI review · {f.severity.upper()} / {f.category}] {safe_text(f.title)}**\n\n{safe_text(f.explanation)}\n\nImpact: {safe_text(f.impact)}\n\nPreconditions: {safe_text(f.preconditions)}\n\nSuggested fix or test: {safe_text(f.suggestion)}\n\n_AI-generated; selected for publication by the repository owner._'
        if f.source=='head' and f.inline_eligible and f.category!='tests' and f.start_line in added:
            comments.append(dict(path=f.path,line=f.start_line,side='RIGHT',body=body))
        else:
            summaries.append(f'{safe_text(f.path)}:{f.start_line}\n\n{body}')
    # Recheck after all remote reads; commit_id also binds the eventual review.
    if client.get(prefix)['head']['sha']!=report.head_sha:
        raise ValueError('PR changed during publication')
    posted_ids=[f.id for f in remaining]
    body='AI review: findings selected by the repository owner.\n\n'+'\n'.join(markers[i] for i in posted_ids)
    body+='\n\n'+'\n\n'.join(summaries)
    payload=dict(commit_id=report.head_sha,event='COMMENT',body=body)
    if comments:
        payload['comments']=comments
    try:
        response=client.request('POST',prefix+'/reviews',payload)
        return PublishResult('posted',response['id'],posted_ids)
    except ApiError:
        # Reconcile an ambiguous write; never blindly send a second review.
        reviews=client.pages(prefix+'/reviews')
        for r in reviews:
            if trusted_review(r) and all(markers[i] in (r.get('body') or '') for i in posted_ids):
                return PublishResult('posted',r['id'],posted_ids,reason='Reconciled after uncertain API outcome')
        raise ValueError('Publication outcome uncertain; inspect PR reviews before retrying') from None
