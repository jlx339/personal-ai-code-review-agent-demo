"""Serializable review contracts with strict boundary validation."""
from dataclasses import asdict, dataclass, field
import json
import re
from pathlib import PurePosixPath
from typing import Any

CATEGORIES = ('correctness', 'security', 'tests')
SEVERITIES = ('critical', 'high', 'medium', 'low')


def safe_path(path: str) -> str:
    if (not isinstance(path, str) or not path or '\\' in path or '\x00' in path
            or any(ord(c) < 32 for c in path) or path.startswith('/')
            or any(p in ('', '.', '..') for p in path.split('/'))
            or str(PurePosixPath(path)) != path):
        raise ValueError('Invalid repository path')
    return path


@dataclass
class ReviewRequest:
    owner: str
    repo: str
    pr_number: int

    def __post_init__(self):
        if not all(isinstance(x, str) and re.fullmatch(r'[A-Za-z0-9_.-]+', x)
                   and x not in ('.', '..') for x in (self.owner, self.repo)):
            raise ValueError('Invalid repository identity')
        if type(self.pr_number) is not int or self.pr_number < 1:
            raise ValueError('Invalid PR number')


@dataclass
class FileSnapshot:
    path: str
    content: str = ''
    patch: str = ''
    added_lines: list[int] = field(default_factory=list)
    status: str = 'modified'
    previous_path: str | None = None
    changed: bool = True
    patch_available: bool = True
    base_content: str | None = None
    removed_lines: list[int] = field(default_factory=list)
    deletion_anchors: list[int] = field(default_factory=list)

    def __post_init__(self):
        safe_path(self.path)


@dataclass
class ReviewSnapshot:
    request: ReviewRequest
    base_sha: str
    head_sha: str
    files: dict[str, FileSnapshot] = field(default_factory=dict)
    scope_notes: list[str] = field(default_factory=list)


@dataclass
class Evidence:
    path: str
    start_line: int
    end_line: int
    excerpt: str
    source: str = 'source'

    def __post_init__(self):
        safe_path(self.path)
        if self.source not in ('source', 'base'):
            raise ValueError('Invalid evidence source')
        if type(self.start_line) is not int or type(self.end_line) is not int or not (
                1 <= self.start_line <= self.end_line):
            raise ValueError('Invalid evidence lines')
        if not isinstance(self.excerpt, str) or not self.excerpt.strip():
            raise ValueError('Evidence excerpt required')


@dataclass
class Finding:
    category: str
    severity: str
    title: str
    path: str
    start_line: int
    end_line: int
    evidence: list[Evidence] = field(default_factory=list)
    impact: str = ''
    preconditions: str = ''
    explanation: str = ''
    suggestion: str = ''
    verification_status: str = 'unverified'
    inline_eligible: bool = False
    id: str = ''
    source: str = 'head'

    def __post_init__(self):
        safe_path(self.path)
        if self.source not in ('head','base'):
            raise ValueError('Invalid finding source')
        if self.category not in CATEGORIES or self.severity not in SEVERITIES:
            raise ValueError('Invalid finding category/severity')
        if type(self.start_line) is not int or type(self.end_line) is not int or not (
                1 <= self.start_line <= self.end_line):
            raise ValueError('Invalid finding lines')
        for key in ('title', 'impact', 'preconditions', 'explanation', 'suggestion', 'id'):
            value = getattr(self, key)
            if not isinstance(value, str) or len(value) > 12000:
                raise ValueError('Invalid finding text')
        if not self.title.strip():
            raise ValueError('Title required')
        if self.verification_status not in ('unverified', 'supported', 'rejected'):
            raise ValueError('Invalid verification status')
        if type(self.inline_eligible) is not bool:
            raise ValueError('Invalid inline eligibility')
        self.evidence = [Evidence(**e) if isinstance(e, dict) else e for e in self.evidence]
        if not all(isinstance(e, Evidence) for e in self.evidence):
            raise ValueError('Invalid evidence')

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: str = ''
    truncated: bool = False


@dataclass
class CheckResult:
    status: str
    detail: str = ''


@dataclass
class ReviewReport:
    repository: str
    pr_number: int
    head_sha: str
    base_sha: str
    schema_version: int = 1
    report_id: str = ''
    reviewer_sha: str = ''
    run_id: str = ''
    status: str = 'partial'
    checks: dict[str, dict] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    scope_notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    trace: list[dict] = field(default_factory=list)

    def __post_init__(self):
        parts = self.repository.split('/')
        if len(parts) != 2:
            raise ValueError('Invalid repository')
        ReviewRequest(*parts, self.pr_number)
        if not all(re.fullmatch(r'[a-f0-9]{40}', s) for s in (self.head_sha, self.base_sha)):
            raise ValueError('Invalid commit SHA')
        if self.schema_version != 1 or self.status not in ('partial', 'complete'):
            raise ValueError('Unsupported report schema/status')
        self.findings = [Finding.from_dict(f) if isinstance(f, dict) else f for f in self.findings]
        ids = [f.id for f in self.findings if f.id]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate finding IDs')

    def to_json(self):
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, value: str):
        return cls(**json.loads(value))


@dataclass
class PublishResult:
    status: str
    review_id: int | None = None
    published_ids: list[str] = field(default_factory=list)
    reason: str = ''
