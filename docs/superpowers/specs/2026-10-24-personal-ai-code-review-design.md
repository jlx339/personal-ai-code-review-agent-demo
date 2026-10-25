# Personal AI Project Code Review Agent Design

Status: Approved by owner in conversation. Implementation plan follows separately.

## Purpose and agreed direction

Help a solo developer review Python AI projects on GitHub by investigating bugs, security risks, and missing tests, then presenting a prioritized, evidence-backed report before the developer chooses which comments to publish.

The owner selected GitHub Actions with LangGraph orchestration, initially supporting PRs from branches within their own repositories. Keep services free and include tools only when needed. A local API connection test succeeded with `gemini-3.5-flash-lite`. The owner's AI Studio screenshots show Free tier with 15 requests per minute, 250,000 input tokens per minute, and 500 requests per day for that model. These are observed quotas, not guaranteed future capacity.

One-liner: My agent helps a solo AI developer investigate a Python pull request in GitHub, replacing manual checks of model calls, tools, security boundaries, and tests; it uses repository and static-analysis tools autonomously, hands findings to the developer before publishing comments, and succeeds when three real code samples produce useful, correctly anchored reports with explicitly recorded misses and false positives.

## Goals and limits

- Three distinct tool-using reviewers: correctness and reliability, security, and tests.
- Findings grounded in the reviewed commit, surrounding code, and test evidence.
- Prioritized JSON and Markdown reports, including explicit incomplete-review status.
- Human selection before GitHub comments are published.
- Bounded requests and retries suitable for a free model API tier.
- Evaluation and submission material that demonstrate state, tool use, recovery, and handoff.

First version supports public repositories owned by the developer, Python source and tests, and same-repository PRs. Install the workflows and reviewer in each target repository; no central cross-repository service is needed. Start with one demo repository. Fork PRs and automated dependency-bot PRs are skipped. Private repositories, additional languages, web research, code edits, merging, and executing reviewed project code are outside the initial scope.

A failure would be silently treating an unavailable tool or malformed output as a clean review, publishing unapproved findings, or reporting speculative missing tests as measured coverage.

## Approaches considered

| Approach | Tradeoff | Decision |
| --- | --- | --- |
| Streamlit with LangGraph | Convenient interactive review, but adds a separate app to the GitHub workflow. | Considered; fallback if needed. |
| GitHub Actions with LangGraph | Runs where the developer works; human selection and durable state need explicit workflow design. | Selected by owner. |
| Deep Agents application like the sample | Flexible delegation, with more variable loops and greater similarity to the reference. | Not selected. |

Originality comes from AI-project review rules, three responsibility-based specialists, explicit evidence validation, and reproducible evaluation. The reference project's prompts and implementation will not be copied.

## Components and control flow

1. A `pull_request_target` workflow runs on opened, updated, and reopened same-repository PRs, using a trusted base-side workflow definition. Explicitly reject fork PRs and bot actors before any model-key access. A default-branch-only manual review trigger is also available. New runs cancel obsolete review runs for that PR.
2. Trusted reviewer code is explicitly checked out from the default branch, never the PR head or a merge ref. GitHub API reads obtain metadata, the base/head SHAs, patches, and source snapshots. PR source is data; it is never imported, installed, or executed. All untrusted fields enter scripts through structured data, never interpolated shell commands. The privileged trigger requires this execution boundary and explicit read-only permissions.
3. Deterministic intake records supported, skipped, unavailable, and oversized files. Initial limits: 10 changed Python files, 1,000 total changed lines, 64 KiB per fetched text file, and 100,000 fetched source characters across the run. Exceeding a limit yields a partial report listing omissions.
4. A LangGraph orchestrator dispatches all three specialists sequentially to respect the shared free-tier quota. Each may choose repository tools, request related context, and revise findings inside a bounded loop. Fixed orchestration and adaptive specialist decisions coexist.
5. A deterministic validator checks schema, paths, line ranges, source evidence, and changed-code relevance. A verifier model pass examines supported candidates and challenges weak assumptions. It may request bounded additional context. Its failure leaves candidates explicitly unverified.
6. The report ranks findings by severity, evidence status, category, and stable ID. Save JSON, Markdown, and a sanitized execution log as an Actions artifact; display a summary and draft finding IDs in the Actions job summary.
7. The developer reads the report, then runs a separate publishing workflow with the review run ID and an explicit list of approved finding IDs.
8. The publisher loads that run's artifact, verifies provenance and the current PR head, and submits one GitHub review using `COMMENT`. It never approves or merges the PR.

## Reviewers and tools

| Reviewer | Focus | Tool choices |
| --- | --- | --- |
| Correctness and reliability | Async mistakes, response parsing, missing failure paths, retry termination, timeout behavior, and agent stopping conditions. | Read source ranges, search bounded repository text, inspect patches, inspect Python syntax. |
| Security | Secret exposure, unsafe command or file operations, authorization mistakes, sensitive logs, and untrusted content reaching privileged tools. | Repository tools and fixed Bandit scan. Mask probable secret values in model inputs and reports. |
| Tests | Existing assertions around changed behavior; missing cases for API errors, malformed output, empty retrieval, retries, and stopping. | Read changed code and relevant existing tests, search assertions and test names, inspect Python syntax. |

Tools have typed arguments and bounded results. Expose specific operations rather than a generic shell. Bandit receives safely materialized files in a temporary directory, uses fixed arguments with `shell=False`, and has a 30-second timeout. The temporary directory contains source data only. A subprocess is not described as an isolation sandbox.

All paths stay within the selected repository snapshot. Do not follow symlinks or accept arbitrary URLs or host paths. PR descriptions, comments, source, and tool results remain untrusted data and cannot change instructions or grant tools. Only known reviewer dependencies are installed from the trusted application revision.

The tests reviewer suggests concrete inputs and expected assertions. It does not claim measured coverage or passing tests because reviewed tests are not executed.

## Finding contract and prioritization

Each finding contains a stable ID, category, severity, title, path, start/end lines, exact redacted-safe source evidence, impact, preconditions, explanation, suggested fix or test, evidence references, and verification status. Preserve an internal mapping to original source lines when masking secrets.

Severity is critical, high, medium, or low, according to concrete impact and reachability. Confidence is described through evidence and explicit uncertainty rather than an automatic approval percentage. Deduplicate by underlying issue, affected location, and category; retain separate issues on the same line.

Only findings with validated locations and changed-code relevance are eligible for publication. Use added-line inline anchors in version one. Findings about absent tests, deleted code, or issues without a valid inline anchor remain in the report; approved ones can appear in the review body with source references. Unsupported or unverified candidates remain clearly labeled and are not publishable.

## State and persistence

Graph state contains run identity, PR identity, trusted reviewer revision, base/head SHAs, file inventory, fetched context, per-agent messages/tool results, candidate and validated findings, retry counts, budget consumption, errors, and completion status.

Serialize report and sanitized diagnostic state to Actions artifacts with seven-day retention. Each analysis run starts fresh; live graph state is in memory, and process crashes require rerunning analysis. Do not claim resumable checkpoints. Publication resumes the approval workflow from the saved report, without rerunning the model. Long-term preference learning and Mem0 are outside scope.

## Permissions and publication boundary

Analysis requests `contents: read` and `pull-requests: read` and reads `GEMINI_API_KEY` from repository secrets. It cannot publish review comments. Publication requests `actions: read`, `contents: read`, and `pull-requests: write`; it needs no model key. A manual dispatch is a specific approval to publish the selected IDs, not blanket consent for all findings.

The publishing workflow exists on the default branch and rejects execution from another ref. Accept only artifacts from the expected review workflow in the same repository, with matching run ID, PR, head SHA, schema version, and successful artifact generation. Treat artifact fields as data, never executable content.

Refresh the PR immediately before publication and reject a changed head. Bind the review to the reviewed commit. Include a report identifier in the review body, check existing reviews to avoid repeat publication, and serialize publication per PR. An ambiguous API write outcome requires checking existing reviews before any retry.

GitHub artifacts and job summaries are automatic internal review outputs. The explicit human gate controls posting PR comments. Repository settings and workflow permissions must be verified during setup; owning a personal account does not establish that they are already configured.

## Free-tier budget and recovery

Use only `gemini-3.5-flash-lite` initially; no paid fallback or automatic billing setup. Default to 12 model requests per run including retries and verification, with at most three turns per specialist and two verifier turns. Account for every model call centrally, including subagents. Cap outputs at 2,000 tokens per request and keep model context bounded.

Space requests by at least five seconds and serialize review workflows repository-wide. Other applications or repositories using the same Google project can still exhaust its shared quotas. On 429, respect retry guidance and retry transient limits at most twice within the global request budget; stop on exhausted daily quota. Retry transient network/5xx errors within the same limit. Fail promptly on credential or permission errors. GitHub job timeout: 15 minutes.

Invalid structured output receives at most one repair attempt within the budget. A failed specialist, missing scanner, unavailable context, or failed verifier produces an explicit partial status and identifies affected checks. No findings means clean only when all required checks completed; otherwise show incomplete. Preserve completed findings whenever possible.

## Evaluation and submission

Select three actual Python AI project PRs or historical changes, recording repository URLs, licenses where relevant, and base/head commit IDs. At least one sample should have known bugs, one security concerns, and one test gaps. These may overlap. Prefer a benign change among the samples to assess false positives. Choose samples with manually established expected findings before inspecting agent results. Fixtures and injected failures supplement these samples; they do not replace the three real samples.

Proposed acceptance targets, to be measured rather than assumed:

- Three real samples produce prioritized reports and sanitized traces.
- All three specialists demonstrably use tools and record outcomes.
- At least 80% of published-eligible findings are judged actionable; report raw counts because the sample is small.
- Detect at least 70% of the manually labeled high/critical issues; report misses and category breakdowns.
- Every publishable inline comment has a deterministically valid source and diff anchor.
- No unapproved comments, duplicate publication on repeated requests, or publication against a stale head.
- Injected rate limits, missing Bandit, malformed model output, and unavailable files yield clear recoverable or partial outcomes.
- Target a completed small-PR analysis within five minutes under available quota; record actual latency and request counts.

Prepare README/setup instructions, architecture documentation, prompts and coding-assistant iteration notes, evaluation data/results, learnings, and a demo script under five minutes. The handout additionally requests a Google Doc and repository submission link. October 25, 2026 is the stated Builder of the Week deadline; November 11 is the final certification deadline. Do not imply that implementation and evaluation are already complete.

## Builder decisions and remaining setup

Proposed defaults are Python-only scope, public repositories, sequential specialists, seven-day artifacts, bounded inputs, and report-based manual approval. These are design calls for the owner to review. Exact dependency versions, internal module names, and implementation details remain with the builder after checking current documentation.

During implementation setup, select the owner/repository, configure its secret without exposing the key, verify Actions permissions, and select the three evaluation samples. No credentials belong in source files, artifacts, or documentation.

## Sources

- Local Week 3 Project Handout (Oct 2026), Project 3E and submission requirements.
- Local reference implementation and Oct Code Review Agent (Deep Agents) document, used for comparison.
- Owner's AI Studio screenshots and successful local API connection test.
- [Gemini 3.5 Flash Lite documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite).
- [Gemini rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).
- [GitHub workflow permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
- [Manual GitHub workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).

## Recorded implementation adjustments

PyPI DNS was unavailable in the coding environment. The core therefore uses validated dataclasses and standard-library HTTP/diff parsing rather than Pydantic, LangChain, HTTPX, and unidiff. LangGraph remains the production coordinator and Bandit the scanner; their installed integration must still be verified. Publication is serialized repository-wide, a stricter boundary than per-PR serialization. Source snapshots retain base-side evidence for deleted-code findings. Dependency lock generation remains an explicit setup prerequisite; no lock or live evaluation is claimed.
