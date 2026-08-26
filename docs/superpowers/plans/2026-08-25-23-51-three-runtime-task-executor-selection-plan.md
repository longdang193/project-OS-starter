---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: three-runtime-task-executor-selection
targets:
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/templates/implementation-plan-template.md
  - .agents/skills/skill-writing-plans/SKILL.md
  - .agents/skills/skill-executing-plans/SKILL.md
  - .agents/skills/skill-deepagents-executing-plans/SKILL.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - README.md
  - tests/test_native_personal_local_workflow.py
  - tests/test_validate_template_required_sections.py
  - AGENTS.md
  - generated_agents/codex/AGENTS.md
  - generated_agents/claude/CLAUDE.md
  - generated_agents/antigravity/GEMINI.md
  - generated_agents/codex/skills/skill-writing-plans/SKILL.md
  - generated_agents/claude/skills/skill-writing-plans/SKILL.md
  - generated_agents/antigravity/skills/skill-writing-plans/SKILL.md
  - generated_agents/codex/skills/skill-executing-plans/SKILL.md
  - generated_agents/claude/skills/skill-executing-plans/SKILL.md
  - generated_agents/antigravity/skills/skill-executing-plans/SKILL.md
  - generated_agents/codex/skills/skill-deepagents-executing-plans/SKILL.md
  - generated_agents/claude/skills/skill-deepagents-executing-plans/SKILL.md
  - generated_agents/antigravity/skills/skill-deepagents-executing-plans/SKILL.md
---

# Three-Runtime Task Executor Selection Implementation Plan

## Goal

Align planning and execution guidance with existing three-runtime local
architecture: Native Codex, DeepAgents through `dcode-project`, and Tura through
`project-delegate`. Make executor selection task-level, advisory, and independent
from profile selection without adding an automatic router, classifier, runtime
fallback, or duplicate policy source.

Repair implementation-plan template corruption and replace tests that preserve
obsolete two-runtime wording with tests for actual executor contract.

## Decisions And Justified Findings

### Executor selection is not model routing

`docs/operating_system/planning/planning-dispatch.md` already owns planning-tier
and routing policy and remains small enough to own one additional executor
selection table. Add explicit `Artifact Selection` and `Executor Selection`
sections rather than creating `executor-routing.md`. Use term `selection` to
avoid conflating controller choice of task runtime with per-turn model routing.

### Task executor is authoritative at task level

Plan template currently exposes plan-level `Executor: codex | deepagents`
while coordination ledger already records executor for every task. Replace
plan-level field with optional default supporting `codex`, `deepagents`, and
`tura`. Task ledger value is authoritative for each Git-tracked task and
overrides default, allowing mixed executors without another orchestration
artifact.

Do not add a `Controller` field. `Coordination State` already records one lead
controller, and runtime-specific procedures determine which platform fulfills
that role.

### Executor and profile remain independent

Select executor from task authority, containment, topology, and expected
runtime benefit. Then select lowest `low`, `normal`, `high`, or `xhigh` profile
that can reliably complete that executor's bounded task contract. Do not create
permanent task-function, profile-rank, or complexity-label mappings to executor.

### Selection is advisory and evidence-based

Codex remains safe default when controller-owned capabilities are required or
no delegated runtime has clear expected advantage. Tura and DeepAgents are
eligible candidates, not deterministic classifications:

- Tura is eligible for one bounded worker task when runtime-managed batching,
  dependency execution, or compact execution state is likely to provide
  material benefit and current nonrecursive worker boundary is sufficient.
- DeepAgents is eligible for one bounded long-horizon or context-heavy task
  when adaptive investigation or isolated internal contexts are likely to
  provide material benefit.

Reserve prefer language for task-specific positive evidence. Add no automatic
controller classifier or executor fallback.

### DeepAgents internal decomposition may include bounded writes

Replace current `read-only decomposition` statement. Runtime-internal
decomposition never becomes plan-level coordination, but nested writers may be
allowed when bounded dispatch explicitly permits them. All nested work remains
inside active task workspace, dependencies, authority, and declared write
ownership; same-workspace writers remain sequential.

### Current source defects require regression proof

Current implementation-plan template contains literal `` `n `` text in
`Template Profile` guidance. Existing workflow tests also assert obsolete
phrases `Codex or DeepAgents` and `Executor: codex | deepagents`. Repair template
and replace prose-preservation checks with narrow semantic contract checks,
including one assertion scoped to plan template's literal `` `n `` defect.

## Implementation Outcomes

### One compact executor-selection policy

`planning-dispatch.md` separately owns artifact selection and task executor
selection. It defines three eligible executors, Codex default behavior,
task-specific benefit criteria, profile independence, and prohibition on fixed
mappings or automatic fallback without duplicating runtime mechanics.

### Mixed-executor plan contract

Implementation-plan template exposes `Default task executor: codex | deepagents
| tura`, defines task ledger executor as authoritative, fixes malformed
`Template Profile` line, and keeps coordination ownership separate from
executor selection.

### Aligned planning and execution guidance

Planning, execution, DeepAgents, personal-local, root, and README guidance use
same three-runtime contract. Detailed selection criteria remain in
`planning-dispatch.md`; root and README contain only concise summaries and links.
DeepAgents nested work uses explicit write permission instead of incorrect
read-only invariant.

### Semantic regression and generated alignment

Focused tests prove allowed executors, task-level override semantics, executor
and profile independence, Codex safe-default guidance, absence of obsolete
two-runtime contracts, and removal of malformed template text. Adapter sync
updates generated root and skill surfaces from canonical sources and leaves
runtime implementation unchanged.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Executor: `codex` (current template contract; Task 1 replaces this field for future plans)
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve existing unrelated working-tree changes
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit named repository files, run focused tests and validators, synchronize declared generated outputs, inspect Git diff and status
- User-approval actions: commit, push, merge, publication, deployment, destructive recovery, discard, cleanup, or user-local runtime modification
- Parallel ownership: `none`; tasks share policy and regression surfaces
- Sequential fallback: `Task 1, Task 2, Task 3`

## Coordination State

- Coordination owner: `single lead controller`
- Branch: `main`
- Base commit: `6e9b65ab0fb9167f0c8d79280e8467f5ff74720c`
- Active task(s): `none`
- Expected workspace: preserve modifications to `scripts/validate_template_required_sections.py` and `tests/test_validate_template_required_sections.py`, untracked `db/`, and two untracked Switchyard plans; add only this plan and later plan-approved changes
- Next action: `none`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | focused policy and plan-template tests | `11 passed`; template validator passed |
| Task 2 | `completed` | current | `codex` | Task 1 | focused workflow guidance tests | `82 passed` |
| Task 3 | `completed` | current | `codex` | Task 2 | drift checks, validators, focused suite, full suite | `176 passed`; sync, validators, stale-policy search, and diff check passed |

## Task Breakdown

### Task 1: Establish Executor Selection And Plan Contract

**Purpose:**
- Add one compact executor-selection SSOT and make mixed-executor plans explicit without adding runtime behavior.

**Task Function:**
- Update planning policy, plan metadata semantics, and regression contract.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: architecture ownership, mixed-executor semantics, backward-compatible plan behavior, and test contract design

**Validator Profile:**
- Controller-selected: `normal`
- Selection basis: bounded document-contract review and focused test verification

**Specification Coverage:**
- Separate executor selection from model routing terminology.
- Keep executor and profile selection independent.
- Make task ledger executor authoritative over plan default.
- Keep selection advisory and Codex as safe default.
- Avoid new controller field, classifier, router, or runtime fallback.
- Repair malformed plan-template text.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `docs/operating_system/planning/planning-dispatch.md` introduction and decision tables.
- Modify: `docs/operating_system/templates/implementation-plan-template.md` `Execution Approach`, `Coordination State`, task guidance, and malformed `Template Profile` text.
- Modify: `tests/test_native_personal_local_workflow.py:test_single_controller_resume_contract_is_documented` for unchanged lead-controller ownership.
- Add: `tests/test_native_personal_local_workflow.py:test_executor_selection_and_task_override_are_documented` for three executors, plan default, task override, profile independence, and malformed template regression.

**Dependencies:**
- Approved findings and exclusions in this plan.
- Current plan template and planning dispatch remain canonical owners.

**Authority:**
- Preauthorized local actions: edit named files, add narrow tests, run focused pytest and template validator.
- Stop for: need to change runtime code, planning schema, executor CLI behavior, or generic coordination ownership.

**Steps:**
1. Add failing semantic assertions for three allowed task executors, plan-default/task-override wording, executor/profile independence, and absence of literal `` `n `` in implementation-plan template.
2. Split `planning-dispatch.md` into explicit `Artifact Selection` and `Executor Selection` sections while preserving existing artifact choices.
3. Add smallest executor decision table: controller authority or unclear benefit selects Codex; bounded Tura and DeepAgents eligibility depends on task-specific expected benefit; fixed mappings and runtime fallback remain prohibited.
4. Replace plan-level `Executor` with optional `Default task executor: codex | deepagents | tura` and state each Git-tracked task ledger row is authoritative.
5. Do not add a `Controller` field; retain existing `Coordination owner` contract.
6. Repair malformed `Template Profile` line without changing unrelated task-template structure.
7. Run focused tests and inspect diff for policy duplication or accidental runtime requirements.

**Verification:**
- `py -3 -m pytest -q tests/test_native_personal_local_workflow.py`
- `py -3 scripts/validate_template_required_sections.py`
- Expected: focused tests and validator pass; narrow regression test proves plan template contains no literal `` `n `` text.

**Exit Criteria:**
- Planning policy owns one advisory executor-selection contract.
- Plan default supports all three executors and task rows remain authoritative.
- No controller field, classifier, router, fallback, or profile mapping is introduced.
- Malformed template text is removed and covered by narrow regression proof.

### Task 2: Align Skills And Personal-Local Guidance

**Purpose:**
- Apply executor contract consistently across canonical skills and maintained guidance while keeping detailed selection logic in one owner.

**Task Function:**
- Reconcile planning, execution, containment, and user-facing documentation.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: several canonical instruction layers, generated consumers, and DeepAgents nested-write ownership constraints

**Validator Profile:**
- Controller-selected: `normal`
- Selection basis: bounded cross-surface consistency review and stale-text search

**Specification Coverage:**
- Writing plans records default and task-level executors without fixed mappings.
- Executing plans dispatches active task using authoritative executor and retains lead acceptance.
- DeepAgents internal decomposition may write only with explicit dispatch permission.
- Personal-local guidance recognizes Codex, DeepAgents, and Tura.
- Root and README stay concise and reference planning owner.
- Runtime-adapter procedure remains excluded; stop and amend this plan before editing it if a contradictory active selection-policy statement is discovered.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `.agents/skills/skill-writing-plans/SKILL.md` `Conditional References`, `Choose Execution Approach`, and task-contract guidance.
- Modify: `.agents/skills/skill-executing-plans/SKILL.md` `Conditional References`, execution-state reconciliation, and active-task dispatch.
- Modify: `.agents/skills/skill-deepagents-executing-plans/SKILL.md` `Dispatch Contract` and `Execution Topology`.
- Modify: `docs/operating_system/procedures/personal-local-worktree-procedure.md` opening executor contract and bounded executor guidance.
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md` `Native Personal-Local Work` with concise independence/default/reference wording.
- Modify: `README.md` native personal-local summary.
- Rename: `tests/test_native_personal_local_workflow.py:test_native_personal_local_workflow_is_documented` to `test_three_runtime_personal_local_workflow_is_documented` and update its semantic assertions.
- Add: `tests/test_native_personal_local_workflow.py:test_deepagents_internal_writers_remain_task_bounded` for explicit nested-write permission and one-task ownership.

**Dependencies:**
- Task 1 executor-selection and plan-template contract complete.

**Authority:**
- Preauthorized local actions: edit named canonical guidance and tests; search canonical and generated text for stale phrases.
- Stop for: need for Tura-specific execution skill, changes to `scripts/dcode_project.py`, setup wrappers, role TOML, Switchyard files, or `runtime-adapter-procedure.md` beyond discovered stale selection claim.

**Steps:**
1. Add or update failing tests for three-runtime recognition, planning-dispatch reference, executor/profile independence, Codex safe default, task-ledger authority, and explicit DeepAgents nested-write permission.
2. Update `skill-writing-plans` to read executor selection from `planning-dispatch.md`, record plan default only when useful, and require each Git-tracked task to name executor.
3. Update `skill-executing-plans` to reconcile active task ledger executor before dispatch; retain controller-owned MCP, Git acceptance, verification, and plan-state updates under personal-local execution.
4. Replace DeepAgents `read-only decomposition` wording with bounded internal decomposition and explicit nested-writer permission. Preserve same-workspace sequential writing and one plan-task ownership.
5. Replace stale `Codex or DeepAgents` wording in personal-local procedure with three supported execution paths while preserving distinct launcher and containment mechanics.
6. Add only short executor/profile independence statement and planning-dispatch reference to root template; do not copy decision matrix.
7. Update README summary with three execution paths and no new mechanics.
8. Search affected canonical surfaces for stale two-runtime and deterministic mapping language; remove only matches superseded by this contract.
9. Run focused workflow tests and inspect diff for duplicated criteria.

**Verification:**
- `py -3 -m pytest -q tests/test_native_personal_local_workflow.py tests/test_dcode_project.py`
- `rg -n 'Codex or DeepAgents|Executor: `codex \| deepagents`|runtime-internal read-only decomposition|low.*Tura|high.*Codex' README.md docs/operating_system .agents/skills tests/test_native_personal_local_workflow.py -g '*.md' -g '*.py'`
- Expected: focused tests pass; search returns only historical plans or deliberately quoted negative assertions, not active canonical guidance.

**Exit Criteria:**
- Canonical guidance recognizes all three task executors without duplicating selection table.
- Executor and profile independence is consistent across planning and execution skills.
- DeepAgents nested writes require explicit permission and remain inside one active task contract.
- Runtime code, setup, roles, Switchyard, and planning schema remain unchanged.

### Task 3: Regenerate Surfaces And Prove Repository Alignment

**Purpose:**
- Generate deterministic consumers and provide fresh evidence that policy, tests, validators, and runtime boundaries remain aligned.

**Task Function:**
- Synchronize generated agent surfaces and run final repository verification.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: deterministic generation, focused validation, stale-policy search, and diff reconciliation

**Validator Profile:**
- Controller-selected: `high`
- Selection basis: final cross-surface acceptance, preservation of unrelated workspace changes, and full-suite review

**Specification Coverage:**
- Generated root and skill copies derive only from canonical sources.
- Active canonical guidance contains no obsolete two-runtime contract.
- Runtime adapter and launcher behavior remain unchanged.
- Existing unrelated workspace changes remain preserved.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Generate: `AGENTS.md` from `docs/operating_system/templates/agents/root-AGENTS.template.md`.
- Generate: `generated_agents/codex/AGENTS.md`, `generated_agents/claude/CLAUDE.md`, and `generated_agents/antigravity/GEMINI.md`.
- Generate: `generated_agents/{codex,claude,antigravity}/skills/skill-writing-plans/SKILL.md`.
- Generate: `generated_agents/{codex,claude,antigravity}/skills/skill-executing-plans/SKILL.md`.
- Generate: `generated_agents/{codex,claude,antigravity}/skills/skill-deepagents-executing-plans/SKILL.md`.
- Verify: all canonical, generated, test, and preserved unrelated paths named in this plan.

**Dependencies:**
- Tasks 1 and 2 complete with focused tests passing.

**Authority:**
- Preauthorized local actions: run adapter sync, drift check, validators, focused tests, full pytest suite, repository searches, and Git diff/status inspection.
- Stop for: generated changes outside named deterministic consumers, modification of preserved unrelated files, runtime code changes, or failures requiring unrelated source edits.

**Steps:**
1. Record pre-generation Git status and preserved unrelated paths.
2. Run `py -3 scripts/sync_agent_adapters.py --all-platforms`.
3. Inspect generated diff and confirm every output derives from named canonical root or skill source.
4. Run adapter drift, generated-header, metadata, and template validators.
5. Run focused workflow, sync, generated-header, and launcher tests.
6. Search canonical and generated active guidance for obsolete two-runtime wording, deterministic executor mappings, malformed template text, and old read-only decomposition claim.
7. Run full pytest suite.
8. Inspect final Git status and diff; confirm preserved unrelated changes are unmodified by this plan and no excluded file changed.
9. Reconcile task ledger, verification evidence, deviations, and residual risks before any completion claim.

**Verification:**
- `py -3 scripts/sync_agent_adapters.py --check --all-platforms`
- `py -3 scripts/validate_generated_header_format.py`
- `py -3 scripts/validate_agent_metadata_schema.py`
- `py -3 scripts/validate_template_required_sections.py`
- `py -3 -m pytest -q tests/test_native_personal_local_workflow.py tests/test_dcode_project.py tests/test_sync_agent_adapters.py tests/test_validate_generated_header_format.py tests/test_validate_template_required_sections.py`
- `py -3 -m pytest -q`
- `git diff --check`
- Expected: all commands pass; generated drift is zero; final diff contains only plan-approved canonical, test, plan, and deterministic generated changes plus preserved pre-existing unrelated changes.

**Exit Criteria:**
- Canonical and generated surfaces are synchronized with no drift.
- Focused and full tests pass, or unrelated pre-existing failures are recorded without unrelated fixes.
- No excluded runtime, role, Switchyard, planning-schema, or user-local file changed.
- Plan plus Git provide enough evidence for fresh controller to verify scope and completion.

## Verification

- [x] Plan status changed to `active` before Task 1 began.
- [x] Task 1 focused executor-policy and plan-template tests pass: `11 passed`.
- [x] Task 2 focused workflow and launcher-boundary tests pass: `82 passed`.
- [x] `py -3 scripts/sync_agent_adapters.py --check --all-platforms`
- [x] `py -3 scripts/validate_generated_header_format.py`
- [x] `py -3 scripts/validate_agent_metadata_schema.py`
- [x] `py -3 scripts/validate_template_required_sections.py`
- [x] Focused executor-selection, launcher, sync, header, and template tests pass: `117 passed`.
- [x] Active canonical and generated guidance contains no stale two-runtime contract, malformed template text, deterministic executor mapping, or read-only DeepAgents decomposition claim.
- [x] `py -3 -m pytest -q`: `176 passed`.
- [x] `git diff --check`
- [x] Final Git status preserves named unrelated working-tree changes and contains no excluded-file modifications.

## Completion Criteria

1. `planning-dispatch.md` separately owns artifact selection and advisory task executor selection.
2. Native Codex, DeepAgents, and Tura are documented task executors for personal-local work.
3. Codex remains safe default when controller capabilities are required or delegated benefit is unclear.
4. Executor selection and profile selection are independent, with no fixed mapping or automatic classifier.
5. Plan-level executor metadata is optional default; each Git-tracked task ledger executor is authoritative.
6. No redundant `Controller` field is added to implementation-plan template.
7. DeepAgents internal decomposition may include writers only when explicitly permitted within active task contract.
8. Implementation-plan template contains no literal `` `n `` corruption.
9. Regression tests enforce semantic executor contracts rather than obsolete prose substrings.
10. Root and README guidance remain concise and point to canonical planning owner instead of duplicating selection matrix.
11. Generated root and skill surfaces match canonical sources and pass drift checks.
12. Runtime code, setup wrappers, role TOML, Switchyard work, planning schema, and user-local configuration remain unchanged.
13. Fresh focused validators and full pytest output support final verification.

## Exclusions

- No automatic executor router or fuzzy classifier.
- No runtime fallback between Tura and DeepAgents.
- No changes to `scripts/dcode_project.py` or `scripts/setup_deepagents_runtime.ps1`.
- No changes to `agents/*.toml` or `repo_config/planning_artifact_schema.yaml`.
- No Tura-specific execution skill.
- No use of Tura as native subagent or parallel-agent backend.
- No Switchyard implementation or configuration changes.
- No user-local runtime deployment.

## Deviations And Residual Risks

- Current working tree contains unrelated tracked and untracked changes. Every
  execution task must reconcile and preserve them before edits and final
  acceptance.
- Existing historical plans may retain old executor wording as historical
  evidence. Stale-text checks must distinguish active canonical guidance from
  immutable history and negative regression assertions.
- Repository-wide `--require-template-selection` currently reports unrelated
  historical plan `docs/superpowers/plans/2026-07-18-mcp-memory-ui-ux-integration.md`.
  This plan uses ordinary required-section validation and does not widen scope
  to repair historical frontmatter.
- `runtime-adapter-procedure.md` is intentionally excluded. Add it only if
  implementation finds active executor-selection claim contradicting canonical
  policy; record that deviation before editing.
