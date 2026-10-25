# Five Minute Demo Script

Record only after live setup and evaluation. Use actual reports; distinguish any scripted failure demonstration from a live model review.

Current source-checked demo: [real PR #2 HIGH run 40175006325](https://github.com/jlx339/personal-ai-code-review-agent-demo/actions/runs/40175006325). It retained an unconditional exception-handler bug (`d96300f55fb3`) and a wrong compression-model check (`73529e1e478f`). Inspect both before selecting either for publication. The report is partial because security investigation was incomplete; do not present it as a complete clean review. The latest comparison matches 1 of 3 original high targets and misses the configuration targets; show those limits rather than claiming the quality target passed. Verify the PR head and artifact availability before recording; publication rejects stale heads.

- 0:00–0:35: Explain the problem: personal Python AI projects need checks for failure handling, unsafe tools, and missing tests. Introduce the three reviewers.
- 0:35–1:10: Show the architecture and the boundary between autonomous read-only analysis and human-selected publication.
- 1:10–2:15: Open a real small Python PR, trigger the review, and show agent/tool events plus the completed artifact. If waiting takes too long, use a genuine earlier run and state that clearly.
- 2:15–3:10: Inspect a high-priority finding, source evidence, a concrete suggested test, and any uncertainty or partial checks.
- 3:10–3:50: Select finding IDs, manually run publication, and show the resulting GitHub comments. Show that unselected findings stay private to the report workflow.
- 3:50–4:25: Demonstrate duplicate or stale-head rejection and explain one tool-failure/partial-report case.
- 4:25–5:00: Show three-real-sample evaluation counts, misses, false positives, AI coding prompts/iterations, and one limitation learned during development.

Submission assets: public GitHub repository, Google Doc containing project overview, datasets, coding prompts, iterations and learnings, and a video no longer than five minutes. The handout states October 25, 2026 for Builder of the Week eligibility and November 11, 2026 as the final certification deadline.
