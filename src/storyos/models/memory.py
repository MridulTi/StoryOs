from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class Memory:
    """A normalized record of one captured experience."""

    content: str
    source: str
    captured_at: datetime
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def short_id(self) -> str:
        return self.id.split("-")[0]
