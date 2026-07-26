from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from storyos.capture.template import ParsedCapture, build_capture_template, parse_capture_document


class CaptureCancelled(Exception):
    """Raised when the user saves an empty capture template."""


class EditorNotFoundError(Exception):
    """Raised when no editor is configured or available."""


def resolve_editor(configured: str | None = None) -> str:
    if configured:
        return configured
    return os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nano"


def capture_via_editor(
    *,
    default_source: str,
    editor: str | None = None,
    captured_at: datetime | None = None,
) -> ParsedCapture:
    when = captured_at or datetime.now()
    template = build_capture_template(default_source=default_source, captured_at=when)
    editor_command = resolve_editor(editor)
    raw = _open_in_editor(template, editor_command)

    try:
        parsed = parse_capture_document(
            raw,
            default_source=default_source,
            default_captured_at=when,
        )
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    if parsed is None:
        raise CaptureCancelled("Capture cancelled — nothing was written.")
    return parsed


def save_capture_file(
    captures_path: Path,
    parsed: ParsedCapture,
    *,
    memory_id: str,
    captured_at: datetime,
) -> Path:
    captures_path.mkdir(parents=True, exist_ok=True)
    stamp = captured_at.strftime("%Y-%m-%d-%H%M%S")
    short_id = memory_id.split("-")[0]
    path = captures_path / f"{stamp}-{short_id}.md"
    path.write_text(
        "\n".join(
            [
                f"source: {parsed.source}",
                f"date: {captured_at.strftime('%Y-%m-%d %H:%M')}",
                "",
                "---",
                "",
                parsed.content,
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _open_in_editor(template: str, editor_command: str) -> str:
    fd, temp_name = tempfile.mkstemp(prefix="storyos-capture-", suffix=".md")
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(template)

        command = [*shlex.split(editor_command), str(temp_path)]
        try:
            exit_code = subprocess.call(command)
        except FileNotFoundError as exc:
            raise EditorNotFoundError(
                f"Editor not found: {editor_command!r}. "
                "Set $EDITOR or [capture].editor in storyos.toml."
            ) from exc

        if exit_code != 0:
            raise CaptureCancelled(f"Editor exited with code {exit_code}.")

        return temp_path.read_text(encoding="utf-8")
    finally:
        temp_path.unlink(missing_ok=True)
