# Demo recording script — target 4 minutes 40 seconds

Use this as your spoken script. Open the tabs in [demo evidence](demo-evidence.md) before recording. The main examples are two source-checked findings from a genuine earlier model run. Walk through the application and its actual outputs on screen; say clearly that the analysis was recorded earlier. Do not claim a fresh model call or upstream patch execution.

## Before recording

1. Open the repository README, real PR #2, its Actions run, both pinned source links, and the existing published review on synthetic PR #1. Links are in `demo-evidence.md`.
2. Open `evals/results/final-high-comparison.json` on GitHub as a durable backup if the Actions artifact expires. It is a saved diagnostic record, not an artifact eligible for publication.
3. Increase browser zoom to 125–150%. Close unrelated tabs and hide notifications. Keep the API key and repository secret settings off screen.
4. Rehearse once. Aim for 4:40 and stop before 5:00. Do not merge any intentionally buggy evaluation PR.

## 0:00–0:30 — What I built

**Show:** repository README.

“Hi, I'm Lixin. This is my Personal AI Code Review Agent for Python AI projects on GitHub. It reviews a pull request for bugs, security risks, and missing tests, then produces a prioritized report. I decide which findings become GitHub comments. I'll show two real bugs it correctly found.”

## 0:30–1:00 — How the agents work

**Show:** `docs/architecture.md`, then the successful analysis job.

“LangGraph coordinates three specialist reviewers and a verifier. Each specialist can choose read-only tools to inspect source, search the repository, inspect Python syntax, or scan for security issues. They share state and a request budget. The application checks exact source evidence, and the verifier challenges the claims. Analysis cannot write reviews; publication is a separate human-approved step.”

## 1:00–2:00 — Real bug one: hidden failures

**Show:** PR #2, run 40175006325 summary, then pinned source around line 334.

“This is an unchanged historical file from the open-source Open Deep Research project, placed in my own evaluation PR. This is a genuine earlier run, which took about 70 seconds of analysis. The first finding is high priority: the exception handler contains `or True`. Even when an exception is not a token-limit error, that condition becomes true. The workflow ends research instead of exposing the unexpected failure. The suggested repair removes `or True` and lets unexpected errors propagate. A useful regression test would make a child task raise a non-token error and assert that it propagates.”

**Point to:** finding `d96300f55fb3`, its quoted source, impact, and suggested regression test. The test described here is a proposal; the historical application was not executed.

## 2:00–3:00 — Real bug two: wrong model setting

**Show:** compression setup around lines 527–551, error check at line 569, and the helper's provider-specific checks around lines 665–701.

“The second finding is medium priority. Research compression uses `compression_model`, but the error handler checks the exception using `research_model`. The helper interprets token-limit errors differently for different model providers. If those settings use different providers, a real compression limit can be misclassified and recovery can fail. The fix is to pass `compression_model` to this check. A regression test should use different research and compression providers and verify that the compression setting reaches the classifier.”

**Point to:** finding `73529e1e478f`. These are two findings from one real sample, not two separate benchmark samples.

## 3:00–3:40 — Human control and recovery

**Show:** `Publish approved AI findings` workflow, then the existing posted review on PR #1.

“After inspecting a report, I select finding IDs and manually run publication. Here is a review I previously approved and published on a separate synthetic smoke-test PR. That verifies the full report-to-comment workflow; these comments are not the two real-code examples. The publisher checks the current PR commit and skips duplicate findings. If a tool fails or a quota is exhausted, the report says partial. The real-code report shown today is partial because security investigation was incomplete; the two displayed correctness findings were verified.”

Do not press Run workflow merely for the recording. The already published review is enough to demonstrate the completed approval path.

## 3:40–4:15 — How I used AI coding tools

**Show:** submission document's prompts and iterations section.

“I used ChatGPT and Codex to understand the assignment, plan the GitHub workflow, write the Python implementation, and debug real failures. My instructions emphasized personal GitHub projects, free tools, and finding real bugs. Iterations improved source context, evidence validation, verifier decisions, and error reporting. The application test suite passes 109 tests; those tests check the software, not the accuracy of every AI judgment.”

## 4:15–4:40 — Results and takeaway

**Show:** three-row dataset table in the submission document.

“I tested three distinct historical Python samples. These two examples show useful real bug detection, but the model found one of three original main bug targets. It still needs human review. My main learning was that an exact code quote is only the beginning: the agent also needs the relevant callers, helper functions, and model settings to understand whether a bug is real.”

End recording. Save the video, check that it plays and is under five minutes, then share a viewer-accessible link.
