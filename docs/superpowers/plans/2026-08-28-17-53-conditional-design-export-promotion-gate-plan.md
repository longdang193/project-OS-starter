---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: conditional-design-export-promotion-gate
targets:
  - docs/operating_system/planning/planning-dispatch.md
  - .agents/skills/skill-spec-drafting/SKILL.md
  - docs/operating_system/templates/draft-specification-template.md
  - docs/operating_system/templates/detailed-specification-template.md
  - docs/operating_system/prompt_templates/design-spec-prompt.md
  - docs/operating_system/rules/frontend-ui-rule.md
  - tests/test_starter_lifecycle_contract.py
  - AGENTS.md
  - .agents/rules
  - generated_agents
  - generated_exports/project-OS-starter-kit
---

# Conditional Design Export Promotion Gate Plan

## Goal

Add a conditional post-approval Design Export gate without creating a new
artifact type, lifecycle status, metadata system, planning layer, or mandatory
UI workflow. Reconcile every canonical draft-promotion instruction so approved
drafts wait only for explicitly applicable prerequisites before in-place
promotion.

## Execution Evidence

- Review result: supplied verdict fixes applied; generator safety, explicit method selection, UX-only triggering, and reviewer/executor separation reconciled.
- Pre-generator baseline: `git diff --name-only` contained only declared canonical files; dirty generator destinations had no unclassified changes. Pre-existing `.playwright-mcp/**` and `db/**` artifacts were not touched.
- Focused proof: `42 passed` before generation; `70 passed` after canonical edits and sync.
- Repository proof: `54 passed`; planning, repo-config, Starter Kit, adapter-sync, and drift checks passed.
- Final proof: full suite `249 passed`; Starter Kit validation passed; adapter sync check passed; `git diff --check` passed with only Git line-ending warnings.

## Implementation Outcomes

### Conditional lifecycle ownership

`planning-dispatch.md` owns one lifecycle definition. It distinguishes owner
approval from specification promotion and keeps Design Export and roadmap or
workstream reconciliation conditional.

### Consistent promotion contract

The planning policy, drafting skill, both specification templates, and design
specification prompt use the same rule: approval does not imply immediate
promotion when explicitly applicable post-approval inputs remain required.

Frozen prototypes remain immutable approved UX reference evidence. Detailed
specifications remain owners of approved behavior, design decisions, contracts,
and invariants. Project design systems remain owners of durable visual
primitives. Source and tests remain owners of implemented behavior.

### Frontend export boundary

The frontend rule requires curation before generated design output becomes a
project design-system source and requires conflicts with frozen UX to be
surfaced for reconciliation. It does not define an OpenDesign playbook or
select a fixed agent profile.

### Executable regression and generated alignment

Focused lifecycle tests enforce conditionality, ownership, and promotion
semantics. Canonical changes regenerate provider projections and pass planning,
repository, Starter Kit, drift, and whitespace verification. Provider names
remain explicit method choices, not Starter dependencies.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Default task executor: `codex`
- Required skills: `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed canonical docs, skill, and focused test; run sync, validators, tests, Starter Kit build, and drift checks; inspect generated diffs
- User-approval actions: push, merge, publication, external writes, destructive cleanup, discard, or edits outside listed targets
- Parallel ownership: none; promotion wording must change in dependency order
- Sequential fallback: execute Tasks 1 through 5 in order

Pre-execution gate: `skill-plan-document-reviewer` returns
`implementation-ready` for lifecycle ownership, conditionality, promotion
semantics, generated boundaries, and verification scope. Before Task 1, record
`git status --short --untracked-files=all` and `git diff --name-only`; classify
dirty paths under canonical targets, `AGENTS.md`, `.agents/rules/**`,
`generated_agents/**`, and `generated_exports/project-OS-starter-kit/**`. Do not
run a generator that can overwrite a dirty generated destination unless that
destination is explicitly approved and classified.

## Task Breakdown

### Task 1: Add conditional Design Export lifecycle gate

**Purpose:**
- Make `planning-dispatch.md` the sole owner of the conditional Design Export
  gate and separate approval from promotion.

**Task Function:**
- Reconcile lifecycle routing policy against existing artifact ownership.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one canonical policy file; no delegated judgment required.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: final repository validation covers policy text and generated surfaces.

**Specification Coverage:**
- Design Export applies only when an applicable owner-approved UX freeze or equivalent approved visual prototype state must produce durable downstream design inputs.
- Roadmap or workstream reconciliation remains optional.
- Approval and promotion are distinct decisions.

**Required Skills:**
- `none`

**Files And Symbols:**
- Inspect: `docs/operating_system/planning/planning-dispatch.md`
- Inspect: `docs/operating_system/tooling/frontend-backend-integration-tools.md`
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Verify: `tests/test_starter_lifecycle_contract.py`

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: modify the named planning policy and focused test later in Task 4.
- Stop for: mandatory-gate wording, new artifact or status proposals, lifecycle duplication, or changes outside listed targets.

**Steps:**
- [x] Add conditional Design Export to Artifact Selection.
- [x] Insert conditional Design Export after an applicable owner-approved UX freeze or equivalent approved visual prototype state in Delivery Lifecycle.
- [x] State that explicit method selection may name a provider such as OpenDesign, while provider availability or installation alone does not select it or make it a Starter dependency.
- [x] State that applicable post-approval gates complete before draft promotion; non-applicable gates are skipped.
- [x] Preserve optional roadmap or workstream reconciliation and existing release or observe ownership.
- [x] Do not add OpenDesign procedure details, fixed profile selection, or a second lifecycle in integration tooling.

**Verification:**
- [x] Inspect lifecycle and ownership sections for one policy owner and conditional wording.
- Expected: Design Export is present in dispatch only as an applicable gate, and integration tooling still states that lifecycle ownership belongs to dispatch.

**Exit Criteria:**
- Planning dispatch describes conditional Design Export and approval-versus-promotion without introducing new artifact or status vocabulary.

### Task 2: Reconcile all draft-promotion instructions

**Purpose:**
- Remove contradictory immediate-promotion guidance across all five canonical promotion owners.

**Task Function:**
- Normalize specification promotion contract and preserve in-place draft history.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic text and template contract reconciliation.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused lifecycle and template validators prove consistency.

**Specification Coverage:**
- Approval does not necessarily imply immediate promotion.
- Draft remains `status: proposed` while explicitly applicable required post-approval inputs remain incomplete.
- Promotion still replaces the same file with `template_id: detailed-specification` and `status: active`.
- No new frontmatter fields, status, artifact, or Engineering Contract alias.
- Prototype references remain evidence or immutable UX reference; they do not own behavior or design-system truth.

**Required Skills:**
- `skill-spec-drafting`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-spec-drafting/SKILL.md`
- Inspect: `docs/operating_system/templates/draft-specification-template.md`
- Inspect: `docs/operating_system/templates/detailed-specification-template.md`
- Inspect: `docs/operating_system/prompt_templates/design-spec-prompt.md`
- Modify: `.agents/skills/skill-spec-drafting/SKILL.md`
- Modify: `docs/operating_system/templates/draft-specification-template.md`
- Modify: `docs/operating_system/templates/detailed-specification-template.md`
- Modify: `docs/operating_system/prompt_templates/design-spec-prompt.md`
- Verify: `repo_config/planning_artifact_schema.yaml`

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: edit only the four named promotion surfaces.
- Stop for: new metadata without an active consumer, unverifiable hash requirements, competing ownership claims, or status-schema changes.

**Steps:**
- [x] Replace immediate-after-approval wording with the applicable-prerequisite promotion rule in the drafting skill.
- [x] Update draft template promotion guidance and prototype evidence wording.
- [x] Update detailed template introduction and prototype evidence fields using ordinary document content only; use revision or reference, not mandatory hash metadata.
- [x] Update design specification prompt to apply the same rule.
- [x] Search all five files for stale immediate-promotion wording and resolve every contradiction.

**Verification:**
- [x] `rg -n -i "after approval|promot|prototype|UX approval|design export|workstream" docs/operating_system/planning/planning-dispatch.md .agents/skills/skill-spec-drafting/SKILL.md docs/operating_system/templates/draft-specification-template.md docs/operating_system/templates/detailed-specification-template.md docs/operating_system/prompt_templates/design-spec-prompt.md`
- Expected: every promotion owner describes the same conditional rule; no new frontmatter key or artifact type appears.

**Exit Criteria:**
- All five promotion owners agree on applicable prerequisites, in-place promotion, and ownership boundaries.

### Task 3: Add minimal frontend export and conflict rules

**Purpose:**
- Define safe adoption of generated design output without turning frontend rules into a provider-specific playbook.

**Task Function:**
- Add narrow design-system ownership and conflict-escalation invariants.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: policy edit needs no visual implementation judgment.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: frontend rule and lifecycle contract assertions provide focused proof.

**Specification Coverage:**
- Generated design exports are curated before adoption as project design-system sources.
- Conflicts with immutable approved UX are surfaced for reconciliation; neither frozen reference nor implementation is silently rewritten.
- Existing project design-system sources remain canonical.

**Required Skills:**
- `none`

**Files And Symbols:**
- Inspect: `docs/operating_system/rules/frontend-ui-rule.md`
- Modify: `docs/operating_system/rules/frontend-ui-rule.md`
- Verify: `tests/test_starter_lifecycle_contract.py`

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: add only two narrow rule statements.
- Stop for: OpenDesign command instructions, fixed `ui` or `combo-ui` routing, new design-system SSOT, or persistent export metadata.

**Steps:**
- [x] Add curation requirement before generated design output becomes project design-system source.
- [x] Add conflict-escalation rule for frozen UX, specification, design-system, and implementation mismatches.
- [x] Confirm existing frontend rule still delegates detailed playbooks to selected design skills.

**Verification:**
- [x] Inspect rule for existing design-system canonical ownership, conditional skill selection, and new curation or conflict language.
- Expected: rule adds boundaries only; no provider-specific workflow or fixed profile mapping appears.

**Exit Criteria:**
- Frontend rule protects SSOT and reconciliation without duplicating lifecycle or provider procedure.

### Task 4: Add focused lifecycle regression coverage

**Purpose:**
- Make the new lifecycle and promotion contract executable without brittle OpenDesign procedure snapshots.

**Task Function:**
- Update focused contract assertions for canonical ownership and conditional behavior.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small deterministic unit test update.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: repository validators and test suite provide independent evidence.

**Specification Coverage:**
- Dispatch owns Design Export lifecycle.
- Design Export and workstream reconciliation are conditional.
- Promotion may wait for explicitly applicable post-approval inputs.
- Integration tooling does not duplicate Delivery Lifecycle.
- Five promotion owners contain aligned guidance.

**Required Skills:**
- `none`

**Files And Symbols:**
- Inspect: `tests/test_starter_lifecycle_contract.py`
- Modify: `tests/test_starter_lifecycle_contract.py`
- Verify: all five promotion-owner files and `docs/operating_system/rules/frontend-ui-rule.md`

**Dependencies:**
- Tasks 1 through 3 complete.

**Authority:**
- Preauthorized local actions: modify focused assertions only.
- Stop for: tests that require exact OpenDesign procedure, fixed profile mapping, or undocumented runtime metadata.

**Steps:**
- [x] Extend lifecycle assertions for conditional Design Export and distinct promotion gating.
- [x] Add assertions that all five promotion owners contain aligned conditional language.
- [x] Add assertions for frontend export curation and conflict escalation.
- [x] Keep assertions semantic and short; do not snapshot provider-specific procedures.

**Verification:**
- [x] `py -3 -m pytest tests/test_starter_lifecycle_contract.py tests/test_validate_template_required_sections.py tests/test_validate_planning_lifecycle.py -q`
- Expected: focused lifecycle, template, and planning tests pass.

**Exit Criteria:**
- Tests fail if lifecycle ownership, conditionality, or promotion consistency regresses.

### Task 5: Regenerate and perform final repository proof

**Purpose:**
- Reconcile canonical changes with generated runtime surfaces and prove Starter Kit integrity.

**Task Function:**
- Run ordered generation, validation, drift, and scope checks.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance requires repository authority and generated-output inspection.

**Validator Profile (optional):**
- Controller-selected: `normal`
- Selection basis: independent validation of cross-file ownership, conditionality, generated alignment, and evidence completeness.

**Specification Coverage:**
- Canonical sources, generated adapters, Starter Kit output, tests, and repository contracts are aligned.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all plan target files, generated adapter diffs, Starter Kit output, and Git status.
- Modify: generated surfaces produced by sync or build commands only.
- Verify: `scripts/sync_agent_adapters.py`, `scripts/validate_repo_contracts.py`, `scripts/validate_repo_config.py`, `scripts/build_starter_kit.py`, `scripts/validate_starter_kit.py`

**Dependencies:**
- Task 4 complete.

**Authority:**
- Preauthorized local actions: run listed checks, regenerate derived outputs, inspect diffs, and remove only command-owned disposable output if required by the documented build procedure.
- Stop for: generated drift, failed validation, stale references, changed paths outside plan targets plus derived outputs, or pre-existing untracked artifacts that cannot be safely classified.

**Steps:**
- [x] Repeat `git status --short --untracked-files=all` and `git diff --name-only`; reclassify generator-owned destinations immediately before any generator runs.
- [x] Stop if a generator-owned destination is dirty and not explicitly approved and classified.
- [x] Run `py -3 scripts/sync_agent_adapters.py --all-platforms`.
- [x] Run `py -3 scripts/sync_agent_adapters.py --all-platforms --check`.
- [x] Run `py -3 scripts/validate_repo_contracts.py` and `py -3 scripts/validate_repo_config.py`.
- [x] Run `py -3 scripts/build_starter_kit.py` and `py -3 scripts/validate_starter_kit.py`.
- [x] Run focused lifecycle, template, planning, Starter Kit, and adapter-sync tests.
- [x] Search canonical and generated sources for stale immediate-promotion wording, fixed Design Export profile routing, new Engineering Contract alias, and duplicated lifecycle sections.
- [x] Run `git diff --check` and inspect final scope against this plan.

**Verification:**
- [x] Inspect generated adapter and Starter Kit diffs against canonical sources.
- [x] Inspect final Git scope against canonical targets, approved generated destinations, and classified pre-existing paths.
- Expected: all checks pass, generated outputs have no drift, no unapproved lifecycle artifact or metadata appears, and only declared canonical or derived files change.

**Exit Criteria:**
- Fresh verification proves lifecycle ownership, promotion consistency, frontend export boundaries, generated alignment, Starter Kit integrity, and clean diff scope.

## Verification

- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/validate_repo_contracts.py`
- `py -3 scripts/validate_repo_config.py`
- `py -3 scripts/build_starter_kit.py`
- `py -3 scripts/validate_starter_kit.py`
- `py -3 -m pytest tests/test_starter_lifecycle_contract.py tests/test_validate_template_required_sections.py tests/test_validate_planning_lifecycle.py tests/test_starter_kit_generation.py tests/test_sync_agent_adapters.py -q`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. `planning-dispatch.md` owns one conditional Design Export lifecycle gate.
2. Approval and promotion are distinct, with only applicable prerequisites able to delay promotion.
3. All five promotion owners use one consistent rule and preserve in-place draft promotion.
4. Frozen prototypes remain immutable UX reference evidence, not behavior or design-system SSOT.
5. Frontend rules require curation and conflict escalation without provider-specific procedure or fixed profile routing.
6. No new artifact type, frontmatter field, status, Engineering Contract alias, manifest entry, or Design Export skill is introduced; named providers remain explicit method choices only.
7. Focused tests, repository validation, generated sync, Starter Kit validation, and whitespace checks pass.
8. `skill-verification-before-completion` returns `verified` before any optional Git disposition.
