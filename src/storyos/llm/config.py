from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomllib
import yaml

from storyos.paths import expand_path

PROVIDER_NAMES = ("cursor", "copilot", "openai", "prompt_only", "template")

_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


@dataclass(frozen=True)
class LLMConfig:
    provider: str = "cursor"
    cursor: dict[str, Any] = field(default_factory=dict)
    copilot: dict[str, Any] = field(default_factory=dict)
    openai: dict[str, Any] = field(default_factory=dict)


def expand_env(value: object) -> object:
    if isinstance(value, str):

        def replace(match: re.Match[str]) -> str:
            return os.environ.get(match.group(1), match.group(0))

        return _ENV_PATTERN.sub(replace, value)
    if isinstance(value, dict):
        return {key: expand_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [expand_env(item) for item in value]
    return value


def resolved_cli_model(model: object) -> str | None:
    if model is None:
        return None
    if not isinstance(model, str):
        return str(model)
    normalized = model.strip().lower()
    if not normalized or normalized == "auto":
        return None
    return model.strip()


def _section(raw: dict, name: str, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    value = raw.get(name)
    if isinstance(value, dict):
        merged = dict(fallback or {})
        merged.update(value)
        return merged
    return dict(fallback or {})


def _try_load_doclog_yaml() -> dict[str, Any]:
    path = Path.home() / ".doclog" / "config.yaml"
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if isinstance(data, dict):
            return expand_env(data)
    except OSError:
        return {}
    return {}


def load_llm_config(raw: dict | None = None) -> LLMConfig:
    raw = raw or {}
    doclog = _try_load_doclog_yaml()
    llm_section = raw.get("llm") if isinstance(raw.get("llm"), dict) else {}
    provider_raw = llm_section.get("provider")
    if provider_raw is None and isinstance(doclog.get("llm"), dict):
        provider_raw = doclog["llm"].get("provider")
    provider = str(provider_raw or "cursor").strip().lower()
    if provider not in PROVIDER_NAMES:
        provider = "cursor"

    return LLMConfig(
        provider=provider,
        cursor=_section(raw, "cursor", doclog.get("cursor") if isinstance(doclog.get("cursor"), dict) else {}),
        copilot=_section(raw, "copilot", doclog.get("copilot") if isinstance(doclog.get("copilot"), dict) else {}),
        openai=_section(raw, "openai", doclog.get("openai") if isinstance(doclog.get("openai"), dict) else {}),
    )


def load_llm_config_from_toml(path: Path) -> LLMConfig:
    if not path.is_file():
        return load_llm_config({})
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    return load_llm_config(raw)
