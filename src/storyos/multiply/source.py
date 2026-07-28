from __future__ import annotations

from dataclasses import dataclass

from storyos.engine.analyzer import parse_structured_fields
from storyos.models.memory import Memory
from storyos.models.story import StoryCandidate


@dataclass(frozen=True)
class StorySource:
    candidate: StoryCandidate
    memory: Memory
    topic: str | None
    impact: str | None
    blockers: str | None
    remember: str | None
    body: str

    @property
    def title(self) -> str:
        return self.candidate.title

    @property
    def hook(self) -> str:
        if self.blockers:
            return _first_sentence(self.blockers) or self.candidate.conflict
        return self.candidate.conflict or self.title

    @property
    def lesson(self) -> str:
        if self.remember:
            return _first_sentence(self.remember) or self.candidate.potential_ending
        if self.impact:
            return _first_sentence(self.impact) or self.candidate.transformation
        return self.candidate.potential_ending or self.candidate.transformation

    @property
    def turn(self) -> str:
        if self.impact:
            return _trim(self.impact, 280)
        return self.candidate.transformation

    @property
    def context(self) -> str:
        fields = parse_structured_fields(self.memory.content)
        if fields.worked_on:
            return _trim(fields.worked_on, 320)
        return _trim(self.body, 320)


@dataclass(frozen=True)
class StoryBundle:
    """Main story plus optional background stories for script generation."""

    main: StorySource
    context: tuple[StorySource, ...] = ()

    @property
    def source(self) -> StorySource:
        return self.main

    def background_text(self) -> str:
        if not self.context:
            return self.main.context
        parts: list[str] = []
        for item in self.context:
            parts.append(f"### {item.title}\n{item.memory.content.strip()}")
        return "\n\n".join(parts)

    def context_story_ids(self) -> list[str]:
        return [item.candidate.short_id() for item in self.context]


def build_story_bundle(
    main: StorySource,
    *context: StorySource,
) -> StoryBundle:
    return StoryBundle(main=main, context=context)


def as_bundle(source: StoryBundle | StorySource) -> StoryBundle:
    if isinstance(source, StoryBundle):
        return source
    return StoryBundle(main=source)


def build_story_source(candidate: StoryCandidate, memory: Memory) -> StorySource:
    fields = parse_structured_fields(memory.content)
    body = _strip_structured_header(memory.content)
    return StorySource(
        candidate=candidate,
        memory=memory,
        topic=fields.topic,
        impact=fields.impact,
        blockers=fields.blockers,
        remember=fields.remember,
        body=body,
    )


def _strip_structured_header(content: str) -> str:
    lines: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            if lines:
                lines.append("")
            continue
        lowered = stripped.lower()
        if lowered.startswith(
            ("topic:", "impact:", "blockers:", "remember:", "worked_on:", "status:", "source:", "date:")
        ):
            continue
        if stripped == "---":
            continue
        if lowered.startswith("## git evidence") or lowered.startswith("## pull requests"):
            break
        lines.append(stripped)
    return "\n".join(lines).strip()


def _first_sentence(text: str | None) -> str | None:
    if not text:
        return None
    compact = " ".join(line.strip() for line in text.splitlines() if line.strip())
    if not compact:
        return None
    for sep in (". ", "! ", "? ", "\n"):
        if sep in compact:
            return compact.split(sep, 1)[0].strip() + (sep.strip() if sep != "\n" else "")
    return compact[:160]


def _trim(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."
