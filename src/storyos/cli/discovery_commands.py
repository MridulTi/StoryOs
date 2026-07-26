from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Optional

import typer

from storyos.cli.formatting import format_story_detail, format_story_summary, parse_since_days
from storyos.config import StoryOSConfig
from storyos.engine.discover import discover_memories
from storyos.models.story import STORY_STATUS_ACTIVE, STORY_STATUS_DISMISSED, STORY_STATUS_PICKED
from storyos.store.memory_store import MemoryStore
from storyos.store.story_store import StoryStore


def register_discovery_commands(
    app: typer.Typer,
    *,
    load_runtime,
    format_dt,
) -> None:
    @app.command("discover")
    def discover_command(
        since: Annotated[
            Optional[str],
            typer.Option("--since", help="Only analyze recent captures, e.g. 7d or 14."),
        ] = None,
        memory_id: Annotated[
            Optional[str],
            typer.Option("--memory", help="Analyze one memory by id."),
        ] = None,
        force: Annotated[
            bool,
            typer.Option("--force", help="Re-analyze dismissed or existing candidates."),
        ] = False,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Analyze captures and discover story candidates."""
        settings, memory_store, story_store = load_runtime(config)
        try:
            since_days = parse_since_days(since)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc

        try:
            result = discover_memories(
                memory_store,
                story_store,
                since_days=since_days,
                memory_id=memory_id,
                force=force,
            )
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc

        scope = _discover_scope_label(since_days=since_days, memory_id=memory_id)
        typer.echo(f"Discovery complete ({scope})")
        typer.echo(f"  analyzed:   {result.analyzed}")
        typer.echo(f"  discovered: {result.discovered}")
        typer.echo(f"  updated:    {result.updated}")
        typer.echo(f"  skipped:    {result.skipped}")
        if result.discovered or result.updated:
            typer.echo("")
            typer.echo("Next: storyos stories list")

    @app.command("today")
    def today_command(
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Discover and show meaningful moments from recent captures."""
        settings, memory_store, story_store = load_runtime(config)
        discover_memories(memory_store, story_store, since_days=2, force=False)

        candidates = story_store.list_candidates(min_score=50, status=STORY_STATUS_ACTIVE, limit=10)
        recent_memories = memory_store.list_since(datetime.now() - timedelta(days=2))
        typer.echo(f"Recent captures: {len(recent_memories)}")
        typer.echo(f"Story candidates: {len(candidates)}")
        typer.echo("")

        if not candidates:
            typer.echo("No strong story candidates yet.")
            typer.echo("Try: storyos sync doclog && storyos discover")
            raise typer.Exit(code=0)

        typer.echo(f"{'ID':<10} {'SCORE':<8} {'WHEN':<17} {'CATEGORIES':<18} TITLE")
        typer.echo("-" * 90)
        memory_times = {
            memory.id: memory.captured_at
            for memory in recent_memories
        }
        for candidate in candidates:
            when = memory_times.get(candidate.memory_id, candidate.discovered_at)
            typer.echo(format_story_summary(candidate, when=when, datetime_format=settings.datetime_format))


def register_develop_alias(app: typer.Typer, *, load_runtime) -> None:
    @app.command("develop")
    def develop_command(
        story_id: Annotated[str, typer.Argument(help="Story id or memory id prefix.")],
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Alias for `storyos stories pick`."""
        _, _, story_store = load_runtime(config)
        candidate = _resolve_candidate(story_store, story_id)
        if candidate is None:
            typer.echo(f"Story not found: {story_id}", err=True)
            raise typer.Exit(code=1)
        story_store.set_status(candidate.id, STORY_STATUS_PICKED)
        typer.echo(f"Picked story {candidate.short_id()}: {candidate.title}")
        typer.echo("Generate scripts: storyos multiply all " + candidate.short_id())


def register_story_commands(
    stories_app: typer.Typer,
    *,
    load_runtime,
    format_dt,
) -> None:
    @stories_app.command("list")
    def stories_list_command(
        min_score: Annotated[int, typer.Option("--min-score", min=0, max=100)] = 0,
        category: Annotated[Optional[str], typer.Option("--category")] = None,
        include_dismissed: Annotated[bool, typer.Option("--include-dismissed")] = False,
        limit: Annotated[int, typer.Option("--limit", "-n", min=1, max=200)] = 20,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """List discovered story candidates."""
        settings, memory_store, story_store = load_runtime(config)
        status = None if include_dismissed else STORY_STATUS_ACTIVE
        candidates = story_store.list_candidates(
            min_score=min_score,
            category=category,
            status=status,
            limit=limit,
        )
        if not candidates:
            typer.echo("No story candidates yet. Try: storyos discover")
            raise typer.Exit(code=0)

        typer.echo(f"{'ID':<10} {'SCORE':<8} {'WHEN':<17} {'CATEGORIES':<18} TITLE")
        typer.echo("-" * 90)
        for candidate in candidates:
            memory = memory_store.get(candidate.memory_id)
            when = memory.captured_at if memory else candidate.discovered_at
            typer.echo(format_story_summary(candidate, when=when, datetime_format=settings.datetime_format))

    @stories_app.command("show")
    def stories_show_command(
        story_id: Annotated[str, typer.Argument(help="Story id or memory id prefix.")],
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Show one story candidate with scoring breakdown."""
        _, memory_store, story_store = load_runtime(config)
        candidate = story_store.get(story_id)
        if candidate is None:
            candidate = story_store.get_by_memory_id(story_id)
        if candidate is None:
            typer.echo(f"Story not found: {story_id}", err=True)
            raise typer.Exit(code=1)

        memory = memory_store.get(candidate.memory_id)
        preview = None
        if memory:
            preview = memory.content.strip()
            if len(preview) > 400:
                preview = preview[:397] + "..."
        typer.echo(format_story_detail(candidate, memory_preview=preview))

    @stories_app.command("dismiss")
    def stories_dismiss_command(
        story_id: Annotated[str, typer.Argument(help="Story id or memory id prefix.")],
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Dismiss a story candidate."""
        _, _, story_store = load_runtime(config)
        candidate = _resolve_candidate(story_store, story_id)
        if candidate is None:
            typer.echo(f"Story not found: {story_id}", err=True)
            raise typer.Exit(code=1)
        story_store.set_status(candidate.id, STORY_STATUS_DISMISSED)
        typer.echo(f"Dismissed story {candidate.short_id()}: {candidate.title}")

    @stories_app.command("pick")
    def stories_pick_command(
        story_id: Annotated[str, typer.Argument(help="Story id or memory id prefix.")],
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Mark a story candidate as picked for development."""
        _, _, story_store = load_runtime(config)
        candidate = _resolve_candidate(story_store, story_id)
        if candidate is None:
            typer.echo(f"Story not found: {story_id}", err=True)
            raise typer.Exit(code=1)
        story_store.set_status(candidate.id, STORY_STATUS_PICKED)
        typer.echo(f"Picked story {candidate.short_id()}: {candidate.title}")
        typer.echo("Generate scripts: storyos multiply all " + candidate.short_id())


def _resolve_candidate(story_store: StoryStore, story_id: str):
    candidate = story_store.get(story_id)
    if candidate is None:
        candidate = story_store.get_by_memory_id(story_id)
    return candidate


def _discover_scope_label(*, since_days: int | None, memory_id: str | None) -> str:
    if memory_id:
        return f"memory {memory_id}"
    if since_days is not None:
        return f"last {since_days} days"
    return "all memories"
