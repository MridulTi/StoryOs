# Content Multiplication

One experience should produce many outputs. **Capture once. Reuse forever.**

## Purpose

After a story is developed (via Story Companion), Content Multiplication transforms it into format-specific drafts — always derived from creator-authored material, never from invented experiences.

## Pipeline

```
Experience (Memory)
        │
        ▼
Story (developed via Companion)
        │
        ├──► Journal entry
        ├──► YouTube script outline
        ├──► Instagram Reel script
        ├──► LinkedIn post
        ├──► Blog article draft
        ├──► Newsletter snippet
        ├──► Podcast outline
        └──► Book notes / chapter seed
```

Each output is a **template application** over the same source story — not a separate AI generation from scratch.

## Output types

| Format | Typical structure | Tone |
|---|---|---|
| Journal | Reflective, private, unstructured OK | Intimate |
| YouTube script | Hook → context → conflict → turn → CTA | Conversational |
| Instagram Reel | 15–60s beats, visual cues | Punchy |
| LinkedIn post | Hook line → story → lesson → question | Professional |
| Blog | Title → sections → conclusion | Long-form |
| Newsletter | Personal note + one insight | Direct |
| Podcast outline | Segments, talking points, anecdotes | Spoken |
| Book notes | Theme, chapter angle, related memories | Archival |

## Visual Story Assistant (related)

For video outputs, multiplication hands off to the **Visual Story Assistant**, which builds a storyboard:

| Scene | Visual | Existing clip | Need recording? |
|---|---|---|---|
| Metro ride | Wide shot | metro_004.mp4 | No |
| Laptop close-up | Detail | keyboard_002.mp4 | No |
| Sunrise | Establishing | — | Yes — capture next weekend |

StoryOS does **not** generate AI video. It maps scenes to personal footage and recommends what to capture.

## Design rules

1. **Single source of truth** — every output links back to the same `Story` and underlying `Memory` records.
2. **Creator edits everything** — outputs are starting points, not publish-ready unless the creator says so.
3. **Format-appropriate, not format-identical** — a LinkedIn post is not a truncated blog; each template respects medium conventions.
4. **No new facts** — multiplication rearranges and reframes; it does not add events, quotes, or emotions.
5. **Shareability tags** — private journal outputs never leak into public-format exports.

## Template system (conceptual)

```yaml
output_template:
  id: linkedin_post_v1
  format: linkedin
  sections:
    - hook: { max_chars: 120, source: story.title_or_custom }
    - body: { source: story.narrative, transform: shorten }
    - lesson: { source: interview.q_why_matters }
    - cta: { optional: true, prompt: "Ask a question" }
```

Templates are versioned and extensible — creators or the community can add formats over time.

## Multiplication vs. generation

| Content multiplication | Generic AI generation |
|---|---|
| Starts from captured life + interview | Starts from a topic prompt |
| Creator's words reframed | AI invents narrative |
| Consistent across formats | Each format independently hallucinated |
| Provenance to source memories | No grounding |

## Phasing

**v1:** Journal + one social format (e.g. LinkedIn) + plain text export  
**v2:** YouTube outline + Reel beats  
**v3:** Visual Story Assistant integration  
**v4:** Custom templates and batch export
