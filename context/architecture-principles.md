# Architecture Principles

Why the system is shaped into layers and phased the way it is.

## Layered subsystem model

**Status:** active  
**Evidence:** inferred  
**Source:** Derived from [foundation.md](../foundation.md) concepts; structured in [docs/architecture.md](../docs/architecture.md)  
**Revisit when:** first implementation stack is chosen or monolith vs. services decision is made

StoryOS decomposes into: Capture Layer → Memory Store → Story Engine + Memory Graph + Long-Term Memory → surfaces (Companion, Timeline, Multiplication, Visual Assistant).

**Reason:** Each foundation concept maps to an isolated subsystem with clear boundaries. Enables phased delivery — memory + engine before connectors, companion before multiplication.

**Rejected alternative:** Single "chat with your journal" monolith. Rejected for now because it hides distinct responsibilities (ingest vs. analyze vs. connect vs. interview vs. export) and makes it harder to enforce "no fabrication" at each stage.

## No AI-generated video

**Status:** active  
**Evidence:** confirmed  
**Source:** [foundation.md](../foundation.md) — Visual Story Assistant  

Visual Story Assistant builds storyboards from existing personal footage and recommends captures — it does not generate synthetic video.

**Reason:** Personal footage is the authenticity moat. AI video would contradict "life is the source material."

## Provenance and explainability

**Status:** active  
**Evidence:** inferred  
**Source:** Implied by "never invent experiences" and discovery example in [foundation.md](../foundation.md)  

Every story candidate, signal, and multiplied output must link to source memories. Scores must be inspectable (which dimension, why).

**Reason:** Without provenance, discovery feels like hallucination. Creators must trust that suggestions come from their life.

**Rejected alternative:** Opaque composite score with no breakdown. Rejected — dimensional stars (conflict, emotion, …) are part of the product UX in foundation.

## Privacy-first stance

**Status:** active  
**Evidence:** inferred  
**Source:** Nature of product (personal diary, voice, photos, reflections) in [foundation.md](../foundation.md)  
**Revisit when:** deployment model (local vs. cloud) is decided

Creator data is highly sensitive. Architecture assumes encrypted storage, single-creator isolation, and explicit shareability tags before any export.

**Rejected alternative:** Cloud-first social platform with default public sharing. Not aligned with product — publishing is user-controlled and downstream.

## Recommended build phasing

**Status:** active  
**Evidence:** inferred  
**Source:** [docs/architecture.md](../docs/architecture.md) — dependency ordering  

1. Memory + manual capture  
2. Story Engine v1  
3. Story Companion  
4. Timeline + Memory Graph  
5. Capture connectors  
6. Content Multiplication  
7. Visual Story Assistant  
8. Long-Term Memory patterns  

**Reason:** Each phase delivers standalone value. Engine without graph still surfaces candidates; companion without multiplication still develops stories.

**Rejected alternative:** Build all capture connectors first. Rejected — connectors add complexity before core discovery loop is proven.

## Technology stack

**Status:** open  
**Evidence:** unknown  
**Source:** No stack specified in foundation or early docs  

Stack intentionally uncommitted. Priorities documented: privacy-first, provenance, explainability, extensibility, human-in-the-loop.

**Revisit when:** implementation begins — record chosen stack and rejected alternatives here.
