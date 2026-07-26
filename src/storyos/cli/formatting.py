from __future__ import annotations

import re
from datetime import datetime

from storyos.models.story import StoryCandidate


def parse_since_days(value: str | None) -> int | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if not normalized:
        return None
    match = re.fullmatch(r"(\d+)\s*d(?:ays?)?", normalized)
    if match:
        return int(match.group(1))
    if normalized.isdigit():
        return int(normalized)
    raise ValueError(f"Invalid --since value {value!r}. Use 7d or 7.")


def format_story_summary(candidate: StoryCandidate, *, when: datetime, datetime_format: str) -> str:
    categories = ", ".join(candidate.categories) if candidate.categories else "-"
    return (
        f"{candidate.short_id():<10} "
        f"{candidate.score:>3}/100 "
        f"{when.strftime(datetime_format):<17} "
        f"{categories:<18} "
        f"{candidate.title}"
    )


def format_story_detail(candidate: StoryCandidate, *, memory_preview: str | None = None) -> str:
    lines = [
        f"id:              {candidate.id}",
        f"memory_id:       {candidate.memory_id}",
        f"title:           {candidate.title}",
        f"score:           {candidate.score}/100",
        f"status:          {candidate.status}",
        f"categories:      {', '.join(candidate.categories) if candidate.categories else '-'}",
        "",
        "dimensions:",
        f"  conflict        {candidate.stars('conflict')} ({candidate.dimensions.conflict}/5)",
        f"  emotion         {candidate.stars('emotion')} ({candidate.dimensions.emotion}/5)",
        f"  transformation  {candidate.stars('transformation')} ({candidate.dimensions.transformation}/5)",
        f"  relatability    {candidate.stars('relatability')} ({candidate.dimensions.relatability}/5)",
        f"  novelty         {candidate.stars('novelty')} ({candidate.dimensions.novelty}/5)",
        "",
        f"conflict:        {candidate.conflict}",
        f"emotion:         {candidate.emotion}",
        f"transformation:  {candidate.transformation}",
        f"potential ending:{candidate.potential_ending}",
    ]
    if memory_preview:
        lines.extend(["", "memory preview:", memory_preview])
    return "\n".join(lines)
