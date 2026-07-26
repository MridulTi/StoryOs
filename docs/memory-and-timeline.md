# Memory Graph and Timeline

Life is not a collection of isolated moments. Stories evolve over months. StoryOS connects related memories into **journeys** and presents them on a **timeline** — a living autobiography.

## Memory Graph

### Purpose

Identify when separate captures are actually parts of one narrative arc.

### Graph model

```
Memory ──relates_to──► Memory
   │                       │
   └──part_of_journey──────┘
              │
              ▼
           Journey
```

**Node types:**

| Node | Description |
|---|---|
| `Memory` | Atomic captured experience |
| `Journey` | Named arc spanning multiple memories |
| `Milestone` | Significant point on a journey or timeline |

**Edge types:**

| Edge | Meaning |
|---|---|
| `continues` | Same thread, later in time |
| `contrasts` | Before/after change |
| `causes` | One experience led to another (inferred, with confidence) |
| `thematically_related` | Shared theme without direct causation |
| `part_of` | Memory belongs to a journey |

### Example journey

Individual captures:

1. "I hate documentation."
2. Started building DevLog.
3. Released DevLog.
4. Someone starred it on GitHub.
5. First community contribution.

**Without graph:** five unrelated notes.  
**With graph:** one journey — *"From documentation frustration to open source."*

### Connection strategies

1. **Explicit** — creator links memories manually
2. **Temporal** — proximity in time + shared entities (project names, people, places)
3. **Semantic** — embedding similarity on content
4. **Thematic** — long-term memory patterns (recurring "burnout" cluster)
5. **Engine-assisted** — Story Engine flags "this may connect to X from March"

All inferred edges carry confidence scores and can be confirmed or rejected by the creator.

## Timeline

### Purpose

Give the creator a chronological view of their life as story material — not just a list of notes.

### Views

| View | Shows |
|---|---|
| **Chronological** | All memories on a time axis |
| **Journeys** | Multi-month arcs overlaid on timeline |
| **Milestones** | Key turning points highlighted |
| **Story candidates** | High-potential moments marked for development |

### Example timeline

```
Failed Interview
      ↓
Started AWS learning
      ↓
First DevOps Job
      ↓
First Production Incident
      ↓
Built LazyOps
      ↓
Open Source contributions
      ↓
Conference Talk
```

The timeline becomes a living autobiography the creator can browse, reflect on, and mine for content.

## Long-term memory integration

The graph and timeline feed **Long-Term Memory**, which tracks:

| Pattern type | Example |
|---|---|
| Recurring themes | Burnout every Q4 |
| Emotional patterns | Anxiety spikes before launches |
| Unfinished stories | Started writing about X, never developed |
| Abandoned projects | Three side projects with no closure |
| Repeated lessons | Same insight rediscovered multiple times |

Long-term memory improves discovery ("you've felt this before") and can resurface dormant story candidates when new memories complete an arc.

## Design principles

1. **Creator confirmation for strong claims** — causal links ("X caused Y") need higher evidence or explicit approval.
2. **Graceful decay** — rejected inferred edges are not re-suggested blindly.
3. **Privacy by scope** — journeys can be tagged private vs. shareable for content multiplication.
4. **No forced narrative** — the graph suggests structure; creator defines meaning.

## Data stored per journey

```yaml
journey:
  id: uuid
  title: "From documentation hate to DevLog"
  memory_ids: [uuid, ...]
  milestones: [{ memory_id, label, date }]
  status: active | resolved | abandoned
  categories: [engineering, open_source, growth]
  created_at: timestamp
  updated_at: timestamp
```
