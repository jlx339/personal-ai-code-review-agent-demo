#!/bin/sh
# Run in the repository root. This installs dependencies; it never reads API keys.
set -eu
cd "$(dirname "$0")/.."
if ! command -v uv >/dev/null 2>&1; then
    echo 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/' >&2
    exit 1
fi
uv sync --python 3.11
uv run pytest -q
printf '\nSetup and tests passed. The reviewer is ready for local configuration.\n'
