# Real review quality: what improved and what remains

The agent now finds genuine defects with exact source lines. It has not met the original accuracy target. Application tests and source evidence checks do not prove every model claim correct.

## Source-checked findings from the current HIGH profile

[PR #2 review run 40175006325](https://github.com/jlx339/personal-ai-code-review-agent-demo/actions/runs/40175006325) found these two clear defects in unchanged historical Python source:

| Finding | Cause and supported fix | Finding ID |
| --- | --- | --- |
| All child-research errors terminate research | `or True` makes the token-limit branch unconditional. Remove it and propagate unexpected exceptions. | `d96300f55fb3` |
| Compression errors use the wrong model setting | The invoked model is `compression_model`, while the provider-specific token-limit check uses `research_model`. Pass `compression_model`. | `73529e1e478f` |

The model also rejected a duplicate of the first issue. The report remains partial because the security specialist did not complete tool investigation. Both retained findings have exact source evidence and supported verifier decisions, but still need owner review before publication. No new evaluation review comments were posted.

The latest legacy multi-agent run found an empty-tool-call indexing risk. Its stated input would raise `IndexError`; reachability and severity need checking against forced-tool-call assumptions. It is not the pre-labeled premature-completion target. The latest LangChain retry run retained no supported finding and rejected a vague missing-test claim for insufficient evidence and assertions. The HIGH configuration run missed both reference targets; earlier LOW runs identified the numeric-zero filter cause but included inaccurate boolean examples.

## Benchmark outcome

The final HIGH round matches **1 of 3 original high-severity reference targets**, up from 0 of 3 in the earlier three-distinct-sample round. The original target of 70% high/critical recall is not met. Do not combine the best findings from different profiles into a purported single-run score. Human-labeled precision is undefined because the owner has not independently judged the findings.

The original target file bytes remain unchanged. Case #335 now includes its actual imported helper and original package layout, correcting missing evaluation context. These results therefore reflect combined application/context/profile changes, not a controlled experiment isolating one change. The initially held-out configuration sample was reused during tuning and is no longer untouched validation data.

## Changes that were tested

- The model selects an application-issued source reference and one cause line; the application builds the quotation. Unknown or out-of-window references fail.
- Context preserves physical source lines, changed functions, local callers, callback wiring, and bounded imported project definitions. The verifier receives that full bounded context.
- Verifier decisions check every candidate ID, category, severity and fix. Optional text corrections may narrow inaccurate examples while keeping evidence anchors fixed. Correction capability did not guarantee correct use in every run.
- Three of the 12 request slots are reserved for verification. Invalid output can be repaired once within the verifier turn limit. Quota and tool failures remain visible.
- The default uses free Flash Lite with HIGH thinking for correctness/verification and MINIMAL for security/tests. Optional Flash models remain explicit choices; reports record actual profiles.

The installed suite passes **109 tests without skips**, including real LangGraph execution and wheel contents. Wheel and source distribution build. Independent reviews found and helped fix Unicode-line handling and relative-import resolution errors; final review found no important remaining defect in the inspected default flow. This is not a comprehensive proof of correctness.

## Free-model availability

Flash 3.6 produced useful findings, then exhausted the configured free daily quota. Older adapter reports labeled network/timeouts as 503, so they do not prove a server outage. The new adapter distinguishes these errors. A separate one-attempt Flash 3.8 probe with a 90-second timeout also timed out and correctly skipped the comparison. No billing was enabled. Availability failures are recorded separately from review-quality scores.

Latest HIGH analysis times were approximately 70 seconds for case #335, 71 seconds for #299, 51 seconds for #38845, and 41 seconds for the configuration sample, excluding Actions setup. Raw outcomes, earlier mistakes, rejected candidates, model attempts, and partial checks are retained under `evals/results/`.

## Submission status

Real bug detection can now be demonstrated. The original accuracy target remains unmet, and some findings/patch suggestions still need correction or rejection by a person. Before claiming the target passed, obtain owner judgments and run further evaluation with an available stronger model or independently validated scenarios. The Google Doc and five-minute video are still owner submission steps; the project submission text is prepared in `submission-draft.md`; recording aids are kept locally.
