from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from storyos.capture.manual import capture_from_text
from storyos.config import init_config, load_config
from storyos.store.memory_store import MemoryStore


def test_capture_from_text_creates_memory() -> None:
    memory = capture_from_text("Got paged at 2AM.", source="journal")
    assert memory.content == "Got paged at 2AM."
    assert memory.source == "journal"
    assert memory.id


def test_capture_rejects_empty_content() -> None:
    with pytest.raises(ValueError, match="empty"):
        capture_from_text("   ", source="journal")


def test_memory_store_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "memories.db"
    store = MemoryStore(db_path)

    memory = capture_from_text(
        "Production incident.",
        source="journal",
        captured_at=datetime(2026, 1, 15, 2, 0, tzinfo=timezone.utc),
    )
    store.add(memory)

    loaded = store.get(memory.id)
    assert loaded is not None
    assert loaded.content == memory.content
    assert loaded.source == memory.source


def test_memory_store_search_and_prefix_lookup(tmp_path: Path) -> None:
    db_path = tmp_path / "memories.db"
    store = MemoryStore(db_path)

    first = capture_from_text("Burnout after on-call.", source="journal")
    second = capture_from_text("Shipped DevLog release.", source="devlog")
    store.add(first)
    store.add(second)

    assert store.count() == 2
    assert len(store.search("DevLog")) == 1

    by_prefix = store.get(first.short_id())
    assert by_prefix is not None
    assert by_prefix.id == first.id


def test_load_config_custom_output_and_capture_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "storyos.toml"
    data_path = tmp_path / "data"
    captures_path = tmp_path / "my-captures"
    outputs_path = tmp_path / "my-scripts"
    config_path.write_text(
        f"""
[data]
path = "{data_path}"

[capture]
captures_path = "{captures_path}"

[outputs]
path = "{outputs_path}"
""".strip(),
        encoding="utf-8",
    )

    settings = load_config(config_path)
    assert settings.captures_path == captures_path.resolve()
    assert settings.outputs_path == outputs_path.resolve()


def test_init_config_writes_toml(tmp_path: Path) -> None:
    config_path = tmp_path / "storyos.toml"
    data_path = tmp_path / "data"

    settings = init_config(config_path, data_path)
    assert config_path.is_file()
    assert settings.data_path == data_path.resolve()
    assert settings.default_source == "journal"
    assert settings.captures_path == (data_path / "captures").resolve()
    assert settings.outputs_path == (data_path / "outputs").resolve()

    reloaded = load_config(config_path)
    assert reloaded.data_path == data_path.resolve()
