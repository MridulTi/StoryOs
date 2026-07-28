from __future__ import annotations

from dataclasses import dataclass

from storyos.models.story import StoryCandidate


@dataclass(frozen=True)
class CompanionQuestion:
    id: str
    gap: str
    text: str


QUESTION_BANK: tuple[CompanionQuestion, ...] = (
    CompanionQuestion("emotion", "emotion", "What were you feeling in that moment?"),
    CompanionQuestion("meaning", "meaning", "Why did this matter to you?"),
    CompanionQuestion("change", "change", "What changed afterwards — in you or in the situation?"),
    CompanionQuestion("decision", "reflection", "Would you make the same decision today?"),
    CompanionQuestion("audience", "audience", "Who would relate to this experience?"),
    CompanionQuestion("detail", "detail", "What do you remember that you haven't written down yet?"),
    CompanionQuestion("stakes", "stakes", "What were you afraid would happen?"),
    CompanionQuestion("resolution", "resolution", "How did it actually turn out?"),
)

MODE_QUESTIONS = {
    "quick": ("emotion", "meaning", "change"),
    "standard": ("emotion", "meaning", "change", "decision", "audience"),
    "deep": tuple(q.id for q in QUESTION_BANK),
}


def questions_for_mode(mode: str, candidate: StoryCandidate) -> list[CompanionQuestion]:
    normalized = mode.strip().lower()
    ids = MODE_QUESTIONS.get(normalized, MODE_QUESTIONS["standard"])
    by_id = {item.id: item for item in QUESTION_BANK}
    selected = [by_id[qid] for qid in ids if qid in by_id]
    intro = CompanionQuestion(
        "intro",
        "context",
        f'You picked: "{candidate.title}". Answer in your own words — StoryOS will not rewrite this.',
    )
    return [intro, *selected]
