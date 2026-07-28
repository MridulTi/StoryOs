from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from storyos.models.developed_story import (
    DEVELOPED_STATUS_DRAFT,
    DEVELOPED_STATUS_READY,
    DevelopedStory,
    InterviewQA,
)


class DevelopedStoryStore:
    """SQLite store for developed stories (Story Companion output)."""

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
                CREATE TABLE IF NOT EXISTS developed_stories (
                    id TEXT PRIMARY KEY,
                    candidate_id TEXT NOT NULL UNIQUE,
                    memory_ids TEXT NOT NULL DEFAULT '[]',
                    title TEXT NOT NULL,
                    interview TEXT NOT NULL DEFAULT '[]',
                    creator_narrative TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'draft',
                    shareability TEXT NOT NULL DEFAULT 'shareable',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_developed_stories_status
                ON developed_stories (status, updated_at DESC)
                """
            )
            connection.commit()

    def upsert(self, story: DevelopedStory) -> DevelopedStory:
        story.updated_at = datetime.now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO developed_stories (
                    id, candidate_id, memory_ids, title, interview,
                    creator_narrative, status, shareability, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(candidate_id) DO UPDATE SET
                    memory_ids = excluded.memory_ids,
                    title = excluded.title,
                    interview = excluded.interview,
                    creator_narrative = excluded.creator_narrative,
                    status = excluded.status,
                    shareability = excluded.shareability,
                    updated_at = excluded.updated_at
                """,
                self._story_to_row(story),
            )
            connection.commit()
        return story

    def get(self, story_id: str) -> DevelopedStory | None:
        row = self._fetch_one_by_id(story_id)
        if row is None:
            return None
        return self._row_to_story(row)

    def get_by_candidate(self, candidate_id: str) -> DevelopedStory | None:
        with self._connect() as connection:
            exact = connection.execute(
                "SELECT * FROM developed_stories WHERE candidate_id = ?",
                (candidate_id,),
            ).fetchone()
            if exact is not None:
                return self._row_to_story(exact)
            prefix_matches = connection.execute(
                "SELECT * FROM developed_stories WHERE candidate_id LIKE ?",
                (f"{candidate_id}%",),
            ).fetchall()
        if not prefix_matches:
            return None
        if len(prefix_matches) > 1:
            raise ValueError(f"Ambiguous candidate id prefix: {candidate_id}")
        return self._row_to_story(prefix_matches[0])

    def list_stories(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[DevelopedStory]:
        query = "SELECT * FROM developed_stories"
        params: list[Any] = []
        if status is not None:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._row_to_story(row) for row in rows]

    def list_dormant(self, *, limit: int = 50) -> list[DevelopedStory]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM developed_stories
                WHERE status = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (DEVELOPED_STATUS_DRAFT, limit),
            ).fetchall()
        return [self._row_to_story(row) for row in rows]

    def list_incomplete_interviews(self, *, limit: int = 50) -> list[DevelopedStory]:
        stories = self.list_stories(status=DEVELOPED_STATUS_DRAFT, limit=limit)
        return [story for story in stories if not story.interview]

    def _fetch_one_by_id(self, story_id: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            exact = connection.execute(
                "SELECT * FROM developed_stories WHERE id = ?",
                (story_id,),
            ).fetchone()
            if exact is not None:
                return exact
            prefix_matches = connection.execute(
                "SELECT * FROM developed_stories WHERE id LIKE ?",
                (f"{story_id}%",),
            ).fetchall()
        if not prefix_matches:
            return None
        if len(prefix_matches) > 1:
            raise ValueError(f"Ambiguous developed story id prefix: {story_id}")
        return prefix_matches[0]

    @staticmethod
    def _story_to_row(story: DevelopedStory) -> tuple[Any, ...]:
        return (
            story.id,
            story.candidate_id,
            json.dumps(story.memory_ids),
            story.title,
            json.dumps([item.as_dict() for item in story.interview]),
            story.creator_narrative,
            story.status,
            story.shareability,
            story.created_at.isoformat(),
            story.updated_at.isoformat(),
        )

    @staticmethod
    def _row_to_story(row: sqlite3.Row) -> DevelopedStory:
        interview_raw = json.loads(row["interview"] or "[]")
        return DevelopedStory(
            id=row["id"],
            candidate_id=row["candidate_id"],
            memory_ids=json.loads(row["memory_ids"] or "[]"),
            title=row["title"],
            interview=[InterviewQA.from_dict(item) for item in interview_raw],
            creator_narrative=row["creator_narrative"],
            status=row["status"],
            shareability=row["shareability"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
