"""Limits for a small, free-tier review."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    model: str = 'gemini-3.5-flash-lite'
    max_requests: int = 12
    specialist_turns: int = 3
    verifier_turns: int = 2
    output_tokens: int = 4000
    request_interval: float = 5.0
    max_files: int = 10
    max_changed_lines: int = 1000
    max_file_bytes: int = 65536
    max_source_chars: int = 100000
    max_tool_calls: int = 4
    tool_output_chars: int = 12000

    def __post_init__(self):
        if self.model != 'gemini-3.5-flash-lite':
            raise ValueError('Only the configured free-tier model is supported')
        if any(v <= 0 for k, v in vars(self).items() if k != 'model'):
            raise ValueError('Limits must be positive')
