"""Conservative secret masking; preserves source line numbering."""
import re

PATTERNS = [
    re.compile(r'(?i)(\b(?:[\w]*api[_-]?key|[\w]*secret|[\w]*password|[\w]*token)\b\s*[:=]\s*[\"\x27])([^\"\x27\n]+)([\"\x27])'),
    re.compile(r'\b(?:AIza[\w-]{20,}|sk-[\w-]{12,}|gh[pousr]_[\w]{15,}|github_pat_[\w]+|AKIA[A-Z0-9]{16})\b'),
    re.compile(r'(?s)-----BEGIN [^-\n]*PRIVATE KEY-----.*?-----END [^-\n]*PRIVATE KEY-----'),
    re.compile(r'(?i)(https?://|postgres(?:ql)?://|mysql://)([^\s/:]+):([^\s/@]+)@'),
]


def redact_source(content: str) -> str:
    content=PATTERNS[2].sub(lambda m:'[REDACTED]'+('\n'*m[0].count('\n')),content)
    content=PATTERNS[0].sub(lambda m:m[1]+'[REDACTED]'+m[3],content)
    content=PATTERNS[1].sub('[REDACTED]',content)
    content=PATTERNS[2].sub(lambda m:'[REDACTED]'+('\n'*m[0].count('\n')),content)
    return PATTERNS[3].sub(lambda m:m[1]+'[REDACTED]@',content)
