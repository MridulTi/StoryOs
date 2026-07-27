from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from storyos.cli.discovery_commands import _resolve_candidate
from storyos.multiply.source import build_story_source
from storyos.multiply.templates import SUPPORTED_FORMATS, render_all, render_script
from storyos.multiply.writer import write_all_scripts, write_script


def register_multiply_commands(
    app: typer.Typer,
    *,
    load_runtime,
) -> None:
    multiply_app = typer.Typer(help="Create scripts from a discovered story.")
    app.add_typer(multiply_app, name="multiply")

    @multiply_app.callback(invoke_without_command=True)
    def multiply_help(ctx: typer.Context) -> None:
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(code=0)

    @multiply_app.command("reel")
    def multiply_reel_command(
        story_id: Annotated[str, typer.Argument(help="Story id or memory id prefix.")],
        output: Annotated[
            Optional[Path],
            typer.Option("--output", "-o", help="Write script to this file path."),
        ] = None,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Create an Instagram Reel script."""
        _run_multiply(story_id, "reel", output=output, config=config, load_runtime=load_runtime)

    @multiply_app.command("shorts")
    def multiply_shorts_command(
        story_id: Annotated[str, typer.Argument(help="Story id or memory id prefix.")],
        output: Annotated[Optional[Path], typer.Option("--output", "-o")] = None,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Create a YouTube Shorts script."""
        _run_multiply(story_id, "shorts", output=output, config=config, load_runtime=load_runtime)

    @multiply_app.command("youtube")
    def multiply_youtube_command(
        story_id: Annotated[str, typer.Argument(help="Story id or memory id prefix.")],
        output: Annotated[Optional[Path], typer.Option("--output", "-o")] = None,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Create a YouTube video script."""
        _run_multiply(story_id, "youtube", output=output, config=config, load_runtime=load_runtime)

    @multiply_app.command("all")
    def multiply_all_command(
        story_id: Annotated[str, typer.Argument(help="Story id or memory id prefix.")],
        output_dir: Annotated[
            Optional[Path],
            typer.Option("--output-dir", "-o", help="Directory for all generated scripts."),
        ] = None,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Create reel, shorts, and YouTube scripts at once."""
        settings, memory_store, story_store = load_runtime(config)
        candidate, memory = _load_story_bundle(story_store, memory_store, story_id)
        source = build_story_source(candidate, memory)
        scripts = render_all(source, prompt_path=settings.script_prompt_path)
        paths = write_all_scripts(
            settings.outputs_path,
            story_short_id=candidate.short_id(),
            title=candidate.title,
            scripts=scripts,
            output_dir=output_dir,
        )
        typer.echo(f"Generated scripts for: {candidate.title}")
        for fmt in SUPPORTED_FORMATS:
            typer.echo(f"  {fmt:<8} {paths[fmt]}")


def _run_multiply(
    story_id: str,
    fmt: str,
    *,
    output: Path | None,
    config: Path | None,
    load_runtime,
) -> None:
    settings, memory_store, story_store = load_runtime(config)
    candidate, memory = _load_story_bundle(story_store, memory_store, story_id)
    source = build_story_source(candidate, memory)
    content = render_script(source, fmt, prompt_path=settings.script_prompt_path)
    path = write_script(
        settings.outputs_path,
        fmt=fmt,
        story_short_id=candidate.short_id(),
        title=candidate.title,
        content=content,
        output=output,
    )
    typer.echo(f"Generated {fmt} script for: {candidate.title}")
    typer.echo(f"  file: {path}")


def _load_story_bundle(story_store, memory_store, story_id: str):
    candidate = _resolve_candidate(story_store, story_id)
    if candidate is None:
        typer.echo(f"Story not found: {story_id}", err=True)
        raise typer.Exit(code=1)
    memory = memory_store.get(candidate.memory_id)
    if memory is None:
        typer.echo(f"Memory not found for story: {story_id}", err=True)
        raise typer.Exit(code=1)
    return candidate, memory
