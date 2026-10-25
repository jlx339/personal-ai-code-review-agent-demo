"""Limits for a small, free-tier review."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    model: str = 'gemini-3.5-flash-lite'
    reasoning_model: str | None = 'gemini-3.8-flash'
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
        allowed=('gemini-3.5-flash-lite','gemini-3.8-flash')
        if self.model not in allowed or self.reasoning_model not in (None,*allowed):
            raise ValueError('Only the configured free-tier model allowlist is supported')
        if any(v <= 0 for k, v in vars(self).items() if k not in ('model','reasoning_model')):
            raise ValueError('Limits must be positive')
