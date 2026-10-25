# Evaluation on Real Python AI Changes

Status: Three historical real-code samples selected and labeled; live scoring pending. Synthetic unit tests and a successful API connection are not a substitute for reviewing three real code samples.

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
| Three real samples | Pinned in `evals/manifest.json`; pre-run expected issues in `evals/expected/`. Execution pending. |
| Real model review precision/recall | Not measured. |
| LangGraph integration | Local real-graph test passed after dependencies installed. |
| GitHub analysis and selected publication | Verified on synthetic PR #1: analysis 40167343339 was partial; owner-selected publication 40167781789 succeeded. |
| Final demo and Google Doc | Not recorded or created. |

## Historical sample method and limitations

The samples are unmodified buggy Python files from `langchain-ai/open_deep_research`, pinned to the base revisions of upstream PRs #335, #286, and #299. They are added as new files in three disposable owned PRs. This tests real code, while keeping publication permissions and credentials in the owned repository. It does not reproduce the upstream bug-introducing change. Supporting modules are not copied, so claims needing unavailable context must remain uncertain. No imported code is executed. MIT attribution is retained in `evals/upstream/LICENSE`.

Expected issues were assessed from pinned source and the upstream proposed fixes before model runs. These upstream PRs were unmerged at selection time, so their descriptions are reference claims rather than proof of maintainer acceptance. All three samples primarily cover correctness in one codebase. Additional security and benign samples would be needed to make broader quality claims.
