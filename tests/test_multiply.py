from __future__ import annotations

from storyos.capture.manual import capture_from_text
from storyos.engine.analyzer import analyze_memory
from storyos.multiply.source import build_story_source
from storyos.multiply.templates import render_all, render_reel_script, render_youtube_script
from storyos.multiply.writer import write_script


SAMPLE = """\
topic: Production incident after hours
impact: Realized praise is not worth burnout.
blockers: The issue was not even ours, but I stayed up fixing it.
remember: Nobody asked me to sacrifice myself.
Got paged at 2AM and could not sleep afterwards.
"""


def test_render_scripts_use_source_material_only() -> None:
    memory = capture_from_text(SAMPLE, source="doclog")
    candidate = analyze_memory(memory)
    assert candidate is not None

    source = build_story_source(candidate, memory)
    reel = render_reel_script(source)
    youtube = render_youtube_script(source)

    assert "Production incident after hours" in reel
    assert "Nobody asked me to sacrifice myself" in reel
    assert "Got paged at 2AM" not in reel or "2AM" in youtube or "praise" in youtube
    assert "Instagram Reel Script" in reel
    assert "YouTube Script" in youtube
    assert candidate.id in reel
    assert memory.id in youtube


def test_render_all_formats() -> None:
    memory = capture_from_text(SAMPLE, source="doclog")
    candidate = analyze_memory(memory)
    assert candidate is not None
    source = build_story_source(candidate, memory)
    scripts = render_all(source)
    assert set(scripts) == {"reel", "shorts", "youtube"}


def test_write_script_to_outputs(tmp_path) -> None:
    memory = capture_from_text(SAMPLE, source="doclog")
    candidate = analyze_memory(memory)
    assert candidate is not None
    source = build_story_source(candidate, memory)
    path = write_script(
        tmp_path / "outputs",
        fmt="reel",
        story_short_id=candidate.short_id(),
        title=candidate.title,
        content=render_reel_script(source),
    )
    assert path.is_file()
    assert path.parent.name == "reel"
