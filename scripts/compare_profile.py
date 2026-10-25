"""Read-only diagnostic experiment; probe once before spending review requests."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

from ai_review.config import Settings


def main():
    config=json.loads(Path('evals/profile-run.json').read_text())
    Settings(reasoning_model=config['model'],reasoning_thinking=config['thinking'])
    prs=config['prs']
    if not isinstance(prs,list) or not 1<=len(prs)<=3 or any(type(n) is not int or n<1 for n in prs):
        raise ValueError('Select one to three explicit PR numbers')
    root=Path('reports/profile');root.mkdir(parents=True,exist_ok=True)
    body={'contents':[{'role':'user','parts':[{'text':'Reply only OK.'}]}],
        'generationConfig':{'maxOutputTokens':1024,'thinkingConfig':{'thinkingLevel':'LOW'}}}
    request=urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{config['model']}:generateContent",
        data=json.dumps(body).encode(),headers={'Content-Type':'application/json',
            'x-goog-api-key':os.environ['GEMINI_API_KEY']},method='POST')
    started=time.monotonic()
    probe={'model':config['model'],'attempts':1,'timeout_seconds':90,'available':False}
    try:
        with urllib.request.urlopen(request,timeout=90) as response:
            raw=response.read(1000001)
            if len(raw)>1000000:
                raise ValueError('Probe response oversized')
            data=json.loads(raw)
            candidate=data.get('candidates',[{}])[0]
            probe.update(http_status=response.status,finish_reason=candidate.get('finishReason'),
                available=candidate.get('finishReason')=='STOP')
    except urllib.error.HTTPError as exc:
        probe.update(http_status=exc.code,error_kind='http')
    except (urllib.error.URLError,TimeoutError) as exc:
        timed_out=isinstance(exc,TimeoutError) or isinstance(getattr(exc,'reason',None),TimeoutError)
        probe.update(error_kind='timeout' if timed_out else 'connection')
    except (ValueError,KeyError,IndexError,TypeError):
        probe.update(error_kind='invalid_response')
    probe['elapsed_seconds']=round(time.monotonic()-started,2)
    (root/'probe.json').write_text(json.dumps(probe,indent=2)+'\n')
    print('MODEL_ENDPOINT_PROBE='+json.dumps(probe),flush=True)
    if not probe['available']:
        print('Comparison stopped after one failed probe; no quality score or publication.')
        return 0
    for number in prs:
        print(f'PROFILE_REVIEW_START={number}',flush=True)
        result=subprocess.run([sys.executable,'-m','ai_review.cli','analyze',
            '--repository',os.environ['GITHUB_REPOSITORY'],'--pr',str(number),
            '--reasoning-model',config['model'],'--reasoning-thinking',config['thinking'],
            '--output',str(root/f'pr-{number}')],shell=False)
        if result.returncode:
            print(f'PROFILE_REVIEW_STOPPED={number}',flush=True)
            return result.returncode
    return 0


if __name__=='__main__':
    sys.exit(main())
