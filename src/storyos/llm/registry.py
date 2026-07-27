from __future__ import annotations

from storyos.llm.config import LLMConfig, PROVIDER_NAMES
from storyos.llm.copilot_cli import CopilotCliProvider
from storyos.llm.cursor_cli import CursorCliProvider
from storyos.llm.openai_api import OpenAIProvider
from storyos.llm.prompt_only import PromptOnlyProvider


def resolve_provider_name(
    override: str | None = None,
    *,
    prompt_only: bool = False,
    template: bool = False,
    config: LLMConfig | None = None,
) -> str:
    if template:
        return "template"
    if prompt_only:
        return "prompt_only"
    if override:
        name = override.strip().lower()
        if name not in PROVIDER_NAMES:
            allowed = ", ".join(PROVIDER_NAMES)
            raise ValueError(f"Unknown provider {override!r}. Choose one of: {allowed}")
        return name
    return (config or LLMConfig()).provider


def get_provider(name: str, config: LLMConfig | None = None) -> object:
    settings = config or LLMConfig()
    normalized = name.strip().lower()

    if normalized == "prompt_only":
        return PromptOnlyProvider()
    if normalized == "cursor":
        return CursorCliProvider(settings.cursor)
    if normalized == "copilot":
        return CopilotCliProvider(settings.copilot)
    if normalized == "openai":
        return OpenAIProvider(settings.openai)
    if normalized == "template":
        return PromptOnlyProvider()

    allowed = ", ".join(PROVIDER_NAMES)
    raise ValueError(f"Unknown provider {name!r}. Choose one of: {allowed}")
