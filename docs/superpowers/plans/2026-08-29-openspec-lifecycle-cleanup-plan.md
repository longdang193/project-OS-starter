---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: openspec-lifecycle-cleanup
parent_spec: none
targets:
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/README.md
  - docs/intent/project-charter.md
  - docs/intent/success-outcomes.md
  - repo_config/planning_artifact_schema.yaml
  - scripts/validate_planning_lifecycle.py
  - tests/test_validate_planning_lifecycle.py
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/rules/doc-contracts-rule.md
  - docs/operating_system/prompt_templates/design-spec-prompt.md
  - docs/operating_system/templates/detailed-specification-template.md
  - .agents/skills/skill-brainstorming/SKILL.md
  - .agents/skills/skill-spec-drafting/SKILL.md
  - .agents/skills/skill-writing-plans/SKILL.md
  - .agents/skills/skill-verification-before-completion/SKILL.md
  - tests/test_starter_lifecycle_contract.py
---

## Goal

Simplify Starter planning to stable intent plus two change artifacts: one
complete specification and one implementation plan. Retire the unused roadmap
artifact, preserve unique intent if any, adopt optional baseline/change-summary
review context, and keep executable truth, plan ownership, generated surfaces,
and starter-kit boundaries unchanged.

## Implementation Outcomes

### Roadmap retirement

`master-workstream-roadmap.md` is removed only after its claims are compared
with existing intent and governance. Any unique durable project promise moves to
its owning intent document; duplicated coordination prose is deleted. Schema,
validator, tests, and active guidance no longer treat roadmap as a planning
artifact.

### Bounded OpenSpec semantics

Specifications require current-baseline inspection when relevant and may include
an optional `Baseline and Change Summary` section for reviewer orientation. The
existing `Requirements and Behavioral Contract` remains the complete normative
post-change contract. No `parent_specs`, delta IDs, automatic folding, capability
directory, semantic delta validator, OpenSpec task file, or OpenSpec runtime is
added.

### Reconciled shipped surfaces

Canonical skills and operating-system docs use affected-scope/spec
reconciliation instead of roadmap/workstream reconciliation. Generated adapter
surfaces are regenerated from canonical sources, and the starter kit is rebuilt
and validated without direct generated-output edits.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Default task executor: `codex`
- Required skills: `skill-code-standards`, `skill-executing-plans`, `skill-verification-before-completion`, `skill-plan-document-reviewer`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect and edit declared canonical files, delete the declared roadmap file, regenerate declared derived surfaces, run declared read-only checks, rebuild disposable starter output
- User-approval actions: publication, push, merge, destructive cleanup outside declared roadmap/output paths, discard of preserved user work
- Parallel ownership: `none; shared governance and schema references require sequential edits`
- Sequential fallback: complete canonical content edits, then generated sync, then starter rebuild and broad verification

## Task Breakdown

### Task 1: Audit and retire roadmap without losing intent

**Purpose:** Remove redundant roadmap ownership while preserving any unique durable
intent claim.

**Task Function:** intent ownership audit and safe artifact retirement

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: low ambiguity, bounded documentation deletion, shared-file safety

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: lead controller performs source inspection and proof

**Specification Coverage:** Roadmap removal; stable intent remains separate from change planning.

**Required Skills:** `skill-code-standards`

**Files And Symbols:**
- Inspect: `docs/intent/master-workstream-roadmap.md`
- Inspect: `docs/intent/project-charter.md`
- Inspect: `docs/intent/success-outcomes.md`
- Inspect: `docs/intent/constraints-and-non-goals.md`
- Modify: `docs/intent/README.md`
- Modify: `docs/intent/project-charter.md` only if audit finds unique durable claims
- Modify: `docs/intent/success-outcomes.md` only if audit finds unique durable claims
- Delete: `docs/intent/master-workstream-roadmap.md`
- Verify: `docs/intent/`

**Dependencies:** None.

**Authority:**
- Preauthorized local actions: inspect declared intent docs, move unique claims into the owning intent file, delete only the declared roadmap file, update its index and rules
- Stop for: unique claim requiring a new artifact, ambiguity about intent ownership, or unrelated intent changes

**Steps:**
- [x] Step 1: Compare every roadmap outcome with charter, success outcomes, constraints, and governance; classify each as duplicate, already owned, or unique.
- [x] Step 2: Move only unique durable claims to the existing owning intent document; preserve stable intent wording and avoid copying roadmap structure.
- [x] Step 3: Remove roadmap link and usage rule from `docs/intent/README.md`, then delete `docs/intent/master-workstream-roadmap.md`.

**Verification:**
- [x] `rg -n -i "roadmap|workstream|master-workstream" docs/intent`
- Expected: no active roadmap artifact or stale intent index entry; stable intent remains in existing intent docs.

**Exit Criteria:** Roadmap deleted, no unique intent lost, and `docs/intent/` still explains project purpose, stakeholders, outcomes, constraints, and non-goals.

### Task 2: Remove roadmap from planning schema and lifecycle validator

**Purpose:** Make executable planning validation recognize only specification and
plan artifacts while retaining optional-artifact behavior.

**Task Function:** schema and validator contract migration

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: direct schema/validator change with existing tests

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused tests and repository validator provide proof

**Specification Coverage:** Roadmap schema/lifecycle removal; spec and plan validation preserved.

**Required Skills:** `skill-code-standards`

**Files And Symbols:**
- Modify: `repo_config/planning_artifact_schema.yaml:allowed_values.status and artifacts`
- Modify: `scripts/validate_planning_lifecycle.py:metadata, parser description, and validate_planning_artifacts`
- Modify: `tests/test_validate_planning_lifecycle.py:metadata and roadmap tests`
- Verify: `scripts/planning_artifact_schema.py`

**Dependencies:** Task 1 completes roadmap source deletion.

**Authority:**
- Preauthorized local actions: remove roadmap schema entries and roadmap-only test fixtures; rename the empty-repository test; add spec/plan preservation regression coverage
- Stop for: any required change to plan `parent_spec` semantics or artifact schema beyond roadmap removal

**Steps:**
- [x] Step 1: Remove roadmap status values and roadmap artifact definition from `repo_config/planning_artifact_schema.yaml`.
- [x] Step 2: Update validator metadata, help text, inputs, and artifact iteration from `roadmap/spec/plan` to `spec/plan`.
- [x] Step 3: Delete only roadmap-specific validation coverage; retain and rename empty-repository coverage to prove planning artifacts remain optional; add a regression that valid spec and plan artifacts still validate.

**Verification:**
- [x] `py -3 -m pytest tests/test_validate_planning_lifecycle.py -q`
- Expected: roadmap-specific test removed, optional planning-artifact behavior passes, spec/plan validation remains enforced.

**Exit Criteria:** Schema and validator agree on exactly two change artifact types; no roadmap validation path remains.

### Task 3: Replace roadmap guidance with bounded reconciliation rules

**Purpose:** Keep useful OpenSpec-inspired behavior without creating a second
planning system or unsupported multi-spec linkage.

**Task Function:** canonical governance and skill contract update

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared prose contract; sequential canonical edits avoid drift

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: lifecycle tests, template checks, and final contract validation

**Specification Coverage:** Current-baseline inspection, optional change summary, full post-change contract, same-change revision, scope/ownership reconciliation during specification drafting, and maintained-contract ownership.

**Required Skills:** `skill-code-standards`

**Files And Symbols:**
- Modify: `docs/operating_system/governance/repo-governance.md:Planning Ownership`
- Modify: `docs/operating_system/planning/planning-dispatch.md:Artifact Selection, Delivery Lifecycle, Artifact Ownership`
- Modify: `docs/operating_system/rules/doc-contracts-rule.md:planning duplication rule`
- Modify: `docs/operating_system/prompt_templates/design-spec-prompt.md:promotion guidance`
- Modify: `docs/operating_system/templates/detailed-specification-template.md:Design Analysis and Requirements sections`
- Modify: `.agents/skills/skill-brainstorming/SKILL.md:artifact destinations`
- Modify: `.agents/skills/skill-spec-drafting/SKILL.md:baseline inspection, promotion, and contract guidance`
- Modify: `.agents/skills/skill-writing-plans/SKILL.md:artifact boundaries and single parent_spec contract`
- Modify: `.agents/skills/skill-verification-before-completion/SKILL.md:maintained-contract verification boundary`
- Modify: `tests/test_starter_lifecycle_contract.py:planning and template contract assertions`

**Dependencies:** Task 2 establishes final planning artifact vocabulary.

**Authority:**
- Preauthorized local actions: remove roadmap/workstream wording, add optional baseline/change-summary guidance, clarify plan-owned ordering and controller-owned status transitions, and update focused contract tests
- Stop for: adding `parent_specs`, delta IDs, capability specs, automatic merge/fold behavior, new lifecycle artifacts, or mandatory baseline documents

**Steps:**
- [x] Step 1: Remove roadmap/workstream artifact ownership and gates from governance, dispatch, document-contract rules, brainstorming, spec drafting, plan writing, and design-spec prompt.
- [x] Step 2: Add optional `Baseline and Change Summary` as reviewer orientation; retain complete `Requirements and Behavioral Contract` as normative post-change specification.
- [x] Step 3: Add same-change revision versus new-spec guidance; state that plans own ordering and coordination, while maintained-contract updates are named implementation scope and verification checks alignment without repairing it.
- [x] Step 4: Update lifecycle tests to lock optional summary semantics, full-contract preservation, no roadmap references, and unchanged single `parent_spec` behavior.

**Verification:**
- [x] `py -3 -m pytest tests/test_starter_lifecycle_contract.py tests/test_validate_template_required_sections.py -q`
- Expected: canonical docs and template contracts pass; existing completed-spec grandfathering remains intact.

**Exit Criteria:** OpenSpec borrowing is optional, review-oriented, and bounded; no second SSOT or multi-spec schema exists.

### Task 4: Regenerate adapters and validate shipped output

**Purpose:** Prove canonical edits propagate to generated surfaces and the
consume-only starter kit.

**Task Function:** generated-surface synchronization and release-boundary verification

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic repository procedures and read-only validation

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: canonical sync, lifecycle, repository, and starter validators

**Specification Coverage:** Generated-source consistency, starter distribution, stale-reference removal, and final repository proof.

**Required Skills:** `skill-executing-plans`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/sync_agent_adapters.py`
- Verify: `generated_agents/`
- Verify: `.agents/rules/`
- Verify: `generated_exports/project-OS-starter-kit/`
- Verify: `repo_config/starter-kit-manifest.json`
- Verify: `scripts/validate_repo_contracts.py`

**Dependencies:** Tasks 1–3 complete.

**Authority:**
- Preauthorized local actions: regenerate adapters, rebuild disposable starter output, run declared validators and tests, inspect diff and stale-reference results
- Stop for: generated drift caused by unrelated files, manifest changes, publication, or cleanup outside task-owned output

**Steps:**
- [x] Step 1: Run `py -3 scripts/sync_agent_adapters.py --all-platforms` from canonical skill and governance sources; do not edit generated copies directly.
- [x] Step 2: Run `py -3 scripts/validate_repo_contracts.py --fast` and focused lifecycle/template tests.
- [x] Step 3: Run `py -3 scripts/validate_repo_config.py`, `py -3 scripts/build_starter_kit.py`, and `py -3 scripts/validate_starter_kit.py`.
- [x] Step 4: Search canonical and generated shipped surfaces for stale roadmap/workstream references; inspect `git diff --check` and final status while preserving pre-existing untracked output.

**Verification:**
- [x] `py -3 -m pytest tests/test_validate_planning_lifecycle.py tests/test_starter_lifecycle_contract.py tests/test_starter_kit_generation.py tests/test_validate_repo_contracts.py -q`
- [x] `rg -n -i "roadmap|workstream|master-workstream" docs .agents repo_config tests generated_agents generated_exports/project-OS-starter-kit`
- [x] `git diff --check`
- Expected: tests and validators pass, stale active references are absent, generated adapters and starter output match canonical sources, and only declared changes exist.

**Exit Criteria:** Verification returns `verified`; no roadmap artifact, schema entry, validator path, active guidance, generated drift, or starter-kit drift remains.

## Verification

Run after all tasks:

1. `py -3 scripts/validate_repo_contracts.py`
2. `py -3 -m pytest tests/test_validate_planning_lifecycle.py tests/test_starter_lifecycle_contract.py tests/test_validate_template_required_sections.py tests/test_starter_kit_generation.py tests/test_validate_repo_contracts.py -q`
3. `py -3 scripts/validate_repo_config.py`
4. `py -3 scripts/build_starter_kit.py`
5. `py -3 scripts/validate_starter_kit.py`
6. `git diff --check`
7. Inspect `git status --short`, canonical/generated diffs, and stale-reference search.

Expected result: all required checks pass; generated output derives from
canonical inputs; roadmap retirement loses no stable intent; detailed specs
remain complete post-change contracts; plan linkage remains singular; no
capability or semantic-delta machinery appears.

## Completion Criteria

The plan is ready for completion verification when:

1. roadmap intent is either preserved in existing owners or proven duplicated
2. roadmap schema, validator, tests, and active guidance are removed or updated
3. optional baseline/change-summary guidance does not replace normative requirements
4. single `parent_spec` semantics remain unchanged
5. canonical skills and docs have no stale roadmap/workstream references
6. generated adapters and starter-kit output pass validation
7. focused and broad verification commands pass
8. no unrelated user changes are discarded

Execution was approved and completed; frontmatter status is `completed`. No
capability spec layer, semantic delta validator, automatic fold, OpenSpec
runtime, or multi-spec linkage is part of this plan.
