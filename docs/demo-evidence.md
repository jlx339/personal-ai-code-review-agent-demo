# Demo evidence and browser tabs

These are selected successful examples, not the complete benchmark. The full record, including misses and partial checks, remains in [review quality results](review-quality-results.md).

## Open these tabs in order

1. [Public project](https://github.com/jlx339/personal-ai-code-review-agent-demo)
2. [Architecture](https://github.com/jlx339/personal-ai-code-review-agent-demo/blob/main/docs/architecture.md)
3. [Real-code evaluation PR #2](https://github.com/jlx339/personal-ai-code-review-agent-demo/pull/2)
4. [Genuine analysis run 40175006325](https://github.com/jlx339/personal-ai-code-review-agent-demo/actions/runs/40175006325)
5. [Bug one: unconditional exception handler, line 334](https://github.com/jlx339/personal-ai-code-review-agent-demo/blob/cb9d2ef83fe3f92923b8e69e493d3462496021c4/eval_samples/case_335/src/open_deep_research/deep_researcher.py#L332-L345)
6. [Compression function and model setup](https://github.com/jlx339/personal-ai-code-review-agent-demo/blob/cb9d2ef83fe3f92923b8e69e493d3462496021c4/eval_samples/case_335/src/open_deep_research/deep_researcher.py#L510-L553)
7. [Bug two: wrong model check, line 569](https://github.com/jlx339/personal-ai-code-review-agent-demo/blob/cb9d2ef83fe3f92923b8e69e493d3462496021c4/eval_samples/case_335/src/open_deep_research/deep_researcher.py#L550-L580)
8. [Actual provider-specific classifier](https://github.com/jlx339/personal-ai-code-review-agent-demo/blob/cb9d2ef83fe3f92923b8e69e493d3462496021c4/eval_samples/case_335/src/open_deep_research/utils.py#L665-L701)
9. [Previously owner-approved published review — synthetic PR #1](https://github.com/jlx339/personal-ai-code-review-agent-demo/pull/1#pullrequestreview-5641796669)
10. [Durable saved diagnostic record](https://github.com/jlx339/personal-ai-code-review-agent-demo/blob/main/evals/results/final-high-comparison.json)

## The two findings to show

| Priority | Finding | Cause | Suggested repair | ID |
| --- | --- | --- | --- | --- |
| High | Unexpected research errors are hidden | `or True` makes the exception branch unconditional | Remove `or True`; propagate unexpected exceptions | `d96300f55fb3` |
| Medium | Compression error classification uses the wrong model | The classifier receives `research_model`, while compression invokes `compression_model` | Pass `compression_model` | `73529e1e478f` |

The second issue matters when provider-specific error handling differs. Using the same model provider may hide the defect. The first repair must include propagating other exceptions; deleting `or True` alone does not fully describe error recovery.

## Provenance and boundaries

- Source is from `langchain-ai/open_deep_research` at upstream revision `20aaa0d422bd290c83f93574810ef1244e8d5955`, with MIT attribution preserved.
- Owned PR #2 head is `cb9d2ef83fe3f92923b8e69e493d3462496021c4`; source links above are pinned to that commit.
- Run 40175006325 used Gemini 3.5 Flash Lite, HIGH correctness/verifier thinking, 10 requests, and 70.35 seconds of analysis. Its overall report is **partial** because security tool investigation was incomplete.
- The verifier rejected a duplicate of the first issue. Only the two supported findings are the main examples.
- This is static source review, not execution of the upstream program or proof of an applied patch. Suggested regression tests were not run against the historical application.
- No new real-code review comments have been published. The existing PR #1 review demonstrates human-approved publication on a separately labeled synthetic example.

## Optional publication after your own inspection

If you choose to publish these two real-code findings, use **Publish approved AI findings**, branch `main`, analysis run ID `40175006325`, and IDs `d96300f55fb3,73529e1e478f`. First confirm that the PR head still matches the pinned commit and the seven-day artifact is available. Changed heads or expired artifacts require a fresh analysis, whose finding IDs may differ. Never use the saved diagnostic JSON as a replacement publication artifact.

Publication is optional for the recording because the completed synthetic publication already demonstrates that boundary. No new publication is needed to finish the submission package.
