# Prompt And Workflow Metadata Governance Alignment Plan

## Goal

Align prompt/workflow metadata and core debugging/testing workflows to a minimal,
non-duplicative contract that is easy for agents to route and execute.

## Scope

In scope:

1. Add/align minimal useful metadata fields on prompt/workflow artifacts:
   - `workflow_id` or `prompt_id`
   - `type` (`workflow|prompt`)
   - `stage` (`planning|execution|closeout|drift|maintenance`)
   - `entry_points`
   - `prerequisites`
   - `next_steps`
   - `owner_layer` (`intent|operating_system|workstream|change`)
   - `status`
   - `skills` (required by your request)
2. Enforce rule: metadata fields must not be duplicated in body prose/sections.
3. Ensure two core workflows are fully defined in standard format (as required
   workflow coverage examples):
   - `live-run-debugging-workflow.md`
   - `test-failure-triage-workflow.md`
4. Add clear agent-usage guidance for metadata-based workflow selection/execution.

Out of scope:

- Workflow-trigger prompt creation or rollout (explicitly deferred).

## Current State Summary

- `docs/operating_system/workflows/workflow-and-prompt-metadata-spec.md` exists.
- `docs/operating_system/workflows/live-run-debugging-workflow.md` exists.
- `docs/operating_system/workflows/test-failure-triage-workflow.md` exists.
- Existing metadata currently uses `id`; requested contract prefers
  `workflow_id` / `prompt_id`.

## Deliverables

1. Updated metadata specification with exact field names, allowed enums, and
   no-duplication rules.
2. Updated required workflow examples:
   - `docs/operating_system/workflows/live-run-debugging-workflow.md`
   - `docs/operating_system/workflows/test-failure-triage-workflow.md`
3. Cleanup guidance for removing duplicated metadata content from bodies.
4. Agent usage guidance (selection + execution) based on metadata.
5. Validator/test updates if required by schema name changes.

## Implementation Steps

1. Define canonical metadata contract update
   - replace `id` with `workflow_id` (workflow files) and `prompt_id`
     (prompt files).
   - keep required fields minimal and explicit.
   - specify list-format expectations for `entry_points`, `prerequisites`,
     `next_steps`, `skills`.

2. Update metadata specification document
   - revise examples to use `workflow_id` / `prompt_id`.
   - keep body-focused rule: execution logic only, no routing/classification
     duplication from metadata.
   - preserve migration guidance with concrete rewrite examples.

3. Align required workflow-example frontmatter
   - update both core workflows to canonical field names and enums.
   - verify metadata/body separation (no repeated routing blocks in body).

4. Add explicit de-duplication guidelines
   - define what counts as duplication versus allowed reference.
   - include quick review checklist for editors.

5. Validate repo contracts
   - run workflow/prompt ladder and section validators.
   - if schema is validated in scripts, update validators/tests accordingly.

6. Document agent usage model
   - route by `type` + `stage` + `entry_points`.
   - gate on `prerequisites`.
   - execute body logic with listed `skills`.
   - transition via `next_steps`.

## Validation Plan

Minimum checks after implementation:

1. `python scripts/validate_prompt_ladder.py`
2. `python scripts/validate_template_required_sections.py`
3. `python scripts/validate_planning_lifecycle.py --strict`
4. `python scripts/validate_repo_contracts.py --fast`
5. Targeted pytest for any validator/schema test updates.

## Risks And Mitigations

1. Risk: Schema rename (`id` -> `workflow_id`/`prompt_id`) breaks validators.
   Mitigation: update validators and tests in same change set.
2. Risk: Aggressive body cleanup removes useful execution detail.
   Mitigation: remove only routing/classification duplication; keep decision
   gates and evidence logic.
3. Risk: Inconsistent rollout across prompt files.
   Mitigation: apply this change first to the two required workflow examples and metadata
   spec; defer broad prompt migration to a separate tracked pass.

## Done Criteria

1. Metadata spec reflects requested fields and rules.
2. Both core workflows are present, complete, and aligned to the standard.
3. No duplicated metadata sections in those workflow bodies.
4. Agent metadata usage guidance is explicit and actionable.
5. Validators/tests pass for touched contracts.
