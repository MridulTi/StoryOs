from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from storyos.graph.models import EDGE_MANUAL, Journey, MemoryEdge


class GraphStore:
    """SQLite store for memory graph edges and journeys."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_edges (
                    id TEXT PRIMARY KEY,
                    from_memory_id TEXT NOT NULL,
                    to_memory_id TEXT NOT NULL,
                    edge_type TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 1.0,
                    confirmed INTEGER NOT NULL DEFAULT 0,
                    reason TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    UNIQUE(from_memory_id, to_memory_id, edge_type)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS journeys (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    memory_ids TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL DEFAULT 'active',
                    categories TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memory_edges_from
                ON memory_edges (from_memory_id)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memory_edges_to
                ON memory_edges (to_memory_id)
                """
            )
            connection.commit()

    def upsert_edge(self, edge: MemoryEdge) -> MemoryEdge:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO memory_edges (
                    id, from_memory_id, to_memory_id, edge_type,
                    confidence, confirmed, reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(from_memory_id, to_memory_id, edge_type) DO UPDATE SET
                    confidence = excluded.confidence,
                    confirmed = excluded.confirmed,
                    reason = excluded.reason
                """,
                (
                    edge.id,
                    edge.from_memory_id,
                    edge.to_memory_id,
                    edge.edge_type,
                    edge.confidence,
                    1 if edge.confirmed else 0,
                    edge.reason,
                    edge.created_at.isoformat(),
                ),
            )
            connection.commit()
        return edge

    def link_memories(
        self,
        from_memory_id: str,
        to_memory_id: str,
        *,
        edge_type: str = EDGE_MANUAL,
        reason: str = "manual link",
    ) -> MemoryEdge:
        edge = MemoryEdge(
            from_memory_id=from_memory_id,
            to_memory_id=to_memory_id,
            edge_type=edge_type,
            confidence=1.0,
            confirmed=True,
            reason=reason,
        )
        return self.upsert_edge(edge)

    def list_edges_for_memory(self, memory_id: str) -> list[MemoryEdge]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM memory_edges
                WHERE from_memory_id = ? OR to_memory_id = ?
                ORDER BY confirmed DESC, confidence DESC
                """,
                (memory_id, memory_id),
            ).fetchall()
        return [self._row_to_edge(row) for row in rows]

    def list_all_edges(self) -> list[MemoryEdge]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM memory_edges ORDER BY created_at DESC").fetchall()
        return [self._row_to_edge(row) for row in rows]

    def upsert_journey(self, journey: Journey) -> Journey:
        journey.updated_at = datetime.now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO journeys (
                    id, title, memory_ids, status, categories, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    memory_ids = excluded.memory_ids,
                    status = excluded.status,
                    categories = excluded.categories,
                    updated_at = excluded.updated_at
                """,
                (
                    journey.id,
                    journey.title,
                    json.dumps(journey.memory_ids),
                    journey.status,
                    json.dumps(journey.categories),
                    journey.created_at.isoformat(),
                    journey.updated_at.isoformat(),
                ),
            )
            connection.commit()
        return journey

    def get_journey(self, journey_id: str) -> Journey | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM journeys WHERE id = ?", (journey_id,)).fetchone()
            if row is not None:
                return self._row_to_journey(row)
            prefix = connection.execute(
                "SELECT * FROM journeys WHERE id LIKE ?",
                (f"{journey_id}%",),
            ).fetchall()
        if not prefix:
            return None
        if len(prefix) > 1:
            raise ValueError(f"Ambiguous journey id prefix: {journey_id}")
        return self._row_to_journey(prefix[0])

    def list_journeys(self, *, limit: int = 50) -> list[Journey]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM journeys ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_journey(row) for row in rows]

    @staticmethod
    def _row_to_edge(row: sqlite3.Row) -> MemoryEdge:
        return MemoryEdge(
            id=row["id"],
            from_memory_id=row["from_memory_id"],
            to_memory_id=row["to_memory_id"],
            edge_type=row["edge_type"],
            confidence=float(row["confidence"]),
            confirmed=bool(row["confirmed"]),
            reason=row["reason"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @staticmethod
    def _row_to_journey(row: sqlite3.Row) -> Journey:
        return Journey(
            id=row["id"],
            title=row["title"],
            memory_ids=json.loads(row["memory_ids"] or "[]"),
            status=row["status"],
            categories=json.loads(row["categories"] or "[]"),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
