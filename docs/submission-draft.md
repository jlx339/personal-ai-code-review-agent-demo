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

Three historical real Python samples come from the MIT-licensed `langchain-ai/open_deep_research` project. Exact source SHAs, original paths, upstream fix references, pre-run expected issues, and licensing are stored under `evals/`. Each evaluation PR adds an unchanged historical buggy source file. This evaluates real code, but does not recreate the original bug-introducing diff. Supporting modules are not copied. All three samples come from one project and mainly assess correctness; the dataset cannot establish broad security or benign-change performance.

The reference fixes concern use of the wrong model setting during token-limit recovery, swallowed child-research errors, and premature final writing while research sections remain incomplete. Their upstream PRs were unmerged when selected, so expected issues are manually assessed source-based labels rather than claims of maintainer-confirmed ground truth. The exact labels were recorded before running the model.

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

A reliability pass added independent verifier category assignment, correct finding identities after category changes, exact duplicate merging, recalculated inline anchors, readable Markdown quotes, and explicit prompt/scanner truncation. Regression tests reproduced each known defect before its fix. The latest local suite has 74 passing tests with no skips, including real LangGraph execution and package building. Those tests check application behavior; they do not prove model judgments correct.

## Results and limitations

See `docs/evaluation.md` and the committed evaluation results for the final three-sample outcome. Keep misses, partial results, and false positives visible. Assistant-assessed judgments require owner review before they are described as human benchmark labels.

The workflow already demonstrates read-only analysis, source-grounded findings, failure reporting, and owner-selected publication. The model can miss genuine bugs or assign the wrong category, even when a workflow completes successfully. No claim of bug-free software or guaranteed detection is made. Coverage means inspection of tests and missing-test suggestions; reviewed code is not executed to measure runtime coverage.

## Submission checklist

- Public GitHub code: available at the repository link above.
- Three-real-sample results: record all three runs and their actual outcomes in the evaluation document.
- Google Doc: copy this draft into a Google Doc, check the final results, and share its link.
- Video: record at most five minutes using `docs/demo-script.md`, showing a genuine report, owner approval, published findings, and one limitation.
