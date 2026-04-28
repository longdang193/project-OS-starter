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

- a `bounded change thread` is one discrete execution-capable slice inside
  either a workstream or the `operating_system` branch
- product workstreams may express those slices explicitly through
  `docs/intent/workstreams/threads/<workstream-id>/`
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
7. Use `docs/intent/workstreams/threads/` when the next bounded slice should
   become an explicit thread file before spec or plan creation.
8. Use
   [workstream-coverage-and-progress-guide.md](C:/Users/HOANG%20PHI%20LONG%20DANG/repos/project-OS-starter/docs/intent/workstream-coverage-and-progress-guide.md)
   for the precise ladder, coverage review, progress tracking, and safe
   parallel execution rules.

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

Keep this document focused on coverage:

- what major threads are needed
- whether the registered workstreams cover them

Do not track detailed progress here; that belongs in the registered workstream
docs and downstream specs/plans.

## Roadmap-Level Completion Checklist

- [ ] The end goal is broken into major delivery threads.
- [ ] Each major delivery thread maps to a registered workstream or to
      `operating_system` intentionally.
- [ ] No major jobs to be done are still obviously unowned.
- [ ] No registered workstream is clearly duplicate or too vague.
- [ ] Cross-workstream dependencies are understood well enough to plan safely.
- [ ] The current set is complete enough to reach the intended end state.

Optional future structure:

```text
docs/intent/
  master-workstream-roadmap.md
  workstreams/
    workstream-<id>.md
    threads/
      <workstream-id>/
        01-<thread-slug>.md
```

The `workstreams/` folder is now the canonical registry for named workstreams.
Keep the roadmap high-level; keep concrete valid IDs in the registry docs and
execution-capable slices in the thread subtree.

## Anti-Patterns

- treating this roadmap as a second source of truth for project intent
- turning this file into a release log or execution diary
- creating a new workstream for every small change
- forcing `operating_system` work into a product workstream just to fit the
  hierarchy
- writing specs or plans that float without either roadmap or
  operating-system context
