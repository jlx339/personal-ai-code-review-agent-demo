"""GitHub REST boundary; errors never include credentials or response bodies."""
import json
import time
import urllib.error
import urllib.request


class ApiError(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__(f'GitHub API request failed (HTTP {status})')


class GitHubClient:
    def __init__(self, token: str, transport=None, sleeper=time.sleep):
        self.token, self.transport, self.sleeper = token, transport, sleeper

    def request(self, method, path, data=None):
        if not path.startswith('/') or path.startswith('//') or any(c in path for c in ('\r','\n','\\')):
            raise ValueError('Only relative GitHub API paths are accepted')
        for attempt in range(3 if method == 'GET' else 1):
            if self.transport:
                status, body = self.transport(method, path, data)
            else:
                headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
                if self.token:
                    headers['Authorization']=f'Bearer {self.token}'
                req=urllib.request.Request('https://api.github.com'+path,
                    data=json.dumps(data).encode() if data is not None else None, headers=headers, method=method)
                try:
                    with urllib.request.urlopen(req, timeout=30) as response:
                        raw=response.read(8_000_001)
                        if len(raw)>8_000_000:
                            raise ValueError('GitHub response exceeds limit')
                        body=json.loads(raw)
                        status=response.status
                except urllib.error.HTTPError as exc:
                    status,body=exc.code,None
                except (urllib.error.URLError, TimeoutError):
                    if method != 'GET' or attempt == 2:
                        raise ApiError(0) from None
                    self.sleeper(2**attempt)
                    continue
            if 200 <= status < 300:
                return body
            if status >= 500 and method == 'GET' and attempt < 2:
                self.sleeper(2**attempt)
                continue
            raise ApiError(status)
        raise ApiError(0)

    def get(self,path):
        return self.request('GET',path)

    def pages(self,path):
        out=[]
        for page in range(1,31):
            rows=self.get(f'{path}{"&" if "?" in path else "?"}per_page=100&page={page}')
            if not isinstance(rows,list):
                raise ValueError('Expected paginated list')
            out.extend(rows)
            if len(rows)<100:
                return out
        raise ValueError('GitHub pagination exceeds review limit')

    def download_artifact(self,path):
        """Follow signed storage redirects without forwarding the GitHub token."""
        from urllib.parse import urlparse
        if not path.startswith('/repos/') or not path.endswith('/zip'):
            raise ValueError('Invalid artifact endpoint')
        if self.transport:
            status,body=self.transport('GET',path,None)
            if status!=200:
                raise ApiError(status)
            return body
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):
                return None
        req=urllib.request.Request('https://api.github.com'+path,headers={'Authorization':f'Bearer {self.token}'})
        try:
            response=urllib.request.build_opener(NoRedirect).open(req,timeout=30)
        except urllib.error.HTTPError as exc:
            if exc.code not in (301,302,303,307):
                raise ApiError(exc.code) from None
            target=exc.headers.get('Location','')
            parsed=urlparse(target)
            if parsed.scheme!='https' or not parsed.hostname or not any(
                parsed.hostname.endswith(s) for s in ('.blob.core.windows.net','.githubusercontent.com')):
                raise ValueError('Untrusted artifact download destination')
            response=urllib.request.urlopen(target,timeout=30)
        with response:
            raw=response.read(2_000_001)
        if len(raw)>2_000_000:
            raise ValueError('Artifact archive exceeds limit')
        return raw
