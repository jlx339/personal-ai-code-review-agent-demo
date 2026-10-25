# Evaluation on Real Python AI Changes

Status: Three distinct historical real-code samples executed. All reports were partial. The quality target was not met. Source-based expected labels precede execution; independent owner judgments remain pending.

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
| Three real samples | Three distinct source hashes, pinned in `evals/manifest.json`, reviewed in PRs #2, #4, and #5. |
| Real model review precision/recall | Assistant assessment: 0/3 pre-labeled high-severity targets matched. Human-labeled actionable precision undefined; owner judgments pending. |
| LangGraph integration | Local real-graph test passed after dependencies installed. |
| GitHub analysis and selected publication | Verified on synthetic PR #1: analysis 40167343339 was partial; owner-selected publication 40167781789 succeeded. |
| Final demo and Google Doc | Not recorded or created. |

## Historical sample method and limitations

The samples are unmodified historical Python files from `langchain-ai/open_deep_research` (upstream PRs #335 and #299) and `langchain-ai/langchain` (upstream PR #38845). They are added as new files in three disposable owned PRs. This tests real code, while keeping publication permissions and credentials in the owned repository. It does not reproduce the upstream bug-introducing change. Supporting modules are not copied, so claims needing unavailable context must remain uncertain. No imported code is executed. MIT attribution is retained under `evals/upstream/`.

Expected issues were assessed from pinned source and upstream fixes before model runs. PRs #335 and #299 were unmerged at selection time; #38845 was merged. Proposed fixes are reference claims rather than proof of correctness. All three samples primarily cover correctness. Additional security and benign samples would be needed to make broader quality claims.

An initial candidate sample from upstream PR #286 was byte-identical to the #335 source despite a different commit SHA. A source-hash check detected the duplicate. Its runs remain recorded as repeat measurements, but are excluded from distinct-sample counts and aggregate recall. The replacement LangChain sample has its own pre-run labels and license.

## Recorded outcomes

| Distinct sample | Latest run | Report | Pre-labeled target outcome |
| --- | --- | --- | --- |
| Wrong compression-model setting / shared state mutation | [40168632697](https://github.com/jlx339/personal-ai-code-review-agent-demo/actions/runs/40168632697) | Partial; one other supported finding | Both targets missed |
| Premature final writing before all research sections finish | [40168831878](https://github.com/jlx339/personal-ai-code-review-agent-demo/actions/runs/40168831878) | Partial; candidate evidence rejected | Target missed |
| Non-retryable tool errors converted to messages | [40169020180](https://github.com/jlx339/personal-ai-code-review-agent-demo/actions/runs/40169020180) | Partial; no supported finding | Target missed |

The first sample's other finding identifies an unconditional exception-handling branch in the actual source. The assistant assessed its critical severity as overstated and its suggested fix as incomplete. It was not matched retroactively to the pre-run target list or published. The owner has not independently labeled actionability, so precision remains undefined. Observed recall against the three pre-labeled high targets is 0/3; overall pre-labeled issues matched is 0/4 including one medium target.

Baseline and follow-up diagnostics are committed under `evals/results/`. Follow-up runs used a recovery change that asks early-answer specialists to inspect source with a tool. Investigation completion improved, but known-issue detection did not meet the target. Deterministic evidence rejection prevented unsupported candidates from becoming publishable. Further work should diagnose exact evidence failures, improve model judgment, and broaden independently judged samples. Passing application tests does not resolve these model-quality failures.
