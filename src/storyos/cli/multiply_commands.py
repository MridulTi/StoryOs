from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from storyos.cli.discovery_commands import _resolve_candidate
from storyos.graph.related import related_memory_ids
from storyos.llm.base import ProviderError
from storyos.llm.registry import PROVIDER_NAMES
from storyos.multiply.formats import ALL_FORMATS, VIDEO_FORMATS
from storyos.multiply.generator import generate_script_content
from storyos.multiply.source import StoryBundle, build_story_bundle, build_story_source
from storyos.multiply.writer import write_all_scripts, write_generation_outputs
from storyos.runtime import load_runtime


def register_multiply_commands(app: typer.Typer) -> None:
    multiply_app = typer.Typer(help="Create scripts from a discovered story.")
    app.add_typer(multiply_app, name="multiply")

    @multiply_app.callback(invoke_without_command=True)
    def multiply_help(ctx: typer.Context) -> None:
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(code=0)

    for fmt in ALL_FORMATS:
        _register_format_command(multiply_app, fmt)

    @multiply_app.command("all")
    def multiply_all_command(
        story_ids: Annotated[
            list[str],
            typer.Argument(help="Main story id first, then optional background story ids."),
        ],
        output_dir: Annotated[
            Optional[Path],
            typer.Option("--output-dir", "-o", help="Directory for all generated scripts."),
        ] = None,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
        provider: Annotated[Optional[str], typer.Option("--provider")] = None,
        prompt_only: Annotated[bool, typer.Option("--prompt-only")] = False,
        template: Annotated[bool, typer.Option("--template")] = False,
        save_prompt: Annotated[bool, typer.Option("--save-prompt")] = False,
        with_related: Annotated[
            bool,
            typer.Option("--with-related", help="Auto-attach top related stories as background."),
        ] = False,
    ) -> None:
        """Create reel, shorts, and YouTube scripts at once."""
        _run_multiply_all(
            story_ids,
            formats=VIDEO_FORMATS,
            output_dir=output_dir,
            config=config,
            provider=provider,
            prompt_only=prompt_only,
            template=template,
            save_prompt=save_prompt,
            with_related=with_related,
        )

    @multiply_app.command("all-formats")
    def multiply_all_formats_command(
        story_ids: Annotated[list[str], typer.Argument(help="Main story id first, then background ids.")],
        output_dir: Annotated[Optional[Path], typer.Option("--output-dir", "-o")] = None,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
        provider: Annotated[Optional[str], typer.Option("--provider")] = None,
        prompt_only: Annotated[bool, typer.Option("--prompt-only")] = False,
        template: Annotated[bool, typer.Option("--template")] = False,
        save_prompt: Annotated[bool, typer.Option("--save-prompt")] = False,
        with_related: Annotated[bool, typer.Option("--with-related")] = False,
    ) -> None:
        """Create every supported output format."""
        _run_multiply_all(
            story_ids,
            formats=ALL_FORMATS,
            output_dir=output_dir,
            config=config,
            provider=provider,
            prompt_only=prompt_only,
            template=template,
            save_prompt=save_prompt,
            with_related=with_related,
        )


def _register_format_command(multiply_app: typer.Typer, fmt: str) -> None:
    def _command(
        story_ids: Annotated[
            list[str],
            typer.Argument(help="Main story id first, then optional background story ids."),
        ],
        output: Annotated[Optional[Path], typer.Option("--output", "-o")] = None,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
        provider: Annotated[Optional[str], typer.Option("--provider")] = None,
        prompt_only: Annotated[bool, typer.Option("--prompt-only")] = False,
        template: Annotated[bool, typer.Option("--template")] = False,
        save_prompt: Annotated[bool, typer.Option("--save-prompt")] = False,
        with_related: Annotated[bool, typer.Option("--with-related")] = False,
    ) -> None:
        _run_multiply(
            story_ids,
            fmt,
            output=output,
            config=config,
            provider=provider,
            prompt_only=prompt_only,
            template=template,
            save_prompt=save_prompt,
            with_related=with_related,
        )

    _command.__doc__ = f"Create a {fmt} output."
    multiply_app.command(fmt)(_command)


def _run_multiply_all(
    story_ids: list[str],
    *,
    formats: tuple[str, ...],
    output_dir: Path | None,
    config: Path | None,
    provider: str | None,
    prompt_only: bool,
    template: bool,
    save_prompt: bool,
    with_related: bool,
) -> None:
    runtime = load_runtime(config)
    bundle, developed = _load_story_bundle(
        runtime,
        story_ids,
        with_related=with_related,
    )

    scripts: dict[str, str] = {}
    prompts: dict[str, str] = {}
    provider_used: str | None = None
    used_ai = False

    for fmt in formats:
        try:
            result = generate_script_content(
                bundle,
                fmt,
                llm=runtime.settings.llm,
                script_prompt_path=runtime.settings.script_prompt_path,
                provider_override=provider,
                prompt_only=prompt_only,
                use_template=template,
                developed=developed,
            )
        except (ProviderError, ValueError) as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc

        scripts[fmt] = result.content
        prompts[fmt] = result.prompt
        provider_used = result.provider
        used_ai = used_ai or result.used_ai

    paths = write_all_scripts(
        runtime.settings.outputs_path,
        story_short_id=bundle.main.candidate.short_id(),
        title=bundle.main.title,
        scripts=scripts,
        output_dir=output_dir,
        prompts=prompts if save_prompt or prompt_only else None,
    )

    typer.echo(_bundle_summary(bundle))
    if provider_used:
        mode = "AI" if used_ai else provider_used
        typer.echo(f"  provider: {mode}")
    for fmt in formats:
        typer.echo(f"  {fmt:<12} {paths[fmt]}")
        prompt_path = paths.get(f"{fmt}-prompt")
        if prompt_path:
            typer.echo(f"               prompt: {prompt_path}")


def _run_multiply(
    story_ids: list[str],
    fmt: str,
    *,
    output: Path | None,
    config: Path | None,
    provider: str | None,
    prompt_only: bool,
    template: bool,
    save_prompt: bool,
    with_related: bool,
) -> None:
    runtime = load_runtime(config)
    bundle, developed = _load_story_bundle(
        runtime,
        story_ids,
        with_related=with_related,
    )

    try:
        result = generate_script_content(
            bundle,
            fmt,
            llm=runtime.settings.llm,
            script_prompt_path=runtime.settings.script_prompt_path,
            provider_override=provider,
            prompt_only=prompt_only,
            use_template=template,
            developed=developed,
        )
    except (ProviderError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    paths = write_generation_outputs(
        runtime.settings.outputs_path,
        fmt=fmt,
        story_short_id=bundle.main.candidate.short_id(),
        title=bundle.main.title,
        content=result.content,
        prompt=result.prompt,
        output=output,
        save_prompt=save_prompt or prompt_only,
    )

    mode = "AI" if result.used_ai else result.provider
    typer.echo(_bundle_summary(bundle, fmt=fmt))
    typer.echo(f"  provider: {mode}")
    typer.echo(f"  file: {paths['script']}")
    if paths.get("prompt"):
        typer.echo(f"  prompt: {paths['prompt']}")


def _load_story_bundle(runtime, story_ids: list[str], *, with_related: bool):
    if not story_ids:
        typer.echo("At least one story id is required.", err=True)
        raise typer.Exit(code=1)

    seen: set[str] = set()
    sources = []
    for story_id in story_ids:
        normalized = story_id.strip()
        if not normalized:
            continue
        if normalized in seen:
            typer.echo(f"Duplicate story id: {normalized}", err=True)
            raise typer.Exit(code=1)
        seen.add(normalized)

        candidate = _resolve_candidate(runtime.story_store, normalized)
        if candidate is None:
            typer.echo(f"Story not found: {normalized}", err=True)
            raise typer.Exit(code=1)
        memory = runtime.memory_store.get(candidate.memory_id)
        if memory is None:
            typer.echo(f"Memory not found for story: {normalized}", err=True)
            raise typer.Exit(code=1)
        sources.append(build_story_source(candidate, memory))

    if not sources:
        typer.echo("At least one story id is required.", err=True)
        raise typer.Exit(code=1)

    main = sources[0]
    auto_count = runtime.settings.multiply.auto_context
    if (with_related or auto_count > 0) and len(sources) == 1:
        limit = auto_count if auto_count > 0 else 2
        related_ids = related_memory_ids(
            main.candidate,
            main.memory,
            memory_store=runtime.memory_store,
            story_store=runtime.story_store,
            graph_store=runtime.graph_store,
            limit=limit,
        )
        for related_id in related_ids:
            if related_id in seen:
                continue
            candidate = _resolve_candidate(runtime.story_store, related_id)
            if candidate is None:
                continue
            memory = runtime.memory_store.get(candidate.memory_id)
            if memory is None:
                continue
            sources.append(build_story_source(candidate, memory))
            seen.add(related_id)

    bundle = build_story_bundle(sources[0], *sources[1:])
    developed = runtime.developed_store.get_by_candidate(bundle.main.candidate.id)
    return bundle, developed


def _bundle_summary(bundle: StoryBundle, *, fmt: str | None = None) -> str:
    if fmt:
        prefix = f"Generated {fmt} script for"
    else:
        prefix = "Generated scripts for"
    line = f"{prefix}: {bundle.main.title}"
    if bundle.context:
        background = ", ".join(item.title for item in bundle.context)
        line += f"\n  background: {background}"
    return line
