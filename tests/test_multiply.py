from __future__ import annotations

from pathlib import Path

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
    reel = render_reel_script(source, prompt_path=Path("/tmp/storypromt.md"))
    youtube = render_youtube_script(source, prompt_path=Path("/tmp/storypromt.md"))

    assert "Production incident after hours" in reel
    assert "Nobody asked me to sacrifice myself" in reel
    assert "## Story Discovery" in reel
    assert "## Full Script" in youtube
    assert "## Shot Suggestions" in youtube
    assert "storypromt.md" in reel


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
