from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from storyos.capture.editor import CaptureCancelled, capture_via_editor, save_capture_file
from storyos.capture.template import ParsedCapture


def test_capture_via_editor_parses_saved_content() -> None:
    with patch(
        "storyos.capture.editor._open_in_editor",
        return_value="source: journal\n\ndate:\n\n---\n\nSomething meaningful happened.\n",
    ):
        parsed = capture_via_editor(default_source="journal", editor="fake")

    assert parsed.content == "Something meaningful happened."
    assert parsed.source == "journal"


def test_capture_via_editor_empty_body_cancels() -> None:
    with patch(
        "storyos.capture.editor._open_in_editor",
        return_value="source: journal\n\ndate:\n\n---\n\n",
    ):
        with pytest.raises(CaptureCancelled):
            capture_via_editor(default_source="journal", editor="fake")


def test_save_capture_file_writes_markdown(tmp_path: Path) -> None:
    parsed = ParsedCapture(
        content="Hello world.",
        source="journal",
        captured_at=None,
    )
    from datetime import datetime

    when = datetime(2026, 7, 26, 12, 0)
    path = save_capture_file(
        tmp_path,
        parsed,
        memory_id="abcd-1234",
        captured_at=when,
    )
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "Hello world." in text
    assert "source: journal" in text
