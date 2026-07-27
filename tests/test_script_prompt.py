from __future__ import annotations

from pathlib import Path

import pytest

from storyos.config import load_config
from storyos.multiply.prompt_loader import bundled_prompt_path, load_script_prompt, resolve_script_prompt_path


def test_bundled_prompt_exists() -> None:
    path = bundled_prompt_path()
    assert path.is_file()
    text = load_script_prompt(str(path))
    assert "Diary to Cinematic Script" in text
    assert "Never invent experiences" in text


def test_resolve_script_prompt_from_config(tmp_path: Path) -> None:
    config_path = tmp_path / "storyos.toml"
    prompt_path = tmp_path / "storypromt.md"
    prompt_path.write_text("# Custom prompt\nNever invent.\n", encoding="utf-8")
    config_path.write_text(
        f"""
[data]
path = "{tmp_path / 'data'}"

[outputs]
script_prompt = "{prompt_path}"
""".strip(),
        encoding="utf-8",
    )

    settings = load_config(config_path)
    assert settings.script_prompt_path == prompt_path.resolve()


def test_resolve_script_prompt_missing_raises(tmp_path: Path) -> None:
    config_path = tmp_path / "storyos.toml"
    with pytest.raises(FileNotFoundError):
        resolve_script_prompt_path(
            config_path=config_path,
            configured=str(tmp_path / "missing.md"),
        )
