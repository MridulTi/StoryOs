from __future__ import annotations

from pathlib import Path

import yaml

from storyos.integrations.doclog import doclog_entry_to_memory, sync_doclog_entries
from storyos.store.memory_store import MemoryStore


def test_doclog_entry_to_memory_from_sample(tmp_path: Path) -> None:
    entry_path = tmp_path / "2026-07-25.yaml"
    entry_path.write_text(
        yaml.safe_dump(
            {
                "date": "2026-07-25",
                "captured_at": "2026-07-25T19:10:22+05:30",
                "repository": {"path": "/repo", "branch": "main"},
                "git": {
                    "commits": [
                        {
                            "hash": "abc1234",
                            "subject": "Fix log upload script",
                            "author": "dev",
                            "commited_at": "2026-07-25T18:00:00+05:30",
                        }
                    ]
                },
                "manual": {"notes": "topic: disk runaway\nimpact: fixed lifecycle"},
                "evidence": {"pr_titles": [], "ticket_ids": []},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    data = yaml.safe_load(entry_path.read_text(encoding="utf-8"))
    memory = doclog_entry_to_memory(entry_path, data)
    assert memory is not None
    assert memory.source == "doclog"
    assert "disk runaway" in memory.content
    assert "`abc1234` Fix log upload script" in memory.content
    assert memory.metadata["external_ref"] == "doclog:entry:2026-07-25.yaml"


def test_sync_doclog_entries_creates_and_updates(tmp_path: Path) -> None:
    home = tmp_path / "doclog"
    entries = home / "entries"
    entries.mkdir(parents=True)
    entry_path = entries / "2026-07-10.yaml"
    entry_path.write_text(
        yaml.safe_dump(
            {
                "date": "2026-07-10",
                "captured_at": "2026-07-10T10:00:00+05:30",
                "repository": {"path": None, "branch": None},
                "git": {"commits": []},
                "manual": {"notes": "First version"},
                "evidence": {"pr_titles": [], "ticket_ids": []},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    store = MemoryStore(tmp_path / "memories.db")
    first = sync_doclog_entries(store, home)
    assert first.created == 1
    assert first.updated == 0
    assert first.skipped == 0

    second = sync_doclog_entries(store, home)
    assert second.created == 0
    assert second.updated == 0
    assert second.skipped == 1

    data = yaml.safe_load(entry_path.read_text(encoding="utf-8"))
    data["manual"]["notes"] = "Updated version"
    entry_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    third = sync_doclog_entries(store, home)
    assert third.created == 0
    assert third.updated == 1
    assert third.skipped == 0

    memory = store.find_by_external_ref("doclog:entry:2026-07-10.yaml")
    assert memory is not None
    assert "Updated version" in memory.content
