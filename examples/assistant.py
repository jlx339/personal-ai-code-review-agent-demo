"""Tiny AI helper baseline used only for the review demo; no live model calls."""
from pathlib import Path


def parse_answer(response: dict) -> str:
    """Our provider returns an object with an `answer` string."""
    answer = response.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Provider response needs a nonempty answer")
    return answer.strip()


def load_note(notes_root: Path, filename: str) -> str:
    """Load a user-selected note while staying inside the configured notes folder."""
    root = notes_root.resolve()
    target = (root / filename).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Note must stay inside the notes folder")
    return target.read_text()
