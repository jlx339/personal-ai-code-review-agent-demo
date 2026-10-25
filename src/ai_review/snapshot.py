"""Pinned source snapshots, safe file reads, and strict unified-hunk parsing."""
import base64
import re
from urllib.parse import quote
from ai_review.schemas import FileSnapshot, ReviewSnapshot, safe_path


def parse_diff(patch: str) -> tuple[list[int], list[int], list[int]]:
    if not patch:
        raise ValueError('Patch unavailable')
    added=[]
    removed=[]
    deletion_anchors=set()
    old_target=0
    old_left=new_left=0
    target=0
    hunks=0
    for line in patch.splitlines():
        match=re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*',line)
        if match:
            if old_left or new_left:
                raise ValueError('Incomplete diff hunk')
            old_start,old_count,new_start,new_count=match.groups()
            old_target=int(old_start)
            old_left=int(old_count) if old_count is not None else 1
            new_left=int(new_count) if new_count is not None else 1
            target=int(new_start)
            hunks+=1
        elif line.startswith('\\ No newline'):
            continue
        elif hunks and line[:1] in ('+','-',' '):
            if line[0] != '+':
                old_left-=1
                if line[0]=='-':
                    removed.append(old_target)
                    deletion_anchors.update(n for n in (target-1,target) if n>0)
                old_target+=1
            if line[0] != '-':
                new_left-=1
                if line[0] == '+':
                    added.append(target)
                target+=1
            if min(old_left,new_left)<0:
                raise ValueError('Invalid diff hunk count')
        elif line.startswith(('--- ','+++ ','diff ','index ')) and not hunks:
            continue
        else:
            raise ValueError('Unsupported diff content')
    if not hunks or old_left or new_left:
        raise ValueError('Incomplete diff')
    return sorted(set(added)),sorted(set(removed)),sorted(deletion_anchors)


def parse_added_lines(patch: str) -> list[int]:
    return parse_diff(patch)[0]


def read_file(client, repository, path, ref, settings):
    safe_path(path)
    item=client.get(f'/repos/{repository}/contents/{quote(path, safe="/")}?ref={quote(ref,safe="")}')
    if not isinstance(item,dict) or item.get('type')!='file' or item.get('encoding')!='base64':
        raise ValueError('Not a regular text file')
    if item.get('size',settings.max_file_bytes+1)>settings.max_file_bytes:
        raise ValueError('File exceeds byte limit')
    raw=base64.b64decode(item['content'].replace('\n',''),validate=True)
    if len(raw)>settings.max_file_bytes or b'\0' in raw:
        raise ValueError('Oversized or binary file')
    return raw.decode('utf-8')


def fetch_snapshot(client,request,settings):
    repo=f'{request.owner}/{request.repo}'
    prefix=f'/repos/{repo}'
    pr=client.get(f'{prefix}/pulls/{request.pr_number}')
    if pr['head']['repo']['full_name']!=repo or pr['base']['repo']['full_name']!=repo:
        raise ValueError('Fork PRs are outside scope')
    if pr['user']['type']=='Bot' or pr.get('state')!='open':
        raise ValueError('Only open non-bot PRs are supported')
    metadata=client.get(prefix)
    if metadata.get('private',False):
        raise ValueError('Only public repositories are supported')
    tree=client.get(f"{prefix}/git/trees/{pr['head']['sha']}?recursive=1")
    if tree.get('truncated'):
        raise ValueError('Repository tree is truncated; cannot establish safe file types')
    modes={x['path']:x.get('mode') for x in tree.get('tree',[])}
    snap=ReviewSnapshot(request,pr['base']['sha'],pr['head']['sha'])
    total_chars=changed_lines=0
    base_modes=None
    for f in client.pages(f'{prefix}/pulls/{request.pr_number}/files'):
        path=f['filename']
        try:
            safe_path(path)
            if not path.endswith('.py'):
                snap.scope_notes.append(f'Skipped unsupported file: {path}')
                continue
            if modes.get(path) in ('120000','160000'):
                raise ValueError('Symlink or submodule rejected')
            changed_lines+=int(f.get('additions',0))+int(f.get('deletions',0))
            if len(snap.files)>=settings.max_files or changed_lines>settings.max_changed_lines:
                raise ValueError('Changed-file or line budget exceeded')
            content=read_file(client,repo,path,snap.head_sha,settings) if f['status']!='removed' else ''
            base_content=None
            if f['status']!='added':
                old_path=f.get('previous_filename') or path
                try:
                    if base_modes is None:
                        base_tree=client.get(f'{prefix}/git/trees/{snap.base_sha}?recursive=1')
                        if base_tree.get('truncated'):
                            raise ValueError('Truncated base inventory')
                        base_modes={x['path']:x.get('mode') for x in base_tree.get('tree',[])}
                    if base_modes.get(old_path) in ('120000','160000'):
                        raise ValueError('Unsafe base file')
                    base_content=read_file(client,repo,old_path,snap.base_sha,settings)
                except (ValueError,RuntimeError,KeyError,UnicodeError):
                    snap.scope_notes.append(f'Base source unavailable: {path}')
            size=len(content)+len(base_content or '')
            if total_chars+size>settings.max_source_chars:
                raise ValueError('Source character budget exceeded')
            total_chars+=size
            patch=f.get('patch') or ''
            try:
                added,removed,anchors=parse_diff(patch)
                patch_available=True
            except ValueError:
                added,removed,anchors=[],[],[]
                patch_available=False
                snap.scope_notes.append(f'Patch unavailable or incomplete: {path}')
            snap.files[path]=FileSnapshot(path,content,patch,added,f['status'],f.get('previous_filename'),True,patch_available,base_content,removed,anchors)
        except (ValueError,KeyError,UnicodeError) as exc:
            snap.scope_notes.append(f'Skipped {path}: {type(exc).__name__}')
        except RuntimeError:
            snap.scope_notes.append(f'File unavailable: {path}')
    return snap
