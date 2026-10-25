# Personal AI Code Review Agent

A GitHub Actions reviewer for personal Python AI projects. Three specialists investigate bugs, security risks, and missing tests. They use read-only tools, then a verifier challenges their findings. You receive a prioritized report and choose which findings to publish.

**Current status:** The installed suite passes 109 tests, including packaging and real LangGraph orchestration. The current HIGH profile identifies an unconditional exception handler and a wrong model setting during token-limit recovery, with exact source evidence. Earlier LOW profiles identified the numeric-zero filtering cause but also included inaccurate boolean examples. Earlier misses, false positives, and provider failures remain recorded. The original review-quality target is not met; human inspection remains necessary. See [evaluation](docs/evaluation.md) and [reliability checks](docs/reliability.md). The Google Doc and recorded video remain outstanding.

## What it does

- Reads PR changes and surrounding Python/test files at an exact commit.
- Looks for model-response errors, async/retry bugs, unsafe tools, credential exposure, and missing assertions.
- Checks exact source evidence and changed-line locations before a finding can be published.
- Reports failed or skipped checks instead of presenting an incomplete review as clean.
- Posts only the finding IDs you explicitly select; never modifies code, approves, or merges a PR.

The initial scope is public repositories you own, Python, and PRs from branches in the same repository. Fork PRs and bot PRs are skipped. Reviewed code and tests are never executed. A missing-tests finding is a reasoned suggestion, not measured test coverage.

## Local setup

Python 3.11 or newer and [uv](https://docs.astral.sh/uv/getting-started/installation/) are required.

```bash
./scripts/setup.sh
```

This installs LangGraph, Bandit, and test dependencies and runs the tests. The dependency lockfile is included and verified; workflows use `uv sync --locked`. If you intentionally change dependencies, regenerate and commit `uv.lock` before enabling Actions.

The core uses standard-library HTTP, validated dataclasses, and strict diff parsing to keep its dependency surface small. LangGraph provides production orchestration; Bandit supplies static security signals. Neither the reference project nor its prompts were copied.

Run a public PR review locally from this repository:

```bash
uv run ai-review analyze --repository YOUR_NAME/YOUR_REPO --pr 1 --prompt-key
```

The command asks for your Gemini key without showing or saving it. You may instead set `GEMINI_API_KEY` in your shell. `GITHUB_TOKEN` is optional for local public reads but increases the available GitHub API quota. Keep keys out of chat, source, screenshots, and reports. This application does not automatically load `.env` files.

Open `reports/current/report.md`. JSON and sanitized diagnostic events are saved alongside it. Local reports cannot be published through the automated approval flow: it requires a trusted GitHub Actions artifact.

## GitHub setup

1. Place this application and its workflows in the target repository's default branch. The first version runs within the repository it reviews.
2. Commit the generated `uv.lock`. Enable Actions in repository settings.
3. Add `GEMINI_API_KEY` under **Settings → Secrets and variables → Actions → New repository secret**. Keep the Google project on its free tier.
4. Open a same-repository Python PR targeting the default branch. The **AI code review** workflow starts automatically. You can also run it manually with a PR number.
5. Read the Actions job summary and download the `ai-review-RUN_ID` artifact. Inspect each finding, its evidence, and the incomplete-check notes.
6. In **Publish approved AI findings → Run workflow**, select the default branch, enter the analysis run ID, and enter the exact finding IDs you approve, separated by commas.

The publisher checks the artifact's workflow, repository, run, and trusted reviewer commit. It refreshes the PR head and source evidence and checks existing publication markers before submitting one COMMENT review. If the PR changed, rerun analysis. If the artifact expired after seven days, rerun analysis.

Analysis has read-only GitHub permissions. Publication gets PR write permission and Actions read permission, without the Gemini key. You do not need to enable automated PR approval or use a personal access token for the repository's Actions workflow.

## Free-tier limits and recovery

The default is `gemini-3.5-flash-lite`, with HIGH thinking for correctness/verification and MINIMAL for security/tests. LOW and MEDIUM can be selected explicitly for comparison. The owner's setup showed 15 requests/minute, 250,000 input tokens/minute, and 500 requests/day; provider quotas may change. Authentication works, and evaluation has exposed both useful detections and missed bugs.

Each run allows 12 model requests including retries, three turns per specialist and two verifier turns. Output caps are 4,000 tokens for MINIMAL, 8,000 for LOW, 12,000 for MEDIUM, and 16,000 for HIGH thinking. Calls are spaced at least five seconds apart. Reviews are serialized in each repository; multiple repositories sharing a Google project may still compete for quota. There is no paid provider fallback or automatic billing setup.

Three request slots are reserved for verification; earlier specialists can become partial rather than consume that reserve. HIGH-thinking Lite calls use a 90-second request timeout; other profiles use 45 seconds. Network/timeouts are distinguished from actual HTTP errors. Imported project definitions and local callers supply bounded context; source quotations are built by the application from delivered references and exact cause lines.

To explicitly compare a different free-tier reasoning model locally, add `--reasoning-model gemini-3.6-flash` (or `gemini-3.8-flash`). In Actions, set the repository variable `AI_REVIEW_REASONING_MODEL` to that allowlisted name. Set `AI_REVIEW_REASONING_THINKING` to LOW, MEDIUM, or HIGH (default HIGH), or use `--reasoning-thinking` locally. The owner's Flash quotas were only 5 requests/minute and 20/day. Flash calls are spaced at least 12.5 seconds apart. In live comparisons, the earlier adapter reported 503 for 3.8 failures (including possible network/timeouts), and 3.6 later exhausted its daily quota. A later one-shot 3.8 probe also timed out after 90 seconds. Reports record the actual profile, attempts, partial checks, and verifier reasons. Changing models does not guarantee better findings, and quota errors never enable billing.

Source limits are 10 changed Python files, 1,000 changed lines, 64 KiB per file, and 100,000 fetched source characters. Missing files, unsupported files, exhausted limits, scanner failures, or unavailable tools make the report partial. Static scans have a 30-second timeout; workflow jobs have a 15-minute timeout.

Free Gemini service terms may allow submitted content to be used for product improvement. Start with public code; do not use confidential code merely because the API key works. See [Gemini pricing and data terms](https://ai.google.dev/gemini-api/docs/pricing).

## Tests and evaluation

```bash
uv run pytest -q
```

Unit tests use synthetic fixtures and scripted API responses. They test failure handling and publication boundaries without model charges or external writes. A LangGraph integration test requires its installed dependency; mocked specialist tests do not establish real model quality.

[Latest source-checked outcomes](docs/review-quality-results.md) and [evaluation instructions](docs/evaluation.md) describe the separate three-real-sample benchmark. [Architecture](docs/architecture.md), [build log](docs/build-log.md), and [demo script](docs/demo-script.md) support the project submission. The [submission checklist](docs/submission-checklist.md), [Google Doc text](docs/submission-draft.md), [4:40 recording script](docs/demo-script.md), and [pinned demo evidence](docs/demo-evidence.md) are prepared. The submission still needs the shared Google Doc and recorded demo of five minutes or less.

Workflow files use JSON syntax, which is a valid YAML subset. This permits semantic configuration tests without a YAML parser. Action revisions are commit-pinned. The tests workflow may execute PR test code with a read-only token and no secrets; privileged analysis never checks out the PR revision.

## Live demo

[Demo repository](https://github.com/jlx339/personal-ai-code-review-agent-demo) · [Synthetic PR 1](https://github.com/jlx339/personal-ai-code-review-agent-demo/pull/1) · [Recorded smoke-test results](docs/live-demo.md). The intentionally faulty PR should not be merged.
