# Synthetic Review Demonstration

The default branch contains a safe miniature AI helper in `examples/assistant.py` and two happy-path tests. The `demo/review-sample` branch replaces that one file with `assistant.py.txt` from this directory.

The deliberate changes are:

1. A provider-response parsing regression: the documented provider returns `answer`, but the change reads `output.text`. The existing happy-path test should fail on the demo branch.
2. Deletion of the notes-directory boundary check, allowing a user-selected `../` filename or absolute path to read files outside that directory. The reviewer should retain this as a base-side/report-body finding if needed.
3. A new bounded timeout retry helper with no tests for successful retry, exhausted attempts, and invalid attempt counts. The tests specialist should suggest concrete missing assertions, without claiming measured coverage.

This is a synthetic smoke test, not one of the assignment's three real samples. No external API requests, credential values, or executable model tools are included in this helper. Do not merge the intentionally faulty branch into the default branch.

To prepare the branch locally without changing your checkout:

```bash
uv run python -m ai_review.demo
```

If the branch already exists, the helper refuses to overwrite it. GitHub upload and PR creation are separate steps.
