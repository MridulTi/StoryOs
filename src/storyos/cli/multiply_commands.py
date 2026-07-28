from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from storyos.cli.discovery_commands import _resolve_candidate
from storyos.llm.base import ProviderError
from storyos.llm.registry import PROVIDER_NAMES
from storyos.multiply.generator import generate_script_content
from storyos.multiply.source import StoryBundle, build_story_bundle, build_story_source
from storyos.multiply.templates import SUPPORTED_FORMATS
from storyos.multiply.writer import write_all_scripts, write_generation_outputs


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
        story_ids: Annotated[
            list[str],
            typer.Argument(help="Main story id first, then optional background story ids."),
        ],
        output: Annotated[
            Optional[Path],
            typer.Option("--output", "-o", help="Write script to this file path."),
        ] = None,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
        provider: Annotated[
            Optional[str],
            typer.Option("--provider", help=f"LLM provider ({', '.join(PROVIDER_NAMES)})."),
        ] = None,
        prompt_only: Annotated[
            bool,
            typer.Option("--prompt-only", help="Write a prompt file instead of calling AI."),
        ] = False,
        template: Annotated[
            bool,
            typer.Option("--template", help="Use built-in template output (no AI)."),
        ] = False,
        save_prompt: Annotated[
            bool,
            typer.Option("--save-prompt", help="Also save the generation prompt beside the script."),
        ] = False,
    ) -> None:
        """Create an Instagram Reel script."""
        _run_multiply(
            story_ids,
            "reel",
            output=output,
            config=config,
            provider=provider,
            prompt_only=prompt_only,
            template=template,
            save_prompt=save_prompt,
            load_runtime=load_runtime,
        )

    @multiply_app.command("shorts")
    def multiply_shorts_command(
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
    ) -> None:
        """Create a YouTube Shorts script."""
        _run_multiply(
            story_ids,
            "shorts",
            output=output,
            config=config,
            provider=provider,
            prompt_only=prompt_only,
            template=template,
            save_prompt=save_prompt,
            load_runtime=load_runtime,
        )

    @multiply_app.command("youtube")
    def multiply_youtube_command(
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
    ) -> None:
        """Create a YouTube video script."""
        _run_multiply(
            story_ids,
            "youtube",
            output=output,
            config=config,
            provider=provider,
            prompt_only=prompt_only,
            template=template,
            save_prompt=save_prompt,
            load_runtime=load_runtime,
        )

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
    ) -> None:
        """Create reel, shorts, and YouTube scripts at once."""
        settings, memory_store, story_store = load_runtime(config)
        bundle = _load_story_bundle(story_store, memory_store, story_ids)

        scripts: dict[str, str] = {}
        prompts: dict[str, str] = {}
        provider_used: str | None = None
        used_ai = False

        for fmt in SUPPORTED_FORMATS:
            try:
                result = generate_script_content(
                    bundle,
                    fmt,
                    llm=settings.llm,
                    script_prompt_path=settings.script_prompt_path,
                    provider_override=provider,
                    prompt_only=prompt_only,
                    use_template=template,
                )
            except (ProviderError, ValueError) as exc:
                typer.echo(str(exc), err=True)
                raise typer.Exit(code=1) from exc

            scripts[fmt] = result.content
            prompts[fmt] = result.prompt
            provider_used = result.provider
            used_ai = used_ai or result.used_ai

        paths = write_all_scripts(
            settings.outputs_path,
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
        for fmt in SUPPORTED_FORMATS:
            typer.echo(f"  {fmt:<8} {paths[fmt]}")
            prompt_path = paths.get(f"{fmt}-prompt")
            if prompt_path:
                typer.echo(f"           prompt: {prompt_path}")


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
    load_runtime,
) -> None:
    settings, memory_store, story_store = load_runtime(config)
    bundle = _load_story_bundle(story_store, memory_store, story_ids)

    try:
        result = generate_script_content(
            bundle,
            fmt,
            llm=settings.llm,
            script_prompt_path=settings.script_prompt_path,
            provider_override=provider,
            prompt_only=prompt_only,
            use_template=template,
        )
    except (ProviderError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    paths = write_generation_outputs(
        settings.outputs_path,
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


def _load_story_bundle(story_store, memory_store, story_ids: list[str]) -> StoryBundle:
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

        candidate = _resolve_candidate(story_store, normalized)
        if candidate is None:
            typer.echo(f"Story not found: {normalized}", err=True)
            raise typer.Exit(code=1)
        memory = memory_store.get(candidate.memory_id)
        if memory is None:
            typer.echo(f"Memory not found for story: {normalized}", err=True)
            raise typer.Exit(code=1)
        sources.append(build_story_source(candidate, memory))

    if not sources:
        typer.echo("At least one story id is required.", err=True)
        raise typer.Exit(code=1)

    return build_story_bundle(sources[0], *sources[1:])


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
