# Real Sample Dataset

Three real historical Python samples are pinned in `manifest.json`. Each review adds an unmodified upstream buggy file to an isolated evaluation PR. The labels under `expected/` were prepared before model execution, using the source and linked upstream fixes. These are real code samples, not the original bug-introducing diffs. All three come from one project and cover correctness; they do not establish security detection or benign-change precision.

MIT attribution is preserved in `upstream/LICENSE`. The upstream files are reviewed as text and are not imported or executed. Do not merge evaluation PRs. Record live reports and manually assess every supported finding before calculating scores with `evaluate.py`. A partial run or missed issue remains visible. Do not publish evaluation findings without owner selection.
