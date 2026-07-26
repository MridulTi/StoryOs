# Glossary

Shared terminology for StoryOS. Use these terms consistently in code, docs, and conversation.

| Term | Definition |
|---|---|
| **Capture** | The act of ingesting a life artifact into StoryOS (journal entry, voice note, git commit, …) |
| **Memory** | A normalized record of one captured experience, with provenance and timestamp |
| **Signal** | A Story Engine analysis result on a dimension (emotion, conflict, …) attached to a memory |
| **Story Candidate** | A discovered story with score, title suggestion, and links to source memories — not yet developed |
| **Story** | A creator-owned narrative developed through Story Companion interview |
| **Story Engine** | Subsystem that analyzes memories for narrative dimensions and scores |
| **Story Score** | Advisory composite rating of story potential with dimensional breakdown |
| **Story Companion** | Interview-based subsystem that helps creators develop stories in their own words |
| **Memory Graph** | Network of memories connected by relationships and journeys |
| **Journey** | A named multi-memory arc (e.g. "documentation frustration → open source") |
| **Timeline** | Chronological presentation of memories, milestones, and journeys |
| **Long-Term Memory** | Pattern layer tracking themes, unfinished stories, and recurring lessons |
| **Content Multiplication** | Transforming one developed story into multiple output formats |
| **Visual Story Assistant** | Storyboard builder mapping scenes to personal footage |
| **Output** | A format-specific artifact produced by multiplication (blog draft, reel script, …) |
| **Media Asset** | Reference to creator-owned photo or video used in storyboards |
| **Provenance** | Traceability from any derived insight back to source capture |
| **Discovery** | The process of finding story candidates in existing memories |
| **Development** | The interview process that turns a candidate into a developed story |

## AI role names

| Role | Meaning |
|---|---|
| Observer | Notices patterns in data |
| Memory | Stores and recalls what creator forgot |
| Interviewer | Asks questions via Story Companion |
| Story Coach | Guides structure and development |

AI is **never** called the storyteller or author.

## Anti-patterns (terms we avoid)

| Avoid | Use instead |
|---|---|
| "Generate a story" | "Discover" or "develop" a story |
| "AI-written post" | "Draft from your story" or "multiplied output" |
| "Prompt" (as primary input) | "Capture" or "what happened today" |
| "Content idea" (disconnected) | "Story candidate" (grounded in memory) |
