from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Optional

import typer

from storyos.cli.discovery_commands import _resolve_candidate
from storyos.cli.formatting import format_story_summary
from storyos.engine.discover import discover_memories
from storyos.graph.related import find_related_stories, persist_inferred_edges
from storyos.models.story import STORY_STATUS_ACTIVE
from storyos.patterns.themes import cluster_themes, find_resurfacing_candidates, list_dormant_stories
from storyos.runtime import load_runtime


def register_graph_commands(stories_app: typer.Typer, app: typer.Typer) -> None:
    @stories_app.command("related")
    def stories_related_command(
        story_id: Annotated[str, typer.Argument(help="Main story id.")],
        limit: Annotated[int, typer.Option("--limit", "-n", min=1, max=50)] = 10,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Suggest background stories for a main story."""
        runtime = load_runtime(config)
        candidate = _resolve_candidate(runtime.story_store, story_id)
        if candidate is None:
            typer.echo(f"Story not found: {story_id}", err=True)
            raise typer.Exit(code=1)
        memory = runtime.memory_store.get(candidate.memory_id)
        if memory is None:
            typer.echo(f"Memory not found for story: {story_id}", err=True)
            raise typer.Exit(code=1)

        matches = find_related_stories(
            candidate,
            memory,
            memory_store=runtime.memory_store,
            story_store=runtime.story_store,
            graph_store=runtime.graph_store,
            limit=limit,
        )
        persist_inferred_edges(memory, matches, graph_store=runtime.graph_store)

        if not matches:
            typer.echo("No related stories found.")
            raise typer.Exit(code=0)

        typer.echo(f"Related to: {candidate.title}")
        typer.echo(f"{'ID':<10} {'SCORE':<8} REASONS")
        typer.echo("-" * 72)
        for match in matches:
            reasons = "; ".join(match.reasons)
            typer.echo(
                f"{match.candidate.short_id():<10} {match.score:>5.0f}   {reasons}"
            )
        typer.echo("")
        ids = " ".join(match.candidate.short_id() for match in matches[:3])
        typer.echo(f"Try: storyos multiply all {candidate.short_id()} {ids}")

    @stories_app.command("link")
    def stories_link_command(
        story_id_a: Annotated[str, typer.Argument(help="First story id.")],
        story_id_b: Annotated[str, typer.Argument(help="Second story id.")],
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Manually link two story memories."""
        runtime = load_runtime(config)
        candidate_a = _resolve_candidate(runtime.story_store, story_id_a)
        candidate_b = _resolve_candidate(runtime.story_store, story_id_b)
        if candidate_a is None or candidate_b is None:
            typer.echo("Both story ids must exist.", err=True)
            raise typer.Exit(code=1)
        runtime.graph_store.link_memories(
            candidate_a.memory_id,
            candidate_b.memory_id,
            reason="manual story link",
        )
        typer.echo(f"Linked {candidate_a.short_id()} ↔ {candidate_b.short_id()}")

    @stories_app.command("dormant")
    def stories_dormant_command(
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """List picked stories that were never fully developed."""
        runtime = load_runtime(config)
        dormant = list_dormant_stories(
            story_store=runtime.story_store,
            developed_store=runtime.developed_store,
        )
        if not dormant:
            typer.echo("No dormant stories.")
            raise typer.Exit(code=0)
        for candidate, reason in dormant:
            typer.echo(f"{candidate.short_id():<10} {reason:<28} {candidate.title}")

    @app.command("timeline")
    def timeline_command(
        days: Annotated[int, typer.Option("--days", min=1, max=3650)] = 30,
        journey: Annotated[Optional[str], typer.Option("--journey", help="Journey id.")] = None,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Show a chronological view of captures and story candidates."""
        runtime = load_runtime(config)
        if journey:
            item = runtime.graph_store.get_journey(journey)
            if item is None:
                typer.echo(f"Journey not found: {journey}", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"Journey: {item.title}")
            memory_ids = item.memory_ids
        else:
            memory_ids = None

        since = datetime.now() - timedelta(days=days)
        memories = runtime.memory_store.list_since(since)
        if memory_ids is not None:
            memories = [memory for memory in memories if memory.id in memory_ids]

        typer.echo(f"{'WHEN':<17} {'SOURCE':<10} {'STORY':<10} PREVIEW")
        typer.echo("-" * 80)
        for memory in memories:
            candidate = runtime.story_store.get_by_memory_id(memory.id)
            story_id = candidate.short_id() if candidate else "-"
            preview = memory.content.replace("\n", " ")
            if len(preview) > 40:
                preview = preview[:37] + "..."
            typer.echo(
                f"{memory.captured_at.strftime(runtime.settings.datetime_format):<17} "
                f"{memory.source:<10} "
                f"{story_id:<10} "
                f"{preview}"
            )

    @app.command("patterns")
    def patterns_command(
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Show recurring themes across your story history."""
        runtime = load_runtime(config)
        patterns = cluster_themes(
            memory_store=runtime.memory_store,
            story_store=runtime.story_store,
        )
        if not patterns:
            typer.echo("Not enough history for patterns yet.")
            raise typer.Exit(code=0)
        typer.echo(f"{'THEME':<24} {'COUNT':<8} STORIES")
        typer.echo("-" * 60)
        for pattern in patterns:
            stories = ", ".join(pattern.story_ids[:5])
            typer.echo(f"{pattern.theme:<24} {pattern.count:<8} {stories}")
