from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0

    def merge(self, other: SyncResult) -> SyncResult:
        return SyncResult(
            created=self.created + other.created,
            updated=self.updated + other.updated,
            skipped=self.skipped + other.skipped,
        )
