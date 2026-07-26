from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from storyos.engine.analyzer import analyze_memory, parse_structured_fields
from storyos.models.memory import Memory
from storyos.models.story import STORY_STATUS_ACTIVE, STORY_STATUS_DISMISSED, StoryCandidate
from storyos.store.memory_store import MemoryStore
from storyos.store.story_store import StoryStore


@dataclass(frozen=True)
class DiscoverResult:
    analyzed: int
    discovered: int
    skipped: int
    updated: int


def discover_memories(
    memory_store: MemoryStore,
    story_store: StoryStore,
    *,
    since_days: int | None = None,
    memory_id: str | None = None,
    force: bool = False,
) -> DiscoverResult:
    if memory_id:
        memory = memory_store.get(memory_id)
        if memory is None:
            raise ValueError(f"Memory not found: {memory_id}")
        memories = [memory]
    elif since_days is not None:
        memories = memory_store.list_since(datetime.now() - timedelta(days=since_days))
    else:
        memories = memory_store.list_all()

    recent_topics = _recent_topics(memories)
    analyzed = 0
    discovered = 0
    skipped = 0
    updated = 0

    for memory in memories:
        analyzed += 1
        existing = story_store.get_by_memory_id(memory.id)
        if existing and existing.status == STORY_STATUS_DISMISSED and not force:
            skipped += 1
            continue

        topic_key = parse_structured_fields(memory.content).topic
        topic_set = set(recent_topics)
        if topic_key:
            topic_set.discard(topic_key.strip().lower())

        candidate = analyze_memory(memory, recent_topics=topic_set)
        if candidate is None:
            skipped += 1
            continue

        if existing:
            candidate.id = existing.id
            candidate.discovered_at = existing.discovered_at
            if existing.status == STORY_STATUS_DISMISSED and force:
                candidate.status = STORY_STATUS_ACTIVE
            elif existing.status != STORY_STATUS_DISMISSED:
                candidate.status = existing.status
            updated += 1
        else:
            discovered += 1

        story_store.upsert(candidate)

    return DiscoverResult(
        analyzed=analyzed,
        discovered=discovered,
        skipped=skipped,
        updated=updated,
    )


def _recent_topics(memories: list[Memory]) -> set[str]:
    topics: set[str] = set()
    for memory in memories:
        topic = parse_structured_fields(memory.content).topic
        if topic:
            topics.add(topic.strip().lower())
    return topics
