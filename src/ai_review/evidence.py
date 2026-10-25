"""References to delivered pinned source; quotations are constructed, never guessed."""
from ai_review.source import source_lines
import hashlib
from ai_review.redaction import redact_source
from ai_review.schemas import Evidence, Finding


class EvidenceCatalog:
    def __init__(self,snapshot):
        self.snapshot=snapshot
        self.spans={}

    def register(self,path,source,start_line,end_line):
        f=self.snapshot.files[path]
        text=f.content if source=='head' else f.base_content if source=='base' else None
        if text is None:
            raise ValueError('Source side unavailable')
        lines=source_lines(redact_source(text))
        if not 1<=start_line<=end_line<=len(lines):
            raise ValueError('Invalid source reference range')
        content='\n'.join(lines[start_line-1:end_line])
        identity=f'{path}:{source}:{start_line}:{end_line}:{content}'
        ref='S'+hashlib.sha256(identity.encode()).hexdigest()[:12]
        block=dict(ref=ref,path=path,source=source,start_line=start_line,end_line=end_line,content=content)
        self.spans[ref]=block
        return dict(block)

    def resolve(self,raw):
        allowed={'category','severity','title','evidence','impact','preconditions','explanation','suggestion'}
        if not isinstance(raw,dict) or set(raw)!=allowed:
            raise ValueError('Candidate fields do not match source-reference schema')
        references=raw['evidence']
        if not isinstance(references,list) or not 1<=len(references)<=3:
            raise ValueError('One to three evidence references required')
        evidence=[]
        anchors=[]
        for item in references:
            if not isinstance(item,dict) or set(item) not in ({'ref','line'},{'ref','start_line','end_line'}):
                raise ValueError('Invalid evidence reference fields')
            if not isinstance(item['ref'],str) or item['ref'] not in self.spans:
                raise ValueError('Unknown source reference')
            block=self.spans[item['ref']]
            if 'line' in item:
                line=item['line']
                if type(line) is not int or not block['start_line']<=line<=block['end_line']:
                    raise ValueError('Cause line outside delivered source')
                start=max(block['start_line'],line-2)
                end=min(block['end_line'],line+2)
                anchors.append((line,line))
            else:
                start,end=item['start_line'],item['end_line']
                anchors.append((start,end))
            if (type(start) is not int or type(end) is not int
                    or not block['start_line']<=start<=end<=block['end_line'] or end-start>=40):
                raise ValueError('Evidence range outside delivered source or exceeds 40 lines')
            lines=block['content'].split('\n')
            excerpt='\n'.join(lines[start-block['start_line']:end-block['start_line']+1])
            evidence.append(Evidence(block['path'],start,end,excerpt,
                source='base' if block['source']=='base' else 'source'))
        anchor=evidence[0]
        text={k:v for k,v in raw.items() if k!='evidence'}
        return Finding(**text,path=anchor.path,start_line=anchors[0][0],end_line=anchors[0][1],
            source='base' if anchor.source=='base' else 'head',evidence=evidence)
