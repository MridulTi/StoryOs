from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from storyos.paths import expand_path


def bundled_prompt_path() -> Path:
    return Path(__file__).resolve().parent.parent / "prompts" / "script_writer.md"


def resolve_script_prompt_path(
    *,
    config_path: Path,
    configured: str | Path | None = None,
) -> Path:
    env_path = os.environ.get("STORYOS_SCRIPT_PROMPT")
    if env_path:
        return expand_path(env_path)

    if configured is not None and str(configured).strip():
        path = Path(str(configured)).expanduser()
        if not path.is_absolute():
            path = (config_path.parent / path).resolve()
        else:
            path = path.resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Script prompt not found: {path}")
        return path

    for candidate in (
        config_path.parent / "storypromt.md",
        config_path.parent / "script_writer.md",
    ):
        if candidate.is_file():
            return candidate.resolve()

    bundled = bundled_prompt_path()
    if bundled.is_file():
        return bundled
    raise FileNotFoundError("No script prompt file found. Set [outputs].script_prompt in storyos.toml.")


@lru_cache(maxsize=4)
def load_script_prompt(path_str: str) -> str:
    path = Path(path_str)
    return path.read_text(encoding="utf-8").strip()
