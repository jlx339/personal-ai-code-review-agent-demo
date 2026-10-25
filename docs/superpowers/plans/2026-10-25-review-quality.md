# Review Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve detection of real bugs while retaining strict source and publication boundaries.

**Architecture:** Shared source-reference catalog canonicalizes evidence from pinned source. Focused bounded source blocks feed specialists and an independent verifier.

**Tech Stack:** Python 3.11, existing LangGraph/Gemini REST/GitHub Actions, no new dependency.

**Spec:** `docs/superpowers/specs/2026-10-25-review-quality-design.md`

## Global Constraints

- Preserve free-tier access, 12-request shared limit, read-only analysis, and explicit owner publication.
- Never execute submitted source or weaken publisher evidence/provenance checks.
- Keep baseline results and pre-label held-out samples before model execution.

## Review Focus

- Unknown or oversized reference ranges must fail before publication.
- Source references must preserve redaction and exact line positions.
- Prompt truncation must occur on line boundaries and remain visible.
- Invalid verifier fields must not partially mark candidates supported.
- Correct source quotations must not be treated as proof of a bug.

### Task 1: Source references and context

Files: create `src/ai_review/evidence.py`, `src/ai_review/context.py`, `tests/test_evidence.py`, `tests/test_context.py`; modify tools and agents.

- [ ] Write failing tests for exact referenced quotes, unknown/out-of-window references, secret masking, function context, and truncation.
- [ ] Run focused tests and confirm failures before implementation.
- [ ] Implement EvidenceCatalog.register/resolve and build_context(snapshot,catalog,limit=60000).
- [ ] Add references to read_source and resolve specialist output through the catalog; preserve existing report schema.
- [ ] Run full suite and commit.

### Task 2: Diagnostics and verification

Files: agents, validation, report, prompts, graph/report tests.

- [ ] Reproduce missing rejection details and unsupported severity/fix acceptance with failing tests.
- [ ] Record per-candidate diagnostic reasons, validate verifier severity and corrected suggestion atomically, and supply contextual source around findings.
- [ ] Run full suite, package build, and independent review; fix important findings before deployment.
- [ ] Commit and update trusted default branch with expected-head lease.

### Task 3: Live evaluation

Files: evaluation manifest/results and project documentation.

- [ ] Rerun unchanged historical samples sequentially and inspect supported findings against pinned source.
- [ ] Prelabel a distinct unseen real sample, preserve license, run once, and inspect results.
- [ ] Record actual detections/misses and remaining limitations. Keep all earlier outcomes.
- [ ] Verify clean local state and remote writes; report whether real detection improved.
