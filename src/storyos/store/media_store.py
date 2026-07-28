from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from storyos.models.media import MediaAsset


class MediaStore:
    """SQLite index of local media files for storyboard matching."""

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
                CREATE TABLE IF NOT EXISTS media_assets (
                    id TEXT PRIMARY KEY,
                    path TEXT NOT NULL UNIQUE,
                    filename TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '[]',
                    duration_seconds REAL,
                    indexed_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def upsert(self, asset: MediaAsset) -> MediaAsset:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO media_assets (
                    id, path, filename, tags, duration_seconds, indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    filename = excluded.filename,
                    tags = excluded.tags,
                    duration_seconds = excluded.duration_seconds,
                    indexed_at = excluded.indexed_at
                """,
                (
                    asset.id,
                    asset.path,
                    asset.filename,
                    json.dumps(asset.tags),
                    asset.duration_seconds,
                    asset.indexed_at.isoformat(),
                ),
            )
            connection.commit()
        return asset

    def list_assets(self, *, limit: int = 500) -> list[MediaAsset]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM media_assets ORDER BY indexed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_asset(row) for row in rows]

    def search_by_tokens(self, tokens: set[str], *, limit: int = 5) -> list[MediaAsset]:
        assets = self.list_assets(limit=1000)
        scored: list[tuple[float, MediaAsset]] = []
        for asset in assets:
            haystack = f"{asset.filename} {' '.join(asset.tags)}".lower()
            hits = sum(1 for token in tokens if token in haystack)
            if hits:
                scored.append((float(hits), asset))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [asset for _, asset in scored[:limit]]

    @staticmethod
    def _row_to_asset(row: sqlite3.Row) -> MediaAsset:
        return MediaAsset(
            id=row["id"],
            path=row["path"],
            filename=row["filename"],
            tags=json.loads(row["tags"] or "[]"),
            duration_seconds=row["duration_seconds"],
            indexed_at=datetime.fromisoformat(row["indexed_at"]),
        )
