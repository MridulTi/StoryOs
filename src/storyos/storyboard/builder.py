from __future__ import annotations

import re
from dataclasses import dataclass

from storyos.models.media import MediaAsset
from storyos.store.media_store import MediaStore

TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}")


@dataclass(frozen=True)
class StoryboardRow:
    scene: str
    visual: str
    clip: str | None
    need_recording: bool
    recommendation: str


def build_storyboard_from_script(
    script_content: str,
    *,
    media_store: MediaStore,
) -> list[StoryboardRow]:
    scenes = _extract_scenes(script_content)
    rows: list[StoryboardRow] = []
    for scene in scenes:
        tokens = _tokens(scene.visual + " " + scene.narration)
        matches = media_store.search_by_tokens(tokens, limit=1)
        clip = matches[0].filename if matches else None
        need_recording = clip is None
        recommendation = ""
        if need_recording:
            recommendation = f"Capture: {scene.visual}"
        rows.append(
            StoryboardRow(
                scene=scene.name,
                visual=scene.visual,
                clip=clip,
                need_recording=need_recording,
                recommendation=recommendation,
            )
        )
    return rows


def render_storyboard_markdown(title: str, rows: list[StoryboardRow]) -> str:
    lines = [
        f"# Storyboard — {title}",
        "",
        "| Scene | Visual | Existing clip | Need recording? | Recommendation |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        clip = row.clip or "—"
        need = "Yes" if row.need_recording else "No"
        rec = row.recommendation or "—"
        lines.append(f"| {row.scene} | {row.visual} | {clip} | {need} | {rec} |")
    return "\n".join(lines) + "\n"


@dataclass
class _Scene:
    name: str
    visual: str
    narration: str


def _extract_scenes(content: str) -> list[_Scene]:
    scenes: list[_Scene] = []
    current_name = "Scene"
    visual = ""
    narration = ""
    for line in content.splitlines():
        if line.startswith("### Scene"):
            if visual or narration:
                scenes.append(_Scene(name=current_name, visual=visual or narration, narration=narration))
            current_name = line.replace("###", "").strip()
            visual = ""
            narration = ""
            continue
        if line.lower().startswith("**what the camera sees:**"):
            visual = line.split(":", 1)[-1].strip()
        if line.lower().startswith("**narration:**"):
            narration = line.split(":", 1)[-1].strip().strip('"')
    if visual or narration:
        scenes.append(_Scene(name=current_name, visual=visual or narration, narration=narration))
    if not scenes:
        scenes.append(_Scene(name="Opening", visual="Direct to camera", narration="Open on the strongest moment"))
    return scenes


def _tokens(text: str) -> set[str]:
    stop = {"the", "and", "for", "with", "from", "your", "camera", "scene"}
    return {
        match.group(0)
        for match in TOKEN_PATTERN.finditer(text.lower())
        if match.group(0) not in stop
    }
