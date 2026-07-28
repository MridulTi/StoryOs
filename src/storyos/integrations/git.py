from __future__ import annotations

import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from storyos.capture.manual import capture_from_text
from storyos.integrations.base import SyncResult
from storyos.models.memory import Memory


def external_ref_for_commit(repo_path: Path, commit_hash: str) -> str:
    return f"git:{repo_path.resolve()}:{commit_hash}"


def sync_git_commits(
    store,
    *,
    repo_path: Path,
    since_days: int = 7,
    max_commits: int = 50,
) -> SyncResult:
    repo_path = repo_path.expanduser().resolve()
    if not (repo_path / ".git").is_dir():
        raise FileNotFoundError(f"Not a git repository: {repo_path}")

    since = (datetime.now() - timedelta(days=since_days)).strftime("%Y-%m-%d")
    command = [
        "git",
        "-C",
        str(repo_path),
        "log",
        f"--since={since}",
        f"-{max_commits}",
        "--pretty=format:%H|%s|%ai",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise FileNotFoundError("git command not found") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"git log failed: {detail}")

    sync = SyncResult()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 2)
        if len(parts) < 3:
            sync = SyncResult(created=sync.created, updated=sync.updated, skipped=sync.skipped + 1)
            continue
        commit_hash, subject, authored = parts
        memory = _commit_to_memory(repo_path, commit_hash, subject, authored)
        if memory is None:
            sync = SyncResult(created=sync.created, updated=sync.updated, skipped=sync.skipped + 1)
            continue

        external_ref = memory.metadata["external_ref"]
        existing = store.find_by_external_ref(external_ref)
        if existing is None:
            store.add(memory)
            sync = SyncResult(created=sync.created + 1, updated=sync.updated, skipped=sync.skipped)
            continue
        sync = SyncResult(created=sync.created, updated=sync.updated, skipped=sync.skipped + 1)

    return sync


def _commit_to_memory(repo_path: Path, commit_hash: str, subject: str, authored: str) -> Memory | None:
    subject = subject.strip()
    if not subject:
        return None
    try:
        captured_at = datetime.fromisoformat(authored.strip().replace(" ", "T", 1))
    except ValueError:
        captured_at = datetime.now()

    short = commit_hash[:7]
    content = "\n".join(
        [
            f"topic: Git commit {short}",
            f"worked_on: {subject}",
            f"source: git",
            "",
            f"Commit `{short}` in {repo_path.name}: {subject}",
        ]
    )
    memory = capture_from_text(
        content,
        source="git",
        captured_at=captured_at,
    )
    memory.metadata.update(
        {
            "external_ref": external_ref_for_commit(repo_path, commit_hash),
            "git_hash": commit_hash,
            "git_repo": str(repo_path),
            "git_subject": subject,
        }
    )
    return memory
