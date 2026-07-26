from __future__ import annotations

from datetime import datetime

import pytest

from storyos.capture.template import build_capture_template, parse_capture_document


def test_build_capture_template_includes_source() -> None:
    when = datetime(2026, 7, 26, 22, 0)
    template = build_capture_template(default_source="journal", captured_at=when)
    assert "source: journal" in template
    assert "---" in template


def test_parse_capture_document_extracts_body_and_source() -> None:
    raw = """\
source: devlog
date: 2026-07-20 14:30

---

Got paged at 2AM fixing production.
"""
    parsed = parse_capture_document(raw, default_source="journal")
    assert parsed is not None
    assert parsed.source == "devlog"
    assert "Got paged at 2AM" in parsed.content
    assert parsed.captured_at == datetime(2026, 7, 20, 14, 30)


def test_parse_capture_document_empty_body_means_cancel() -> None:
    raw = """\
source: journal

---


"""
    assert parse_capture_document(raw, default_source="journal") is None


def test_parse_capture_document_invalid_date_raises() -> None:
    raw = """\
date: not-a-date

---

Something happened.
"""
    with pytest.raises(ValueError, match="Invalid date"):
        parse_capture_document(raw, default_source="journal")
