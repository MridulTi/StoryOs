# Story Engine

The Story Engine analyzes captured memories across multiple narrative dimensions and produces **story candidates** the creator can choose to develop.

The goal of scoring is not ranking for its own sake — it helps creators decide **what deserves attention**.

## Analysis dimensions

Every memory is evaluated across five dimensions.

### 1. Emotional signal

How emotionally meaningful was this moment?

Example signals: happiness, fear, burnout, curiosity, excitement, failure, pride, nostalgia, love, regret.

The engine identifies emotional weight present in the source material — it does not assign emotions the creator did not express or imply.

### 2. Conflict

Stories require conflict. The engine looks for:

- Internal conflict (doubt, identity tension, values clash)
- External conflict (obstacles, people, systems)
- Decisions, sacrifices, risks
- Failure and uncertainty

A memory with no detectable conflict may still be valuable (e.g. quiet reflection) but typically has lower immediate story potential.

### 3. Transformation

A story is not an event — it is **change**. The engine attempts to answer: *What changed?*

Did the creator:

- Learn something?
- Change perspective?
- Solve a problem?
- Lose or gain something?
- Build something?
- Become someone different?

Transformation is often incomplete in raw capture. The Story Companion fills gaps through interview — the engine flags *potential* transformation, not fabricated arcs.

### 4. Relatability

Would other people identify with this experience?

Common relatable themes: rejection, exhaustion, first days, fear of loss, burnout, imposter syndrome, moving cities, learning something hard.

Relatability increases outward-facing content potential; low relatability does not mean low personal value (private journal stories matter too).

### 5. Novelty

How fresh or unexpected is this experience relative to the creator's history?

Repeated themes (e.g. third burnout entry this month) may score lower on novelty but higher on pattern significance for long-term memory.

## Story potential score

Each memory (or cluster) receives a composite **Story Score** with per-dimension breakdown.

Example presentation:

```
Story Potential: 92/100

Conflict        ★★★★★
Emotion         ★★★★☆
Transformation  ★★★★★
Relatability    ★★★★★
Novelty         ★★★☆☆
```

Scores are **advisory**. A low-scored private moment may be exactly what the creator needs for their journal. A high-scored moment is a nudge: *"There is a story here."*

## Story types

StoryOS automatically categorizes discoveries. A single story may belong to multiple categories.

| Category | Examples |
|---|---|
| Career | Job changes, promotions, layoffs |
| Engineering | Bugs, incidents, technical wins |
| Startup | Founding, pivots, fundraising |
| Burnout | Exhaustion, recovery, boundaries |
| Relationships | Family, friends, partners |
| Fear | Anxiety, risk avoidance |
| Identity | Who am I becoming? |
| Philosophy | Beliefs, worldview shifts |
| Success / Failure | Wins and lessons |
| Leadership | Teams, decisions, responsibility |
| Childhood | Formative memories |
| Funny | Humor, absurdity |
| Productivity | Systems, habits |
| Creativity | Making, blocks, breakthroughs |
| Growth | Learning, change over time |

Categories improve filtering, timeline clustering, and content multiplication template selection.

## Discovery output

A story candidate includes:

| Field | Description |
|---|---|
| `title` | Suggested working title (creator can rename) |
| `sourceMemories` | Links to underlying captures |
| `conflict` | Identified tension |
| `emotion` | Primary emotional signal |
| `transformation` | Detected or suspected change |
| `potentialEnding` | A narrative direction implied by the material — not written prose |
| `score` | Composite and dimensional breakdown |
| `categories` | Story type tags |

### Example

**Input:**

> Today I got paged at 2AM. Spent an hour fixing production. The issue wasn't even ours. I couldn't sleep afterwards.

**Output:**

| Field | Value |
|---|---|
| Title | The hidden cost of being "helpful" |
| Conflict | Production incident; responsibility beyond one's team |
| Emotion | Exhaustion |
| Transformation | Realized praise isn't worth burnout |
| Potential ending | Nobody asked me to sacrifice myself |
| Score | 92/100 |

Notice: nothing was invented. The engine surfaced what was already in the text.

## Engine constraints

1. **No fabrication** — if a dimension is absent from source material, mark it unknown or low-confidence; do not fill with plausible fiction.
2. **Provenance** — every signal cites which memory (and which passage) it came from.
3. **Confidence levels** — distinguish strong inference from weak suggestion.
4. **Creator override** — creator can dismiss, recategorize, or re-score; feedback improves long-term memory.
5. **Batch + incremental** — analyze on ingest and re-analyze when related memories connect.

## Relationship to other subsystems

```
Memory Store
     │
     ▼
Story Engine ──► StoryCandidate ──► Story Companion
     │                                      │
     ▼                                      ▼
Memory Graph ◄── journey links      Content Multiplication
     │
     ▼
Timeline / Long-Term Memory
```
