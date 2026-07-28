# StoryOS

> **People don't lack content. They fail to recognize the stories they are already living.**

StoryOS is a personal storytelling operating system. It helps creators discover meaningful stories hidden inside everyday life — by capturing experiences, identifying emotional patterns, connecting memories, and coaching authentic storytelling.

StoryOS is **not** an AI writing tool or script generator. It discovers stories the creator is already living; the creator remains the author.

## Documentation

| Document | Purpose |
|---|---|
| [docs/index.md](docs/index.md) | Documentation map — start here |
| [docs/vision.md](docs/vision.md) | Mission, problem, philosophy, success metric |
| [docs/architecture.md](docs/architecture.md) | System design, components, data flows |
| [foundation.md](foundation.md) | Original vision document (source of truth for product intent) |
| [context/index.md](context/index.md) | Why the system is shaped this way — read before non-trivial changes |

## Core loop

```
Life → Capture → Understand → Find Story → Develop Story → Publish
```

Instead of: Topic → Prompt → Generate.

## Quick start (CLI)

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

storyos init
storyos capture          # opens your editor with a template
storyos sync doclog      # import DocLogs entries as story memories
storyos discover         # analyze captures and find story candidates
storyos stories list     # review scored stories
storyos multiply all <main-story-id> [background-story-ids...]
storyos today            # recent meaningful moments
storyos memories list
storyos memories show <id>
storyos memories search "today"
```

Configuration lives in `storyos.toml` (see [storyos.example.toml](storyos.example.toml)). By default:

- **Config:** `~/.config/storyos/storyos.toml` (override with `--config` or `STORYOS_CONFIG`)
- **Data:** path from `[data].path` in that file (SQLite at `memories.db`)
- **Captures:** `[capture].captures_path` (default: `{data}/captures`)
- **Scripts:** `[outputs].path` (default: `{data}/outputs`, with `reel/`, `shorts/`, `youtube/` inside)
- **Script prompt:** `[outputs].script_prompt` (defaults to bundled prompt, or `storypromt.md` beside config)

Set `[capture].editor` in TOML (or `$EDITOR`) for editor-based capture. Quick capture still works: `storyos capture "short note"`.

Example paths in `storyos.toml`:

```toml
[capture]
captures_path = "~/Documents/StoryOS/captures"

[outputs]
path = "~/Documents/StoryOS/scripts"
script_prompt = "~/Documents/personal/StoryOS/storypromt.md"
```

Check active paths anytime: `storyos config path`

### Script generation (AI)

`storyos multiply` uses your configured LLM to turn a discovered story into cinematic scripts. By default it calls the **Cursor CLI** (`agent`), matching DocLogs if you already use it.

```bash
storyos multiply reel <main-id>                 # Cursor AI (default)
storyos multiply all <main-id> <bg-id> <bg-id>  # main story + background context
storyos multiply all <main-id> --provider openai
storyos multiply reel <main-id> --template      # template-only output
storyos multiply reel <main-id> --prompt-only --save-prompt
```

Configure in `storyos.toml`:

```toml
[llm]
provider = "cursor"   # cursor | copilot | openai | prompt_only | template

[cursor]
command = "agent"
model = "auto"

[openai]
api_key = "${OPENAI_API_KEY}"
model = "gpt-4o-mini"
```

If `[cursor]` / `[copilot]` are omitted, StoryOS inherits them from `~/.doclog/config.yaml`. The script structure follows your `[outputs].script_prompt` file (e.g. `storypromt.md`). AI is instructed to **never invent experiences** — only reshape your captured memory.

**Main + background stories:** pass the emotional arc first, then supporting captures:

```bash
storyos multiply all abc123 def456 ghi789
# abc123 = main story ("feeling stuck and tired")
# def456, ghi789 = background (oncall pages, late-night calls)
```

**DocLogs:** if you use [DocLogs](https://github.com/MridulTi/DocLogs) (`doclog capture`), run `storyos sync doclog` to index `~/.doclog/entries/*.yaml` as StoryOS memories — same data, story discovery on top.

## Package layout

```
src/storyos/
├── cli/          # Typer CLI
├── capture/      # Capture layer (manual journal for now)
├── models/       # Memory and future entities
├── store/        # SQLite memory store
├── config.py     # TOML configuration
└── paths.py      # Config/data path resolution
```

## Status

| Phase | Feature | CLI |
|---|---|---|
| 1 | Capture + memory store | `capture`, `memories`, `sync doclog` |
| 2 | Story discovery | `discover`, `stories`, `today` |
| 3 | Story Companion | `develop` |
| 4 | Memory graph + timeline | `stories related`, `stories link`, `timeline` |
| 5 | Connectors | `sync`, `sync git`, `sync doclog` |
| 6 | Content multiplication | `multiply reel/shorts/youtube/journal/linkedin/...`, `multiply all-formats` |
| 7 | Visual story assistant | `media scan`, `storyboard` |
| 8 | Long-term memory | `patterns`, `stories dormant`, `discover --resurface` |

Main + background stories: `storyos multiply all <main-id> <bg-id>...` or `--with-related`.

## For agents

Read [AGENTS.md](AGENTS.md) before working in this repository.
