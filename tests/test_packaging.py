"""Catch installs that omit the source package, CLI, or agent prompts."""
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest


def test_wheel_contains_importable_package_prompts_and_cli(tmp_path):
    uv=shutil.which('uv')
    if uv is None:
        pytest.skip('uv is required for the packaging integration check')
    result=subprocess.run(
        [uv,'build','--offline','--wheel','--out-dir',str(tmp_path)],
        cwd=Path(__file__).parents[1],capture_output=True,text=True,timeout=60,
    )
    assert result.returncode==0, result.stderr
    wheels=list(tmp_path.glob('*.whl'))
    assert len(wheels)==1
    with zipfile.ZipFile(wheels[0]) as wheel:
        names=wheel.namelist()
        assert 'ai_review/cli.py' in names
        for name in ('correctness','security','tests','verifier'):
            assert f'ai_review/prompts/{name}.md' in names
        entrypoints=next(n for n in names if n.endswith('.dist-info/entry_points.txt'))
        assert 'ai-review = ai_review.cli:main' in wheel.read(entrypoints).decode()
