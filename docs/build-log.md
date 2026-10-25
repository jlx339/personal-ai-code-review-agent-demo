# Build Log

## Intent and AI coding prompts

The owner requested an original Code Review Agent inspired by the Week 3 handout and sample, scoped to personal AI projects on GitHub. The selected approach was GitHub Actions plus LangGraph, three reviewers, and manual publication. The owner asked to include other available services only when useful and preferred a free model provider.

Planning prompts included: understand the handout and sample; propose a distinct code reviewer; check personal-account Actions permissions; find a free API; and implement the approved design step by step. The owner successfully tested Gemini 3.5 Flash Lite through a small local connection script.

## Implementation decisions and iterations

- Kept the supplied reference repository unchanged and created a new local Git repository on `feat/personal-ai-review`.
- A builder check identified that a plain `pull_request` workflow could run a PR-modified workflow definition. The design changed to a guarded trusted `pull_request_target` analysis with no PR checkout or source execution.
- PyPI DNS failed in the coding environment. Existing local pytest was available, so the core uses validated dataclasses, standard-library HTTP, and a strict unified-diff parser. LangGraph remains the production coordinator and Bandit the fixed scanner. Dependency installation and lock generation remain explicit setup steps, not claimed successes.
- Wrote regression tests before each core component and observed missing-feature failures before passing implementations.
- A pagination fixture initially matched `per_page=100` as though it were `page=1`; corrected its page-boundary condition.
- Added native Gemini response handling to preserve thought signatures across function calls and centrally count model retries.
- Added exact evidence matching, supported/rejected verifier outcomes, and explicit partial reports instead of confidence-based automatic approval.
- Separated model-key analysis from GitHub-write publication. Publication rechecks exact source, commit freshness, workflow provenance, and duplicate finding markers.
- Repository-wide publication serialization is stricter than the planned per-PR lock and avoids resolving untrusted report state before acquiring the lock.

## Verification record

The final local suite passed 53 tests with one explicit skipped LangGraph integration test, using an existing cached pytest environment. Those tests cover deterministic code and scripted external responses; they do not establish live Gemini review quality or that Actions ran successfully. Re-run the suite after subsequent changes and record the final result before submission.

## Independent review and fixes

A separate reviewer found multiline private-key leakage through partial source tools, unhandled malformed model envelopes, and deletion-only findings being dropped. Regression tests reproduced each issue before the fixes. Source is now redacted before slicing; invalid model envelopes become recoverable failures; and base-side evidence can support selected review-body findings. Additional tests cover terminal API errors, spoofed publication markers, and syntax-inventory truncation.

## Remaining evidence

Install dependencies and commit `uv.lock`; verify actual LangGraph execution; choose three real samples; run model evaluations; enable the workflows in a target public repository; demonstrate selected publication and stale/duplicate rejection; record the demo; and create the required Google Doc.

## Packaging correction and installed verification

The owner's first setup run exposed missing Hatch wheel package selection: the distribution name differs from `src/ai_review`. Added explicit wheel package configuration. A packaging regression test reproduced the failure without that configuration and passed with it, checking the CLI and all four prompt files in the built wheel. The owner's cached dependencies enabled offline installation in the coding environment. The full installed suite now passes 55 tests, including the real LangGraph adapter and packaging test, with no skips. The generated `uv.lock` is included. Live Gemini review quality, Actions execution, and the three-real-sample benchmark remain pending.
