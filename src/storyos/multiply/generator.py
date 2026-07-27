from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from storyos.llm.base import ProviderError
from storyos.llm.config import LLMConfig
from storyos.llm.registry import get_provider, resolve_provider_name
from storyos.multiply.prompt_builder import build_generation_prompt, wrap_generated_script
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
    bundle: StoryBundle,
    fmt: str,
    *,
    llm: LLMConfig,
    script_prompt_path: Path,
    provider_override: str | None = None,
    prompt_only: bool = False,
    use_template: bool = False,
) -> GenerationResult:
    prompt = build_generation_prompt(bundle, fmt, script_prompt_path=script_prompt_path)
    provider_name = resolve_provider_name(
        provider_override,
        prompt_only=prompt_only,
        template=use_template,
        config=llm,
    )

    if provider_name == "template":
        content = render_script(bundle, fmt, prompt_path=script_prompt_path)
        return GenerationResult(content=content, provider="template", prompt=prompt, used_ai=False)

    if provider_name == "prompt_only":
        content = _prompt_only_markdown(
            prompt,
            bundle=bundle,
            fmt=fmt,
            script_prompt_path=script_prompt_path,
        )
        return GenerationResult(content=content, provider="prompt_only", prompt=prompt, used_ai=False)

    provider = get_provider(provider_name, llm)
    if not provider.is_available():
        raise ProviderError(
            f"Provider {provider_name!r} is not available. {provider.availability_hint()}"
        )

    body = provider.generate(prompt)
    content = wrap_generated_script(
        body,
        bundle=bundle,
        fmt=fmt,
        provider=provider_name,
        prompt_path=script_prompt_path,
    )
    return GenerationResult(content=content, provider=provider_name, prompt=prompt, used_ai=True)


def _prompt_only_markdown(
    prompt: str,
    *,
    bundle: StoryBundle,
    fmt: str,
    script_prompt_path: Path,
) -> str:
    source = bundle.main
    context_line = ""
    if bundle.context:
        ids = ", ".join(item.candidate.short_id() for item in bundle.context)
        context_line = f"\n- background stories: `{ids}`"

    return f"""# Script generation prompt — {source.title}

> Provider: prompt_only  
> Format: {fmt}  
> Paste the prompt below into Cursor, Copilot, or ChatGPT.

---

## Prompt

{prompt}

---

## Metadata

- main story: `{source.candidate.id}`
- main memory: `{source.memory.id}`{context_line}
- script prompt file: `{script_prompt_path}`
"""
