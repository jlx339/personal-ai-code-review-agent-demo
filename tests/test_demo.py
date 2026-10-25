"""Check that preparing a demo branch cannot overwrite the developer's files."""
from pathlib import Path
import subprocess

import pytest
from ai_review.demo import create_demo_branch


def git(repo,*args):
    return subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True,text=True).stdout.strip()


def test_demo_branch_preserves_checkout_and_refuses_overwrite(tmp_path):
    git(tmp_path,'init','-b','main')
    git(tmp_path,'config','user.name','Demo Test')
    git(tmp_path,'config','user.email','demo@example.invalid')
    (tmp_path/'assistant.py').write_text('answer = "safe"\n')
    git(tmp_path,'add','assistant.py')
    git(tmp_path,'commit','-m','baseline')
    base=git(tmp_path,'rev-parse','HEAD')
    variant=tmp_path/'variant.txt'
    variant.write_text('answer = "demo"\n')
    sha=create_demo_branch(tmp_path,variant,'assistant.py')
    assert git(tmp_path,'rev-parse','HEAD')==base
    assert git(tmp_path,'branch','--show-current')=='main'
    assert (tmp_path/'assistant.py').read_text()=='answer = "safe"\n'
    assert git(tmp_path,'show',f'{sha}:assistant.py')=='answer = "demo"'
    assert git(tmp_path,'rev-parse',f'{sha}^')==base
    with pytest.raises(ValueError,match='already exists'):
        create_demo_branch(tmp_path,variant,'assistant.py')
