from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

STORY_STATUS_ACTIVE = "active"
STORY_STATUS_DISMISSED = "dismissed"
STORY_STATUS_PICKED = "picked"


@dataclass(slots=True)
class StoryDimensions:
    emotion: int
    conflict: int
    transformation: int
    relatability: int
    novelty: int

    def as_dict(self) -> dict[str, int]:
        return {
            "emotion": self.emotion,
            "conflict": self.conflict,
            "transformation": self.transformation,
            "relatability": self.relatability,
            "novelty": self.novelty,
        }

    def composite_score(self) -> int:
        weighted = (
            self.conflict * 0.25
            + self.transformation * 0.25
            + self.emotion * 0.20
            + self.relatability * 0.20
            + self.novelty * 0.10
        )
        return min(100, max(0, round(weighted * 20)))


@dataclass(slots=True)
class StoryCandidate:
    memory_id: str
    title: str
    score: int
    dimensions: StoryDimensions
    conflict: str
    emotion: str
    transformation: str
    potential_ending: str
    categories: list[str] = field(default_factory=list)
    signals: dict[str, Any] = field(default_factory=dict)
    status: str = STORY_STATUS_ACTIVE
    id: str = field(default_factory=lambda: str(uuid4()))
    discovered_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def short_id(self) -> str:
        return self.id.split("-")[0]

    def stars(self, dimension: str) -> str:
        value = getattr(self.dimensions, dimension, 0)
        return "★" * value + "☆" * (5 - value)
