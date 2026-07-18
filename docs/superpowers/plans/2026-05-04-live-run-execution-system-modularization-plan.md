---
layer: operating_system
artifact_type: plan
status: proposed
parent_workstream: none
parent_thread: none
parent_spec: docs/superpowers/specs/2026-05-04-prompt-ladder-non-standalone-spec.md
targets:
related_features: []
related_stages: []
---

# Live Run Execution System Modularization Plan

## Goal

Refactor the current monolithic live-run debugging flow into a modular
live-run execution system with one orchestrator workflow and focused
single-responsibility sub-workflows.

## Scope

In scope:

1. Introduce master orchestrator:
2. Add modular sub-workflows:
3. Align all above with metadata contract and chaining rules.

Out of scope:

- Prompt-trigger automation additions.
- Non-live-run planning lifecycle contract changes.

## Design Principles

1. Orchestrator routes; sub-workflows execute.
2. One workflow = one responsibility.
3. Partial entry is first-class (debugging/preflight/execution can be entry).
4. No blind actions:
   - debugging is evidence-first
   - fixes are bounded/minimal
5. No metadata/body duplication:
   - routing/classification lives in frontmatter
   - body focuses on execution logic and decision gates

## Target Workflow Topology

Primary chain:


Loop edges:

- execution failure -> debugging -> execution (targeted rerun) or verification
- verification fail/regression -> debugging
- closeout gap -> scenario planning or preflight (minimal corrective loop)

## Metadata Contract For New/Updated Workflows

Each workflow file must include:

- `workflow_id`
- `type: workflow`
- `stage` (`planning|execution|closeout|drift|maintenance`)
- `entry_points`
- `prerequisites`
- `next_steps`
- `owner_layer`
- `status`
- `skills` (required by current repo contract)

Rules:

1. Metadata fields must be present and non-empty where required.
2. Body must not duplicate metadata lists as standalone routing sections.
3. `next_steps` must point to valid existing prompt/workflow files.

## Per-Workflow Responsibilities


- Defines lifecycle states and routing gates only.
- Accepts partial entry states (e.g., pre-existing failure).
- Decision logic:
  - no scenarios -> scenario planning
  - prerequisites missing -> preflight
  - run failed -> debugging
  - run succeeded -> verification -> closeout
- Must not copy step-level execution from sub-workflows.


- Define scenario catalog and run triggers.
- Map each scenario to workstream/thread/spec targets.
- Define expected evidence outputs per scenario.


- Validate prerequisites:
  - required artifacts present
  - observability/tracing surfaces enabled
  - traceability IDs resolvable
  - environment/config correctness
- Block execution when evidence capture is not viable.


- Execute selected pipeline path/stages.
- Capture run outputs, intermediate artifacts, telemetry pointers.
- Emit success/failure signal for orchestrator routing.


- Keep evidence-first boundary analysis.
- Enforce bounded minimal fix policy.
- Rerun only affected scope first, then escalate as needed.
- Preserve failure -> fix -> validation traceability chain.


- Validate issue resolution and expected outputs.
- Check regression risk using targeted + expanded verification gates.
- Determine whether closeout is eligible or debugging loop is required.


- Record root cause, fix summary, validation evidence, residual risks.
- Feed learnings back to:
  - tests
  - specs
  - future scenario definitions
- Provide explicit closeout decision and follow-up actions.

## Implementation Steps

1. Create orchestrator workflow file with routing-only body.
2. Create five new sub-workflow files (planning, preflight, execution,
   verification, closeout).
   update its links.
4. Normalize metadata + next-step linkage across all live-run workflows.
5. Add/update references from workflow README/index files if present.
6. Run validators and resolve linkage/contract errors.

## Validation Plan

Required:

1. `python scripts/validate_prompt_ladder.py`
2. `python scripts/validate_template_required_sections.py`
3. `python scripts/validate_repo_contracts.py --fast`

Recommended:

4. targeted check that each `next_steps` entry in new live-run workflows
   resolves to an existing file.
5. manual routing walkthrough for:
   - green path (success to closeout)
   - failure path (debug loop to verification)
   - partial entry at debugging

## Done Criteria

1. All 7 workflows exist with required metadata fields.
2. Orchestrator contains routing logic only, no duplicated execution detail.
3. Sub-workflows are independently executable and single-responsibility.
4. Partial entry is explicitly supported in metadata + body logic.
5. Evidence-first and bounded-fix constraints are explicit in debugging flow.
6. Validation passes for touched contracts.

## Risks And Mitigations

1. Risk: overlap between orchestrator and sub-workflow steps.
   Mitigation: enforce “route-only” rule in orchestrator review checklist.
2. Risk: stale links in `next_steps`.
   Mitigation: run linkage validation and manual chain walkthrough.
3. Risk: over-broad stage/owner classification.
   Mitigation: keep values minimal and consistent with existing metadata spec.
