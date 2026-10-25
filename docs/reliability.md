# Reliability checks and practical limits

This is an assisted code reviewer. Passing application tests does not establish that its model finds every defect or that its findings are always correct. The owner must inspect supported findings before publishing them.

## Verified behavior

The installed local suite passes 75 tests without skips. It includes the real LangGraph flow and a built-wheel packaging check. Regression cases cover malformed model output, transient and terminal API errors, request budgets, unavailable scanning, source and tool limits, credential redaction, exact evidence, deleted code, category correction, duplicate IDs, source anchors, trusted workflow provenance, stale PRs, explicit approval, and duplicate/uncertain publication.

An independent code review identified an inline-anchor problem after category changes. A regression reproduced it, and the fix was reviewed again without further important findings in that change. This review was scoped to the reliability changes, not a certification of all application code.

Both wheel and source distribution build locally. GitHub baseline tests pass. The owner-approved publication workflow successfully posted both selected synthetic findings against the reviewed commit. No evaluation findings are automatically published.

## Static scan of the reviewer itself

A local Bandit scan of `src/` reported zero high, three medium, and eleven low findings. The three medium findings are B310 warnings at HTTP calls in `github.py` and `model.py`. Inspection found fixed HTTPS API origins for GitHub/Gemini and an HTTPS/hostname allowlist for the artifact redirect. These were assessed as generic URL-opening warnings for the current inputs; they were not silently suppressed, and the scan was not reported as clean. This tool scan does not constitute a comprehensive security audit.

## Model evaluation

The first three real-code runs were all partial. None matched the three pre-labeled high-severity targets. One run found another source-supported exception-handling issue. The other two retained no supported findings. The full baseline diagnostics remain in `evals/results/baseline.json`.

That baseline exposed specialists ending without tool investigation. The loop now asks an early-answer specialist to investigate within its existing turn budget before accepting a final answer. A regression test covers this recovery. It still reports partial results if the specialist never investigates. Follow-up outcomes must be recorded alongside the baseline, rather than replacing misses with a better-looking selected run.

## Remaining limits

The model may miss bugs, misclassify an issue, or propose a false positive. Exact evidence matching intentionally drops unsupported quotations; this can reduce recall when the model quotes source incorrectly. Bounded contexts and tools can leave checks incomplete. Test review suggests missing tests; it does not execute submitted code or measure runtime test coverage.

The final dataset is narrow: three distinct historical files from two projects. A byte-identical candidate was excluded from distinct counts and retained as a repeated measurement. Source hashes are recorded in the manifest. Upstream fixes and manual source inspection supplied reference labels. The evaluation uses full files added to owned PRs, rather than the original bug-introducing diffs, and omits supporting modules. Broader claims require independent owner judgments, more projects, security cases, benign changes, and repeated measurements.

Final follow-up: all three distinct reports were partial; none matched the three pre-labeled high targets. Tool-investigation recovery improved execution discipline, but did not meet the detection target. One other supported issue was retained; owner actionability judgments remain pending. The reliability pass is complete for the known defects found, while review quality remains an explicit limitation.
