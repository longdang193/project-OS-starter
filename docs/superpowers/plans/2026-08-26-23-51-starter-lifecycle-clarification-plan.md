---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: starter-lifecycle-clarification
targets:
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/tooling/frontend-backend-integration-tools.md
  - docs/operating_system/templates/draft-specification-template.md
  - docs/operating_system/templates/detailed-specification-template.md
  - .agents/skills/skill-spec-drafting/SKILL.md
  - .agents/skills/skill-writing-plans/SKILL.md
  - .agents/skills/skill-full-stack-integration/SKILL.md
  - .agents/skills/skill-requesting-code-review/SKILL.md
  - .agents/skills/skill-requesting-code-review/code-reviewer.md
  - .agents/skills/skill-verification-before-completion/SKILL.md
  - .agents/skills/skill-subagent-driven-development/implementer-prompt.md
  - .agents/skills/skill-subagent-driven-development/task-reviewer-prompt.md
  - .agents/skills/skill-brainstorming/spec-document-reviewer-prompt.md
  - tests/test_starter_lifecycle_contract.py
  - generated_agents
  - generated_exports/project-OS-starter-kit
---

# Starter Lifecycle Clarification Plan

## Execution Evidence

- Reconciliation state: verified at base `HEAD` `01ff90918e0c93c5bfe51ad0bc67ca14c57d2d75` plus current working-tree patch; committed-content equivalence is not claimed.
- Previous completion record was reopened because active prompt and evidence contracts had drifted after `01ff909`.
- Co-executed scope: runtime-resolution plan owns `repo_config/starter-kit-manifest.json`; lifecycle verification must not reject that authorized change as unrelated.
- Fresh proof: repository validators passed; adapter sync check passed; Starter Kit build and validation passed; focused lifecycle/runtime suites passed (`85 passed` across the final validation set); `git diff --check` passed.

## Goal

Make Starter delivery lifecycle explicit without creating new permanent artifacts, duplicating contracts, or turning optional workflow gates into mandatory phases.

## Implementation Outcomes

### Conditional lifecycle has one policy owner

`docs/operating_system/planning/planning-dispatch.md` owns the conditional delivery lifecycle and stage handoffs. `frontend-backend-integration-tools.md` remains limited to cross-boundary routing and evidence responsibilities.

### Specifications expose boundary ownership

Draft specifications record prototype-derived system and contract obligations. Detailed specifications record applicable frontend, backend, and shared-contract responsibilities without prescribing production component trees.

### Skills route the same lifecycle

Specification drafting, plan writing, full-stack integration, code review, and completion verification use consistent approval, repository-reconciliation, contract, and evidence terminology. Code review uses only supported controller-selected profiles.

### Generated and shipped surfaces remain aligned

Canonical docs and skills regenerate provider projections, pass repository contract checks, rebuild the consume-only Starter Kit, and pass focused regression tests. No new lifecycle artifact type is introduced; authorized manifest changes belong to the runtime-resolution plan.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Default task executor: `codex`
- Required skills: `skill-writing-skills`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed canonical docs and skills; run listed local validators, tests, sync, and Starter Kit rebuild commands; inspect generated diffs
- User-approval actions: commit, push, merge, publication, external writes, destructive cleanup, or changes outside listed targets
- Parallel ownership: none; canonical and generated surfaces require ordered updates
- Sequential fallback: execute Tasks 1 through 5 in order
- Pre-execution gate: `skill-plan-document-reviewer` must return `implementation-ready` for lifecycle ownership, optionality, evidence separation, generated boundaries, and task scope before Task 1 starts.

## Dependency Boundary

This plan clarifies lifecycle ownership only. A separate runtime tool-resolution plan owns capability requirements, evidence requirements, and runtime resolution; this plan must not partially implement that work.

## Task Breakdown

### Task 1: Establish conditional lifecycle ownership

**Purpose:**
- Define one lifecycle policy owner while preserving existing optional artifact selection and cross-boundary routing.

**Task Function:**
- Edit operating-system governance documentation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: low implementation risk; exact document ownership is already established.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final repository contract and documentation checks cover this change.

**Specification Coverage:**
- Approved review correction: use conditional lifecycle gates, avoid new lifecycle artifacts, keep integration routing scoped to frontend/backend work.

**Required Skills:**
- `none`

**Files And Symbols:**
- Inspect: `docs/operating_system/planning/planning-dispatch.md` sections `Artifact Selection` and `Artifact Ownership`
- Inspect: `docs/operating_system/tooling/frontend-backend-integration-tools.md` sections `Artifact Ownership` and `Routing Matrix`
- Inspect: `docs/operating_system/governance/repo-governance.md` section `Planning Ownership`
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `docs/operating_system/tooling/frontend-backend-integration-tools.md`
- Verify: the two modified documents and `docs/operating_system/governance/repo-governance.md`

**Dependencies:**
- Fresh `git status --short` and `git rev-parse HEAD` captured before execution; unrelated user changes remain untouched.

**Authority:**
- Preauthorized local actions: add one conditional `Delivery Lifecycle` section to planning dispatch; add one lifecycle ownership handoff note to integration tooling; preserve existing artifact owners and routing rows.
- Stop for: any proposal requiring a new lifecycle artifact, mandatory prototype for backend-only work, mandatory E2E for non-cross-boundary work, generic release/observability ownership, or runtime provider-routing changes.

**Steps:**
- [x] Add `Delivery Lifecycle` to `planning-dispatch.md` as conditional gates: Discovery/Research when uncertainty exists; Prototype/Iterate when UX or behavior needs validation; Design Review and UX/Behavior Approval when material design judgment is required; Detailed Specification when durable behavior or contracts need definition; Repository Reconciliation; Implementation Plan when work is multi-step; Implementation; Integration when boundaries are crossed; applicable verification; independent review when required; project-owned Release/Deploy and Observe.
- [x] State skip rules beside the gates: design-clear reversible work may go directly to execution; each discovery, prototype, design-review, specification, reconciliation, planning, integration, verification, and review gate is used only when its trigger applies; material backend behavior requires direct backend proof; E2E applies only to cross-boundary journeys.
- [x] Add one handoff note to `frontend-backend-integration-tools.md` pointing lifecycle ownership to planning dispatch and retaining only frontend/backend/shared-contract integration responsibilities; defer runtime capability resolution to the separate runtime plan.
- [x] Keep `Release/Deploy` and `Observe` explicitly optional and project-owned; do not add generic release or telemetry skills.

**Verification:**
- [x] `rg -n "Delivery Lifecycle|project-owned|prototype|draft specification|repository reconciliation|End-to-End|Release/Deploy|Observe" docs/operating_system/planning/planning-dispatch.md docs/operating_system/tooling/frontend-backend-integration-tools.md`
- Expected: one full conditional lifecycle definition exists in planning dispatch; integration tooling points to that owner without duplicating lifecycle policy or changing runtime provider routing.

**Exit Criteria:**
- Lifecycle ownership, optionality, and frontend/backend integration boundaries are unambiguous without adding an artifact or registry.

### Task 2: Add applicable boundary guidance to specification templates

**Purpose:**
- Capture system and contract implications discovered during prototyping without creating duplicate specification fields.

**Task Function:**
- Edit specification templates without changing their required frontmatter contract.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded template edits; no unresolved product behavior.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing template validator plus focused tests cover required sections and frontmatter.

**Specification Coverage:**
- Approved review correction: strengthen existing draft-to-detailed specification lifecycle; do not create duplicate boundary fields, an Engineering Contract, or prescribed implementation structure.

**Required Skills:**
- `none`

**Files And Symbols:**
- Inspect: `docs/operating_system/templates/draft-specification-template.md` section `Prototype and Validation Findings`
- Inspect: `docs/operating_system/templates/detailed-specification-template.md` sections `Requirements and Behavioral Contract` and `Validation Plan`
- Modify: `docs/operating_system/templates/draft-specification-template.md`
- Modify: `docs/operating_system/templates/detailed-specification-template.md`
- Verify: `tests/test_validate_template_required_sections.py`

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: add optional template guidance and applicability notes; preserve existing required section names, frontmatter, in-place promotion, and backend verification claims.
- Stop for: adding a new template ID, changing `target_globs`, making boundary sections universally mandatory, or adding production file/component names.

**Steps:**
- [x] Add one guidance sentence under draft `Prototype and Validation Findings`: record any capability, data/state, contract, feasibility, or failure-behavior implication exposed by prototype validation.
- [x] Add an optional `Boundary Ownership` table inside detailed `Requirements and Behavioral Contract` with columns `Boundary`, `Owner or canonical contract`, and `Required evidence`; include only material frontend, backend, or shared-contract rows.
- [x] State that prototype references remain evidence and implementation mechanisms remain repository or plan decisions; do not require irrelevant boundary classes or bureaucratic `Not applicable` entries.
- [x] Keep exact files, component decomposition, sequencing, commands, rollout steps, and implementation mechanisms in plans or source rather than specifications.

**Verification:**
- [x] `py -3 -m pytest tests/test_validate_template_required_sections.py -q`
- Expected: existing template and fixture validation passes with no new required section failure.

**Exit Criteria:**
- Draft and detailed templates expose boundary obligations while retaining current promotion and validation contracts.

### Task 3: Align skill routing and evidence language

**Purpose:**
- Make reusable skills apply the same conditional lifecycle without duplicating the full lifecycle policy.

**Task Function:**
- Edit canonical skill instructions and correct invalid reviewer routing.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded prose and routing edits across known skill owners; no code behavior change.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository contract validation and generated adapter drift checks provide direct proof.

**Specification Coverage:**
- Approved review corrections: repository reconciliation wording, prototype reference boundary, independent-review inputs, explicit frontend/backend/E2E evidence classes, and supported reviewer profiles.

**Required Skills:**
- `skill-writing-skills`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-spec-drafting/SKILL.md` section `Draft To Final Lifecycle`
- Inspect: `.agents/skills/skill-writing-plans/SKILL.md` sections `Planning Process` and `Right-Size Tasks`
- Inspect: `.agents/skills/skill-full-stack-integration/SKILL.md` sections `Core Method` and `Common Mistakes`
- Inspect: `.agents/skills/skill-requesting-code-review/SKILL.md` sections `How to Request` and `Integration`
- Inspect: `.agents/skills/skill-requesting-code-review/code-reviewer.md` section `Code Reviewer Prompt Template`
- Inspect: `.agents/skills/skill-verification-before-completion/SKILL.md` sections `Map Claims To Evidence` and `Run Required Broad Proof`
- Modify: `.agents/skills/skill-spec-drafting/SKILL.md`
- Modify: `.agents/skills/skill-writing-plans/SKILL.md`
- Modify: `.agents/skills/skill-full-stack-integration/SKILL.md`
- Modify: `.agents/skills/skill-requesting-code-review/SKILL.md`
- Modify: `.agents/skills/skill-requesting-code-review/code-reviewer.md`
- Modify: `.agents/skills/skill-verification-before-completion/SKILL.md`
- Modify: `tests/test_starter_lifecycle_contract.py`
- Verify: generated skill projections after Task 4

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: update routing prose, section names, evidence inputs, and profile wording in listed canonical skills.
- Stop for: changing skill IDs, adding a second lifecycle registry, changing executor policy, or replacing direct backend proof with browser evidence.

**Steps:**
- [x] In `skill-spec-drafting`, describe approval as the handoff from unsettled draft behavior to active detailed specification; retain in-place promotion and no parallel permanent draft.
- [x] In `skill-writing-plans`, rename the repository step to `Reconcile Approved Scope With Repository Truth` and add frontend, backend, and shared mapping requirements only for cross-boundary tasks.
- [x] In `skill-full-stack-integration`, state that prototypes and generated HTML are reference evidence for behavior and states, not production architecture or canonical contracts.
- [x] In `skill-requesting-code-review` and `code-reviewer.md`, replace `general-purpose` with controller-selected `low`, `normal`, `high`, or `xhigh`; require review context to include approved scope/specification, prototype reference when material, plan, diff, and each applicable frontend, backend, and E2E evidence class plus approved deviations.
- [x] In `skill-verification-before-completion`, add applicability-based claim language for frontend verification and E2E verification while retaining direct backend proof as a separate requirement.
- [x] State that independent review cannot replace fresh executable verification and that E2E evidence cannot replace direct backend evidence.
- [x] Add `tests/test_starter_lifecycle_contract.py` with stable assertions for one lifecycle owner, conditional discovery/prototype gates, conditional E2E, supported reviewer profiles, and separate backend/browser evidence.

**Verification:**
- [x] `py -3 -m pytest tests/test_starter_lifecycle_contract.py -q`
- Expected: no `general-purpose` reviewer routing remains in the reviewer skill or prompt; required evidence distinctions, reconciliation wording, and lifecycle ownership assertions pass.

**Exit Criteria:**
- Canonical skills route lifecycle handoffs consistently and use only supported reviewer profile names.

### Task 4: Regenerate adapters and rebuild Starter Kit

**Purpose:**
- Propagate canonical changes into generated provider surfaces and consume-only Starter Kit output.

**Task Function:**
- Run canonical synchronization and generated-output validation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic repository generation commands; no delegated reasoning needed.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: sync, repository contract, and Starter Kit validators are authoritative for generated surfaces.

**Specification Coverage:**
- Generated surfaces match canonical sources; factory-only maintenance remains outside consume-only output.

**Required Skills:**
- `none`

**Files And Symbols:**
- Inspect: `scripts/sync_agent_adapters.py`
- Inspect: `repo_config/starter-kit-manifest.json`
- Generate: `generated_agents/`
- Generate: `generated_exports/project-OS-starter-kit/`
- Verify: `scripts/validate_repo_config.py`, `scripts/validate_repo_contracts.py`, `scripts/validate_starter_kit.py`

**Dependencies:**
- Task 3 complete.

**Authority:**
- Preauthorized local actions: run sync, drift check, repository config validation, Starter Kit build, and Starter Kit validation.
- Stop for: generated output requiring manual edits, manifest changes, forbidden paths copied into Starter Kit, or source-only references appearing in shipped content.

**Steps:**
- [x] Run `py -3 scripts/sync_agent_adapters.py --all-platforms`.
- [x] Run `py -3 scripts/sync_agent_adapters.py --all-platforms --check` and confirm zero drift.
- [x] Run `py -3 scripts/validate_repo_config.py`.
- [x] Run `py -3 scripts/build_starter_kit.py`.
- [x] Run `py -3 scripts/validate_starter_kit.py`.
- [x] Inspect generated diff and confirm generated files changed only because canonical sources changed.

**Verification:**
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `py -3 scripts/validate_repo_config.py`
- [x] `py -3 scripts/validate_starter_kit.py`
- Expected: all commands exit successfully; generated adapter and Starter Kit drift checks pass.

**Exit Criteria:**
- Generated provider surfaces and Starter Kit output reflect canonical changes without hand-maintained duplicates or factory tooling leakage.

### Task 5: Run final contract, test, and scope verification

**Purpose:**
- Prove documentation, skill routing, generated outputs, and Starter Kit boundaries remain aligned at one fresh repository state.

**Task Function:**
- Perform final evidence collection and repository reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance requires lead-controller judgment over scope, generated state, and fresh command output.

**Validator Profile:**
- Controller-selected: `normal`
- Selection basis: independent policy review should challenge cross-file ownership, lifecycle-routing, optionality, and evidence consistency after deterministic checks and generated diff inspection.

**Specification Coverage:**
- All implementation outcomes in this plan; no unresolved required work, stale generated output, or unrecorded scope deviation.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all plan target files
- Inspect: `git status --short`, `git diff --check`, and full working-tree diff
- Verify: `tests/test_starter_lifecycle_contract.py`, `tests/test_validate_template_required_sections.py`, `tests/test_starter_kit_generation.py`, `tests/test_validate_repo_contracts.py`, `tests/test_sync_agent_adapters.py`

**Dependencies:**
- Tasks 1 through 4 complete.

**Authority:**
- Preauthorized local actions: run focused tests, repository validators, drift checks, `git diff --check`, and inspect final scope.
- Stop for: failed required proof, generated drift, changed files outside approved targets, stale lifecycle terms, or unresolved ownership conflict.

**Steps:**
- [x] Run `py -3 scripts/validate_repo_contracts.py`.
- [x] Run `py -3 -m pytest tests/test_starter_lifecycle_contract.py tests/test_validate_template_required_sections.py tests/test_starter_kit_generation.py tests/test_validate_repo_contracts.py tests/test_sync_agent_adapters.py -q`.
- [x] Run `git diff --check`.
- [x] Inspect `git status --short` and the complete diff; confirm no new lifecycle artifact, manifest change, generated-output hand edit, or unrelated file exists.
- [x] Search for stale reviewer routing and rejected lifecycle terms with `rg -n "general-purpose|Engineering Contract|UX Contract|Repo Reconciliation Document|mandatory.*E2E|Independent Audit" docs .agents generated_agents -g '*.md' -g '*.yaml' -g '*.yml'` and classify any remaining match as historical evidence or required cleanup.
- [x] Record final result as `verified`, `incomplete`, or `blocked` using fresh command output; do not mark this plan completed from checkboxes alone.
- [x] If final review causes any canonical edit, return to its affected task, rerun Task 4 generation and validation, then rerun the complete Task 5 proof set.

**Verification:**
- [x] `py -3 scripts/validate_repo_contracts.py`
- [x] `py -3 -m pytest tests/test_starter_lifecycle_contract.py tests/test_validate_template_required_sections.py tests/test_starter_kit_generation.py tests/test_validate_repo_contracts.py tests/test_sync_agent_adapters.py -q`
- [x] `git diff --check`
- Expected: repository contract validation, focused tests, generated checks, and whitespace validation pass; final diff contains only approved canonical and generated outputs.

**Exit Criteria:**
- Fresh evidence proves lifecycle ownership, template boundaries, skill routing, generated projections, and Starter Kit output are aligned; plan is `completed`.

## Verification

- `py -3 scripts/validate_repo_contracts.py`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/validate_repo_config.py`
- `py -3 scripts/build_starter_kit.py`
- `py -3 scripts/validate_starter_kit.py`
- `py -3 -m pytest tests/test_starter_lifecycle_contract.py tests/test_validate_template_required_sections.py tests/test_starter_kit_generation.py tests/test_validate_repo_contracts.py tests/test_sync_agent_adapters.py -q`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. `planning-dispatch.md` owns one conditional lifecycle definition and integration tools does not duplicate it.
2. Draft and detailed specification templates expose applicable system and boundary responsibilities without new artifact types or required frontmatter changes.
3. Canonical skills use consistent approval, reconciliation, integration, reviewer-profile, and evidence terminology.
4. Lifecycle semantics have focused regression coverage; runtime tool resolution remains covered by its separate plan.
5. Generated adapters synchronize without drift and the consume-only Starter Kit builds and validates successfully.
6. Focused tests, repository contract validation, Starter Kit validation, and `git diff --check` pass at the final inspected state.
7. No required work, failed check, stale status, or unrecorded scope deviation remains.
8. Final verification performed under `skill-verification-before-completion` is recorded as `verified` before any optional handoff to `skill-finishing-a-development-branch`.
