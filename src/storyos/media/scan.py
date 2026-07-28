from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from storyos.models.media import MediaAsset
from storyos.store.media_store import MediaStore

MEDIA_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".jpg", ".jpeg", ".png", ".webp", ".heic"}


@dataclass(frozen=True)
class MediaScanResult:
    indexed: int = 0
    skipped: int = 0


def scan_media_paths(store: MediaStore, paths: list[Path]) -> MediaScanResult:
    indexed = 0
    skipped = 0
    for root in paths:
        resolved = root.expanduser().resolve()
        if not resolved.exists():
            skipped += 1
            continue
        if resolved.is_file():
            if _index_file(store, resolved):
                indexed += 1
            else:
                skipped += 1
            continue
        for file_path in resolved.rglob("*"):
            if not file_path.is_file():
                continue
            if _index_file(store, file_path):
                indexed += 1
            else:
                skipped += 1
    return MediaScanResult(indexed=indexed, skipped=skipped)


def _index_file(store: MediaStore, path: Path) -> bool:
    if path.suffix.lower() not in MEDIA_EXTENSIONS:
        return False
    tags = _tags_from_path(path)
    asset = MediaAsset(
        path=str(path),
        filename=path.name,
        tags=tags,
    )
    store.upsert(asset)
    return True


def _tags_from_path(path: Path) -> list[str]:
    stem = path.stem.lower().replace("_", " ").replace("-", " ")
    parts = [part for part in stem.split() if part]
    parts.extend(part.lower() for part in path.parts[-3:])
    return list(dict.fromkeys(parts))
