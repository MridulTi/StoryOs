from __future__ import annotations

from dataclasses import dataclass
from collections import Counter

from storyos.models.memory import Memory
from storyos.models.story import StoryCandidate
from storyos.store.developed_store import DevelopedStoryStore
from storyos.store.memory_store import MemoryStore
from storyos.store.story_store import StoryStore


@dataclass(frozen=True)
class ThemePattern:
    theme: str
    count: int
    memory_ids: tuple[str, ...]
    story_ids: tuple[str, ...]


def cluster_themes(
    *,
    memory_store: MemoryStore,
    story_store: StoryStore,
    limit: int = 20,
) -> list[ThemePattern]:
    candidates = story_store.list_candidates(min_score=0, status=None, limit=500)
    emotion_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    emotion_memories: dict[str, list[str]] = {}
    emotion_stories: dict[str, list[str]] = {}
    category_memories: dict[str, list[str]] = {}
    category_stories: dict[str, list[str]] = {}

    for candidate in candidates:
        if candidate.emotion:
            key = candidate.emotion.lower()
            emotion_counts[key] += 1
            emotion_memories.setdefault(key, []).append(candidate.memory_id)
            emotion_stories.setdefault(key, []).append(candidate.short_id())
        for category in candidate.categories:
            cat = category.lower()
            category_counts[cat] += 1
            category_memories.setdefault(cat, []).append(candidate.memory_id)
            category_stories.setdefault(cat, []).append(candidate.short_id())

    patterns: list[ThemePattern] = []
    for theme, count in emotion_counts.most_common(limit):
        if count < 2:
            continue
        patterns.append(
            ThemePattern(
                theme=theme,
                count=count,
                memory_ids=tuple(dict.fromkeys(emotion_memories.get(theme, []))),
                story_ids=tuple(dict.fromkeys(emotion_stories.get(theme, []))),
            )
        )
    for theme, count in category_counts.most_common(limit):
        if count < 2:
            continue
        patterns.append(
            ThemePattern(
                theme=f"category:{theme}",
                count=count,
                memory_ids=tuple(dict.fromkeys(category_memories.get(theme, []))),
                story_ids=tuple(dict.fromkeys(category_stories.get(theme, []))),
            )
        )
    patterns.sort(key=lambda item: item.count, reverse=True)
    return patterns[:limit]


def find_resurfacing_candidates(
    *,
    memory_store: MemoryStore,
    story_store: StoryStore,
    since_days: int = 14,
) -> list[tuple[StoryCandidate, Memory, str]]:
    from datetime import datetime, timedelta

    recent = memory_store.list_since(datetime.now() - timedelta(days=since_days))
    if not recent:
        return []

    themes = {item.theme for item in cluster_themes(memory_store=memory_store, story_store=story_store)}
    results: list[tuple[StoryCandidate, Memory, str]] = []
    older = story_store.list_candidates(min_score=50, status=None, limit=100)

    for candidate in older:
        memory = memory_store.get(candidate.memory_id)
        if memory is None:
            continue
        if memory.captured_at >= datetime.now() - timedelta(days=since_days):
            continue
        theme_key = candidate.emotion.lower() if candidate.emotion else ""
        if theme_key and theme_key in themes:
            results.append((candidate, memory, f"recurring theme: {theme_key}"))
            continue
        for category in candidate.categories:
            if f"category:{category.lower()}" in themes:
                results.append((candidate, memory, f"recurring category: {category}"))
                break

    for memory in recent:
        candidate = story_store.get_by_memory_id(memory.id)
        if candidate is None:
            continue
        theme_key = candidate.emotion.lower() if candidate.emotion else ""
        if theme_key in themes:
            results.append((candidate, memory, f"new capture matches theme: {theme_key}"))

    return results[:20]


def list_dormant_stories(
    *,
    story_store: StoryStore,
    developed_store: DevelopedStoryStore,
    limit: int = 20,
) -> list[tuple[StoryCandidate, str]]:
    from storyos.models.story import STORY_STATUS_PICKED

    picked = story_store.list_candidates(min_score=0, status=STORY_STATUS_PICKED, limit=100)
    dormant: list[tuple[StoryCandidate, str]] = []
    for candidate in picked:
        developed = developed_store.get_by_candidate(candidate.id)
        if developed is None:
            dormant.append((candidate, "picked but no interview started"))
        elif developed.status == "draft" and not developed.interview:
            dormant.append((candidate, "interview not started"))
        elif developed.status == "draft":
            dormant.append((candidate, "interview in draft"))
    incomplete = developed_store.list_incomplete_interviews(limit=limit)
    developed_ids = {item.candidate_id for item in incomplete}
    for candidate, reason in dormant:
        if candidate.id in developed_ids and reason == "picked but no interview started":
            continue
    return dormant[:limit]
