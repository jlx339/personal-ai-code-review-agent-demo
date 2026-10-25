# Personal AI Code Review Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for inline implementation or superpowers:subagent-driven-development if the owner chooses delegated execution. Steps use checkbox syntax for tracking.

**Goal:** Build a free-tier GitHub PR reviewer with three tool-using agents, verifiable reports, and human-selected publication.

**Architecture:** A trusted GitHub Actions analysis workflow invokes a LangGraph application. Three specialists investigate repository snapshots through bounded tools; deterministic validation and a verifier produce report artifacts. A separate manual workflow publishes approved findings against the original commit.

**Tech Stack:** Python 3.11+, LangGraph, LangChain Gemini integration, Pydantic, HTTPX, unidiff, Bandit, pytest, GitHub Actions, Gemini 3.5 Flash Lite. Resolve compatible current dependency versions before installation and commit a lockfile; no paid integrations.

**Spec:** `../specs/2026-10-24-personal-ai-code-review-design.md`

## Global Constraints

- `gemini-3.5-flash-lite` only; no paid fallback or billing setup.
- Public Python repositories owned by the developer; same-repository, non-bot PRs only.
- 10 changed Python files, 1,000 total changed lines, 64 KiB per fetched text file, and 100,000 fetched source characters per run.
- 12 total model requests including repairs/retries; at most three turns per specialist and two verifier turns; 2,000 output tokens per request; requests spaced at least five seconds.
- Bandit timeout 30 seconds; Actions job timeout 15 minutes; artifacts retained seven days.
- Trusted default-branch workflow/application only; never execute PR code or interpolate PR fields into shell commands.
- Missing checks produce partial results; malformed output must never become a clean report.
- Explicit selected finding IDs before publication; validate provenance, refreshed head SHA, anchors, and duplicate markers.
- Repository starts locally under `week3/personal-ai-code-review-agent/`; preserve `3E-Code-Review-Agent/` unchanged. This directory is currently not a Git repository. Initialize a separate repository for the new project and copy the approved design and plan into its docs. Do not create a remote until its name/destination is established.

## Review Focus

- Renames, deleted files, and missing/truncated patches must produce correct scope notes, not invented anchors (Tasks 2 and 5).
- Duplicate code lines and secret masking must retain original line identity (Tasks 2 and 5).
- Daily quota exhaustion and malformed model output must preserve completed findings (Tasks 3 and 4).
- PR changes after approval and ambiguous GitHub write responses must not cause stale or duplicate comments (Task 6).
- Modified PR workflows and forged artifact metadata must not gain publication authority (Tasks 6 and 7).

## File Map

All paths below are relative to the new project repository.

| Files | Responsibility |
| --- | --- |
| `pyproject.toml`, `uv.lock`, `.gitignore`, `.env.example` | Dependencies, packaging, and credential exclusions. |
| `src/ai_review/config.py`, `schemas.py` | Validated limits and serializable contracts. |
| `src/ai_review/github.py`, `snapshot.py` | API reads, PR snapshots, scope and diff handling. |
| `src/ai_review/tools.py`, `redaction.py` | Bounded agent tools, static analysis, and secret masking. |
| `src/ai_review/model.py`, `budget.py` | Gemini integration, shared request accounting, retries. |
| `src/ai_review/agents.py`, `graph.py`, `prompts/*.md` | Three specialists and verifier with explicit orchestration. |
| `src/ai_review/validation.py`, `report.py` | Evidence/anchor validation, deduplication, report rendering. |
| `src/ai_review/publish.py`, `cli.py` | Report provenance, human-selected publication, entrypoints. |
| `.github/workflows/analyze.yml`, `publish.yml`, `tests.yml` | Trusted analysis, manual publication, credential-free tests. |
| `tests/`, `evals/`, `docs/` | Regression tests, real-sample evaluation, setup and submission materials. |

## Task 1: Establish contracts and limits

**Files:** Create packaging/configuration files, `src/ai_review/__init__.py`, `config.py`, `schemas.py`, and `tests/test_contracts.py`.

**Interfaces:** `Settings` contains the exact global limits and model ID. Pydantic contracts: `ReviewRequest(owner, repo, pr_number)`, `FileSnapshot(path, previous_path, status, patch, content, added_lines)`, `ReviewSnapshot(request, base_sha, head_sha, files, scope_notes)`, `Evidence(path, start_line, end_line, excerpt, source)`, `Finding(id, category, severity, title, path, start_line, end_line, evidence, impact, preconditions, explanation, suggestion, verification_status, inline_eligible)`, `ReviewReport(schema_version, report_id, repository, pr_number, base_sha, head_sha, reviewer_sha, run_id, status, checks, findings, scope_notes, errors, usage)`. Add JSON-serializable `ToolResult` and `CheckResult` contracts. Exact enums live centrally.

- [ ] Write `test_limits_match_design`, `test_report_round_trip`, and `test_invalid_finding_rejected`; assert 12-call limit, three specialist turns, positive ordered lines, and forbidden unknown categories.
- [ ] Run `uv run pytest tests/test_contracts.py -q`; observe missing implementation failures.
- [ ] Implement contracts, package entrypoint, dependency lock, `.env.example` containing names only, and `.gitignore` excluding `.env`, reports, caches, and local secrets. Copy planning documents into project docs.
- [ ] Run the contract tests; require all passing. Commit `feat: define review contracts and limits`.

## Task 2: Build trusted snapshot reads and bounded tools

**Files:** Create `github.py`, `snapshot.py`, `tools.py`, `redaction.py`, `tests/test_snapshot.py`, `tests/test_tools.py`, and sanitized fixture files.

**Interfaces:** `GitHubClient(token: str, transport=None)` wraps API calls; `fetch_snapshot(client, request: ReviewRequest, settings: Settings) -> ReviewSnapshot`. `SnapshotTools(snapshot, client, settings)` exposes `read_source(path, start_line, end_line) -> ToolResult`, `search_source(query, paths) -> ToolResult`, `inspect_python(path) -> ToolResult`, `scan_security(paths) -> ToolResult`. Related files are fetched at the pinned head SHA, within the same aggregate budget. `redact_source(content: str) -> str` preserves line count.

- [ ] Write tests for paginated file lists, renames/deletions, malformed or missing patches, exact boundary limits, binary/non-UTF8 files, traversal/symlinks, repeated code lines, and secret masking. Assert missing patches are reported as unavailable and never inline eligible.
- [ ] Write scanner tests asserting fixed argument lists, `shell=False`, timeout=30, bounded output, missing executable handling, and no reviewed-file imports. Mock HTTP and subprocess calls.
- [ ] Run `uv run pytest tests/test_snapshot.py tests/test_tools.py -q`; observe failures.
- [ ] Implement bounded reads, patch parsing, line-preserving redaction, and typed tools. Keep internal original-source validation separate from redacted model context. Restrict repository search to a bounded Python/test inventory and return truncation notes.
- [ ] Run both suites; require all passing. Commit `feat: add bounded repository review tools`.

## Task 3: Add Gemini and shared free-tier accounting

**Files:** Create `budget.py`, `model.py`, `tests/test_budget.py`, `tests/test_model.py`.

**Interfaces:** `RequestBudget(settings, clock, sleeper)` admits requests centrally and records request count, reported tokens, and waits. `ReviewModel.invoke(messages, tools=None, response_schema=None) -> ModelResult` wraps Gemini with injected transport/model for tests. `ModelResult` records normalized message, tool calls, usage, and errors. Every attempt goes through the same budget.

- [ ] Write tests that the thirteenth request is refused, requests wait at least five seconds, output limit is 2,000, and no provider fallback exists. Verify missing keys never appear in logs/errors.
- [ ] Write 429 tests for retry-after, daily exhaustion stopping promptly, two transient retries maximum, 401/403 failing without retries, timeout/5xx bounded retries, and unknown usage reported as unknown rather than zero-cost certainty.
- [ ] Run `uv run pytest tests/test_budget.py tests/test_model.py -q`; observe failures.
- [ ] Implement Gemini integration with current SDK-supported tool/structured-output APIs; consult official docs for exact signatures. Read `GEMINI_API_KEY` from environment only. Inject clock/sleeper so tests do not wait or use the network.
- [ ] Run suites; require passing. Commit `feat: add quota-aware Gemini model access`.

## Task 4: Implement three specialist loops and orchestrator

**Files:** Create `agents.py`, `graph.py`, four prompt Markdown files, `tests/test_graph.py`.

**Interfaces:** `build_review_graph(model: ReviewModel, tools: SnapshotTools, settings: Settings)` returns the compiled graph. `run_analysis(snapshot, model, tools, settings, run_metadata) -> ReviewReport` invokes it. Typed state stores snapshot, per-reviewer outcomes, findings, evidence, errors, request usage, and completion status; no client objects enter serialized report state.

- [ ] Write scripted-model tests where each specialist chooses a tool, sees its result, and emits findings; assert sequential correctness/security/tests dispatch and bounded turns. Verify source instructions cannot grant a new tool and untrusted content is explicitly framed as data.
- [ ] Write tests for malformed JSON receiving one repair, failed repair yielding partial status, one failed reviewer preserving others' findings, budget exhaustion, and an empty result being clean only after all required checks succeed.
- [ ] Run `uv run pytest tests/test_graph.py -q`; observe failures.
- [ ] Implement distinct prompts and LangGraph transitions. Use typed tool dispatch with permission checks and bounded result messages. Route model proposals through Task 5 validation before the verifier; verifier has at most two turns. Until Task 5 is available, test the validation boundary through an injected validator callable.
- [ ] Run graph tests with fake models only; require passing. Commit `feat: orchestrate three bounded review agents`.

## Task 5: Validate findings and produce actionable reports

**Files:** Create `validation.py`, `report.py`, `tests/test_validation.py`, `tests/test_report.py`; integrate validator into graph.

**Interfaces:** `validate_findings(snapshot: ReviewSnapshot, candidates: list[Finding]) -> ValidationResult` returns retained, rejected, and report-only findings with reasons. `render_markdown(report: ReviewReport) -> str`; `save_report(report, output_dir: Path) -> None` writes `report.json`, `report.md`, and sanitized `trace.json`.

- [ ] Write tests for exact evidence match, duplicate-line ambiguity, masked-secret mapping, invented paths/lines, changed-code relevance, separate issues on one line, cross-agent duplicate issues, and severity ordering. Assert absent-test findings remain report-only and unverified findings are not publishable.
- [ ] Write tests that partial reports list omitted checks/files, contain stable IDs, escape untrusted Markdown/HTML where necessary, contain no raw fixture secret values, and do not claim measured test coverage. Ensure model-produced suggestions are rendered as text, never executed.
- [ ] Run `uv run pytest tests/test_validation.py tests/test_report.py -q`; observe failures.
- [ ] Implement deterministic validation and stable finding IDs, then add the bounded verifier pass to Task 4. Mask secrets before model input and any artifact/log output. Preserve line identity without guessing by first matching duplicate text.
- [ ] Run Tasks 4–5 suites; require passing. Commit `feat: validate evidence and generate review reports`.

## Task 6: Implement manual selected publication

**Files:** Create `publish.py`, `cli.py`, `tests/test_publish.py`, `tests/test_cli.py`.

**Interfaces:** `analyze` CLI accepts owner/repo/PR and output directory. `publish` CLI accepts run ID and explicit approved IDs. `load_verified_report(client, repository, run_id, expected_workflow) -> ReviewReport`; `publish_selected(client, report, approved_ids: list[str]) -> PublishResult`. Define `PublishResult(status, review_id, published_ids, reason)` centrally.

- [ ] Write tests rejecting unexpected workflow/repository/ref, mismatched run/head/schema, expired/missing artifacts, zip traversal/oversized archives, unknown IDs, empty selection, and unverified findings. Verify artifact provenance using GitHub API metadata rather than trusting report fields alone.
- [ ] Write tests for head changes before publication, binding `commit_id` to reviewed SHA, inline/body routing, duplicate report markers, and ambiguous write timeout reconciliation. Assert no automatic blind retry of a write and no approval/merge API calls.
- [ ] Run `uv run pytest tests/test_publish.py tests/test_cli.py -q`; observe failures.
- [ ] Implement typed inputs, fresh PR checks, marker lookup with pagination, one COMMENT review, and bounded safe artifact parsing. Use a marker combining report identity and selected IDs; already published IDs must not be reposted. Reject stale/malformed artifacts with actionable errors.
- [ ] Run suites; require passing. Commit `feat: publish only explicitly selected review findings`.

## Task 7: Wire trusted GitHub Actions workflows

**Files:** Create three workflow YAML files, `tests/test_workflows.py`, `README.md` setup section.

**Interfaces:** Analysis passes GitHub metadata and trusted reviewer SHA into `analyze`; uploads the Task 5 artifact. Publication obtains run ID and comma-separated finding IDs through manual inputs and invokes `publish`. Pass untrusted values through environment variables/structured CLI input, never expression interpolation into shell code.

- [ ] Write workflow-configuration tests asserting `pull_request_target`, explicit same-repository/non-bot guards, default-branch-only manual dispatch, trusted checkout ref, no PR-head checkout, read-only analysis token, seven-day retention, and 15-minute timeout. Assert only analysis reads `GEMINI_API_KEY` and publisher requests Actions read plus PR write.
- [ ] Test per-PR cancellation of obsolete queued analyses and repository-wide serialized model execution. Use an analysis caller and a serialized reusable job if necessary; add a workflow file for the reusable job rather than pretending one concurrency key achieves both. Publication is serialized per PR and never cancels an in-progress write.
- [ ] Run `uv run pytest tests/test_workflows.py -q`; observe failures.
- [ ] Implement workflows with commit-SHA-pinned actions, trusted dependency lock, job summaries, artifacts, and separate credential-free test workflow. Verify supported Actions syntax against current official docs before committing. Add actionlint validation if available.
- [ ] Run workflow tests and `uv run pytest -q`; require passing. Commit `ci: add trusted review and approval workflows`.

## Task 8: Evaluate and prepare the submission

**Files:** Create `evals/manifest.json`, `evals/expected/`, `evals/evaluate.py`, `tests/test_evaluation.py`, `docs/evaluation.md`, `docs/architecture.md`, `docs/build-log.md`, `docs/demo-script.md`, and complete README.

**Interfaces:** `evaluate(report: ReviewReport, expected: list[ExpectedIssue]) -> EvalMetrics` records actionable findings, false positives, misses, high/critical recall, anchor validity, latency, and requests. Match issues by manually reviewed issue identity/location rather than trusting an LLM score. CLI supports pinned local sample manifests for reproducibility.

- [ ] Write scoring tests with known true/false/missed issues; assert exact precision/recall and undefined metrics when denominators are zero. Run `uv run pytest tests/test_evaluation.py -q`, observe failure, then implement scoring and rerun.
- [ ] Select three real AI-project changes with owner/repo and base/head SHAs, expected issues, provenance, and license notes. Establish labels before reviewing agent output. A benign case can be one sample. Do not substitute synthetic examples for real samples.
- [ ] Run `uv run pytest -q` and lockfile consistency checks. Verify no real credentials or raw secret detections enter tracked files. Record results rather than claiming checks not performed.
- [ ] Run a small live Gemini review with the owner's configured environment, inspect model/tool behavior, then evaluate all three pinned samples within available free quota. Record raw counts and findings against the design's 80% actionable precision and 70% high/critical recall targets; iterate prompts if needed and preserve iteration notes.
- [ ] After a target GitHub repository and secret exist, run one end-to-end PR analysis, selected publication, repeat-publication rejection, and stale-head rejection. Keep tests of publish failure paths mocked unless a live test is specifically necessary.
- [ ] Write setup/architecture, coding-assistant prompts and iterations, limitations, and a five-minute demo script. Supply Google Doc-ready project documentation in the repository; creating the external Google Doc and recording/uploading video require the corresponding access and owner participation. Commit `docs: add evaluation results and project submission guide`.

## Owner setup and external dependencies

Local development and mocked tests can proceed without credentials. Before live GitHub validation, establish the destination repository name, create/push it through authorized GitHub access, add `GEMINI_API_KEY` as a repository secret, and verify Actions permissions. Never request the key in chat or claim a locally set key is automatically available in the agent process. Select actual evaluation samples from accessible repositories; ask for a preferred repository only if connected GitHub sources cannot resolve it.

Record network, quota, missing-credential, or account-permission blockers explicitly. Continue independent offline work when live validation is unavailable, but do not mark the whole project complete without its real-sample evaluation and end-to-end evidence.

## Final verification and handoff

- [ ] Verify each spec requirement maps to a task and all cross-task interfaces agree.
- [ ] Run the full test suite once after final edits, inspect the diff, and perform a whole-project review before completion.
- [ ] Report measured results, remaining limitations, exact repository/setup status, and submission artifacts.

Execution recommendation: inline implementation in the current session, with one final independent review. The components share contracts closely, and this avoids repeated implementation handoffs. Delegated implementation remains available if the owner prefers separate per-task reviews.

## Execution status

- Tasks 1–3 and 5–6: local core implemented and regression-tested; dependency substitutions recorded in the design and build log.
- Task 4: specialist loops tested; actual LangGraph adapter test is present and skipped until dependency installation.
- Task 7: trusted workflows and semantic configuration tests implemented; generated lock and live workflow runs pending.
- Task 8: evaluation scorer and submission documentation implemented; three real samples, measured model quality, live selected publication, Google Doc, and video pending.
- Independent code review completed; its actionable findings were reproduced and fixed. Latest full local test result: 53 passed, 1 skipped.

This is an implemented local build awaiting external setup and live validation, not a completed assignment submission.

Packaging follow-up: explicit Hatch package selection fixed and regression-tested RED→GREEN. Dependency installation and wheel building verified; generated lock included. Real LangGraph test now passes. Latest suite: 55 passed, no skips. Task 4 installed integration is verified; Task 7 live Actions and Task 8 real evaluation remain pending.
