from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

EDGE_CONTINUES = "continues"
EDGE_CONTRASTS = "contrasts"
EDGE_CAUSES = "causes"
EDGE_THEMATIC = "thematically_related"
EDGE_PART_OF = "part_of"
EDGE_MANUAL = "manual"


@dataclass(slots=True)
class MemoryEdge:
    from_memory_id: str
    to_memory_id: str
    edge_type: str
    confidence: float = 1.0
    confirmed: bool = False
    reason: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)


@dataclass(slots=True)
class Journey:
    title: str
    memory_ids: list[str] = field(default_factory=list)
    status: str = "active"
    categories: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def short_id(self) -> str:
        return self.id.split("-")[0]
