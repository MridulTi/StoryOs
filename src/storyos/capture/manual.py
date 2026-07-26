from __future__ import annotations

import sys
from datetime import datetime

from storyos.models.memory import Memory


def capture_from_text(
    content: str,
    *,
    source: str,
    captured_at: datetime | None = None,
) -> Memory:
    text = content.strip()
    if not text:
        raise ValueError("Capture content cannot be empty.")

    when = captured_at or datetime.now()
    return Memory(
        content=text,
        source=source,
        captured_at=when,
    )


def read_stdin_content() -> str:
    if sys.stdin.isatty():
        return ""
    return sys.stdin.read()
