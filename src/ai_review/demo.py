"""Prepare an explicitly synthetic demo branch without changing the checkout."""
import os
from pathlib import Path
import subprocess
import tempfile
from ai_review.schemas import safe_path


def create_demo_branch(repo: Path, variant: Path, target: str) -> str:
    safe_path(target)
    ref='refs/heads/demo/review-sample'
    def git(*args,env=None,input=None):
        return subprocess.run(['git','-C',str(repo),*args],env=env,input=input,
            capture_output=True,text=True,check=True).stdout.strip()
    exists=subprocess.run(['git','-C',str(repo),'show-ref','--verify','--quiet',ref])
    if exists.returncode==0:
        raise ValueError('Demo branch already exists; it will not be overwritten')
    base=git('rev-parse','HEAD')
    content=variant.read_text()
    blob=git('hash-object','-w','--stdin',input=content)
    with tempfile.TemporaryDirectory(prefix='ai-review-index-') as directory:
        env={**os.environ,'GIT_INDEX_FILE':str(Path(directory)/'index')}
        git('read-tree',base,env=env)
        git('update-index','--add','--cacheinfo',f'100644,{blob},{target}',env=env)
        tree=git('write-tree',env=env)
        commit=git('commit-tree',tree,'-p',base,'-m','demo: introduce deliberate review findings',env=env)
    git('update-ref',ref,commit,'0'*40)
    return commit


if __name__=='__main__':
    root=Path(__file__).resolve().parents[2]
    sha=create_demo_branch(root,root/'examples/demo-change/assistant.py.txt','examples/assistant.py')
    print(f'Prepared demo/review-sample at {sha}. Working files are unchanged.')
