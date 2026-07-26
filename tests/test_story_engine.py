from __future__ import annotations

from datetime import datetime

from storyos.capture.manual import capture_from_text
from storyos.engine.analyzer import analyze_memory
from storyos.engine.discover import discover_memories
from storyos.models.story import STORY_STATUS_DISMISSED
from storyos.store.memory_store import MemoryStore
from storyos.store.story_store import StoryStore

DOCLOG_SAMPLE = """\
topic: FSM Logstash pod-log disk runaway — 10.104.8.77
worked_on: |
  Central Logstash node ingesting FSM EKS pod logs from Kafka.
impact: |
  Explained why disk filled despite cron running — broken log lifecycle, not cron failure.
  Separated rotate (logrotate) vs archive (upload script on closed copies only).
blockers: |
  Three script iterations in one week — each fixed one symptom not the full pipeline.
remember: |
  Golden rule: active .log = Logstash owns it. Only upload .log.1 rotated snapshots.
status: complete
"""


def test_analyze_memory_finds_high_scoring_doclog_story() -> None:
    memory = capture_from_text(DOCLOG_SAMPLE, source="doclog")
    candidate = analyze_memory(memory)
    assert candidate is not None
    assert candidate.score >= 60
    assert "Logstash" in candidate.title or "disk" in candidate.title.lower()
    assert candidate.emotion in ("exhaustion", "frustration", "reflection")
    assert "engineering" in candidate.categories
    assert candidate.dimensions.conflict >= 3
    assert candidate.dimensions.transformation >= 3


def test_analyze_memory_skips_short_capture() -> None:
    memory = capture_from_text("short", source="journal")
    assert analyze_memory(memory) is None


def test_discover_memories_persists_candidates(tmp_path) -> None:
    db_path = tmp_path / "memories.db"
    memory_store = MemoryStore(db_path)
    story_store = StoryStore(db_path)

    memory_store.add(capture_from_text(DOCLOG_SAMPLE, source="doclog"))
    result = discover_memories(memory_store, story_store)
    assert result.discovered == 1
    assert story_store.count_by_status("active") == 1

    listed = story_store.list_candidates(min_score=0)
    assert len(listed) == 1
    assert listed[0].score >= 60


def test_discover_respects_dismissed_unless_forced(tmp_path) -> None:
    db_path = tmp_path / "memories.db"
    memory_store = MemoryStore(db_path)
    story_store = StoryStore(db_path)
    memory_store.add(capture_from_text(DOCLOG_SAMPLE, source="doclog"))

    discover_memories(memory_store, story_store)
    candidate = story_store.list_candidates()[0]
    story_store.set_status(candidate.id, STORY_STATUS_DISMISSED)

    rediscover = discover_memories(memory_store, story_store)
    assert rediscover.skipped == 1

    forced = discover_memories(memory_store, story_store, force=True)
    assert forced.updated == 1
    refreshed = story_store.get(candidate.id)
    assert refreshed is not None
    assert refreshed.status == "active"


def test_discover_since_filters_by_date(tmp_path) -> None:
    db_path = tmp_path / "memories.db"
    memory_store = MemoryStore(db_path)
    story_store = StoryStore(db_path)

    old = capture_from_text(DOCLOG_SAMPLE, source="doclog", captured_at=datetime(2020, 1, 1))
    new = capture_from_text(DOCLOG_SAMPLE + "\nextra detail for novelty", source="doclog")
    memory_store.add(old)
    memory_store.add(new)

    result = discover_memories(memory_store, story_store, since_days=7)
    assert result.analyzed == 1
    assert result.discovered == 1
