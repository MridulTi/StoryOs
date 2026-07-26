from __future__ import annotations

import re
from dataclasses import dataclass

from storyos.models.memory import Memory
from storyos.models.story import StoryCandidate, StoryDimensions

FIELD_PATTERN = re.compile(
    r"^(topic|impact|blockers|remember|worked_on|status)\s*:\s*(.*)$",
    re.IGNORECASE | re.MULTILINE,
)

EMOTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "exhaustion": ("exhaust", "tired", "couldn't sleep", "burnout", "on-call", "2am", "2 am"),
    "fear": ("afraid", "fear", "anxious", "anxiety", "worried", "panic"),
    "frustration": ("frustrat", "annoyed", "angry", "hate", "stuck"),
    "pride": ("proud", "celebrat", "shipped", "released", "won"),
    "curiosity": ("curious", "learned", "discovered", "investigat"),
    "regret": ("regret", "should have", "wish i", "mistake"),
}

CONFLICT_KEYWORDS = (
    "problem",
    "incident",
    "outage",
    "failed",
    "failure",
    "blocker",
    "blocked",
    "risk",
    "sacrifice",
    "conflict",
    "root cause",
    "production",
    "emergency",
    "crisis",
    "broken",
    "bug",
    "issue",
)

TRANSFORMATION_KEYWORDS = (
    "realized",
    "learned",
    "changed",
    "understand",
    "now i",
    "impact:",
    "remember:",
    "solution",
    "fixed",
    "prevent",
    "separated",
    "finally",
)

RELATABILITY_KEYWORDS = (
    "imposter",
    "first day",
    "rejected",
    "burnout",
    "on-call",
    "production",
    "interview",
    "junior",
    "senior",
    "team",
    "manager",
    "startup",
    "deadline",
)

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "engineering": ("production", "deploy", "incident", "logstash", "kubernetes", "aws", "devops", "git"),
    "burnout": ("burnout", "exhaust", "on-call", "2am", "sacrifice"),
    "failure": ("failed", "failure", "mistake", "outage", "incident"),
    "success": ("shipped", "released", "fixed", "solved", "complete"),
    "leadership": ("team", "led", "mentor", "manager", "decision"),
    "growth": ("learned", "realized", "changed", "growth", "impact:"),
    "productivity": ("workflow", "automated", "process", "efficiency"),
    "startup": ("startup", "founder", "mvp", "launch"),
}


@dataclass(frozen=True)
class ParsedFields:
    topic: str | None = None
    impact: str | None = None
    blockers: str | None = None
    remember: str | None = None
    worked_on: str | None = None
    status: str | None = None


def analyze_memory(memory: Memory, *, recent_topics: set[str] | None = None) -> StoryCandidate | None:
    content = memory.content.strip()
    if len(content) < 40:
        return None

    fields = parse_structured_fields(content)
    lowered = content.lower()
    recent_topics = recent_topics or set()

    emotion_label, emotion_score, emotion_hits = _score_emotion(lowered)
    conflict_label, conflict_score, conflict_hits = _score_conflict(content, fields, lowered)
    transform_label, transform_score, transform_hits = _score_transformation(content, fields, lowered)
    relatability_score, relatability_hits = _score_keyword_hits(lowered, RELATABILITY_KEYWORDS, cap=5)
    novelty_score, novelty_hits = _score_novelty(fields, lowered, recent_topics)

    dimensions = StoryDimensions(
        emotion=emotion_score,
        conflict=conflict_score,
        transformation=transform_score,
        relatability=relatability_score,
        novelty=novelty_score,
    )
    score = dimensions.composite_score()
    if score < 35:
        return None

    title = suggest_title(content, fields)
    categories = detect_categories(lowered, fields)
    potential_ending = suggest_potential_ending(fields, content)

    return StoryCandidate(
        memory_id=memory.id,
        title=title,
        score=score,
        dimensions=dimensions,
        conflict=conflict_label,
        emotion=emotion_label,
        transformation=transform_label,
        potential_ending=potential_ending,
        categories=categories,
        signals={
            "emotion_hits": emotion_hits,
            "conflict_hits": conflict_hits,
            "transformation_hits": transform_hits,
            "relatability_hits": relatability_hits,
            "novelty_hits": novelty_hits,
            "structured_fields": {
                key: value
                for key, value in {
                    "topic": fields.topic,
                    "impact": _first_line(fields.impact),
                    "blockers": _first_line(fields.blockers),
                    "remember": _first_line(fields.remember),
                }.items()
                if value
            },
        },
    )


def parse_structured_fields(content: str) -> ParsedFields:
    values: dict[str, str] = {}
    for match in FIELD_PATTERN.finditer(content):
        key = match.group(1).lower()
        if key not in values:
            values[key] = match.group(2).strip()

    block_start = content.find("blockers:")
    if block_start >= 0:
        values.setdefault("blockers", _extract_block(content, "blockers"))
    impact_start = content.find("impact:")
    if impact_start >= 0:
        values.setdefault("impact", _extract_block(content, "impact"))
    remember_start = content.find("remember:")
    if remember_start >= 0:
        values.setdefault("remember", _extract_block(content, "remember"))
    worked_on_start = content.find("worked_on:")
    if worked_on_start >= 0:
        values.setdefault("worked_on", _extract_block(content, "worked_on"))

    return ParsedFields(
        topic=values.get("topic"),
        impact=values.get("impact"),
        blockers=values.get("blockers"),
        remember=values.get("remember"),
        worked_on=values.get("worked_on"),
        status=values.get("status"),
    )


def suggest_title(content: str, fields: ParsedFields) -> str:
    if fields.topic:
        title = fields.topic.strip().strip("\"'")
        if title.lower().startswith("topic:"):
            title = title.split(":", 1)[1].strip()
        return _truncate(title, 90)

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.lower().startswith(("source:", "date:", "repo:", "branch:")):
            continue
        if stripped == "---":
            continue
        if stripped.lower().startswith(
            ("topic:", "impact:", "blockers:", "remember:", "worked_on:", "status:")
        ):
            continue
        return _truncate(stripped, 90)

    return _truncate(content.replace("\n", " "), 90)


def suggest_potential_ending(fields: ParsedFields, content: str) -> str:
    for candidate in (fields.remember, fields.impact, fields.blockers):
        line = _first_line(candidate)
        if line:
            return _truncate(line, 160)
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if lines:
        return _truncate(lines[-1], 160)
    return ""


def detect_categories(lowered: str, fields: ParsedFields) -> list[str]:
    categories: list[str] = []
    haystack = lowered
    if fields.topic:
        haystack += " " + fields.topic.lower()
    for name, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            categories.append(name)
    if memory_source_is_doclog(fields, lowered):
        if "engineering" not in categories:
            categories.append("engineering")
    return categories[:5]


def memory_source_is_doclog(fields: ParsedFields, lowered: str) -> bool:
    return bool(fields.topic or fields.impact or "git evidence" in lowered)


def _score_emotion(lowered: str) -> tuple[str, int, list[str]]:
    best_label = "reflection"
    best_score = 2
    hits: list[str] = []
    for label, keywords in EMOTION_KEYWORDS.items():
        matched = [keyword for keyword in keywords if keyword in lowered]
        if matched:
            hits.extend(matched)
            score = min(5, 2 + len(matched))
            if score > best_score:
                best_score = score
                best_label = label
    return best_label, best_score, hits[:6]


def _score_conflict(content: str, fields: ParsedFields, lowered: str) -> tuple[str, int, list[str]]:
    hits = [word for word in CONFLICT_KEYWORDS if word in lowered]
    if fields.blockers:
        hits.append("blockers")
    if "the problem" in lowered or "root cause" in lowered:
        hits.append("problem statement")

    score = min(5, max(1, len(set(hits)) // 2 + 1))
    if fields.blockers:
        score = min(5, score + 1)

    label = _first_line(fields.blockers) or _first_sentence(content) or "Tension present in the capture"
    return _truncate(label, 120), score, hits[:8]


def _score_transformation(content: str, fields: ParsedFields, lowered: str) -> tuple[str, int, list[str]]:
    hits = [word for word in TRANSFORMATION_KEYWORDS if word in lowered]
    if fields.impact:
        hits.append("impact")
    if fields.remember:
        hits.append("remember")

    score = min(5, max(1, len(set(hits)) // 2 + (2 if fields.impact else 0)))
    label = _first_line(fields.impact) or _first_line(fields.remember) or "Change implied in the capture"
    return _truncate(label, 120), score, hits[:8]


def _score_keyword_hits(lowered: str, keywords: tuple[str, ...], cap: int) -> tuple[int, list[str]]:
    hits = [word for word in keywords if word in lowered]
    score = min(cap, max(1, len(set(hits)) // 2 + 1))
    return score, hits[:8]


def _score_novelty(fields: ParsedFields, lowered: str, recent_topics: set[str]) -> tuple[int, list[str]]:
    topic = (fields.topic or "").strip().lower()
    hits: list[str] = []
    if topic and topic in recent_topics:
        return 2, ["repeated topic"]
    if topic:
        hits.append("fresh topic")
        return 4, hits
    if "again" in lowered or "recurred" in lowered or "third time" in lowered:
        return 2, ["recurring theme"]
    return 3, ["default novelty"]


def _extract_block(content: str, field_name: str) -> str:
    pattern = re.compile(rf"^{field_name}\s*:\s*(.*)$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(content)
    if not match:
        return ""
    start = match.end()
    rest = content[start:]
    block_lines = [match.group(1).strip()]
    for line in rest.splitlines():
        stripped = line.strip()
        if not stripped:
            if block_lines:
                break
            continue
        if re.match(r"^[a-z_]+\s*:", stripped, re.IGNORECASE):
            break
        block_lines.append(stripped)
    return "\n".join(part for part in block_lines if part).strip()


def _first_line(value: str | None) -> str | None:
    if not value:
        return None
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _first_sentence(content: str) -> str | None:
    compact = " ".join(line.strip() for line in content.splitlines() if line.strip())
    if not compact:
        return None
    for separator in (". ", ".\n", "! ", "? "):
        if separator.strip() in compact:
            return compact.split(separator.strip()[0])[0].strip()
    return compact[:120]


def _truncate(value: str, limit: int) -> str:
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."
