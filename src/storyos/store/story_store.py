from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from storyos.models.story import (
    STORY_STATUS_ACTIVE,
    STORY_STATUS_DISMISSED,
    STORY_STATUS_PICKED,
    StoryCandidate,
    StoryDimensions,
)


class StoryStore:
    """SQLite store for discovered story candidates."""

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
                CREATE TABLE IF NOT EXISTS story_candidates (
                    id TEXT PRIMARY KEY,
                    memory_id TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    conflict TEXT NOT NULL DEFAULT '',
                    emotion TEXT NOT NULL DEFAULT '',
                    transformation TEXT NOT NULL DEFAULT '',
                    potential_ending TEXT NOT NULL DEFAULT '',
                    categories TEXT NOT NULL DEFAULT '[]',
                    dimensions TEXT NOT NULL DEFAULT '{}',
                    signals TEXT NOT NULL DEFAULT '{}',
                    discovered_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_story_candidates_score
                ON story_candidates (score DESC, discovered_at DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_story_candidates_status
                ON story_candidates (status, score DESC)
                """
            )
            connection.commit()

    def upsert(self, candidate: StoryCandidate) -> StoryCandidate:
        now = datetime.now()
        candidate.updated_at = now
        if candidate.discovered_at is None:
            candidate.discovered_at = now

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO story_candidates (
                    id, memory_id, title, score, status, conflict, emotion,
                    transformation, potential_ending, categories, dimensions,
                    signals, discovered_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(memory_id) DO UPDATE SET
                    title = excluded.title,
                    score = excluded.score,
                    status = excluded.status,
                    conflict = excluded.conflict,
                    emotion = excluded.emotion,
                    transformation = excluded.transformation,
                    potential_ending = excluded.potential_ending,
                    categories = excluded.categories,
                    dimensions = excluded.dimensions,
                    signals = excluded.signals,
                    updated_at = excluded.updated_at
                """,
                self._candidate_to_row(candidate),
            )
            connection.commit()
        return candidate

    def get(self, candidate_id: str) -> StoryCandidate | None:
        row = self._fetch_one_by_id(candidate_id)
        if row is None:
            return None
        return self._row_to_candidate(row)

    def get_by_memory_id(self, memory_id: str) -> StoryCandidate | None:
        with self._connect() as connection:
            exact = connection.execute(
                "SELECT * FROM story_candidates WHERE memory_id = ?",
                (memory_id,),
            ).fetchone()
            if exact is not None:
                return self._row_to_candidate(exact)

            prefix_matches = connection.execute(
                "SELECT * FROM story_candidates WHERE memory_id LIKE ?",
                (f"{memory_id}%",),
            ).fetchall()
        if not prefix_matches:
            return None
        if len(prefix_matches) > 1:
            raise ValueError(f"Ambiguous memory id prefix: {memory_id}")
        return self._row_to_candidate(prefix_matches[0])

    def list_candidates(
        self,
        *,
        min_score: int = 0,
        category: str | None = None,
        status: str | None = STORY_STATUS_ACTIVE,
        limit: int = 50,
    ) -> list[StoryCandidate]:
        query = "SELECT * FROM story_candidates WHERE score >= ?"
        params: list[Any] = [min_score]

        if status is not None:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY score DESC, discovered_at DESC LIMIT ?"
        params.append(limit)

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()

        candidates = [self._row_to_candidate(row) for row in rows]
        if category:
            needle = category.strip().lower()
            candidates = [
                candidate
                for candidate in candidates
                if any(item.lower() == needle for item in candidate.categories)
            ]
        return candidates

    def list_for_memories(self, memory_ids: set[str]) -> list[StoryCandidate]:
        if not memory_ids:
            return []
        placeholders = ",".join("?" for _ in memory_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM story_candidates WHERE memory_id IN ({placeholders})",
                tuple(memory_ids),
            ).fetchall()
        return [self._row_to_candidate(row) for row in rows]

    def set_status(self, candidate_id: str, status: str) -> StoryCandidate | None:
        candidate = self.get(candidate_id)
        if candidate is None:
            return None
        candidate.status = status
        candidate.updated_at = datetime.now()
        with self._connect() as connection:
            connection.execute(
                "UPDATE story_candidates SET status = ?, updated_at = ? WHERE id = ?",
                (status, candidate.updated_at.isoformat(), candidate.id),
            )
            connection.commit()
        return candidate

    def count_by_status(self, status: str | None = None) -> int:
        with self._connect() as connection:
            if status is None:
                row = connection.execute("SELECT COUNT(*) AS total FROM story_candidates").fetchone()
            else:
                row = connection.execute(
                    "SELECT COUNT(*) AS total FROM story_candidates WHERE status = ?",
                    (status,),
                ).fetchone()
        return int(row["total"])

    def _fetch_one_by_id(self, candidate_id: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            exact = connection.execute(
                "SELECT * FROM story_candidates WHERE id = ?",
                (candidate_id,),
            ).fetchone()
            if exact is not None:
                return exact
            prefix_matches = connection.execute(
                "SELECT * FROM story_candidates WHERE id LIKE ?",
                (f"{candidate_id}%",),
            ).fetchall()
        if not prefix_matches:
            return None
        if len(prefix_matches) > 1:
            raise ValueError(f"Ambiguous story id prefix: {candidate_id}")
        return prefix_matches[0]

    @staticmethod
    def _candidate_to_row(candidate: StoryCandidate) -> tuple[Any, ...]:
        return (
            candidate.id,
            candidate.memory_id,
            candidate.title,
            candidate.score,
            candidate.status,
            candidate.conflict,
            candidate.emotion,
            candidate.transformation,
            candidate.potential_ending,
            json.dumps(candidate.categories),
            json.dumps(candidate.dimensions.as_dict()),
            json.dumps(candidate.signals),
            candidate.discovered_at.isoformat(),
            candidate.updated_at.isoformat(),
        )

    @staticmethod
    def _row_to_candidate(row: sqlite3.Row) -> StoryCandidate:
        dimensions_raw = json.loads(row["dimensions"] or "{}")
        return StoryCandidate(
            id=row["id"],
            memory_id=row["memory_id"],
            title=row["title"],
            score=int(row["score"]),
            status=row["status"],
            conflict=row["conflict"],
            emotion=row["emotion"],
            transformation=row["transformation"],
            potential_ending=row["potential_ending"],
            categories=json.loads(row["categories"] or "[]"),
            dimensions=StoryDimensions(
                emotion=int(dimensions_raw.get("emotion", 0)),
                conflict=int(dimensions_raw.get("conflict", 0)),
                transformation=int(dimensions_raw.get("transformation", 0)),
                relatability=int(dimensions_raw.get("relatability", 0)),
                novelty=int(dimensions_raw.get("novelty", 0)),
            ),
            signals=json.loads(row["signals"] or "{}"),
            discovered_at=datetime.fromisoformat(row["discovered_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
