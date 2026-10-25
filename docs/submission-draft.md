# Personal AI Code Review Agent

Draft for the required Google Doc. This local document has not been uploaded to Google Docs. Video recording remains outstanding.

## Overview

My agent helps a personal Python AI-project developer review pull requests in GitHub. It replaces manually checking changed code for functional bugs, unsafe behavior, and missing tests. Three specialists inspect pinned source using five read-only tools. A verifier challenges their findings, and the owner chooses which supported findings to publish. The target is a useful small-PR review within five minutes; real detection quality is measured separately from workflow success.

Repository: https://github.com/jlx339/personal-ai-code-review-agent-demo

## How it works

GitHub Actions starts a trusted base-branch reviewer when an owned, same-repository pull request changes. LangGraph coordinates static analysis, correctness review, security review, test review, exact source validation, verification, and a prioritized report. Findings include severity, source evidence, impact, preconditions, and a suggested fix or test. The five tools read source, search source, list Python files, inspect Python syntax, and run a fixed Bandit scan.

The reviewer treats code and tool output as untrusted text. It does not import or run the submitted Python. Analysis has a Gemini API key and read-only GitHub access. A separate manual workflow has GitHub review-write access and publishes only explicitly selected supported finding IDs. It checks workflow provenance, current PR commit, exact evidence, and existing publication markers. It never approves or merges a PR.

The current model is Gemini 3.5 Flash Lite, using the owner's configured free tier. Request, tool, context, and output limits bound each run. No additional paid service, vector database, persistent memory service, or voice tool is required.

## Datasets

The small synthetic PR #1 deliberately changes an AI response parser and removes a path containment check. It tests the workflow and approval boundary; it does not count as a real-code benchmark.

Three distinct historical real Python samples come from the MIT-licensed `langchain-ai/open_deep_research` and `langchain-ai/langchain` projects. Exact source SHAs, content hashes, original paths, upstream fix references, pre-run expected issues, and licensing are stored under `evals/`. Each evaluation PR adds an unchanged historical buggy source file. This evaluates real code, but does not recreate the original bug-introducing diff. Supporting modules are not copied. The samples mainly assess correctness; the dataset cannot establish broad security or benign-change performance. One byte-identical candidate was detected by a content comparison and excluded from distinct-sample counts; its runs remain recorded as repeats.

The reference fixes concern use of the wrong model setting during token-limit recovery, premature final writing while research sections remain incomplete, and handling tool exceptions excluded by a retry filter. Two upstream fixes were unmerged when selected and one was merged. Expected issues are source-based labels rather than a claim that every upstream proposal is correct. The exact labels were recorded before running the model.

## AI-assisted coding prompts

Actual user instructions included:

- “fully understand everything we need, and lets plan a similar project, not exactly the same but we can use the similar context.”
- “just personal ai projects on github”
- “i want something free but good”
- “go ahead, also make sure that the ai review is bug free”

These shaped the scope: GitHub Actions, Python AI projects, Gemini free-tier access, and explicit reliability checks. The last request became a verification exercise rather than an unsupported guarantee. Implementation planning and design decisions are preserved in `docs/superpowers/`. Runtime specialist and verifier prompts are under `src/ai_review/prompts/`; they are distinct from the instructions used to build the application.

## Iterations and observations

The first setup run failed because Hatch could not find the package from the distribution name. Explicit package selection fixed installation, and a packaging regression test now checks the built CLI and prompt files.

Live model runs exposed oversized responses, overly broad output categories, short-file source windows, and source-directory search failures. Bounded structured output, tool handling, and specialist schemas improved recovery. Failed and truncated checks remain visible as partial reports.

Live GitHub publication exposed differences between PR metadata and the trusted reusable-workflow revision. Publication now verifies these independently. The owner successfully selected and published both supported synthetic findings in run 40167781789; the posted review is linked in `docs/live-demo.md`.

A reliability pass added independent verifier category assignment, correct finding identities after category changes, exact duplicate merging, recalculated inline anchors, readable Markdown quotes, and explicit prompt/scanner truncation. Regression tests reproduced each known defect before its fix. Specialists now receive an investigation request when they try to end early without tools. The latest local suite has 75 passing tests with no skips, including real LangGraph execution and package building. Those tests check application behavior; they do not prove model judgments correct.

## Results and limitations

All three distinct reports were partial. None matched the three pre-labeled high-severity targets; none matched the additional medium target. One other source-supported exception-handling finding was retained. Its severity and suggested fix also need human inspection. Requiring investigation improved specialist tool use, but did not meet the detection target. See `docs/evaluation.md` and the committed baseline/follow-up diagnostics. Assistant-assessed judgments require owner review before they are described as human benchmark labels; human-labeled precision remains undefined.

The workflow already demonstrates read-only analysis, source-grounded findings, failure reporting, and owner-selected publication. The model can miss genuine bugs or assign the wrong category, even when a workflow completes successfully. No claim of bug-free software or guaranteed detection is made. Coverage means inspection of tests and missing-test suggestions; reviewed code is not executed to measure runtime coverage.

## Submission checklist

- Public GitHub code: available at the repository link above.
- Three-real-sample results: recorded, with misses and partial reports visible; the quality target is not met.
- Google Doc: copy this draft into a Google Doc, check the final results, and share its link.
- Video: record at most five minutes using `docs/demo-script.md`, showing a genuine report, owner approval, published findings, and one limitation.
