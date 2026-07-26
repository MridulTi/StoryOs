# AGENTS.md

StoryOS is a personal storytelling operating system. Before implementing or changing anything non-trivial, read the docs below to understand what we're building and why.

## Where to look

- **Product vision and concepts:** [docs/index.md](docs/index.md)
- **System architecture:** [docs/architecture.md](docs/architecture.md)
- **Original vision (source intent):** [foundation.md](foundation.md)
- **Why decisions were made:** [context/index.md](context/index.md)
- **Personal/local notes:** if `AGENTS.local.md` exists in this repo, read that too

Read `context/index.md` before making non-trivial changes to understand prior decisions and avoid re-litigating or accidentally reverting them.

## Codebase

- Python package: `src/storyos/` (install with `pip install -e ".[dev]"`)
- CLI entry point: `storyos` → `storyos.cli.app:main`
- Config: TOML at `~/.config/storyos/storyos.toml` (see `storyos.example.toml`)

## Working principles

1. StoryOS **discovers** stories — it never invents experiences.
2. The creator is always the author; AI is observer, memory, interviewer, and coach — never the storyteller.
3. Authenticity beats perfect writing.
4. Capture once, reuse infinitely.

<!-- keep-the-why:config -->
- context: `context/`
- init: complete
- context-schema: 0.4.2
- capture-confirmation: confirm-when-unsure
<!-- /keep-the-why:config -->
