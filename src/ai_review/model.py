"""Gemini Developer API adapter retaining native tool-call thought signatures."""
from dataclasses import dataclass, field, replace
import json
import urllib.error
import urllib.request


class ModelError(RuntimeError):
    pass


@dataclass
class ModelResult:
    message: dict
    text: str = ''
    tool_calls: list[dict] = field(default_factory=list)
    usage: dict = field(default_factory=dict)


class ReviewModel:
    def __init__(self,key,settings,budget,transport=None):
        if not key:
            raise ValueError('GEMINI_API_KEY is required')
        self.key,self.settings,self.budget,self.transport=key,settings,budget,transport
        self.terminal_error=None

    def for_model(self,name,thinking_level=None):
        settings=replace(self.settings,model=name,thinking_level=thinking_level)
        return self if settings==self.settings else ReviewModel(self.key,settings,self.budget,self.transport)

    def _send(self,body):
        req=urllib.request.Request(
            f'https://generativelanguage.googleapis.com/v1beta/models/{self.settings.model}:generateContent',
            data=json.dumps(body).encode(),headers={'Content-Type':'application/json','x-goog-api-key':self.key},method='POST')
        try:
            timeout=90 if body.get('generationConfig',{}).get('thinkingConfig',{}).get('thinkingLevel')=='HIGH' else 45
            with urllib.request.urlopen(req,timeout=timeout) as response:
                raw=response.read(1000001)
                if len(raw)>1000000:
                    raise ModelError('Model response exceeds limit')
                return response.status,json.loads(raw),dict(response.headers)
        except urllib.error.HTTPError as exc:
            try:
                error=json.loads(exc.read(32000))
            except (ValueError,UnicodeError):
                error={}
            return exc.code,error,dict(exc.headers)
        except (urllib.error.URLError,TimeoutError) as exc:
            timed_out=isinstance(exc,TimeoutError) or isinstance(getattr(exc,'reason',None),TimeoutError)
            return 0,{'kind':'timeout' if timed_out else 'connection'},{}

    def invoke(self,messages,tools=None,response_schema=None,system='',reserve_requests=0):
        if self.terminal_error:
            raise ModelError(self.terminal_error)
        strong=self.settings.model in ('gemini-3.6-flash','gemini-3.8-flash')
        level=self.settings.thinking_level or ('LOW' if strong else 'MINIMAL')
        reasoning=level!='MINIMAL'
        cap=16000 if level=='HIGH' else 12000 if level=='MEDIUM' else 8000
        config={'maxOutputTokens':max(self.settings.output_tokens,cap) if reasoning else self.settings.output_tokens,
            'thinkingConfig':{'thinkingLevel':level}}
        if response_schema:
            config.update(responseMimeType='application/json',responseJsonSchema=response_schema)
        body={'contents':messages,'generationConfig':config}
        if system:
            body['systemInstruction']={'parts':[{'text':system}]}
        if tools:
            body['tools']=[{'functionDeclarations':tools}]
        for attempt in range(3):
            self.budget.admit(self.settings.model,12.5 if strong else self.settings.request_interval,reserve=reserve_requests)
            try:
                status,data,headers=(self.transport or self._send)(body)
            except (ValueError,UnicodeError):
                raise ModelError('Invalid model response') from None
            if status==200:
                try:
                    candidate=data['candidates'][0]
                    if candidate.get('finishReason') not in (None,'STOP'):
                        raise ValueError('Incomplete model response')
                    message=candidate['content']
                    if not isinstance(message,dict) or not isinstance(message.get('parts'),list) or not message['parts']:
                        raise ValueError('Invalid content')
                    message.setdefault('role','model')
                    calls=[]
                    pieces=[]
                    for part in message['parts']:
                        if not isinstance(part,dict):
                            raise ValueError('Invalid part')
                        if 'text' in part:
                            if not isinstance(part['text'],str):
                                raise ValueError('Invalid text')
                            if not part.get('thought'):
                                pieces.append(part['text'])
                        if 'functionCall' in part:
                            call=part['functionCall']
                            if (not isinstance(call,dict) or not isinstance(call.get('name'),str)
                                    or not isinstance(call.get('args'),dict)):
                                raise ValueError('Invalid tool call')
                            calls.append(call)
                    text=''.join(pieces)
                    if not text and not calls:
                        raise ValueError('No usable content')
                    usage=data.get('usageMetadata',{})
                    if not isinstance(usage,dict) or any(type(v) is not int or v<0 for k,v in usage.items()
                            if k in ('promptTokenCount','candidatesTokenCount','thoughtsTokenCount')):
                        raise ValueError('Invalid usage')
                    normalized=dict(input_tokens=usage.get('promptTokenCount'),
                        output_tokens=(usage.get('candidatesTokenCount',0)+usage.get('thoughtsTokenCount',0)) if usage else None)
                except (KeyError,IndexError,TypeError,ValueError,AttributeError):
                    reason=candidate.get('finishReason') if isinstance(locals().get('candidate'),dict) else None
                    suffix=f' ({reason})' if reason in ('MAX_TOKENS','SAFETY','RECITATION','MALFORMED_FUNCTION_CALL') else ''
                    raise ModelError('Model returned an invalid or incomplete response'+suffix) from None
                self.budget.usage.append(normalized)
                return ModelResult(message,text,calls,normalized)
            error_text=json.dumps(data).lower()
            daily=status==429 and any(x in error_text for x in ('perday','per_day','daily','requestsperday'))
            if status in (401,403,400,404) or daily or attempt==2 or status not in (0,429,500,502,503,504):
                if status==0:
                    message='Model request timed out' if isinstance(data,dict) and data.get('kind')=='timeout' else 'Model connection failed'
                else:
                    message=f'Model request failed (HTTP {status})' + ('; daily quota exhausted' if daily else '')
                if daily or status in (400,401,403,404) or attempt==2:
                    self.terminal_error=message
                raise ModelError(message)
            retry=headers.get('Retry-After',headers.get('retry-after','5'))
            try:
                delay=float(retry)
            except (ValueError,TypeError):
                delay=5
            if delay>60:
                raise ModelError('Model retry delay exceeds run limit')
            self.budget.sleeper(max(5,delay))
        raise ModelError('Model retries exhausted')
