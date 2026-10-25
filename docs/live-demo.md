# Live GitHub Demo

Repository: https://github.com/jlx339/personal-ai-code-review-agent-demo

Synthetic smoke-test PR: https://github.com/jlx339/personal-ai-code-review-agent-demo/pull/1

The default branch contains the reviewer and a safe miniature AI helper. The PR deliberately changes only `examples/assistant.py`, introducing a provider-response regression, removing a file-access containment check, and adding retry behavior without tests. Do not merge the intentionally faulty branch.

The repository's Gemini secret has been configured by the owner. No API key is stored in this project. The baseline GitHub test workflow passed; ordinary tests on the demo branch intentionally fail on the changed response contract.

Initial live reviews returned partial results, which were preserved rather than labeled clean. These runs exposed source-window handling, overly broad specialist output categories, and a mistaken assumption about GitHub run metadata. The publisher now separately checks the PR head and the trusted base-side reusable workflow revision.

Only a supported, source-validated finding from a trusted completed analysis run is eligible for manual publication. Open the latest AI code review run, inspect its summary, and run Publish approved AI findings from the default branch with the run ID and exact approved finding IDs. The assistant has not published any AI findings automatically.

This synthetic PR demonstrates the workflow. It is not the three-real-sample evaluation required for submission; the three-distinct-sample evaluation is now recorded in `evals/results/final-high-comparison.json`. The video recording remains an owner step.

## Latest verified smoke test

Run: https://github.com/jlx339/personal-ai-code-review-agent-demo/actions/runs/40167343339

The Actions job completed and saved its artifact. The review status is **partial**, not clean. It used 10 model requests and approximately 46 seconds of analysis. Bandit completed; the tests specialist and verifier completed; the correctness specialist had a truncated source-search result. Two other candidates failed deterministic source evidence/location checks and were discarded.

Supported findings available for human inspection:

| Finding ID | Result | Severity |
| --- | --- | --- |
| `4eb2a58f2056` | `parse_answer` reads incorrect provider-response keys. | High |
| `d503b703f05e` | `load_note` no longer checks that paths remain inside the notes folder. | High |

Both were emitted under correctness by the model, although the path-containment issue is a security concern. This category drift and the missing validated retry-test recommendation are limitations of this smoke test, not hidden successes. The two supported issues match deliberately seeded regressions; no precision claim about real projects is established.

The owner manually approved and published both findings. [Publication run 40167781789](https://github.com/jlx339/personal-ai-code-review-agent-demo/actions/runs/40167781789) succeeded, and [review 5641796669](https://github.com/jlx339/personal-ai-code-review-agent-demo/pull/1#pullrequestreview-5641796669) contains both selected IDs against the reviewed commit. This verifies the analysis → owner selection → publication path. Findings were not posted automatically.

Follow-up hardening adds independent verifier category assignment, updates IDs after category correction, merges resulting exact duplicates, preserves readable quotes in Markdown, and makes prompt-context truncation explicit in the final partial report. These changes have regression tests; model quality must still be measured on real code.

## Recording package

Use [the 4:40 script](demo-script.md) and [pinned real-code evidence](demo-evidence.md). Lead with the two accurate real-code findings from run 40175006325; label this page’s existing published review as a separate synthetic workflow demonstration. See [submission checklist](submission-checklist.md) for the remaining handoff steps.
