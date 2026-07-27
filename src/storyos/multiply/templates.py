from __future__ import annotations

from pathlib import Path

from storyos.multiply.source import StorySource

SUPPORTED_FORMATS = ("reel", "shorts", "youtube")

FORMAT_LABELS = {
    "reel": "Instagram Reel (30–45s vertical)",
    "shorts": "YouTube Shorts (45–60s vertical, 9:16)",
    "youtube": "YouTube (5–8 minutes)",
}


def render_script(source: StorySource, fmt: str, *, prompt_path: Path | None = None) -> str:
    normalized = fmt.strip().lower()
    if normalized not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format {fmt!r}. Choose from: reel, shorts, youtube.")

    prompt_ref = str(prompt_path) if prompt_path else "storyos script prompt"
    sections = _story_discovery(source)
    scenes = _scenes_for_format(source, normalized)

    return f"""# {source.title} — {FORMAT_LABELS[normalized]}

> Generated with StoryOS script prompt: `{prompt_ref}`  
> Rules: discover the story in the capture — **never invent experiences**. Edit before recording.

---

## Story Discovery

**Core Story:** {sections["core_story"]}

**Central Conflict:** {sections["central_conflict"]}

**Transformation:** {sections["transformation"]}

**Emotional Theme:** {sections["emotional_theme"]}

**Why This Story Matters:** {sections["why_it_matters"]}

---

## Title

{source.title}

---

## Hook

"{source.hook}"

Open with a **moment**, not a lesson. The audience should immediately wonder: *What happened?*

---

## Full Script

{_render_scenes(scenes)}

---

## Ending

Do not end with advice. Leave emotional space.

**Closing line (from your capture):**  
"{source.candidate.potential_ending or source.lesson}"

**Lingering image idea:** {_lingering_image(source)}

---

## Shot Suggestions

| Scene | Camera | A-roll | B-roll | Movement | Lighting |
|---|---|---|---|---|---|
{_shot_table(scenes)}

---

## Music Direction

**Mood:** {_music_mood(source)}  
**Tempo:** Slow burn with one lift at the turn  
**Emotional progression:** Curiosity → connection → reflection → silence

---

## Source

- story: `{source.candidate.id}`
- memory: `{source.memory.id}`
- prompt: `{prompt_ref}`
- score: {source.candidate.score}/100
"""


def render_all(source: StorySource, *, prompt_path: Path | None = None) -> dict[str, str]:
    return {
        fmt: render_script(source, fmt, prompt_path=prompt_path)
        for fmt in SUPPORTED_FORMATS
    }


def render_reel_script(source: StorySource, *, prompt_path: Path | None = None) -> str:
    return render_script(source, "reel", prompt_path=prompt_path)


def render_shorts_script(source: StorySource, *, prompt_path: Path | None = None) -> str:
    return render_script(source, "shorts", prompt_path=prompt_path)


def render_youtube_script(source: StorySource, *, prompt_path: Path | None = None) -> str:
    return render_script(source, "youtube", prompt_path=prompt_path)


def _story_discovery(source: StorySource) -> dict[str, str]:
    return {
        "core_story": source.topic or source.title,
        "central_conflict": source.candidate.conflict,
        "transformation": source.candidate.transformation,
        "emotional_theme": source.candidate.emotion,
        "why_it_matters": source.candidate.potential_ending or _first_line(source.impact) or source.lesson,
    }


def _scenes_for_format(source: StorySource, fmt: str) -> list[dict[str, str]]:
    if fmt == "reel":
        return [
            _scene("Moment", "0:00–0:03", source.hook, "Close-up or bold text overlay", "Direct to camera"),
            _scene("Curiosity", "0:03–0:10", source.candidate.conflict, "Quick cut b-roll", "Handheld"),
            _scene("Conflict", "0:10–0:22", _short_line(source.context, 180), "Workspace / incident footage", "Screen glow"),
            _scene("Discovery", "0:22–0:35", source.turn, "The fix or turning point", "Static then push-in"),
            _scene("Reflection", "0:35–0:45", source.lesson, "Calmer frame, same as open for loop", "Soft natural light"),
        ]
    if fmt == "shorts":
        return [
            _scene("Moment", "0:00–0:05", source.hook, "Cold open, large on-screen text", "Direct to camera"),
            _scene("Curiosity", "0:05–0:15", source.candidate.conflict, "Fast b-roll", "Handheld energy"),
            _scene("Story", "0:15–0:30", _short_line(source.context, 200), "Screen or environment", "Mixed"),
            _scene("Discovery", "0:30–0:45", source.turn, "One clear turning-point shot", "Contrast lighting"),
            _scene("Open Ending", "0:45–0:60", source.lesson, "Hold on face or empty frame", "Quiet, still"),
        ]
    return [
        _scene("Moment", "0:00–0:20", source.hook, "Open on the strongest physical detail", "Direct to camera"),
        _scene("Curiosity", "0:20–1:00", source.candidate.conflict, "Establish the stakes visually", "Observational"),
        _scene("Story", "1:00–2:30", _short_line(source.context, 420), "B-roll from your library", "Natural movement"),
        _scene("Conflict", "2:30–4:00", _bullet_narration(source.blockers), "Incident / problem visuals", "Tighter, tense"),
        _scene("Discovery", "4:00–5:30", source.turn, "Show what changed", "Release in framing"),
        _scene("Reflection", "5:30–6:30", source.lesson, "Return to narrator, slower pace", "Soft, intimate"),
        _scene("Open Ending", "6:30–7:00", source.candidate.potential_ending or "...", "Lingering image, no CTA lesson", "Silence-friendly"),
    ]


def _scene(name: str, timing: str, narration: str, visual: str, camera: str) -> dict[str, str]:
    return {
        "name": name,
        "timing": timing,
        "narration": narration,
        "visual": visual,
        "camera": camera,
        "a_roll": "Creator on camera" if "camera" in camera.lower() else "Voiceover over b-roll",
        "b_roll": visual,
        "movement": "Handheld" if "handheld" in camera.lower() else "Static",
        "lighting": "Natural / intimate",
    }


def _render_scenes(scenes: list[dict[str, str]]) -> str:
    blocks: list[str] = []
    for index, scene in enumerate(scenes, start=1):
        blocks.append(
            f"""### Scene {index} — {scene["name"]} ({scene["timing"]})

**Narration:**  
"{scene["narration"]}"

**What the camera sees:** {scene["visual"]}  
**Camera:** {scene["camera"]}  
**A-roll:** {scene["a_roll"]}  
**B-roll:** {scene["b_roll"]}  
**Movement:** {scene["movement"]}  
**Lighting mood:** {scene["lighting"]}
"""
        )
    return "\n".join(blocks)


def _shot_table(scenes: list[dict[str, str]]) -> str:
    rows = []
    for index, scene in enumerate(scenes, start=1):
        rows.append(
            f"| {index}. {scene['name']} | {scene['camera']} | {scene['a_roll']} | {scene['b_roll']} | {scene['movement']} | {scene['lighting']} |"
        )
    return "\n".join(rows)


def _lingering_image(source: StorySource) -> str:
    if source.blockers:
        return _first_line(source.blockers) or "A quiet frame after the incident ends."
    return "An ordinary detail from the day — unchanged, but seen differently now."


def _music_mood(source: StorySource) -> str:
    emotion = source.candidate.emotion.lower()
    if emotion in {"exhaustion", "fear", "frustration"}:
        return "Tense, sparse, late-night"
    if emotion in {"pride", "curiosity"}:
        return "Hopeful, restrained, forward-moving"
    return "Intimate, observational, human"


def _bullet_narration(text: str | None) -> str:
    if not text:
        return "(Expand from your capture — do not invent details.)"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "(Expand from your capture — do not invent details.)"
    return " / ".join(lines[:3])


def _short_line(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _first_line(text: str | None) -> str:
    if not text:
        return ""
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""
