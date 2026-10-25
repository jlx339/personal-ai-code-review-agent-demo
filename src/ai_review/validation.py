"""Deterministic source evidence checks; no first-match reanchoring."""
from dataclasses import dataclass,field
import hashlib
import json
from ai_review.redaction import redact_source


@dataclass
class ValidationResult:
    retained: list = field(default_factory=list)
    rejected: list = field(default_factory=list)


def finding_identity(f):
    return json.dumps([f.path,f.source,f.start_line,f.end_line,f.category,f.title.casefold().strip()],separators=(',',':'))


def assign_finding_id(f):
    f.id=hashlib.sha256(finding_identity(f).encode()).hexdigest()[:12]


def validate_findings(snapshot,candidates):
    out=ValidationResult()
    seen=set()
    for f in candidates:
        source=snapshot.files.get(f.path)
        content=(source.base_content if f.source=='base' else source.content) if source else None
        if not source or not source.changed or content is None or f.end_line>len(content.splitlines()) or not f.evidence:
            out.rejected.append('Candidate lacks valid changed-source location/evidence')
            continue
        if not source.patch_available:
            out.rejected.append('Candidate has no complete patch for relevance validation')
            continue
        relevant=source.removed_lines if f.source=='base' else source.added_lines+source.deletion_anchors
        if not any(f.start_line<=n<=f.end_line for n in relevant):
            out.rejected.append('Candidate does not overlap changed source')
            continue
        valid=True
        anchor_evidence=False
        for e in f.evidence:
            ef=snapshot.files.get(e.path)
            evidence_content=(ef.base_content if e.source=='base' else ef.content) if ef else None
            if evidence_content is None or e.end_line>len(evidence_content.splitlines()):
                valid=False
                break
            actual='\n'.join(redact_source(evidence_content).splitlines()[e.start_line-1:e.end_line])
            if actual != redact_source(e.excerpt):
                valid=False
                break
            if e.path==f.path and (e.source=='base')==(f.source=='base') and e.start_line<=f.start_line and e.end_line>=f.end_line:
                anchor_evidence=True
        if not valid or not anchor_evidence or not f.impact.strip() or not f.explanation.strip():
            out.rejected.append('Candidate evidence or impact is unsupported')
            continue
        identity=finding_identity(f)
        if identity in seen:
            continue
        seen.add(identity)
        assign_finding_id(f)
        f.inline_eligible=f.source=='head' and f.category!='tests' and f.start_line in source.added_lines
        f.verification_status='unverified'
        out.retained.append(f)
    return out
