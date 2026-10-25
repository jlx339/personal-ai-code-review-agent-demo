# Evaluation on Real Python AI Changes

Status: Pending. Synthetic unit tests and a successful API connection are not a substitute for reviewing three real code samples.

## Dataset selection

Choose three actual public AI-project PRs or historical changes and record each repository, URL, license, base SHA, head SHA, and affected Python files in `evals/manifest.json`. Prefer small changes within the application's limits. Include known correctness, security, and test-gap cases across the set; a benign change helps measure false positives. Cases may overlap categories.

The runtime intentionally only accepts open same-repository PRs in an owned repository. For historical or third-party changes, prepare an offline pinned snapshot or reproduce the attributed change in a branch of an owned evaluation repository. Preserve upstream provenance and license. Do not represent a manufactured bug as an upstream real issue.

Before running the reviewer, manually label expected issues using source and relevant history. Record issue IDs, severity, affected source, preconditions, and justification. Label whether each returned supported finding is actionable and which expected issue it matches. False positives and misses must remain visible.

## Scoring

`ai_review.evaluation.evaluate(report, expected, labels)` computes actionable precision and high/critical issue recall using human judgments, plus raw counts, missed issue IDs, unlabeled finding IDs, latency, and model requests. A missing denominator is reported as undefined; missing human labels do not become a perfect score. A supported verifier decision is still a candidate for human judgment.

Targets from the approved design:

- At least 80% actionable precision and 70% high/critical recall, with raw counts.
- Every publishable inline comment has a correct deterministic source/diff anchor.
- A small-PR review targets five minutes, subject to available quota.
- No unapproved, stale-head, or duplicate publication.

Run separate controlled failures for rate limits, invalid model output, unavailable Bandit, and missing source. Record partial results and recovery behavior. Real GitHub publication should be demonstrated on a disposable demo PR with explicit selected findings, never on an unrelated upstream project.

## Results

| Evidence | Current state |
| --- | --- |
| Gemini authentication | Owner successfully ran a one-request connection check. |
| Core regression tests | Run `pytest -q`; latest counts are recorded in the build log. |
| Three real samples | Not selected or executed yet. |
| Real model review precision/recall | Not measured. |
| LangGraph integration | Local real-graph test passed after dependencies installed. |
| GitHub analysis and selected publication | Awaiting target repository setup and secret. |
| Final demo and Google Doc | Not recorded or created. |
