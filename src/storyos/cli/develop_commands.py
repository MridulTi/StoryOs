from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from storyos.cli.discovery_commands import _resolve_candidate
from storyos.companion.interview import EditorNotFoundError, InterviewCancelled, run_interview
from storyos.companion.questions import questions_for_mode
from storyos.models.developed_story import (
    DEVELOPED_STATUS_DRAFT,
    DEVELOPED_STATUS_READY,
    DevelopedStory,
    SHAREABILITY_PRIVATE,
    SHAREABILITY_SHAREABLE,
)
from storyos.models.story import STORY_STATUS_PICKED
from storyos.runtime import load_runtime


def register_develop_command(app: typer.Typer) -> None:
    @app.command("develop")
    def develop_command(
        story_id: Annotated[str, typer.Argument(help="Story id or memory id prefix.")],
        mode: Annotated[
            str,
            typer.Option("--mode", help="Interview depth: quick, standard, or deep."),
        ] = "standard",
        ready: Annotated[
            bool,
            typer.Option("--ready", help="Mark the developed story as ready after interview."),
        ] = False,
        private: Annotated[
            bool,
            typer.Option("--private", help="Mark developed story as private (journal-only outputs)."),
        ] = False,
        config: Annotated[Optional[Path], typer.Option("--config")] = None,
    ) -> None:
        """Interview yourself to deepen a discovered story."""
        runtime = load_runtime(config)
        candidate = _resolve_candidate(runtime.story_store, story_id)
        if candidate is None:
            typer.echo(f"Story not found: {story_id}", err=True)
            raise typer.Exit(code=1)

        runtime.story_store.set_status(candidate.id, STORY_STATUS_PICKED)
        existing = runtime.developed_store.get_by_candidate(candidate.id)
        existing_answers = {
            item.question_id: item.answer for item in (existing.interview if existing else [])
        }

        questions = questions_for_mode(mode, candidate)
        typer.echo(f"Developing: {candidate.title}")
        typer.echo(f"  mode: {mode} ({len(questions) - 1} questions)")
        typer.echo("")

        try:
            transcript = run_interview(
                questions,
                editor=runtime.settings.editor,
                existing=existing_answers,
            )
        except InterviewCancelled as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=0) from exc
        except EditorNotFoundError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc

        creator_narrative = "\n\n".join(
            f"{item.question}\n{item.answer}" for item in transcript if item.answer.strip()
        )
        story = DevelopedStory(
            candidate_id=candidate.id,
            memory_ids=[candidate.memory_id],
            title=candidate.title,
            interview=transcript,
            creator_narrative=creator_narrative,
            status=DEVELOPED_STATUS_READY if ready else DEVELOPED_STATUS_DRAFT,
            shareability=SHAREABILITY_PRIVATE if private else SHAREABILITY_SHAREABLE,
        )
        if existing:
            story = DevelopedStory(
                id=existing.id,
                candidate_id=candidate.id,
                memory_ids=[candidate.memory_id],
                title=candidate.title,
                interview=transcript,
                creator_narrative=creator_narrative,
                status=story.status,
                shareability=story.shareability,
                created_at=existing.created_at,
            )
        runtime.developed_store.upsert(story)

        typer.echo(f"Saved developed story {story.short_id()}")
        typer.echo(f"  answers: {len(transcript)}")
        typer.echo(f"  status:  {story.status}")
        typer.echo(f"  share:   {story.shareability}")
        typer.echo("")
        typer.echo(f"Next: storyos multiply all {candidate.short_id()}")
