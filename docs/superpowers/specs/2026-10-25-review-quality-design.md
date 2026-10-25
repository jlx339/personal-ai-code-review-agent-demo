# Review quality improvements

The owner approved trying the evidence, context, verification, and repeated real-code evaluation changes discussed in chat. Preserve GitHub Actions, LangGraph, free-tier access, exact publication checks, and all earlier evaluation results. Implement inline in the existing isolated project branch.

## Approaches

Model replacement alone would leave copying and source-window failures intact. Loosening quotation matching would hide unsupported evidence. The selected approach is application-issued source references with canonical quotations, focused context, explicit rejection diagnostics, and independent severity/fix verification. Compare another model only if these improvements still fail and its free access is verified.

## Interfaces and boundaries

An EvidenceCatalog shared by tools/session registers only source spans actually supplied to the model. Findings select reference IDs and line ranges inside those spans. The application constructs path, source side, and exact redacted excerpts; unknown/out-of-range references fail. Existing deterministic validation and publisher source rechecks remain unchanged. References establish source identity, not truth of the model's interpretation.

Context uses imports plus changed enclosing functions and nearby lines, splits large spans on line boundaries, and budgets 60,000 numbered source characters. Whole-file additions can include the full file within that budget. Unshown sections produce scope notes. Tools issue equivalent references for later source reads. All source remains untrusted and unexecuted.

Verifier independently checks category, severity, preconditions, and completeness of the suggested fix. Required verdict fields are validated before any finding becomes supported. Critical requires concrete catastrophic or broad impact; ordinary functional failures generally rank high/medium. Record rejection reasons and source anchors without leaking keys.

## Evaluation

Rerun the same three distinct pinned historical samples, preserve previous misses, and manually inspect every supported finding. Add a distinct held-out real sample, label it before its first run, and do not expose labels to prompts. Record false positives, severity/fix problems, partial checks, latency, and request use. Do not post findings without owner selection or claim human-labeled metrics without owner labels. Success requires supported, source-correct detection of real known defects; do not submit a misleading success claim.
