from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from storyos.paths import default_data_path, expand_path, resolve_config_path


@dataclass(frozen=True)
class DoclogConfig:
    enabled: bool
    home: Path


@dataclass(frozen=True)
class StoryOSConfig:
    data_path: Path
    default_source: str
    datetime_format: str
    config_path: Path
    captures_path: Path
    outputs_path: Path
    editor: str | None = None
    doclog: DoclogConfig | None = None

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
# Base directory for generated scripts (creates reel/, shorts/, youtube/ inside).
# path = "{data_path}/outputs"

[cli]
datetime_format = "%Y-%m-%d %H:%M"

[integrations.doclog]
enabled = true
home = "~/.doclog"
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
            editor=None,
            doclog=DoclogConfig(enabled=True, home=_default_doclog_home()),
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
    return StoryOSConfig(
        data_path=data_path,
        default_source=str(capture_section.get("default_source", "journal")),
        datetime_format=str(cli_section.get("datetime_format", "%Y-%m-%d %H:%M")),
        config_path=path,
        captures_path=_load_optional_path(capture_section, "captures_path", data_path / "captures"),
        outputs_path=_load_optional_path(outputs_section, "path", data_path / "outputs"),
        editor=editor,
        doclog=_load_doclog_config(raw),
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
