---
prompt_id: bug-intake-and-routing-prompt
type: prompt
stage: drift
owner_layer: change
entry_points:
  - a new bug report/failure is received and routing is not yet decided
  - debugging started but bug class/severity is still ambiguous
prerequisites:
  - initial bug evidence exists (error, failing test, artifact, or report)
  - in-scope roadmap/workstream/thread context is available or explicitly unknown
next_steps:
  - implementation-next-action-gate-prompt.md
  - patch-and-pattern-detection-prompt.md
  - live-run-system-dispatch-prompt.md
skills:
  - planning-dispatch
  - systematic-debugging
status: active
---
# Bug Intake And Routing Prompt

## Use When

you need to classify a bug and choose the correct debugging/patch entry path

## Prerequisites

### Required

- initial failure evidence is available

### Optional

- related run id, trace id, or failing test command

## Next Prompts

- implementation-next-action-gate-prompt.md
- patch-and-pattern-detection-prompt.md
- live-run-system-dispatch-prompt.md

## Not For

claiming fixes before root-cause and route classification

```text
Classify this bug and select one routing path.

Context:
- roadmap/workstream/thread in scope:
- failure signal:
- affected components:
- known blockers:

Please:
1. classify bug type: runtime | test | contract | metadata | drift
2. classify severity: critical | high | medium | low
3. identify likely failure boundary and evidence strength
4. select one route:
   - live-run path
   - test-failure path
   - direct bounded patch path
   - drift reconciliation path
5. return one selected next action and why alternatives are not yet eligible
```

Expected output:
- bug class/severity, selected route, and one selected next action

