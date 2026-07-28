from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from storyos.llm.config import LLMConfig, load_llm_config
from storyos.multiply.prompt_loader import bundled_prompt_path, resolve_script_prompt_path
from storyos.paths import default_data_path, expand_path, resolve_config_path


@dataclass(frozen=True)
class DoclogConfig:
    enabled: bool
    home: Path


@dataclass(frozen=True)
class GitConfig:
    enabled: bool
    repo: Path | None
    since_days: int


@dataclass(frozen=True)
class MultiplyConfig:
    auto_context: int


@dataclass(frozen=True)
class StoryOSConfig:
    data_path: Path
    default_source: str
    datetime_format: str
    config_path: Path
    captures_path: Path
    outputs_path: Path
    script_prompt_path: Path
    llm: LLMConfig
    multiply: MultiplyConfig
    editor: str | None = None
    doclog: DoclogConfig | None = None
    git: GitConfig | None = None

    @property
    def database_path(self) -> Path:
        return self.data_path / "memories.db"


def _default_doclog_home() -> Path:
    override = os.environ.get("DOCLOG_HOME")
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".doclog").resolve()


def _load_doclog_config(raw: dict) -> DoclogConfig | None:
    integrations = raw.get("integrations") or {}
    doclog_section = integrations.get("doclog")
    if doclog_section is None:
        return DoclogConfig(enabled=True, home=_default_doclog_home())

    enabled = bool(doclog_section.get("enabled", True))
    home_raw = doclog_section.get("home")
    home = expand_path(str(home_raw)) if home_raw else _default_doclog_home()
    return DoclogConfig(enabled=enabled, home=home)


def _load_git_config(raw: dict) -> GitConfig | None:
    integrations = raw.get("integrations") or {}
    git_section = integrations.get("git")
    if git_section is None:
        return GitConfig(enabled=False, repo=None, since_days=7)
    enabled = bool(git_section.get("enabled", False))
    repo_raw = git_section.get("repo")
    repo = expand_path(str(repo_raw)) if repo_raw else None
    since_days = int(git_section.get("since_days", 7))
    return GitConfig(enabled=enabled, repo=repo, since_days=since_days)


def _load_multiply_config(raw: dict) -> MultiplyConfig:
    multiply_section = raw.get("multiply") if isinstance(raw.get("multiply"), dict) else {}
    auto_context = int(multiply_section.get("auto_context", 0))
    return MultiplyConfig(auto_context=max(0, auto_context))


def _load_optional_path(raw: dict, key: str, default: Path) -> Path:
    value = raw.get(key)
    if value is None or str(value).strip() == "":
        return default
    return expand_path(str(value))


def default_config_dict() -> dict:
    return {
        "data": {"path": str(default_data_path())},
        "capture": {"default_source": "journal"},
        "cli": {"datetime_format": "%Y-%m-%d %H:%M"},
    }


def config_template() -> str:
    return """\
# StoryOS configuration
# Docs: https://github.com/storyos/storyos

[data]
path = "{data_path}"

[capture]
default_source = "journal"
# captures_path = "{data_path}/captures"

[outputs]
# Base directory for generated reel/shorts/youtube scripts.
# path = "{data_path}/outputs"
# Script prompt used to shape generated scripts (defaults to bundled prompt, or storypromt.md beside config).
# script_prompt = "storypromt.md"

[cli]
datetime_format = "%Y-%m-%d %H:%M"

[llm]
# Default AI provider for `storyos multiply` (cursor, copilot, openai, prompt_only, template).
provider = "cursor"

[cursor]
# command = "agent"
# model = "auto"
# mode = "ask"
# timeout_seconds = 120

[integrations.doclog]
enabled = true
home = "~/.doclog"

[integrations.git]
enabled = false
# repo = "."
# since_days = 7

[multiply]
# auto_context = 2
"""


def load_config(config_path: Path | None = None) -> StoryOSConfig:
    path = resolve_config_path(config_path)
    if not path.is_file():
        defaults = default_config_dict()
        data_path = expand_path(defaults["data"]["path"])
        return StoryOSConfig(
            data_path=data_path,
            default_source=defaults["capture"]["default_source"],
            datetime_format=defaults["cli"]["datetime_format"],
            config_path=path,
            captures_path=data_path / "captures",
            outputs_path=data_path / "outputs",
            script_prompt_path=bundled_prompt_path(),
            llm=load_llm_config({}),
            multiply=MultiplyConfig(auto_context=0),
            editor=None,
            doclog=DoclogConfig(enabled=True, home=_default_doclog_home()),
            git=GitConfig(enabled=False, repo=None, since_days=7),
        )

    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    data_section = raw.get("data", {})
    capture_section = raw.get("capture", {})
    cli_section = raw.get("cli", {})
    outputs_section = raw.get("outputs", {})

    data_path = expand_path(str(data_section.get("path", str(default_data_path()))))
    editor_raw = capture_section.get("editor")
    editor = str(editor_raw).strip() if editor_raw else None
    if editor == "":
        editor = None
    script_prompt_raw = outputs_section.get("script_prompt")
    script_prompt_path = resolve_script_prompt_path(
        config_path=path,
        configured=str(script_prompt_raw) if script_prompt_raw else None,
    )
    return StoryOSConfig(
        data_path=data_path,
        default_source=str(capture_section.get("default_source", "journal")),
        datetime_format=str(cli_section.get("datetime_format", "%Y-%m-%d %H:%M")),
        config_path=path,
        captures_path=_load_optional_path(capture_section, "captures_path", data_path / "captures"),
        outputs_path=_load_optional_path(outputs_section, "path", data_path / "outputs"),
        script_prompt_path=script_prompt_path,
        llm=load_llm_config(raw),
        multiply=_load_multiply_config(raw),
        editor=editor,
        doclog=_load_doclog_config(raw),
        git=_load_git_config(raw),
    )


def init_config(config_path: Path | None = None, data_path: Path | None = None) -> StoryOSConfig:
    path = resolve_config_path(config_path)
    resolved_data = data_path or default_data_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        config_template().format(data_path=resolved_data),
        encoding="utf-8",
    )
    return load_config(path)
