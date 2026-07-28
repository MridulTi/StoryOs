from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass(slots=True)
class MediaAsset:
    path: str
    filename: str
    tags: list[str] = field(default_factory=list)
    duration_seconds: float | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    indexed_at: datetime = field(default_factory=datetime.now)

    def short_id(self) -> str:
        return self.id.split("-")[0]
