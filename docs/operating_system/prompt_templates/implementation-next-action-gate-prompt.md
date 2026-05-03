# Implementation Next-Action Gate Prompt

## Use When

partial execution completed and the next constrained action must be selected

## Prerequisites

### Required

- in-scope roadmap/workstream/thread and plan/spec context identified

### Optional

- latest validator outputs

## Next Prompts

- implementation-next-action-gate-prompt.md
- thread-closeout-readiness-prompt.md

## Not For

initial intent/roadmap construction
Use this after an agent completes part of an implementation plan and needs the
next allowed action.

```text
Determine the next execution action from existing planning artifacts only.

Context:
- roadmap/workstream/thread in scope:
- implementation plan path:
- related detailed spec(s):
- implementation execution map path:
- current completion statuses:
- unresolved issues:

Constraint:
Do not invent unrelated next steps. Choose the next action only from:
- documented roadmap/workstream/thread scope
- approved specs
- implementation execution map ordering/dependencies
- current implementation plan tasks
- open blockers and downstream impact

Please:
1. verify what was completed against current item Key Deliverables
2. list unresolved problems and required adjustments
3. verify dependency order and downstream impact
4. identify next eligible action from existing plan/spec/map documents
5. if no action is eligible, return the minimal prerequisite action needed to unblock
6. return one selected next action and why alternatives are not yet eligible
   - if closure criteria are already satisfied, select `close now` and explain why further actions are not eligible
```

Expected output:
- one constrained next action grounded in existing planning artifacts
