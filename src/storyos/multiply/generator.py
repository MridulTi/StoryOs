from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from storyos.llm.base import ProviderError
from storyos.llm.config import LLMConfig
from storyos.llm.registry import get_provider, resolve_provider_name
from storyos.models.developed_story import DevelopedStory
from storyos.multiply.prompt_builder import build_generation_prompt, check_shareability, wrap_generated_script
from storyos.multiply.source import StoryBundle, StorySource
from storyos.multiply.templates import render_script


@dataclass(frozen=True)
class GenerationResult:
    content: str
    provider: str
    prompt: str
    used_ai: bool
    prompt_path_written: Path | None = None


def generate_script_content(
    source: StoryBundle | StorySource,
    fmt: str,
    *,
    llm: LLMConfig,
    script_prompt_path: Path,
    provider_override: str | None = None,
    prompt_only: bool = False,
    use_template: bool = False,
    developed: DevelopedStory | None = None,
) -> GenerationResult:
    check_shareability(fmt, developed)
    prompt = build_generation_prompt(
        source,
        fmt,
        script_prompt_path=script_prompt_path,
        developed=developed,
    )
    provider_name = resolve_provider_name(
        provider_override,
        prompt_only=prompt_only,
        template=use_template,
        config=llm,
    )

    if provider_name == "template":
        content = render_script(source, fmt, prompt_path=script_prompt_path)
        return GenerationResult(content=content, provider="template", prompt=prompt, used_ai=False)

    if provider_name == "prompt_only":
        content = _prompt_only_markdown(prompt, source=source, fmt=fmt, script_prompt_path=script_prompt_path)
        return GenerationResult(content=content, provider="prompt_only", prompt=prompt, used_ai=False)

    provider = get_provider(provider_name, llm)
    if not provider.is_available():
        raise ProviderError(
            f"Provider {provider_name!r} is not available. {provider.availability_hint()}"
        )

    body = provider.generate(prompt)
    content = wrap_generated_script(
        body,
        source=source,
        fmt=fmt,
        provider=provider_name,
        prompt_path=script_prompt_path,
        developed=developed,
    )
    return GenerationResult(content=content, provider=provider_name, prompt=prompt, used_ai=True)


def _prompt_only_markdown(
    prompt: str,
    *,
    source: StoryBundle | StorySource,
    fmt: str,
    script_prompt_path: Path,
) -> str:
    from storyos.multiply.source import as_bundle

    bundle = as_bundle(source)
    main = bundle.main
    context_line = ""
    if bundle.context:
        context_line = f"\n- background stories: `{', '.join(bundle.context_story_ids())}`"

    return f"""# Script generation prompt — {main.title}

> Provider: prompt_only  
> Format: {fmt}  
> Paste the prompt below into Cursor, Copilot, or ChatGPT.

---

## Prompt

{prompt}

---

## Metadata

- main story: `{main.candidate.id}`
- main memory: `{main.memory.id}`{context_line}
- script prompt file: `{script_prompt_path}`
"""
