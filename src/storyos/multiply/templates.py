from __future__ import annotations

from storyos.multiply.source import StorySource

SUPPORTED_FORMATS = ("reel", "shorts", "youtube")


def render_script(source: StorySource, fmt: str) -> str:
    normalized = fmt.strip().lower()
    if normalized == "reel":
        return render_reel_script(source)
    if normalized == "shorts":
        return render_shorts_script(source)
    if normalized == "youtube":
        return render_youtube_script(source)
    raise ValueError(f"Unsupported format {fmt!r}. Choose from: reel, shorts, youtube.")


def render_all(source: StorySource) -> dict[str, str]:
    return {fmt: render_script(source, fmt) for fmt in SUPPORTED_FORMATS}


def render_reel_script(source: StorySource) -> str:
    return f"""# Instagram Reel Script — {source.title}

> Derived from your capture. Edit before recording. Do not add facts that are not in the source memory.

**Format:** 30–45s vertical reel  
**Emotion:** {source.candidate.emotion}  
**Score:** {source.candidate.score}/100

---

## Beat 1 — Hook (0:00–0:03)
**On camera / text on screen:**  
"{source.hook}"

**Visual:** Close-up, direct to camera OR bold text overlay.

**Audio:** Start with pattern interrupt — no intro logo.

---

## Beat 2 — Problem (0:03–0:12)
**Say:**  
"{source.candidate.conflict}"

**Visual:** B-roll that matches the moment (screen, workspace, commute, incident screenshot — use your own footage).

---

## Beat 3 — Turn (0:12–0:28)
**Say:**  
"{source.turn}"

**Visual:** Show the work, the fix, or the moment things changed.

---

## Beat 4 — Payoff (0:28–0:40)
**Say:**  
"{source.lesson}"

**Visual:** Calmer shot. Let the line land.

---

## Beat 5 — CTA (0:40–0:45)
**Say:**  
"If this feels familiar, you are not alone. Follow for more real engineering stories."

**Visual:** Same as opening frame for loop-friendly ending.

---

## Caption draft
{source.title}

{source.lesson}

#engineering #storytelling #devops

---

## Source
- story: {source.candidate.id}
- memory: {source.memory.id}
"""


def render_shorts_script(source: StorySource) -> str:
    return f"""# YouTube Shorts Script — {source.title}

> Derived from your capture. Edit before recording. Do not add facts that are not in the source memory.

**Format:** 45–60s vertical (9:16)  
**Emotion:** {source.candidate.emotion}  
**Score:** {source.candidate.score}/100

---

## 0:00 — Cold open
**Say:**  
"{source.hook}"

**On-screen text:** Same line, large type in the first 2 seconds.

---

## 0:05 — Stakes
**Say:**  
"{source.candidate.conflict}"

**Visual:** Fast cut. Keep energy high.

---

## 0:15 — What happened
**Say:**  
"{_short_line(source.context, 220)}"

**Visual:** Quick b-roll or screen recording from your library.

---

## 0:30 — What changed
**Say:**  
"{source.turn}"

**Visual:** One clear shot that represents the turning point.

---

## 0:45 — Lesson
**Say:**  
"{source.lesson}"

**Visual:** Back to camera.

---

## 0:55 — Close
**Say:**  
"Save this if you have been through something similar."

**Pinned comment idea:**  
"{source.lesson}"

---

## Title options
1. {source.title}
2. {source.hook}
3. What nobody tells you about {source.candidate.emotion}

---

## Source
- story: {source.candidate.id}
- memory: {source.memory.id}
"""


def render_youtube_script(source: StorySource) -> str:
    return f"""# YouTube Script — {source.title}

> Derived from your capture. Edit before recording. Do not add facts that are not in the source memory.

**Target length:** 5–8 minutes  
**Emotion:** {source.candidate.emotion}  
**Score:** {source.candidate.score}/100

---

## Title options
1. {source.title}
2. {source.hook}
3. The real story behind {source.candidate.emotion}

## Thumbnail text
"{_short_line(source.hook, 48)}"

---

## Hook (0:00–0:20)
**Say:**  
"{source.hook}"

**Notes:** Open with tension, not context. No channel intro yet.

---

## Context (0:20–1:30)
**Say:**  
"{_short_line(source.context, 420)}"

**Notes:** Only use details from your capture. Cut anything you cannot stand behind.

---

## Conflict (1:30–3:00)
**Say:**  
"{source.candidate.conflict}"

**Expand from your notes:**  
{_bullet_block(source.blockers)}

**B-roll ideas:** Use your own footage where possible. Note gaps to record later.

---

## Turning point (3:00–4:30)
**Say:**  
"{source.turn}"

**Notes:** This is the change — what shifted, what you learned, what broke.

---

## Lesson (4:30–5:30)
**Say:**  
"{source.lesson}"

**Potential ending line:**  
"{source.candidate.potential_ending}"

---

## CTA (5:30–6:00)
**Say:**  
"If this story felt familiar, comment with the moment you realized the same thing. Subscribe for more stories from real work — not generic advice."

---

## Description draft
{source.title}

In this video: {source.hook}

Key takeaway: {source.lesson}

---
Generated from StoryOS memory `{source.memory.short_id()}`.

---

## Source
- story: {source.candidate.id}
- memory: {source.memory.id}
"""


def _short_line(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _bullet_block(text: str | None) -> str:
    if not text:
        return "- (Add detail from your capture before recording.)"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "- (Add detail from your capture before recording.)"
    return "\n".join(f"- {line}" for line in lines[:6])
