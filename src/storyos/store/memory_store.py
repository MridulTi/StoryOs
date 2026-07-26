from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from storyos.models.memory import Memory


class MemoryStore:
    """Local SQLite-backed memory store (Phase 1)."""

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
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    captured_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_captured_at
                ON memories (captured_at DESC)
                """
            )
            connection.commit()

    def add(self, memory: Memory) -> Memory:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO memories (id, content, source, captured_at, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    memory.id,
                    memory.content,
                    memory.source,
                    memory.captured_at.isoformat(),
                    memory.created_at.isoformat(),
                    json.dumps(memory.metadata),
                ),
            )
            connection.commit()
        return memory

    def get(self, memory_id: str) -> Memory | None:
        row = self._fetch_one_by_id(memory_id)
        if row is None:
            return None
        return self._row_to_memory(row)

    def find_by_external_ref(self, external_ref: str) -> Memory | None:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM memories WHERE metadata LIKE ?",
                (f'%"external_ref": "{external_ref}"%',),
            ).fetchall()
        if not rows:
            return None
        if len(rows) > 1:
            raise ValueError(f"Multiple memories found for external ref: {external_ref}")
        return self._row_to_memory(rows[0])

    def update(
        self,
        memory_id: str,
        *,
        content: str,
        source: str,
        captured_at: datetime,
        metadata: dict[str, Any],
    ) -> Memory:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE memories
                SET content = ?, source = ?, captured_at = ?, metadata = ?
                WHERE id = ?
                """,
                (
                    content,
                    source,
                    captured_at.isoformat(),
                    json.dumps(metadata),
                    memory_id,
                ),
            )
            connection.commit()
        memory = self.get(memory_id)
        if memory is None:
            raise ValueError(f"Memory not found after update: {memory_id}")
        return memory

    def list_recent(self, limit: int = 20) -> list[Memory]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM memories
                ORDER BY captured_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_memory(row) for row in rows]

    def list_all(self, limit: int = 5000) -> list[Memory]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM memories
                ORDER BY captured_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_memory(row) for row in rows]

    def list_since(self, since: datetime, limit: int = 5000) -> list[Memory]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM memories
                WHERE captured_at >= ?
                ORDER BY captured_at DESC
                LIMIT ?
                """,
                (since.isoformat(), limit),
            ).fetchall()
        return [self._row_to_memory(row) for row in rows]

    def search(self, query: str, limit: int = 20) -> list[Memory]:
        pattern = f"%{query.strip()}%"
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM memories
                WHERE content LIKE ? OR source LIKE ?
                ORDER BY captured_at DESC
                LIMIT ?
                """,
                (pattern, pattern, limit),
            ).fetchall()
        return [self._row_to_memory(row) for row in rows]

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM memories").fetchone()
        return int(row["total"])

    def _fetch_one_by_id(self, memory_id: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            exact = connection.execute(
                "SELECT * FROM memories WHERE id = ?",
                (memory_id,),
            ).fetchone()
            if exact is not None:
                return exact

            prefix_matches = connection.execute(
                "SELECT * FROM memories WHERE id LIKE ?",
                (f"{memory_id}%",),
            ).fetchall()

        if not prefix_matches:
            return None
        if len(prefix_matches) > 1:
            raise ValueError(f"Ambiguous memory id prefix: {memory_id}")
        return prefix_matches[0]

    @staticmethod
    def _row_to_memory(row: sqlite3.Row) -> Memory:
        metadata_raw = row["metadata"] or "{}"
        return Memory(
            id=row["id"],
            content=row["content"],
            source=row["source"],
            captured_at=datetime.fromisoformat(row["captured_at"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            metadata=json.loads(metadata_raw),
        )
