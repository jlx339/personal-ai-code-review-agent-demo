"""Build line-complete changed-function context without executing submitted code."""
from ai_review.source import source_lines
import ast
import json
from ai_review.redaction import redact_source


def _ranges(content,changed):
    lines=source_lines(content)
    if not lines:
        return []
    points=sorted({n for n in changed if 1<=n<=len(lines)})
    if not points:
        return []
    # Imports/module context and changed enclosing functions. Whole-file additions
    # naturally retain the whole file; unrelated functions in small diffs stay out.
    windows=[(1,min(20,len(lines)))]
    try:
        nodes=[n for n in ast.walk(ast.parse(content))
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
    except (SyntaxError,ValueError):
        nodes=[]
    for point in points:
        enclosing=[n for n in nodes if n.lineno<=point<=n.end_lineno]
        if enclosing:
            node=min(enclosing,key=lambda n:n.end_lineno-n.lineno)
            windows.append((max(1,node.lineno-3),min(len(lines),node.end_lineno+3)))
        else:
            windows.append((max(1,point-12),min(len(lines),point+12)))
    merged=[]
    for start,end in sorted(windows):
        if merged and start<=merged[-1][1]+1:
            merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
        else:
            merged.append((start,end))
    return merged


def build_context(snapshot,catalog,limit=60000):
    files=[]
    remaining=limit
    for f in list(snapshot.files.values()):
        if not f.changed:
            continue
        item=dict(path=f.path,status=f.status,added_lines=f.added_lines,removed_lines=f.removed_lines,
            deletion_anchors=f.deletion_anchors,head_source=[],base_source=[])
        truncated=False
        for side,content,changed in [('head',f.content,f.added_lines+f.deletion_anchors),
                ('base',f.base_content or '',f.removed_lines)]:
            lines=source_lines(redact_source(content))
            windows=_ranges(content,changed)
            for start,end in windows:
                cursor=start
                while cursor<=end:
                    last=cursor-1
                    chars=0
                    for line in range(cursor,min(end,cursor+199)+1):
                        cost=len(str(line))+2+len(lines[line-1])+1
                        if cost>remaining-chars or cost+chars>12000:
                            break
                        chars+=cost
                        last=line
                    if last<cursor:
                        truncated=True
                        break
                    block=catalog.register(f.path,side,cursor,last)
                    block['content']='\n'.join(f'{n}: {lines[n-1]}' for n in range(cursor,last+1))
                    item[side+'_source'].append(block)
                    remaining-=chars
                    cursor=last+1
                if cursor<=end:
                    truncated=True
        note=f'Prompt source context truncated: {f.path}'
        if truncated and note not in snapshot.scope_notes:
            snapshot.scope_notes.append(note)
        item['truncated']=truncated
        files.append(item)
    return json.dumps(dict(files=files,scope_notes=snapshot.scope_notes))
