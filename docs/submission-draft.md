# Personal AI Code Review Agent

Prepared submission text for the required Google Doc. Author: Lixin Jin. Project: Week 3, Project 3E — Code Review Agent. Copy this document into Google Docs and set viewer access before submitting. The demo recording is a separate deliverable.

## Overview

My agent helps a personal Python AI-project developer review pull requests in GitHub. It replaces manually checking changed code for functional bugs, unsafe behavior, and missing tests. Three specialists inspect pinned source using five read-only tools. A verifier challenges their findings, and the owner chooses which supported findings to publish. The target is a useful small-PR review within five minutes; real detection quality is measured separately from workflow success.

Repository: https://github.com/jlx339/personal-ai-code-review-agent-demo

## How it works

GitHub Actions starts a trusted base-branch reviewer when an owned, same-repository pull request changes. LangGraph coordinates static analysis, correctness review, security review, test review, exact source validation, verification, and a prioritized report. Findings include severity, source evidence, impact, preconditions, and a suggested fix or test. The five tools read source, search source, list Python files, inspect Python syntax, and run a fixed Bandit scan.

The reviewer treats code and tool output as untrusted text. It does not import or run the submitted Python. Analysis has a Gemini API key and read-only GitHub access. A separate manual workflow has GitHub review-write access and publishes only explicitly selected supported finding IDs. It checks workflow provenance, current PR commit, exact evidence, and existing publication markers. It never approves or merges a PR.

The default is Gemini 3.5 Flash Lite with HIGH thinking for correctness/verification and MINIMAL for security/tests, using the owner's configured free tier. Optional Flash3.6/3.8 profiles are explicit choices with smaller quotas. Request, tool, context, and output limits bound each run. No additional paid service, vector database, persistent memory service, or voice tool is required.

## Datasets

The small synthetic PR #1 deliberately changes an AI response parser and removes a path containment check. It tests the workflow and approval boundary; it does not count as a real-code benchmark.

Three distinct historical real Python samples come from the MIT-licensed `langchain-ai/open_deep_research` and `langchain-ai/langchain` projects. Exact source SHAs, content hashes, original paths, upstream fix references, pre-run expected issues, and licensing are stored under `evals/`. Each evaluation PR adds an unchanged historical buggy source file. This evaluates real code, but does not recreate the original bug-introducing diff. For case #335, the actual pinned imported helper was added as unchanged supporting context; the other samples have limited supporting context. The samples mainly assess correctness; the dataset cannot establish broad security or benign-change performance. One byte-identical candidate was detected by a content comparison and excluded from distinct-sample counts; its runs remain recorded as repeats.

The reference fixes concern use of the wrong model setting during token-limit recovery, premature final writing while research sections remain incomplete, and handling tool exceptions excluded by a retry filter. Two upstream fixes were unmerged when selected and one was merged. Expected issues are source-based labels rather than a claim that every upstream proposal is correct. The exact labels were recorded before running the model.

## Real-code sample results

| Real sample | Owned evaluation PR | Latest recorded outcome |
| --- | --- | --- |
| Open Deep Research, `deep_researcher.py` | [PR #2](https://github.com/jlx339/personal-ai-code-review-agent-demo/pull/2) | Two source-checked real defects: unconditional exception handling and the wrong model setting during compression. One original main target matched. Security investigation was partial. |
| Open Deep Research, legacy `multi_agent.py` | [PR #4](https://github.com/jlx339/personal-ai-code-review-agent-demo/pull/4) | Original premature-completion target missed. An empty-tool-call indexing risk needs reachability review. |
| LangChain, `tool_retry.py` | [PR #5](https://github.com/jlx339/personal-ai-code-review-agent-demo/pull/5) | Original exception-filtering target missed. Unsupported missing-test claim rejected; report partial. |

The demo focuses on the two accurate findings in the first row. These are two bugs in one sample. Complete outcomes remain in the repository; selected examples are not an overall accuracy score. The extra configuration sample was initially held out, then reused during tuning, and is not counted as untouched validation.

## Agent framework

| Field | Implementation |
| --- | --- |
| User and surface | Owner of a personal Python AI project; GitHub pull requests and Actions reports. |
| Goal | Produce actionable bug, security, and test suggestions with source evidence and human control over publication. |
| Flow | Intake → static scan → correctness → security → tests → source validation → verifier → prioritized report → owner selection → publication. |
| Tools | Read source, search source, list Python files, inspect Python syntax, and scan security; all are read-only with respect to the reviewed repository. |
| State | Pinned source, tool observations, candidates, checks, and shared budgets for one analysis process; saved Actions artifacts retained seven days. No persistent conversational memory or process resume. |
| Hard limits | Never execute reviewed code in privileged analysis, modify code, approve or merge a PR, or publish unselected findings. |
| Human handoff | Owner reads the report and selects supported finding IDs before a separate workflow writes comments. |
| Recovery | Bounded retries, invalid-output repair, verifier request reserve, and explicit partial reports; stale or invalid publication inputs are rejected. |
| Success measure | End-to-end report and selected publication demonstrated; useful real bug detection demonstrated. Original 70% main-target recall goal remains unmet at 1/3. |

## AI-assisted coding prompts

Actual user instructions included:

- “fully understand everything we need, and lets plan a similar project, not exactly the same but we can use the similar context.”
- “just personal ai projects on github”
- “i want something free but good”
- “go ahead, also make sure that the ai review is bug free”
- “can we try those? I would like to make the agent to be able to correctly find real bugs before we submit this project.”

These shaped the scope: GitHub Actions, Python AI projects, Gemini free-tier access, and explicit reliability checks. The last request became a verification exercise rather than an unsupported guarantee. Implementation planning and recording aids are kept as local working notes. Runtime specialist and verifier prompts are under `src/ai_review/prompts/`; they are distinct from the instructions used to build the application.

## Iterations and observations

The first setup run failed because Hatch could not find the package from the distribution name. Explicit package selection fixed installation, and a packaging regression test now checks the built CLI and prompt files.

Live model runs exposed oversized responses, overly broad output categories, short-file source windows, and source-directory search failures. Bounded structured output, tool handling, and specialist schemas improved recovery. Failed and truncated checks remain visible as partial reports.

Live GitHub publication exposed differences between PR metadata and the trusted reusable-workflow revision. Publication now verifies these independently. The owner successfully selected and published both supported synthetic findings in run 40167781789; the [posted review is available on PR #1](https://github.com/jlx339/personal-ai-code-review-agent-demo/pull/1#pullrequestreview-5641796669).

A reliability pass added independent verifier category assignment, correct finding identities after category changes, exact duplicate merging, recalculated inline anchors, readable Markdown quotes, and explicit prompt/scanner truncation. Regression tests reproduced each known defect before its fix. Specialists now receive an investigation request when they try to end early without tools. The latest local suite has 109 passing tests with no skips, including real LangGraph execution and package building. Those tests check application behavior; they do not prove model judgments correct.

## Results and limitations

The initial three-distinct-sample round matched none of the three high-severity reference targets. The final HIGH profile matched the wrong-model token-limit target and found an additional genuine unconditional-exception defect, with exact source lines and source-checked fixes in run 40175006325. Original high-target matches are now 1/3, below the 70% target. The HIGH configuration run missed both reference targets. Earlier LOW runs found the numeric-zero filtering cause but included inaccurate boolean examples. These misses and mistakes remain in the record. Owner judgments are pending, so human-labeled precision is undefined. See `docs/review-quality-results.md` and the raw evaluation results.

The workflow already demonstrates read-only analysis, source-grounded findings, failure reporting, and owner-selected publication. The model can miss genuine bugs or assign the wrong category, even when a workflow completes successfully. No claim of bug-free software or guaranteed detection is made. Coverage means inspection of tests and missing-test suggestions; reviewed code is not executed to measure runtime coverage.

## Submission checklist

- Public GitHub code: available at the repository link above.
- Three-real-sample results: recorded, with misses and partial reports visible; the quality target is not met.
- Google Doc: copy this draft into a Google Doc, check the final results, and share its link.
- Video: record at most five minutes, showing the genuine real-code report, two accurate examples, the existing human-approved synthetic publication, and one limitation. The planned recording targets 4 minutes 40 seconds.

## Final lessons

Matching a quotation is not enough. The reviewer also needs callers, imported definitions, real defaults, valid triggers, and a complete fix. An omitted helper caused a false ResearchComplete absence claim; providing the real pinned helper let the reviewer challenge it. Source references now produce application-owned quotations, verifier reasons are visible, and optional claim corrections cannot move evidence anchors. The latest default analysis times were 41–71 seconds per sample, excluding setup. The original accuracy target remains unmet, and the initially held-out source was reused during tuning.

Flash 3.6 reached its daily free quota. The old adapter also mapped network/timeouts to 503; new diagnostics distinguish them. A one-attempt Flash 3.8 probe timed out after 90 seconds and skipped the comparison without claiming a quality score. No billing was enabled. Independent code review found no important remaining issue in the inspected application flow; this does not prove model judgments correct.

## Demo evidence

The featured real review is [run 40175006325](https://github.com/jlx339/personal-ai-code-review-agent-demo/actions/runs/40175006325). Finding `d96300f55fb3` identifies `or True` hiding unexpected child-research errors. Finding `73529e1e478f` identifies the compression classifier receiving the wrong model setting. Exact source quotations and verifier explanations are preserved in `evals/results/final-high-comparison.json`.

The already completed owner-approved publication is [review 5641796669 on synthetic PR #1](https://github.com/jlx339/personal-ai-code-review-agent-demo/pull/1#pullrequestreview-5641796669). It demonstrates the publication workflow separately from the real-code examples.
