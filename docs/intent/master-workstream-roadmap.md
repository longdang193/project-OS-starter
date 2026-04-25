# Master Workstream Roadmap

This document is the top-down planning bridge from project intent into durable
major work.

It does not replace the intent layer. It translates intent into planning
threads that later specs and implementation plans can attach to without drifting
from the project's original purpose.

## Purpose

Use this roadmap to answer:

- which durable workstreams serve the project's intent
- which kinds of work belong under those workstreams
- which kinds of work belong in the `operating_system` branch instead
- what downstream specs and plans should point back to

## Planning Tree

Use this planning model:

```text
intent
├─ workstreams
│  ├─ workstream-a
│  ├─ workstream-b
│  └─ ...
└─ operating_system
   ├─ planning and routing
   ├─ validation and sync
   ├─ publication and private/public governance
   ├─ instruction surfaces and agent workflow
   └─ other repo-method concerns
```

Then:

- a `change` is one bounded slice inside either a workstream or the
  `operating_system` branch
- specs describe bounded design
- implementation plans describe bounded execution

## Workstreams vs Operating-System

Use a **workstream** when the work is a durable product-direction thread derived
from project intent.

Examples:

- a major user-facing capability area
- a long-running delivery track
- a durable architecture theme tied to project outcomes

Use **operating_system** when the work is about how the repo operates rather
than what the project delivers.

Examples:

- planning workflow and routing
- validation and sync rules
- publication boundaries
- instruction surfaces, skills, and agent behavior
- repo governance and documentation method

Do not force operating-system work into fake product workstreams.

## How To Use This Roadmap

1. Start from the intent docs in this folder.
2. Identify the durable thread that best serves that intent.
3. Decide whether the work belongs under:
   - a product workstream
   - the `operating_system` branch
4. Create bounded specs and implementation plans downstream.
5. Use `parent_workstream` when a spec or plan belongs to a real workstream.
6. Use `docs/intent/workstreams/` as the canonical registry for valid named
   workstream IDs.

When a human or agent still needs help moving from this roadmap into the right
thread, use the roadmap-aware prompts under
`docs/operating_system/prompt_templates/`, especially:

- `roadmap-to-workstream-prompt.md`
- `workstream-to-spec-prompt.md`
- `workstream-alignment-review-prompt.md`
- `roadmap-gap-prompt.md`
- `roadmap-vs-execution-divergence-prompt.md`

If the work is repo-method work, it may still correctly use
`parent_workstream: none`.

## Recommended Roadmap Shape

As this structure matures, keep this doc stable and high-level.

Recommended contents:

- intent outcomes that matter most
- durable workstreams derived from those outcomes
- success signals for each workstream
- boundaries for what does not belong in each workstream
- explicit notes about operating-system work that stays outside product
  workstreams

Optional future structure:

```text
docs/intent/
  master-workstream-roadmap.md
  workstreams/
    workstream-<id>.md
```

The `workstreams/` folder is now the canonical registry for named workstreams.
Keep the roadmap high-level; keep concrete valid IDs in the registry docs.

## Anti-Patterns

- treating this roadmap as a second source of truth for project intent
- turning this file into a release log or execution diary
- creating a new workstream for every small change
- forcing `operating_system` work into a product workstream just to fit the
  hierarchy
- writing specs or plans that float without either roadmap or
  operating-system context
