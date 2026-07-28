from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from storyos.config import StoryOSConfig, load_config
from storyos.store.developed_store import DevelopedStoryStore
from storyos.store.graph_store import GraphStore
from storyos.store.media_store import MediaStore
from storyos.store.memory_store import MemoryStore
from storyos.store.story_store import StoryStore


@dataclass(frozen=True)
class StoryOSRuntime:
    settings: StoryOSConfig
    memory_store: MemoryStore
    story_store: StoryStore
    developed_store: DevelopedStoryStore
    graph_store: GraphStore
    media_store: MediaStore


def load_runtime(config: Path | None = None) -> StoryOSRuntime:
    settings = load_config(config)
    settings.data_path.mkdir(parents=True, exist_ok=True)
    db = settings.database_path
    return StoryOSRuntime(
        settings=settings,
        memory_store=MemoryStore(db),
        story_store=StoryStore(db),
        developed_store=DevelopedStoryStore(db),
        graph_store=GraphStore(db),
        media_store=MediaStore(db),
    )
