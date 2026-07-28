from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

DEVELOPED_STATUS_DRAFT = "draft"
DEVELOPED_STATUS_READY = "ready"
DEVELOPED_STATUS_ARCHIVED = "archived"

SHAREABILITY_PRIVATE = "private"
SHAREABILITY_SHAREABLE = "shareable"


@dataclass(slots=True)
class InterviewQA:
    question_id: str
    question: str
    answer: str

    def as_dict(self) -> dict[str, str]:
        return {
            "question_id": self.question_id,
            "question": self.question,
            "answer": self.answer,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> InterviewQA:
        return cls(
            question_id=str(raw.get("question_id", "")),
            question=str(raw.get("question", "")),
            answer=str(raw.get("answer", "")),
        )


@dataclass(slots=True)
class DevelopedStory:
    candidate_id: str
    memory_ids: list[str]
    title: str
    interview: list[InterviewQA] = field(default_factory=list)
    creator_narrative: str = ""
    status: str = DEVELOPED_STATUS_DRAFT
    shareability: str = SHAREABILITY_SHAREABLE
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def short_id(self) -> str:
        return self.id.split("-")[0]

    def narrative_text(self) -> str:
        if self.creator_narrative.strip():
            return self.creator_narrative.strip()
        parts: list[str] = []
        for item in self.interview:
            if item.answer.strip():
                parts.append(f"Q: {item.question}\nA: {item.answer.strip()}")
        return "\n\n".join(parts)
