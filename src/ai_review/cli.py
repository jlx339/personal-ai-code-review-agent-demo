"""Command-line entrypoints for analysis and selected publication."""
import argparse
from dataclasses import asdict
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
from ai_review.config import Settings
from ai_review.github import GitHubClient
from ai_review.schemas import ReviewRequest
from ai_review.redaction import redact_source


def main(argv=None):
    parser=argparse.ArgumentParser(description='Review Python AI PRs; publish only selected findings.')
    commands=parser.add_subparsers(dest='command',required=True)
    analyze=commands.add_parser('analyze')
    analyze.add_argument('--repository',default=os.environ.get('GITHUB_REPOSITORY'),required=not bool(os.environ.get('GITHUB_REPOSITORY')))
    analyze.add_argument('--pr',type=int,required=True)
    analyze.add_argument('--output',type=Path,default=Path('reports/current'))
    analyze.add_argument('--prompt-key',action='store_true',help='Read Gemini key privately without saving it')
    analyze.add_argument('--reasoning-model',choices=['gemini-3.5-flash-lite','gemini-3.6-flash','gemini-3.8-flash'],
        default=os.environ.get('AI_REVIEW_REASONING_MODEL','gemini-3.5-flash-lite'),
        help='Free-tier allowlisted model for correctness and verification; quotas differ')
    publish=commands.add_parser('publish')
    publish.add_argument('--repository',default=os.environ.get('GITHUB_REPOSITORY'),required=not bool(os.environ.get('GITHUB_REPOSITORY')))
    publish.add_argument('--run-id',required=True)
    publish.add_argument('--approved-ids',required=True)
    args=parser.parse_args(argv)
    try:
        owner,repo=args.repository.split('/')
        client=GitHubClient(os.environ.get('GITHUB_TOKEN',''))
        if args.command=='publish':
            ids=[x.strip() for x in args.approved_ids.split(',') if x.strip()]
            if not ids:
                raise ValueError('Select explicit finding IDs before publication')
            if not client.token:
                raise ValueError('GITHUB_TOKEN is required for publication')
            from ai_review.publish import load_verified_report,publish_selected
            if os.environ.get('GITHUB_ACTIONS')=='true':
                default=client.get(f'/repos/{owner}/{repo}')['default_branch']
                if os.environ.get('GITHUB_REF')!=f'refs/heads/{default}':
                    raise ValueError('Publish must run from the default branch')
            report=load_verified_report(client,args.repository,args.run_id,'.github/workflows/analyze.yml')
            result=publish_selected(client,report,ids)
            print(json.dumps(asdict(result)))
        else:
            request=ReviewRequest(owner,repo,args.pr)
            settings=Settings(reasoning_model=args.reasoning_model)
            key=os.environ.get('GEMINI_API_KEY','')
            if not key and args.prompt_key:
                key=getpass.getpass('Gemini API key (hidden; not saved): ')
            from ai_review.budget import RequestBudget
            from ai_review.model import ReviewModel
            from ai_review.snapshot import fetch_snapshot
            from ai_review.tools import SnapshotTools
            from ai_review.graph import run_analysis
            from ai_review.report import save_report, diagnostic_summary
            model=ReviewModel(key,settings,RequestBudget(settings))
            snapshot=fetch_snapshot(client,request,settings)
            sha=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
            metadata={'reviewer_sha':sha,'run_id':os.environ.get('GITHUB_RUN_ID','local')}
            report=run_analysis(snapshot,model,SnapshotTools(snapshot,client,settings),settings,metadata)
            save_report(report,args.output)
            print('AI_REVIEW_DIAGNOSTICS='+diagnostic_summary(report))
            print(f'Review {report.status}: {len(report.findings)} candidates. Report: {args.output / "report.md"}')
            summary=os.environ.get('GITHUB_STEP_SUMMARY')
            if summary:
                with open(summary,'a') as f:
                    f.write((args.output/'report.md').read_text())
        return 0
    except (ValueError,RuntimeError,KeyError,OSError,subprocess.CalledProcessError) as exc:
        print('Review stopped: '+redact_source(str(exc)),file=sys.stderr)
        return 1


if __name__=='__main__':
    sys.exit(main())
