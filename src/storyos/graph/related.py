from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta

from storyos.engine.analyzer import parse_structured_fields
from storyos.graph.models import EDGE_THEMATIC, MemoryEdge
from storyos.models.memory import Memory
from storyos.models.story import StoryCandidate
from storyos.store.graph_store import GraphStore
from storyos.store.memory_store import MemoryStore
from storyos.store.story_store import StoryStore

TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}")


@dataclass(frozen=True)
class RelatedMatch:
    candidate: StoryCandidate
    memory: Memory
    score: float
    reasons: tuple[str, ...]


def find_related_stories(
    main: StoryCandidate,
    main_memory: Memory,
    *,
    memory_store: MemoryStore,
    story_store: StoryStore,
    graph_store: GraphStore,
    limit: int = 10,
) -> list[RelatedMatch]:
    candidates = story_store.list_candidates(min_score=0, status=None, limit=200)
    main_tokens = _content_tokens(main_memory.content)
    main_fields = parse_structured_fields(main_memory.content)
    matches: list[RelatedMatch] = []

    for candidate in candidates:
        if candidate.id == main.id or candidate.memory_id == main.memory_id:
            continue
        memory = memory_store.get(candidate.memory_id)
        if memory is None:
            continue

        score, reasons = _score_relation(
            main,
            main_memory,
            main_tokens,
            main_fields,
            candidate,
            memory,
            graph_store=graph_store,
        )
        if score <= 0:
            continue
        matches.append(
            RelatedMatch(
                candidate=candidate,
                memory=memory,
                score=score,
                reasons=reasons,
            )
        )

    matches.sort(key=lambda item: item.score, reverse=True)
    return matches[:limit]


def persist_inferred_edges(
    main_memory: Memory,
    matches: list[RelatedMatch],
    *,
    graph_store: GraphStore,
) -> None:
    for match in matches[:5]:
        edge = MemoryEdge(
            from_memory_id=main_memory.id,
            to_memory_id=match.memory.id,
            edge_type=EDGE_THEMATIC,
            confidence=min(1.0, match.score / 100.0),
            confirmed=False,
            reason="; ".join(match.reasons),
        )
        graph_store.upsert_edge(edge)


def related_memory_ids(
    main: StoryCandidate,
    main_memory: Memory,
    *,
    memory_store: MemoryStore,
    story_store: StoryStore,
    graph_store: GraphStore,
    limit: int = 2,
) -> list[str]:
    matches = find_related_stories(
        main,
        main_memory,
        memory_store=memory_store,
        story_store=story_store,
        graph_store=graph_store,
        limit=limit,
    )
    return [match.candidate.short_id() for match in matches]


def _score_relation(
    main: StoryCandidate,
    main_memory: Memory,
    main_tokens: set[str],
    main_fields,
    candidate: StoryCandidate,
    memory: Memory,
    *,
    graph_store: GraphStore,
) -> tuple[float, tuple[str, ...]]:
    reasons: list[str] = []
    score = 0.0

    delta = abs((memory.captured_at - main_memory.captured_at).total_seconds())
    if delta <= timedelta(days=7).total_seconds():
        score += 35
        reasons.append("same week")

    other_tokens = _content_tokens(memory.content)
    overlap = main_tokens & other_tokens
    if len(overlap) >= 3:
        score += min(30, len(overlap) * 4)
        reasons.append(f"shared words ({', '.join(sorted(list(overlap))[:4])})")

    if main.emotion and candidate.emotion and main.emotion.lower() == candidate.emotion.lower():
        score += 15
        reasons.append(f"same emotion ({main.emotion})")

    shared_categories = set(main.categories) & set(candidate.categories)
    if shared_categories:
        score += 10
        reasons.append(f"shared category ({', '.join(sorted(shared_categories))})")

    other_fields = parse_structured_fields(memory.content)
    if main_fields.topic and other_fields.topic:
        topic_overlap = _content_tokens(main_fields.topic) & _content_tokens(other_fields.topic)
        if topic_overlap:
            score += 10
            reasons.append("related topics")

    for edge in graph_store.list_edges_for_memory(main_memory.id):
        other_id = edge.to_memory_id if edge.from_memory_id == main_memory.id else edge.from_memory_id
        if other_id == memory.id:
            score += 25 if edge.confirmed else 15
            reasons.append("linked memory" if edge.confirmed else "inferred link")

    return score, tuple(reasons)


def _content_tokens(content: str) -> set[str]:
    stop = {
        "the", "and", "for", "that", "this", "with", "from", "have", "were", "was",
        "are", "not", "but", "you", "your", "after", "before", "when", "what",
    }
    tokens = {match.group(0) for match in TOKEN_PATTERN.finditer(content.lower())}
    return {token for token in tokens if token not in stop}
