from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from pathlib import Path

from storyos.companion.questions import CompanionQuestion
from storyos.models.developed_story import InterviewQA


class InterviewCancelled(Exception):
    """Raised when the user cancels the interview."""


class EditorNotFoundError(Exception):
    """Raised when no editor is configured or available."""


def resolve_editor(configured: str | None = None) -> str:
    if configured:
        return configured
    return os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nano"


def ask_question(
    question: CompanionQuestion,
    *,
    editor: str | None = None,
    existing_answer: str = "",
) -> str:
    template = _question_template(question, existing_answer=existing_answer)
    editor_command = resolve_editor(editor)
    raw = _open_in_editor(template, editor_command, prefix=f"storyos-interview-{question.id}")
    answer = _extract_answer(raw)
    if not answer.strip():
        raise InterviewCancelled(f"No answer provided for: {question.text}")
    return answer.strip()


def run_interview(
    questions: list[CompanionQuestion],
    *,
    editor: str | None = None,
    existing: dict[str, str] | None = None,
) -> list[InterviewQA]:
    existing = existing or {}
    transcript: list[InterviewQA] = []
    for question in questions:
        if question.id == "intro":
            continue
        answer = ask_question(
            question,
            editor=editor,
            existing_answer=existing.get(question.id, ""),
        )
        transcript.append(
            InterviewQA(
                question_id=question.id,
                question=question.text,
                answer=answer,
            )
        )
    return transcript


def _question_template(question: CompanionQuestion, *, existing_answer: str) -> str:
    lines = [
        f"# {question.text}",
        "",
        "Write your answer below. StoryOS saves your words exactly — no AI rewriting.",
        "",
        "---",
        "",
        existing_answer.strip(),
        "",
    ]
    return "\n".join(lines)


def _extract_answer(raw: str) -> str:
    lines = raw.splitlines()
    body: list[str] = []
    past_separator = False
    for line in lines:
        if line.strip() == "---" and not past_separator:
            past_separator = True
            continue
        if past_separator:
            body.append(line)
    if body:
        return "\n".join(body).strip()
    return raw.strip()


def _open_in_editor(template: str, editor_command: str, *, prefix: str) -> str:
    fd, temp_name = tempfile.mkstemp(prefix=f"{prefix}-", suffix=".md")
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(template)

        command = [*shlex.split(editor_command), str(temp_path)]
        try:
            exit_code = subprocess.call(command)
        except FileNotFoundError as exc:
            raise EditorNotFoundError(
                f"Editor not found: {editor_command!r}. "
                "Set $EDITOR or [capture].editor in storyos.toml."
            ) from exc

        if exit_code != 0:
            raise InterviewCancelled(f"Editor exited with code {exit_code}.")

        return temp_path.read_text(encoding="utf-8")
    finally:
        temp_path.unlink(missing_ok=True)
