"""Find bounded project definitions for imported symbols used by changed files."""
import ast
from pathlib import PurePosixPath


def load_dependencies(snapshot,tools):
    imports=[]
    for f in list(snapshot.files.values()):
        if not f.changed or not f.content:
            continue
        try:
            tree=ast.parse(f.content)
        except (SyntaxError,ValueError):
            continue
        called=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Call):
                target=node.func
                while isinstance(target,ast.Attribute):
                    target=target.value
                if isinstance(target,ast.Name):
                    called.add(target.id)
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.module:
                names={alias.name for alias in node.names if (alias.asname or alias.name) in called}
                if names:
                    imports.append((f.path,node.module,node.level,names))
    if not imports:
        return {}
    inventory=tools.dispatch('list_python_files',{})
    if not inventory.ok:
        return {}
    available=set(inventory.data)
    requested={}
    for source,module,level,names in imports:
        module_path=module.replace('.','/')
        parent=PurePosixPath(source).parent
        if level:
            if level>len(parent.parts):
                continue
            root=parent
            for _ in range(level-1):
                root=root.parent
            roots=[root]
        else:
            roots=[p for p in parent.parents if p.name=='src']
            if parent.name=='src':
                roots.insert(0,parent)
            roots.extend([PurePosixPath('.'),PurePosixPath('src')])
        candidates=[]
        for root in roots:
            candidates.extend([str(root/(module_path+'.py')),str(root/module_path/'__init__.py')])
        path=next((p for p in candidates if p in available),None)
        if path and path!=source and (path in requested or len(requested)<4):
            requested.setdefault(path,set()).update(names)
    ranges={}
    for path,names in requested.items():
        try:
            f=tools._file(path)
            tree=ast.parse(f.content)
            spans=sorted({(n.lineno,n.end_lineno) for n in ast.walk(tree)
                if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.name in names})
            if spans:
                ranges[path]=spans
        except (ValueError,RuntimeError,SyntaxError,KeyError,UnicodeError):
            note=f'Dependency source unavailable under limits: {path}'
            if note not in snapshot.scope_notes:
                snapshot.scope_notes.append(note)
    return ranges
