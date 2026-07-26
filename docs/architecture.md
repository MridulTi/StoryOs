# Architecture

StoryOS is a personal storytelling operating system composed of layered subsystems. Each layer has a single responsibility; together they turn raw life data into discoverable, developable, publishable stories.

## System overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Creator surfaces                          │
│   (capture UI, companion chat, timeline, storyboard, exports)   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     Application / API layer                        │
│   ingestion · discovery · development · multiplication · search  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐   ┌──────────▼─────────┐   ┌────────▼────────┐
│  Story Engine  │   │    Memory Graph     │   │ Long-Term Memory │
│   (analysis)   │   │  (relationships)    │   │   (patterns)     │
└───────┬────────┘   └──────────┬─────────┘   └────────┬────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                         Memory Store                               │
│              captures · metadata · embeddings · media refs         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                        Capture Layer                               │
│   connectors: journal, voice, git, calendar, photos, chat, ...   │
└─────────────────────────────────────────────────────────────────┘
```

## Core pipeline

Every experience flows through the same stages:

| Stage | Input | Output | Owner subsystem |
|---|---|---|---|
| **Capture** | Raw life artifacts | Normalized memory records | Capture Layer |
| **Understand** | Memory records | Structured signals (emotion, conflict, …) | Story Engine |
| **Connect** | Analyzed memories | Graph edges, journeys, clusters | Memory Graph |
| **Discover** | Connected memories | Story candidates with scores | Story Engine + Memory Graph |
| **Develop** | Story candidate | Enriched narrative via interview | Story Companion |
| **Visualize** | Developed story | Storyboard mapped to personal footage | Visual Story Assistant |
| **Multiply** | Developed story | Journal, script, post, reel, … | Content Multiplication |
| **Publish** | Final artifacts | External outputs (user-controlled) | Export / integrations |

## Subsystems

### 1. Capture Layer

**Purpose:** Ingest experiences without forcing the creator to "write for StoryOS."

**Responsibilities:**

- Connect to external sources (manual entry, voice, git, calendar, files, …)
- Normalize incoming data into a common **Memory** schema
- Preserve provenance (source, timestamp, raw reference)
- Support passive and active capture modes

**Design constraints:**

- Capture must feel lightweight — friction kills the habit.
- Never rewrite or embellish source material on ingest.
- All sources are optional; the system works with whatever the creator already uses.

### 2. Memory Store

**Purpose:** Durable, queryable storage for everything captured.

**Responsibilities:**

- Persist memories, analysis results, graph edges, story drafts
- Index for semantic and temporal search
- Reference media assets (photos, clips) without duplicating unnecessarily
- Enforce per-creator isolation (single-user system first)

**Conceptual entities:**

| Entity | Description |
|---|---|
| `Memory` | A single captured experience or artifact |
| `Signal` | Story Engine output attached to a memory |
| `StoryCandidate` | A discovered story with score and metadata |
| `Story` | A developed narrative the creator owns |
| `Journey` | A connected sequence of memories over time |
| `MediaAsset` | Reference to personal photo/video footage |
| `Output` | A multiplied content artifact (blog draft, reel script, …) |

### 3. Story Engine

**Purpose:** Analyze memories and surface story potential.

See [story-engine.md](story-engine.md) for dimension definitions, scoring, and categorization.

**Key rule:** Analysis extracts what is already present. It never fabricates events, emotions, or transformations.

### 4. Memory Graph

**Purpose:** Connect isolated moments into evolving narratives.

See [memory-and-timeline.md](memory-and-timeline.md).

**Example:** "I hate documentation" → started DevLog → released DevLog → GitHub star → community contribution — four notes, one journey.

### 5. Timeline

**Purpose:** Present the creator's life as a living autobiography.

**Responsibilities:**

- Chronological view of memories and milestones
- Highlight journeys and turning points
- Surface "story arcs" that span months or years

### 6. Story Companion

**Purpose:** Interview the creator to deepen a discovered story without writing it for them.

See [story-companion.md](story-companion.md).

### 7. Visual Story Assistant

**Purpose:** Build a storyboard from the creator's existing personal footage.

**Responsibilities:**

- Map story scenes to existing clips where possible
- Flag gaps ("Capture next weekend: sunrise shot")
- Maximize reuse of personal media — **no AI-generated video**

### 8. Content Multiplication

**Purpose:** Turn one developed story into many output formats.

See [content-multiplication.md](content-multiplication.md).

### 9. Long-Term Memory

**Purpose:** Learn patterns across the creator's history.

**Responsibilities:**

- Track recurring themes (burnout, imposter syndrome, …)
- Notice unfinished or abandoned story threads
- Improve discovery relevance over time
- Surface "this connects to something from six months ago"

## Data flow: discovery example

**Input (captured journal entry):**

> Today I got paged at 2AM. Spent an hour fixing production. The issue wasn't even ours. I couldn't sleep afterwards.

**Pipeline:**

1. **Capture** → stored as `Memory` with source=journal, timestamp=today
2. **Story Engine** → signals: exhaustion (emotion), production incident + misplaced responsibility (conflict), realization about burnout (transformation), high relatability
3. **Discovery** → `StoryCandidate`: *"The hidden cost of being helpful"* — score 92/100
4. **Story Companion** → interview questions: What were you feeling? Why did this matter? What changed afterwards?
5. **Content Multiplication** → optional outputs: LinkedIn post outline, YouTube script skeleton, journal reflection

**Critical:** The AI did not invent anything. It discovered the story already present.

## Technology stance (initial)

No stack is committed yet. Architectural priorities regardless of implementation:

| Priority | Implication |
|---|---|
| Privacy-first | Creator data is sensitive; local-first or encrypted-by-default |
| Provenance | Every derived insight links back to source memories |
| Explainability | Scores and suggestions must be inspectable, not black-box |
| Extensibility | New capture connectors and output formats plug in cleanly |
| Human-in-the-loop | Discovery suggests; creator decides what deserves attention |

## Phased build order (recommended)

1. **Memory + manual capture** — journal/text entry, store, search
2. **Story Engine v1** — basic signal extraction and story scoring
3. **Story Companion** — interview flow for top candidates
4. **Timeline + Memory Graph** — connect related memories
5. **Capture connectors** — git, voice, calendar, …
6. **Content Multiplication** — export templates
7. **Visual Story Assistant** — media library + storyboard
8. **Long-Term Memory** — pattern learning across history

Each phase should deliver user value before the next layer adds complexity.

## Boundaries (what StoryOS is not)

| Not this | Because |
|---|---|
| AI writing tool | Creator is the author; AI discovers and coaches |
| Script generator | Starts from life, not from a topic prompt |
| AI video generator | Reuses personal footage; recommends what to capture |
| Social media scheduler | Publishing is downstream; discovery is the core |
| Generic note app | Optimized for story discovery, not general PKM |
