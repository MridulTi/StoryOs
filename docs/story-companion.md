# Story Companion

The Story Companion develops discovered stories through **interview**, not generation. It preserves authenticity while deepening the narrative.

## Purpose

Instead of writing the story for the creator, StoryOS asks questions that help the creator articulate what they already lived.

## Flow

```
StoryCandidate (from Story Engine)
        │
        ▼
Companion opens session
        │
        ▼
Guided interview (5–10 questions)
        │
        ▼
Creator answers in their own words
        │
        ▼
Structured Story draft (creator-authored content)
        │
        ▼
Optional: Content Multiplication / Visual Story Assistant
```

## Interview design

Questions target gaps the Story Engine could not fill from capture alone:

| Gap | Example question |
|---|---|
| Emotion | What were you feeling in that moment? |
| Meaning | Why did this matter to you? |
| Change | What changed afterwards — in you or in the situation? |
| Reflection | Would you make the same decision today? |
| Audience | Who would relate to this experience? |
| Detail | What do you remember that you haven't written down yet? |
| Stakes | What were you afraid would happen? |
| Resolution | How did it actually turn out? |

### Example session

**Companion:** I think this could become a great story — *"The hidden cost of being helpful."*

1. What were you feeling when you got paged at 2AM?
2. Why did you stay up fixing something that wasn't your team's fault?
3. What changed afterwards — in how you think about being "helpful"?
4. Would you respond the same way if it happened again tonight?
5. Who would relate to this — junior engineers, team leads, someone else?

**Creator answers in their own voice.** The companion may suggest structure (beginning / tension / turn / ending) but never substitutes AI prose for creator answers.

## Output

A developed **Story** contains:

| Field | Source |
|---|---|
| Working title | Engine suggestion, creator-edited |
| Source memories | Linked captures |
| Creator narrative | Assembled from interview answers (creator words) |
| Structure notes | Suggested beats, not AI-written paragraphs |
| Interview transcript | Full Q&A for reference |
| Status | draft · ready · published · archived |

## Companion roles (AI behavior)

| Do | Don't |
|---|---|
| Ask focused, empathetic questions | Write the story body |
| Reflect back what the creator said | Invent details or dialogue |
| Suggest structural gaps | Impose a generic hero's journey |
| Offer optional framing ("this could open with…") | Publish without creator approval |
| Stop when the creator has said enough | Pad with filler questions |

## Session modes

| Mode | When |
|---|---|
| **Quick** | 3 questions for low-stakes journal stories |
| **Standard** | 5–7 questions for blog/post candidates |
| **Deep** | Extended interview for long-form (YouTube, essay) |

Mode is suggested by story score and intended output format; creator always chooses.

## Integration points

- **Input:** `StoryCandidate` from Story Engine
- **Context:** Memory Graph journeys for "this connects to earlier…" prompts
- **Output:** `Story` entity → Content Multiplication, Visual Story Assistant
- **Feedback:** Completed interviews train long-term memory on what questions unlock this creator's best material

## Privacy

Interview answers are as sensitive as raw captures. Same storage, encryption, and isolation rules apply. Private stories stay out of multiplication exports unless explicitly marked shareable.
