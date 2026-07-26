from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ParsedCapture:
    content: str
    source: str
    captured_at: datetime | None


def build_capture_template(*, default_source: str, captured_at: datetime) -> str:
    date_hint = captured_at.strftime("%Y-%m-%d %H:%M")
    return f"""# StoryOS — What happened today?
#
# Write below the dashed line, then save and close this file.
# Leave the body empty to cancel without saving.
#
# Optional fields (above the line):
#   source — provenance label (default: {default_source})
#   date   — when it happened (default: now), e.g. {date_hint}

source: {default_source}
date:

---

"""


def parse_capture_document(
    raw: str,
    *,
    default_source: str,
    default_captured_at: datetime | None = None,
) -> ParsedCapture | None:
    """Parse editor output. Returns None when the user cancelled (empty body)."""
    normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
    if "---" not in normalized:
        body = _strip_leading_comment_lines(normalized).strip()
        if not body:
            return None
        return ParsedCapture(
            content=body,
            source=default_source,
            captured_at=default_captured_at,
        )

    header, body = normalized.split("\n---\n", 1)
    source = default_source
    captured_at = default_captured_at

    for line in header.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.lower().startswith("source:"):
            value = stripped.split(":", 1)[1].strip()
            if value:
                source = value
        elif stripped.lower().startswith("date:"):
            value = stripped.split(":", 1)[1].strip()
            if value:
                captured_at = _parse_capture_date(value)

    content = body.strip()
    if not content:
        return None

    return ParsedCapture(content=content, source=source, captured_at=captured_at)


def _strip_leading_comment_lines(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)


def _parse_capture_date(value: str) -> datetime:
    formats = (
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    )
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(
        f"Invalid date {value!r}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM."
    )
