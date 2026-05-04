---
template_id: implementation-plan
artifact_type: plan
layer: operating_system
status: proposed
parent_thread: none
parent_spec: none
---

# Workflows Folder Rollout Plan

## Goal

Create `docs/operating_system/workflows/` as the canonical home for
multi-step, gate-based procedures that orchestrate prompt ladders end-to-end.

## Key Deliverables

- new folder: `docs/operating_system/workflows/`
- initial workflow docs:
  - `roadmap-to-closeout-workflow.md`
  - `drift-detection-and-reconciliation-workflow.md`
  - `spec-to-plan-to-execution-workflow.md`
- cross-links from prompt README to workflow docs
- clear boundary rule between `prompt_templates/` and `workflows/`

## Task Breakdown

- task 1:
  - create `docs/operating_system/workflows/`
- task 2:
  - author `roadmap-to-closeout-workflow.md`
  - include:
    - purpose
    - entry criteria
    - ordered steps
    - decision gates
    - exit criteria
    - related prompts
    - related skills
    - failure/recovery path
- task 3:
  - author `drift-detection-and-reconciliation-workflow.md`
  - include same section contract as task 2
- task 4:
  - author `spec-to-plan-to-execution-workflow.md`
  - include same section contract as task 2
- task 5:
  - update `docs/operating_system/prompt_templates/README.md`:
    - explain when to use workflows vs prompt templates
    - link to the new workflow docs
- task 6:
  - verify links and sequencing consistency with current prompt ladder

## Verification

- confirm files exist at expected paths
- verify each workflow includes required sections
- verify referenced prompt links resolve
- manual consistency pass against current closeout and next-action gate model

## Completion Criteria

Plan is complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

