from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

from storyos.models.memory import Memory


@dataclass(frozen=True)
class DoclogSyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0


def resolve_doclog_home(configured: Path | None = None) -> Path:
    if configured is not None:
        return configured.expanduser().resolve()
    override = os.environ.get("DOCLOG_HOME")
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".doclog").resolve()


def doclog_entries_dir(home: Path) -> Path:
    return home / "entries"


def external_ref_for_entry(entry_path: Path) -> str:
    return f"doclog:entry:{entry_path.name}"


def load_doclog_entry(entry_path: Path) -> dict | None:
    if not entry_path.is_file():
        return None
    with entry_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else None


def doclog_entry_to_memory(entry_path: Path, data: dict) -> Memory | None:
    notes = (data.get("manual") or {}).get("notes")
    commits = (data.get("git") or {}).get("commits") or []
    pr_titles = (data.get("evidence") or {}).get("pr_titles") or []
    ticket_ids = (data.get("evidence") or {}).get("ticket_ids") or []

    if not notes and not commits and not pr_titles and not ticket_ids:
        return None

    content = _build_content(data, notes=notes, commits=commits, pr_titles=pr_titles, ticket_ids=ticket_ids)
    captured_at = _parse_captured_at(data.get("captured_at"), entry_path)

    repository = data.get("repository") or {}
    stat = entry_path.stat()
    return Memory(
        content=content,
        source="doclog",
        captured_at=captured_at,
        metadata={
            "external_ref": external_ref_for_entry(entry_path),
            "doclog_path": str(entry_path.resolve()),
            "doclog_date": data.get("date") or entry_path.stem,
            "doclog_mtime": stat.st_mtime,
            "branch": repository.get("branch"),
            "repository_path": repository.get("path"),
            "commit_count": len(commits),
            "pr_titles": pr_titles,
            "ticket_ids": ticket_ids,
        },
    )


def sync_doclog_entries(store, home: Path) -> DoclogSyncResult:
    entries_path = doclog_entries_dir(home)
    if not entries_path.is_dir():
        raise FileNotFoundError(f"DocLogs entries directory not found: {entries_path}")

    result = DoclogSyncResult()
    for entry_path in sorted(entries_path.glob("*.yaml")):
        data = load_doclog_entry(entry_path)
        if not data:
            result = DoclogSyncResult(
                created=result.created,
                updated=result.updated,
                skipped=result.skipped + 1,
            )
            continue

        memory = doclog_entry_to_memory(entry_path, data)
        if memory is None:
            result = DoclogSyncResult(
                created=result.created,
                updated=result.updated,
                skipped=result.skipped + 1,
            )
            continue

        external_ref = memory.metadata["external_ref"]
        existing = store.find_by_external_ref(external_ref)
        if existing is None:
            store.add(memory)
            result = DoclogSyncResult(created=result.created + 1, updated=result.updated, skipped=result.skipped)
            continue

        existing_mtime = existing.metadata.get("doclog_mtime")
        if existing_mtime == memory.metadata["doclog_mtime"]:
            result = DoclogSyncResult(
                created=result.created,
                updated=result.updated,
                skipped=result.skipped + 1,
            )
            continue

        store.update(
            existing.id,
            content=memory.content,
            source=memory.source,
            captured_at=memory.captured_at,
            metadata=memory.metadata,
        )
        result = DoclogSyncResult(created=result.created, updated=result.updated + 1, skipped=result.skipped)

    return result


def _build_content(
    data: dict,
    *,
    notes: str | None,
    commits: list,
    pr_titles: list,
    ticket_ids: list,
) -> str:
    parts: list[str] = []

    repository = data.get("repository") or {}
    branch = repository.get("branch")
    repo_path = repository.get("path")
    if branch or repo_path:
        header_bits = []
        if repo_path:
            header_bits.append(f"repo: {repo_path}")
        if branch:
            header_bits.append(f"branch: {branch}")
        parts.append(" | ".join(header_bits))

    if notes and notes.strip():
        parts.append(notes.strip())

    if commits:
        lines = ["## Git evidence", ""]
        for commit in commits:
            commit_hash = str(commit.get("hash", ""))[:7]
            subject = commit.get("subject", "").strip()
            lines.append(f"- `{commit_hash}` {subject}")
        parts.append("\n".join(lines))

    if pr_titles:
        lines = ["## Pull requests", ""] + [f"- {title}" for title in pr_titles]
        parts.append("\n".join(lines))

    if ticket_ids:
        lines = ["## Tickets", ""] + [f"- {ticket}" for ticket in ticket_ids]
        parts.append("\n".join(lines))

    return "\n\n".join(parts)


def _parse_captured_at(value: object, entry_path: Path) -> datetime:
    if isinstance(value, str) and value.strip():
        normalized = value.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass

    day = entry_path.stem
    try:
        return datetime.fromisoformat(f"{day}T12:00:00")
    except ValueError:
        return datetime.now()
