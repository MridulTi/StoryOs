from __future__ import annotations

import re
from pathlib import Path

from storyos.multiply.templates import SUPPORTED_FORMATS, render_all, render_script


def slugify(value: str, *, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        return "story"
    return slug[:limit].strip("-")


def output_path(
    outputs_path: Path,
    *,
    fmt: str,
    story_short_id: str,
    title: str,
) -> Path:
    directory = outputs_path / fmt
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{story_short_id}-{slugify(title)}.md"
    return directory / filename


def write_script(
    outputs_path: Path,
    *,
    fmt: str,
    story_short_id: str,
    title: str,
    content: str,
    output: Path | None = None,
) -> Path:
    path = output or output_path(
        outputs_path,
        fmt=fmt,
        story_short_id=story_short_id,
        title=title,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_all_scripts(
    outputs_path: Path,
    *,
    story_short_id: str,
    title: str,
    scripts: dict[str, str],
    output_dir: Path | None = None,
) -> dict[str, Path]:
    written: dict[str, Path] = {}
    for fmt in SUPPORTED_FORMATS:
        content = scripts[fmt]
        if output_dir is not None:
            path = output_dir / f"{story_short_id}-{slugify(title)}-{fmt}.md"
        else:
            path = None
        written[fmt] = write_script(
            outputs_path,
            fmt=fmt,
            story_short_id=story_short_id,
            title=title,
            content=content,
            output=path,
        )
    return written
