from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from storyos.cli.app import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "storyos 0.1.0" in result.stdout


def test_init_and_capture_flow(tmp_path: Path) -> None:
    config_path = tmp_path / "storyos.toml"
    data_path = tmp_path / "data"
    config_args = ["--config", str(config_path)]

    init_result = runner.invoke(
        app,
        ["init", *config_args, "--data-path", str(data_path)],
    )
    assert init_result.exit_code == 0, init_result.stdout

    capture_result = runner.invoke(
        app,
        ["capture", "What happened today?", *config_args],
    )
    assert capture_result.exit_code == 0, capture_result.stdout
    assert "Captured memory" in capture_result.stdout
    assert "file:" in capture_result.stdout

    list_result = runner.invoke(
        app,
        ["memories", "list", *config_args],
    )
    assert list_result.exit_code == 0, list_result.stdout
    assert "What happened today?" in list_result.stdout


def test_capture_via_editor(tmp_path: Path) -> None:
    config_path = tmp_path / "storyos.toml"
    data_path = tmp_path / "data"
    config_args = ["--config", str(config_path)]

    runner.invoke(app, ["init", *config_args, "--data-path", str(data_path)])

    with patch(
        "storyos.capture.editor._open_in_editor",
        return_value="source: journal\n\ndate:\n\n---\n\nLate night production incident.\n",
    ):
        result = runner.invoke(
            app,
            ["capture", *config_args, "--editor", "fake-editor"],
        )

    assert result.exit_code == 0, result.stdout
    assert "Captured memory" in result.stdout

    list_result = runner.invoke(app, ["memories", "list", *config_args])
    assert "Late night production incident." in list_result.stdout
