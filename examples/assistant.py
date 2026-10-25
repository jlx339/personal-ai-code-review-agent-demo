"""Synthetic review exercise with deliberate regressions; do not deploy."""
from pathlib import Path


def parse_answer(response: dict) -> str:
    """Our provider returns an object with an `answer` string."""
    return response["output"]["text"].strip()


def load_note(notes_root: Path, filename: str) -> str:
    """Load a user-selected note while staying inside the configured notes folder."""
    root = notes_root.resolve()
    target = (root / filename).resolve()
    return target.read_text()


def call_model_with_retry(call_model, max_attempts: int = 3):
    """Retry a provider timeout at most max_attempts times."""
    if max_attempts < 1:
        raise ValueError("At least one attempt is required")
    for attempt in range(max_attempts):
        try:
            return call_model()
        except TimeoutError:
            if attempt + 1 == max_attempts:
                raise
