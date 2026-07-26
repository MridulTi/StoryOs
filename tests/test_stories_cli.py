from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from storyos.cli.app import app

runner = CliRunner()

DOCLOG_SAMPLE = """\
topic: Production incident after hours
impact: Realized praise is not worth burnout.
blockers: The issue was not even ours, but I stayed up fixing it.
remember: Nobody asked me to sacrifice myself.
Got paged at 2AM and could not sleep afterwards.
"""


def test_discover_and_stories_flow(tmp_path: Path) -> None:
    config_path = tmp_path / "storyos.toml"
    data_path = tmp_path / "data"
    config_args = ["--config", str(config_path)]

    runner.invoke(app, ["init", *config_args, "--data-path", str(data_path)])

    capture_result = runner.invoke(
        app,
        ["capture", DOCLOG_SAMPLE, *config_args, "--source", "doclog"],
    )
    assert capture_result.exit_code == 0, capture_result.output

    discover_result = runner.invoke(app, ["discover", *config_args])
    assert discover_result.exit_code == 0, discover_result.output
    assert "discovered:" in discover_result.stdout

    list_result = runner.invoke(app, ["stories", "list", *config_args, "--min-score", "40"])
    assert list_result.exit_code == 0, list_result.output

    show_line = next(
        line
        for line in list_result.stdout.splitlines()
        if line and not line.startswith("-") and "SCORE" not in line and "ID" not in line
    )
    story_id = show_line.split()[0]

    show_result = runner.invoke(app, ["stories", "show", story_id, *config_args])
    assert show_result.exit_code == 0, show_result.output
    assert "score:" in show_result.stdout.lower()

    pick_result = runner.invoke(app, ["stories", "pick", story_id, *config_args])
    assert pick_result.exit_code == 0, pick_result.output
    assert "Picked story" in pick_result.stdout

    multiply_result = runner.invoke(app, ["multiply", "all", story_id, *config_args])
    assert multiply_result.exit_code == 0, multiply_result.output
    assert "reel" in multiply_result.stdout
    assert "youtube" in multiply_result.stdout
