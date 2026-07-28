from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from storyos.cli.discovery_commands import _resolve_candidate
from storyos.media.scan import scan_media_paths
from storyos.runtime import load_runtime
from storyos.storyboard.builder import build_storyboard_from_script, render_storyboard_markdown


def register_media_commands(app: typer.Typer) -> None:
    media_app = typer.Typer(help="Index personal media for storyboards.")
    app.add_typer(media_app, name="media")

    @media_app.command("scan")
    def media_scan_command(
        paths: Annotated[list[Path], typer.Argument(help="Directories or files to index.")],
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Index local photos and videos for storyboard matching."""
        runtime = load_runtime(config)
        result = scan_media_paths(runtime.media_store, paths)
        typer.echo(f"Indexed media: {result.indexed}")
        typer.echo(f"Skipped:       {result.skipped}")

    @app.command("storyboard")
    def storyboard_command(
        story_id: Annotated[str, typer.Argument(help="Story id.")],
        script: Annotated[
            Optional[Path],
            typer.Option("--script", "-s", help="Use this script file instead of latest output."),
        ] = None,
        gaps_only: Annotated[bool, typer.Option("--gaps", help="Show only scenes needing recording.")] = False,
        output: Annotated[Optional[Path], typer.Option("--output", "-o")] = None,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Build a storyboard from a script and your media library."""
        runtime = load_runtime(config)
        candidate = _resolve_candidate(runtime.story_store, story_id)
        if candidate is None:
            typer.echo(f"Story not found: {story_id}", err=True)
            raise typer.Exit(code=1)

        content = _load_script_content(runtime, candidate.short_id(), candidate.title, script)
        rows = build_storyboard_from_script(content, media_store=runtime.media_store)
        if gaps_only:
            rows = [row for row in rows if row.need_recording]

        markdown = render_storyboard_markdown(candidate.title, rows)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown, encoding="utf-8")
            typer.echo(f"Storyboard written: {output}")
        else:
            typer.echo(markdown)


def _load_script_content(runtime, story_short_id: str, title: str, script: Path | None) -> str:
    if script is not None:
        return script.read_text(encoding="utf-8")
    outputs = runtime.settings.outputs_path
    for fmt in ("reel", "shorts", "youtube"):
        directory = outputs / fmt
        if not directory.is_dir():
            continue
        matches = sorted(directory.glob(f"{story_short_id}-*.md"))
        if matches:
            return matches[-1].read_text(encoding="utf-8")
    raise typer.BadParameter(
        f"No generated script found for {story_short_id}. Run storyos multiply first or pass --script."
    )
