from __future__ import annotations

from pathlib import Path

from storyos.capture.manual import capture_from_text
from storyos.engine.analyzer import analyze_memory
from storyos.multiply.source import build_story_bundle, build_story_source
from storyos.multiply.templates import render_all, render_reel_script, render_youtube_script
from storyos.multiply.writer import write_script


SAMPLE = """\
topic: Production incident after hours
impact: Realized praise is not worth burnout.
blockers: The issue was not even ours, but I stayed up fixing it.
remember: Nobody asked me to sacrifice myself.
Got paged at 2AM and could not sleep afterwards.
"""

ONCALL = """\
topic: Oncall page at 2AM
impact: Could not sleep after fixing someone else's issue.
blockers: Pager went off twice. Slack lit up.
remember: The fix wasn't even on our team.
Stayed up until 4AM staring at the ceiling.
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


def test_background_stories_in_prompt_and_template(tmp_path) -> None:
    main_memory = capture_from_text(
        "topic: Feeling stuck and tired\nimpact: Running on empty.\nremember: I need rest, not more praise.",
        source="journal",
    )
    bg_memory = capture_from_text(ONCALL, source="doclog")
    main_candidate = analyze_memory(main_memory)
    bg_candidate = analyze_memory(bg_memory)
    assert main_candidate is not None
    assert bg_candidate is not None

    bundle = build_story_bundle(
        build_story_source(main_candidate, main_memory),
        build_story_source(bg_candidate, bg_memory),
    )
    prompt_path = tmp_path / "storypromt.md"
    prompt_path.write_text("Never invent.", encoding="utf-8")

    from storyos.multiply.prompt_builder import build_generation_prompt

    prompt = build_generation_prompt(bundle, "reel", script_prompt_path=prompt_path)
    assert "Main story memory" in prompt
    assert "Background stories" in prompt
    assert "Pager went off twice" in prompt
    assert "Running on empty" in prompt

    reel = render_reel_script(bundle, prompt_path=prompt_path)
    assert "Pager went off twice" in reel
    assert "background:" in reel
