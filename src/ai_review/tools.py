"""Read-only tools; reviewed Python is parsed, never executed."""
import ast
import json
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import quote
from ai_review.schemas import FileSnapshot, ToolResult, safe_path
from ai_review.redaction import redact_source
from ai_review.snapshot import read_file


class SnapshotTools:
    def __init__(self,snapshot,client,settings):
        self.snapshot,self.client,self.settings=snapshot,client,settings
        self.events=[]
        self.failures=[]
        self._inventory=None

    def _file(self,path):
        safe_path(path)
        if not path.endswith('.py'):
            raise ValueError('Only Python source supported')
        if path not in self.snapshot.files:
            if not self.client:
                raise ValueError('File outside available snapshot')
            repo=f'{self.snapshot.request.owner}/{self.snapshot.request.repo}'
            if self._inventory is None:
                tree=self.client.get(f'/repos/{repo}/git/trees/{self.snapshot.head_sha}?recursive=1')
                if tree.get('truncated'):
                    raise ValueError('Repository tree unavailable')
                self._inventory={x['path']:x.get('mode') for x in tree.get('tree',[])}
            if self._inventory.get(path) not in ('100644','100755'):
                raise ValueError('Not a regular repository file')
            content=read_file(self.client,repo,path,self.snapshot.head_sha,self.settings)
            if sum(len(x.content)+len(x.base_content or '') for x in self.snapshot.files.values())+len(content)>self.settings.max_source_chars:
                raise ValueError('Source character budget exceeded')
            self.snapshot.files[path]=FileSnapshot(path,content,changed=False)
        return self.snapshot.files[path]

    def read_source(self,path:str,start_line:int,end_line:int,source:str='head')->ToolResult:
        try:
            if type(start_line) is not int or type(end_line) is not int or not (1<=start_line<=end_line<=start_line+199):
                raise ValueError('Invalid source range; maximum 200 lines')
            f=self._file(path)
            content=f.base_content if source=='base' else f.content if source=='head' else None
            if content is None:
                raise ValueError('Source side unavailable')
            lines=redact_source(content).splitlines()
            if end_line>len(lines):
                raise ValueError('Source range exceeds file')
            text='\n'.join(lines[start_line-1:end_line])
            return ToolResult(True,dict(path=path,start_line=start_line,end_line=end_line,
                content=text[:self.settings.tool_output_chars]),truncated=len(text)>self.settings.tool_output_chars)
        except (ValueError,RuntimeError,KeyError,UnicodeError):
            return ToolResult(False,error='Requested source unavailable or outside limits')

    def search_source(self,query:str,paths:list[str],source:str='head')->ToolResult:
        if not isinstance(query,str) or not 1<=len(query)<=200 or len(paths)>20:
            return ToolResult(False,error='Invalid search limits')
        results=[]
        try:
            for path in paths:
                f=self._file(path)
                content=f.base_content if source=='base' else f.content if source=='head' else None
                if content is None:
                    raise ValueError('Source side unavailable')
                for number,line in enumerate(redact_source(content).splitlines(),1):
                    if query.casefold() in line.casefold():
                        results.append(dict(path=path,line=number,content=redact_source(line)[:500]))
                        if len(results)>=20:
                            return ToolResult(True,results,truncated=True)
            return ToolResult(True,results)
        except (ValueError,RuntimeError,KeyError,UnicodeError):
            return ToolResult(False,error='Search source unavailable')

    def list_python_files(self)->ToolResult:
        if not self.client:
            return ToolResult(True, sorted(self.snapshot.files))
        repo=f'{self.snapshot.request.owner}/{self.snapshot.request.repo}'
        try:
            tree=self.client.get(f'/repos/{repo}/git/trees/{quote(self.snapshot.head_sha)}?recursive=1')
            paths=sorted(x['path'] for x in tree.get('tree',[]) if x.get('mode') in ('100644','100755') and x['path'].endswith('.py'))
            return ToolResult(True,paths[:200],truncated=tree.get('truncated',False) or len(paths)>200)
        except (ValueError,RuntimeError,KeyError):
            return ToolResult(False,error='Repository inventory unavailable')

    def inspect_python(self,path:str)->ToolResult:
        try:
            tree=ast.parse(self._file(path).content)
            items=[dict(name=n.name,line=n.lineno,kind=type(n).__name__)
                for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
            return ToolResult(True,items[:100],truncated=len(items)>100)
        except SyntaxError as exc:
            return ToolResult(False,error=f'Python syntax error at line {exc.lineno}')
        except (ValueError,RuntimeError,KeyError):
            return ToolResult(False,error='Source unavailable')

    def scan_security(self,paths:list[str])->ToolResult:
        if not isinstance(paths,list) or not 1<=len(paths)<=self.settings.max_files:
            return ToolResult(False,error='Invalid scan scope')
        try:
            with tempfile.TemporaryDirectory(prefix='ai-review-') as root:
                targets=[]
                for i,path in enumerate(paths):
                    f=self._file(path)
                    dest=Path(root)/f'file_{i}.py'
                    dest.write_text(f.content)
                    targets.append(str(dest))
                # File objects bound output memory; no shell or reviewed code execution.
                with tempfile.TemporaryFile(mode='w+') as out, tempfile.TemporaryFile(mode='w+') as err:
                    proc=subprocess.run(['bandit','-f','json','-q',*targets],shell=False,
                        stdout=out,stderr=err,text=True,timeout=30)
                    out.seek(0)
                    raw=out.read(1000001)
                    if proc.returncode not in (0,1) or len(raw)>1000000:
                        return ToolResult(False,error='Static scanner failed or exceeded output limit')
                    parsed=json.loads(raw)
                    if parsed.get('errors'):
                        return ToolResult(False,error='Static scanner could not inspect all files')
                    findings=[]
                    for result in parsed.get('results',[])[:50]:
                        file_name=result.get('filename')
                        if file_name not in targets:
                            continue
                        findings.append(dict(path=paths[targets.index(file_name)],line=result['line_number'],
                            rule=result['test_id'],severity=result['issue_severity'],text=redact_source(result['issue_text'])))
                    return ToolResult(True,findings)
        except FileNotFoundError:
            return ToolResult(False,error='Bandit unavailable')
        except (subprocess.TimeoutExpired,ValueError,KeyError,RuntimeError):
            return ToolResult(False,error='Static scan failed or timed out')

    def dispatch(self,name,args):
        allowed={'read_source':self.read_source,'search_source':self.search_source,
                 'inspect_python':self.inspect_python,'scan_security':self.scan_security,
                 'list_python_files':self.list_python_files}
        if name not in allowed:
            result=ToolResult(False,error='Tool not permitted')
        else:
            try:
                result=allowed[name](**args)
            except (TypeError,ValueError,AttributeError):
                result=ToolResult(False,error='Invalid tool arguments')
        self.events.append(dict(tool=name,ok=result.ok,truncated=result.truncated))
        if not result.ok or result.truncated:
            self.failures.append(f'{name}: {result.error or "output truncated"}')
        return result
