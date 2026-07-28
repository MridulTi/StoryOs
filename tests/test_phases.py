from __future__ import annotations

from storyos.capture.manual import capture_from_text
from storyos.engine.analyzer import analyze_memory
from storyos.graph.related import find_related_stories
from storyos.models.developed_story import DevelopedStory, InterviewQA
from storyos.multiply.formats import PUBLIC_FORMATS
from storyos.multiply.generator import generate_script_content
from storyos.multiply.prompt_builder import check_shareability
from storyos.multiply.source import build_story_bundle, build_story_source
from storyos.llm.config import LLMConfig
from storyos.patterns.themes import cluster_themes
from storyos.store.developed_store import DevelopedStoryStore
from storyos.store.graph_store import GraphStore
from storyos.store.memory_store import MemoryStore
from storyos.store.story_store import StoryStore
from storyos.storyboard.builder import build_storyboard_from_script, render_storyboard_markdown
from storyos.store.media_store import MediaStore
from storyos.models.media import MediaAsset
import pytest


MAIN = """\
topic: Feeling stuck and tired
impact: Realized I'm depleted, not lazy.
remember: This has been building for weeks.
"""

BG = """\
topic: Oncall page at 2AM
impact: Could not sleep after fixing someone else's issue.
blockers: Slack kept buzzing. Laptop glow in a dark room.
"""


def _stores(tmp_path):
    db = tmp_path / "memories.db"
    return MemoryStore(db), StoryStore(db), GraphStore(db), DevelopedStoryStore(db), MediaStore(db)


def test_related_stories_rank_background(tmp_path) -> None:
    memory_store, story_store, graph_store, _, _ = _stores(tmp_path)
    main_memory = capture_from_text(MAIN, source="doclog")
    bg_memory = capture_from_text(BG, source="doclog")
    memory_store.add(main_memory)
    memory_store.add(bg_memory)
    main_candidate = analyze_memory(main_memory)
    bg_candidate = analyze_memory(bg_memory)
    assert main_candidate and bg_candidate
    story_store.upsert(main_candidate)
    story_store.upsert(bg_candidate)

    matches = find_related_stories(
        main_candidate,
        main_memory,
        memory_store=memory_store,
        story_store=story_store,
        graph_store=graph_store,
    )
    assert matches
    assert matches[0].candidate.id == bg_candidate.id


def test_developed_store_roundtrip(tmp_path) -> None:
    _, story_store, _, developed_store, _ = _stores(tmp_path)
    memory = capture_from_text(MAIN, source="doclog")
    candidate = analyze_memory(memory)
    assert candidate
    story_store.upsert(candidate)
    story = DevelopedStory(
        candidate_id=candidate.id,
        memory_ids=[candidate.memory_id],
        title=candidate.title,
        interview=[InterviewQA("emotion", "What were you feeling?", "Empty and wired.")],
        creator_narrative="Empty and wired.",
    )
    developed_store.upsert(story)
    loaded = developed_store.get_by_candidate(candidate.id)
    assert loaded is not None
    assert loaded.interview[0].answer == "Empty and wired."


def test_shareability_blocks_public_formats() -> None:
    developed = DevelopedStory(
        candidate_id="c1",
        memory_ids=["m1"],
        title="Private",
        shareability="private",
    )
    with pytest.raises(ValueError):
        check_shareability("linkedin", developed)
    check_shareability("journal", developed)


def test_theme_clustering(tmp_path) -> None:
    memory_store, story_store, _, _, _ = _stores(tmp_path)
    for sample in (MAIN, BG, MAIN.replace("weeks", "months")):
        memory = capture_from_text(sample, source="doclog")
        memory_store.add(memory)
        candidate = analyze_memory(memory)
        if candidate:
            story_store.upsert(candidate)
    patterns = cluster_themes(memory_store=memory_store, story_store=story_store)
    assert patterns


def test_storyboard_builder(tmp_path) -> None:
    _, _, _, _, media_store = _stores(tmp_path)
    media_store.upsert(MediaAsset(path="/vids/laptop-glow.mp4", filename="laptop-glow.mp4", tags=["laptop", "glow"]))
    script = """### Scene 1 — Conflict (0:10–0:22)

**Narration:**  
"Slack kept buzzing."

**What the camera sees:** Laptop glow in a dark room
"""
    rows = build_storyboard_from_script(script, media_store=media_store)
    markdown = render_storyboard_markdown("Test", rows)
    assert "laptop-glow.mp4" in markdown or "Capture:" in markdown
