from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer

from storyos import __version__
from storyos.capture.editor import (
    CaptureCancelled,
    EditorNotFoundError,
    capture_via_editor,
    save_capture_file,
)
from storyos.capture.manual import capture_from_text, read_stdin_content
from storyos.capture.template import ParsedCapture
from storyos.config import StoryOSConfig, init_config, load_config
from storyos.cli.develop_commands import register_develop_command
from storyos.cli.discovery_commands import register_discovery_commands, register_story_commands
from storyos.cli.graph_commands import register_graph_commands
from storyos.cli.media_commands import register_media_commands
from storyos.cli.multiply_commands import register_multiply_commands
from storyos.integrations.base import SyncResult
from storyos.integrations.doclog import sync_doclog_entries
from storyos.integrations.git import sync_git_commits
from storyos.runtime import load_runtime
from storyos.store.memory_store import MemoryStore

app = typer.Typer(
    no_args_is_help=True,
    help="StoryOS — discover stories in the life you're already living.",
)
memories_app = typer.Typer(help="Browse and search captured memories.")
stories_app = typer.Typer(help="Discover and pick story candidates.")
config_app = typer.Typer(help="Inspect StoryOS configuration.")
sync_app = typer.Typer(help="Import captures from external tools.")
app.add_typer(memories_app, name="memories")
app.add_typer(stories_app, name="stories")
app.add_typer(config_app, name="config")
app.add_typer(sync_app, name="sync")


def _load_runtime(config: Path | None):
    return load_runtime(config)


def _format_dt(value: datetime, fmt: str) -> str:
    return value.strftime(fmt)


register_discovery_commands(app, load_runtime=load_runtime, format_dt=_format_dt)
register_develop_command(app)
register_story_commands(stories_app, load_runtime=load_runtime, format_dt=_format_dt)
register_graph_commands(stories_app, app)
register_multiply_commands(app)
register_media_commands(app)


@app.callback()
def main_callback() -> None:
    """StoryOS command-line interface."""


@app.command("init")
def init_command(
    config: Annotated[
        Optional[Path],
        typer.Option("--config", help="Path to storyos.toml (default: platform config dir)."),
    ] = None,
    data_path: Annotated[
        Optional[Path],
        typer.Option("--data-path", help="Override [data].path in the new config."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite an existing config file."),
    ] = False,
) -> None:
    """Create config and data directories."""
    settings = load_config(config)
    if settings.config_path.is_file() and not force:
        typer.echo(f"Config already exists: {settings.config_path}")
        typer.echo("Use --force to overwrite.")
        raise typer.Exit(code=1)

    created = init_config(config, data_path)
    created.data_path.mkdir(parents=True, exist_ok=True)
    MemoryStore(created.database_path)

    typer.echo(f"Initialized StoryOS")
    typer.echo(f"  config: {created.config_path}")
    typer.echo(f"  data:   {created.data_path}")
    typer.echo(f"  db:     {created.database_path}")
    typer.echo("")
    typer.echo('Capture your first memory: storyos capture')


@app.command("capture")
def capture_command(
    text: Annotated[
        Optional[str],
        typer.Argument(help="Quick capture text. Omit to open your editor."),
    ] = None,
    source: Annotated[
        Optional[str],
        typer.Option("--source", "-s", help="Provenance label (journal, voice, git, …)."),
    ] = None,
    editor: Annotated[
        Optional[str],
        typer.Option(
            "--editor",
            "-e",
            help="Editor command (default: $VISUAL, $EDITOR, or nano).",
        ),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option("--config", help="Path to storyos.toml."),
    ] = None,
) -> None:
    """Capture a memory — opens an editor with a template by default."""
    runtime = _load_runtime(config)
    settings = runtime.settings
    store = runtime.memory_store
    resolved_source = source or settings.default_source
    resolved_editor = editor or settings.editor

    stdin_text: str | None = None
    if text is None and not sys.stdin.isatty():
        stdin_text = read_stdin_content()

    if text is not None:
        try:
            memory = capture_from_text(text, source=resolved_source)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
    elif stdin_text is not None and stdin_text.strip():
        try:
            memory = capture_from_text(stdin_text, source=resolved_source)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
    else:
        try:
            parsed = capture_via_editor(
                default_source=resolved_source,
                editor=resolved_editor,
            )
        except CaptureCancelled as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=0) from exc
        except EditorNotFoundError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc

        memory = capture_from_text(
            parsed.content,
            source=parsed.source,
            captured_at=parsed.captured_at,
        )

    capture_path = save_capture_file(
        settings.captures_path,
        ParsedCapture(
            content=memory.content,
            source=memory.source,
            captured_at=memory.captured_at,
        ),
        memory_id=memory.id,
        captured_at=memory.captured_at,
    )
    memory.metadata["capture_file"] = str(capture_path)

    store.add(memory)
    typer.echo(f"Captured memory {memory.short_id()}")
    typer.echo(f"  source: {memory.source}")
    typer.echo(f"  at:     {_format_dt(memory.captured_at, settings.datetime_format)}")
    typer.echo(f"  file:   {capture_path}")


@memories_app.command("list")
def memories_list_command(
    limit: Annotated[int, typer.Option("--limit", "-n", min=1, max=500)] = 20,
    config: Annotated[Optional[Path], typer.Option("--config")] = None,
) -> None:
    """List recent memories."""
    runtime = _load_runtime(config)
    settings = runtime.settings
    store = runtime.memory_store
    items = store.list_recent(limit=limit)

    if not items:
        typer.echo("No memories yet. Try: storyos capture")
        raise typer.Exit(code=0)

    typer.echo(f"{'ID':<10} {'WHEN':<17} {'SOURCE':<10} PREVIEW")
    typer.echo("-" * 72)
    for memory in items:
        preview = memory.content.replace("\n", " ")
        if len(preview) > 36:
            preview = preview[:33] + "..."
        typer.echo(
            f"{memory.short_id():<10} "
            f"{_format_dt(memory.captured_at, settings.datetime_format):<17} "
            f"{memory.source:<10} "
            f"{preview}"
        )


@memories_app.command("show")
def memories_show_command(
    memory_id: Annotated[str, typer.Argument(help="Full or short memory id.")],
    config: Annotated[Optional[Path], typer.Option("--config")] = None,
) -> None:
    """Show one memory in full."""
    runtime = _load_runtime(config)
    settings = runtime.settings
    store = runtime.memory_store
    try:
        memory = store.get(memory_id)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if memory is None:
        typer.echo(f"Memory not found: {memory_id}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"id:         {memory.id}")
    typer.echo(f"source:     {memory.source}")
    typer.echo(f"captured:   {_format_dt(memory.captured_at, settings.datetime_format)}")
    typer.echo(f"created:    {_format_dt(memory.created_at, settings.datetime_format)}")
    capture_file = memory.metadata.get("capture_file")
    if capture_file:
        typer.echo(f"file:       {capture_file}")
    typer.echo("")
    typer.echo(memory.content)


@memories_app.command("search")
def memories_search_command(
    query: Annotated[str, typer.Argument(help="Text to search in memory content and source.")],
    limit: Annotated[int, typer.Option("--limit", "-n", min=1, max=500)] = 20,
    config: Annotated[Optional[Path], typer.Option("--config")] = None,
) -> None:
    """Search captured memories."""
    runtime = _load_runtime(config)
    settings = runtime.settings
    store = runtime.memory_store
    items = store.search(query, limit=limit)

    if not items:
        typer.echo(f"No memories matched: {query!r}")
        raise typer.Exit(code=0)

    typer.echo(f"{'ID':<10} {'WHEN':<17} {'SOURCE':<10} PREVIEW")
    typer.echo("-" * 72)
    for memory in items:
        preview = memory.content.replace("\n", " ")
        if len(preview) > 36:
            preview = preview[:33] + "..."
        typer.echo(
            f"{memory.short_id():<10} "
            f"{_format_dt(memory.captured_at, settings.datetime_format):<17} "
            f"{memory.source:<10} "
            f"{preview}"
        )


@config_app.command("path")
def config_path_command(
    config: Annotated[Optional[Path], typer.Option("--config")] = None,
) -> None:
    """Print active config and data paths."""
    settings = load_config(config)
    typer.echo(f"config: {settings.config_path}")
    typer.echo(f"data:   {settings.data_path}")
    typer.echo(f"db:     {settings.database_path}")
    typer.echo(f"captures: {settings.captures_path}")
    typer.echo(f"outputs:  {settings.outputs_path}")
    typer.echo(f"prompt:   {settings.script_prompt_path}")
    typer.echo(f"llm:      {settings.llm.provider}")
    typer.echo(f"multiply: auto_context={settings.multiply.auto_context}")
    if settings.doclog and settings.doclog.enabled:
        typer.echo(f"doclog: {settings.doclog.home / 'entries'}")
    elif settings.doclog:
        typer.echo("doclog: disabled")


@sync_app.callback(invoke_without_command=True)
def sync_default(
    ctx: typer.Context,
    config: Annotated[Optional[Path], typer.Option("--config")] = None,
) -> None:
    """Import from all enabled integrations."""
    if ctx.invoked_subcommand is not None:
        return
    _run_all_sync(config)


@sync_app.command("all")
def sync_all_command(
    config: Annotated[Optional[Path], typer.Option("--config")] = None,
) -> None:
    """Import from all enabled integrations."""
    _run_all_sync(config)


@sync_app.command("doclog")
def sync_doclog_command(
    config: Annotated[Optional[Path], typer.Option("--config")] = None,
) -> None:
    """Import DocLogs daily entries from ~/.doclog/entries/."""
    _run_doclog_sync(config)


def _run_all_sync(config: Path | None) -> None:
    runtime = load_runtime(config)
    total = SyncResult()
    if runtime.settings.doclog and runtime.settings.doclog.enabled:
        try:
            result = sync_doclog_entries(runtime.memory_store, runtime.settings.doclog.home)
            total = SyncResult(
                created=total.created + result.created,
                updated=total.updated + result.updated,
                skipped=total.skipped + result.skipped,
            )
            typer.echo(f"DocLogs: created={result.created} updated={result.updated} skipped={result.skipped}")
        except FileNotFoundError as exc:
            typer.echo(str(exc), err=True)
    if runtime.settings.git and runtime.settings.git.enabled and runtime.settings.git.repo:
        try:
            result = sync_git_commits(
                runtime.memory_store,
                repo_path=runtime.settings.git.repo,
                since_days=runtime.settings.git.since_days,
            )
            total = SyncResult(
                created=total.created + result.created,
                updated=total.updated + result.updated,
                skipped=total.skipped + result.skipped,
            )
            typer.echo(f"Git: created={result.created} updated={result.updated} skipped={result.skipped}")
        except (FileNotFoundError, RuntimeError) as exc:
            typer.echo(str(exc), err=True)
    typer.echo(f"Total: created={total.created} updated={total.updated} skipped={total.skipped}")


def _run_doclog_sync(config: Path | None) -> None:
    runtime = load_runtime(config)
    settings = runtime.settings
    if settings.doclog is None or not settings.doclog.enabled:
        typer.echo("DocLogs integration is disabled in storyos.toml.", err=True)
        raise typer.Exit(code=1)

    store = runtime.memory_store
    try:
        result = sync_doclog_entries(store, settings.doclog.home)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"DocLogs sync from {settings.doclog.home / 'entries'}")
    typer.echo(f"  created: {result.created}")
    typer.echo(f"  updated: {result.updated}")
    typer.echo(f"  skipped: {result.skipped}")


@sync_app.command("git")
def sync_git_command(
    repo: Annotated[Optional[Path], typer.Option("--repo", help="Git repository path.")] = None,
    since_days: Annotated[int, typer.Option("--since", min=1, max=365)] = 7,
    config: Annotated[Optional[Path], typer.Option("--config")] = None,
) -> None:
    """Import recent git commits as background memories."""
    runtime = load_runtime(config)
    settings = runtime.settings
    repo_path = repo or (settings.git.repo if settings.git else None) or Path.cwd()
    try:
        result = sync_git_commits(
            runtime.memory_store,
            repo_path=repo_path,
            since_days=since_days,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Git sync from {repo_path}")
    typer.echo(f"  created: {result.created}")
    typer.echo(f"  updated: {result.updated}")
    typer.echo(f"  skipped: {result.skipped}")


@app.command("version")
def version_command() -> None:
    """Show installed version."""
    typer.echo(f"storyos {__version__}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
