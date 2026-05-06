---
workflow_id: live-run-system
type: workflow
stage: execution
owner_layer: change
entry_points:
  - live run execution is requested end-to-end
  - a partial live-run state already exists and needs routing
prerequisites:
  - in-scope roadmap/workstream/thread and spec context is identified
  - target runtime path or failure context is available
next_steps:
  - live-run-scenario-planning-workflow.md
  - live-run-preflight-check-workflow.md
  - live-run-execution-workflow.md
  - live-run-debugging-workflow.md
  - multi-worktree-execution-workflow.md
  - live-run-verification-workflow.md
  - live-run-closeout-workflow.md
skills:
  - planning-dispatch
  - executing-plans
status: active
outputs:
  - selected next workflow decision with reason
  - lifecycle state snapshot
validators:
  - route decision references current artifacts and signals
---

# Live Run System Workflow

## Goal

Orchestrate the full live-run lifecycle by routing to the correct modular
sub-workflow based on current state and run signals.

## Lifecycle States

1. Scenario definition ready or missing.
2. Preflight readiness pass or fail.
3. Execution success or failure.
4. Verification pass or fail.
5. Closeout ready or blocked.

## Routing Logic

1. If no validated scenario set exists for the target path, route to
   `live-run-scenario-planning-workflow.md`.
2. If scenario exists but preflight evidence is missing/incomplete, route to
   `live-run-preflight-check-workflow.md`.
3. If preflight passes and no run result exists yet, route to
   `live-run-execution-workflow.md`.
4. If run result is failure and independent lanes are identifiable, route to
   `multi-worktree-execution-workflow.md`.
5. If run result is failure and lane splitting is not justified, route to
   `live-run-debugging-workflow.md`.
6. If run result is success, route to `live-run-verification-workflow.md`.
7. If multi-worktree merge/reconcile is complete with evidence aligned, route
   to `live-run-verification-workflow.md`.
8. If verification passes and closure evidence is complete, route to
   `live-run-closeout-workflow.md`.
9. If verification fails or regressions appear, route back to
   `live-run-debugging-workflow.md`.

## Partial Entry Rules

- If a known failure already exists, enter directly at debugging.
- If multi-worktree lanes already exist, enter at
  `multi-worktree-merge-and-reconcile-prompt.md` or verification based on
  current evidence state.
- If execution already succeeded and artifacts exist, enter at verification.
- If a closeout draft exists with open gaps, enter at closeout.

## Flow Overview

```mermaid
flowchart TD
  A["Start: live-run request or existing failure"] --> B{"Scenario set exists?"}
  B -- "no" --> C["live-run-scenario-planning-workflow.md"]
  B -- "yes" --> D{"Preflight ready?"}
  C --> D
  D -- "no" --> E["live-run-preflight-check-workflow.md"]
  D -- "yes" --> F{"Independent lanes detected?"}
  E --> F

  F -- "yes" --> G["multi-worktree-execution-workflow.md"]
  G --> H["multi-worktree-merge-and-reconcile-prompt.md"]
  H --> I{"All lanes merged + evidence reconciled?"}
  I -- "no" --> G
  I -- "yes" --> J["live-run-verification-workflow.md"]

  F -- "no" --> K["live-run-execution-workflow.md"]
  K --> L{"Run status"}
  L -- "failed" --> M["live-run-debugging-workflow.md"]
  M --> N{"Need lane split now?"}
  N -- "yes" --> G
  N -- "no" --> K
  L -- "passed" --> J

  J --> O{"Verification passed?"}
  O -- "no" --> M
  O -- "yes" --> P["live-run-closeout-workflow.md"]
```

## Exit Criteria

- A concrete next workflow is selected.
- Selection is justified by current artifacts/signals.
- No blind transition is made without required evidence.
