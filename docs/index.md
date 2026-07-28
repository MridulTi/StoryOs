# StoryOS Documentation

This folder describes **what StoryOS is** and **how it is designed**. For the reasoning behind design choices, see [context/index.md](../context/index.md).

## Start here

1. [vision.md](vision.md) — mission, problem, philosophy, guiding principles
2. [architecture.md](architecture.md) — system components, layers, and data flows
3. [glossary.md](glossary.md) — shared terminology

## Deep dives

| Topic | Document |
|---|---|
| Story analysis and scoring | [story-engine.md](story-engine.md) |
| Memory graph and timeline | [memory-and-timeline.md](memory-and-timeline.md) |
| Interview-based story development | [story-companion.md](story-companion.md) |
| One experience → many outputs | [content-multiplication.md](content-multiplication.md) |

## Implementation checklist

| Phase | Status | Key commands |
|---|---|---|
| 1 Memory + capture | Done | `capture`, `memories`, `sync doclog` |
| 2 Story Engine v1 | Done | `discover`, `stories list/show` |
| 3 Story Companion | Done | `develop` |
| 4 Memory Graph + Timeline | Done | `stories related`, `stories link`, `timeline` |
| 5 Capture connectors | Done (doclog + git) | `sync`, `sync git` |
| 6 Content multiplication | Done | `multiply`, `multiply all-formats` |
| 7 Visual Story Assistant | Done | `media scan`, `storyboard` |
| 8 Long-Term Memory | Done | `patterns`, `stories dormant`, `discover --resurface` |

## Source document

[foundation.md](../foundation.md) is the original vision document. The docs in this folder expand it into structured, agent-readable architecture. When intent is unclear, defer to `foundation.md`.
