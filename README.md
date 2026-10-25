# Personal AI Code Review Agent

A GitHub Actions reviewer for personal Python AI projects. Three specialists investigate bugs, security risks, and missing tests. They use read-only tools, then a verifier challenges their findings. You receive a prioritized report and choose which findings to publish.

**Current status:** The installed suite passes 75 tests, including packaging and real LangGraph orchestration. Owner-selected publication succeeded on the synthetic demo. Three historical real-code samples have been reviewed, with partial reports and missed known bugs. The review-quality target is not met; this is an assisted reviewer requiring human inspection. See [evaluation](docs/evaluation.md) and [reliability checks](docs/reliability.md). The Google Doc and recorded video remain outstanding.

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

The initial model is `gemini-3.5-flash-lite`. The owner's setup showed 15 requests/minute, 250,000 input tokens/minute, and 500 requests/day; provider quotas may change. Authentication works, but the real-code evaluation has exposed inconsistent detection and missed bugs.

Each run allows 12 model requests including retries, three turns per specialist, two verifier turns, and 2,000 output tokens per request. Calls are spaced at least five seconds apart. Reviews are serialized in each repository; multiple repositories sharing a Google project may still compete for quota. There is no paid provider fallback or automatic billing setup.

Source limits are 10 changed Python files, 1,000 changed lines, 64 KiB per file, and 100,000 fetched source characters. Missing files, unsupported files, exhausted limits, scanner failures, or unavailable tools make the report partial. Static scans have a 30-second timeout; workflow jobs have a 15-minute timeout.

Free Gemini service terms may allow submitted content to be used for product improvement. Start with public code; do not use confidential code merely because the API key works. See [Gemini pricing and data terms](https://ai.google.dev/gemini-api/docs/pricing).

## Tests and evaluation

```bash
uv run pytest -q
```

Unit tests use synthetic fixtures and scripted API responses. They test failure handling and publication boundaries without model charges or external writes. A LangGraph integration test requires its installed dependency; mocked specialist tests do not establish real model quality.

[Evaluation instructions](docs/evaluation.md) describe the separate three-real-sample benchmark. [Architecture](docs/architecture.md), [build log](docs/build-log.md), and [demo script](docs/demo-script.md) support the project submission. A [Google Doc draft](docs/submission-draft.md) is prepared locally. The submission still needs the shared Google Doc and recorded demo of five minutes or less.

Workflow files use JSON syntax, which is a valid YAML subset. This permits semantic configuration tests without a YAML parser. Action revisions are commit-pinned. The tests workflow may execute PR test code with a read-only token and no secrets; privileged analysis never checks out the PR revision.

## Live demo

[Demo repository](https://github.com/jlx339/personal-ai-code-review-agent-demo) · [Synthetic PR 1](https://github.com/jlx339/personal-ai-code-review-agent-demo/pull/1) · [Recorded smoke-test results](docs/live-demo.md). The intentionally faulty PR should not be merged.
