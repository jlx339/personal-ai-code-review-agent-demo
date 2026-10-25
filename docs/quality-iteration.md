# Source-reference quality iteration

The owner approved improving evidence handling, context, verifier judgments, and real-code evaluation before submission. This iteration uses the same free model initially so any measured change can be attributed to the application changes, subject to model nondeterminism.

Implemented: application-issued references for delivered pinned source, exact application-built quotations, line-complete changed-function windows with a 60,000-character budget, precise candidate rejection reasons, and independent verifier category/severity/fix reassessment. Report and publication contracts remain unchanged; source references do not prove a claim is true.

Regression tests reproduced unknown/out-of-range references, copied-quote dependence, loss of other valid candidates, incomplete diagnostics, unchecked severity, and source-line errors. Independent review found a Unicode/redaction crash. Physical LF source-line segmentation now stays consistent across context, tools, evidence, diff parsing, validation, and publication. That issue was reproduced before its fix. Local suite: 88 passed, no skips. Package build passed before the final line-segmentation fix and will be checked again before completion.

The existing three distinct files will be rerun unchanged. A held-out legacy configuration file, pinned to upstream PR #311's base revision, has separately recorded expected issues before its first live run. It was selected after the prompts and implementation were written. Labels remain outside model input. The proposed upstream fix is unmerged; source inspection supplies the reference assessment. Earlier failed runs remain committed.

Live results pending. No evaluation findings will be published automatically. Any detection, false positive, severity error, incomplete fix, or partial run must remain visible. New tests are evidence about application behavior, not proof of model review quality.
