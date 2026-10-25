import base64
import pytest
from ai_review.github import GitHubClient, ApiError
from ai_review.snapshot import fetch_snapshot, parse_added_lines
from ai_review.schemas import ReviewRequest
from ai_review.config import Settings

SHA = 'a'*40
PATCH = '@@ -1 +1,2 @@\n-x = 1\n+x = 2\n+print(x)'


class FakeGitHub:
    def __init__(self, files=None, content='x = 2\nprint(x)\n'):
        self.files = files if files is not None else [dict(filename='app.py', status='modified', patch=PATCH, additions=2, deletions=1)]
        self.content = content
    def get(self, path):
        if '/contents/' in path:
            return dict(type='file', encoding='base64', content=base64.b64encode(self.content.encode()).decode(), size=len(self.content))
        if '/git/trees/' in path:
            return dict(truncated=False, tree=[])
        return dict(base=dict(sha='b'*40, repo=dict(full_name='me/demo')), head=dict(sha=SHA, repo=dict(full_name='me/demo')), user=dict(type='User'), state='open')
    def pages(self, path):
        return self.files


def test_diff_lines_are_not_invented():
    assert parse_added_lines(PATCH) == [1, 2]
    with pytest.raises(ValueError):
        parse_added_lines('@@ -1 +1 @@\n+extra\n+oops')


def test_snapshot_scope_and_pinned_head():
    s = fetch_snapshot(FakeGitHub(), ReviewRequest('me','demo',1), Settings())
    assert s.head_sha == SHA
    assert s.files['app.py'].added_lines == [1,2]


def test_missing_patch_and_removed_files_are_visible():
    f = [dict(filename='gone.py', status='removed'), dict(filename='app.py',status='modified')]
    s = fetch_snapshot(FakeGitHub(f), ReviewRequest('me','demo',1), Settings())
    assert len(s.scope_notes) == 2
    assert not s.files['app.py'].patch_available


def test_limits_and_symlinks_are_not_silently_clean():
    s = fetch_snapshot(FakeGitHub(content='x'*65537), ReviewRequest('me','demo',1), Settings())
    assert not s.files and s.scope_notes


def test_http_client_paginates_and_rejects_external_paths():
    calls = []
    def transport(method, path, data):
        calls.append(path)
        return (200, [{}]*100 if path.endswith('&page=1') else [{'end':True}])
    client = GitHubClient('', transport=transport)
    assert len(client.pages('/repos/me/demo/pulls/1/files')) == 101
    with pytest.raises(ValueError):
        client.get('https://evil.example/steal')


def test_deletion_patch_tracks_base_lines_without_inventing_added_lines():
    from ai_review.snapshot import parse_diff
    patch='@@ -1,3 +1,2 @@\n def f(user):\n-    authorize(user)\n     return secret'
    added,removed,anchors=parse_diff(patch)
    assert added==[] and removed==[2]
    assert anchors==[1,2]


def test_removed_file_retains_base_source():
    f=[dict(filename='gone.py',status='removed',patch='@@ -1 +0,0 @@\n-x=1',additions=0,deletions=1)]
    snap=fetch_snapshot(FakeGitHub(f,content='x=1\n'),ReviewRequest('me','demo',1),Settings())
    assert snap.files['gone.py'].content==''
    assert snap.files['gone.py'].base_content=='x=1\n'
    assert snap.files['gone.py'].removed_lines==[1]
