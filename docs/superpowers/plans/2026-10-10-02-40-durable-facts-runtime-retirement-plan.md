---
layer: change
artifact_type: plan
status: active
template_id: implementation-plan
contract_version: "1"
name: durable-facts-runtime-retirement
targets:
  - scripts/project_os_runtime/reconciliation.py
  - scripts/project_os_runtime/acceptance.py
  - scripts/project_os_runtime/results.py
  - scripts/project_os_runtime/attempt.py
  - scripts/project_os_runtime/secretary_evidence.py
  - scripts/project_os_runtime/secretary_events.py
  - scripts/project_os_runtime/secretary_adapter.py
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/dcode_project.py
  - scripts/manage_switchyard_runtime.py
  - repo_config/planning_artifact_schema.yaml
  - .github/workflows/repo-contracts.yml
  - .github/workflows/runtime-contracts.yml
  - docs/operating_system/
  - .agents/skills/
  - generated_agents/
  - tests/
---

# Durable Facts, Runtime Retirement, Canonical Retention

## Goal

Make one authority own each lifecycle fact and make every receiver revalidate
mutable evidence before acting:

> Source owners publish facts. Receivers revalidate facts. Controllers make
> decisions. Runtime owners retire resources. Consumers authorize evidence
> disposal. Git and GitHub preserve durable consequence.

Retire active Tura and Switchyard paths, retain Codex and DeepAgents, make
dispatch independent from unavailable remote evidence, separate eligibility
from completed state, prevent Worker self-acceptance from authorizing deletion,
and preserve historical completed Plans without preserving retired active
runtime paths.

This plan responds to the verdict requesting changes to PR #68. It is a plan,
not approval to modify code or external GitHub state.

## Implementation Outcomes

### Phase-specific reconciliation

`project_os_runtime.reconciliation` exposes one pure read-only reconciler with
separate dispatch, verify, accept, integrate, retire, and prune contracts.
GitHub evidence is controller-supplied and ephemeral. Missing `attempt_id`,
unavailable GitHub, and `checkpoint_sha != lane_head_sha` do not create false
dispatch contradictions.

### Authority-correct acceptance and retention

Worker `TaskResult` and receipts remain evidence. CoS acceptance plus a
canonical Plan/Git checkpoint authorizes bounded evidence release. A Worker
cannot authorize deletion by writing `accepted=True`.

### Resource-specific retirement

Herdr and runtime owners retire worker, descendants, pane, session, worktree,
and MCP resources from one launcher-owned immutable binding. Retirement shares
pane/role-view locks with dispatch, reports uncertain cleanup as unresolved,
and remains idempotent without treating an absent pane as proof of dead
processes.

### Canonical-only durable state

Plan, Git, GitHub, and CoS decisions remain durable owners. Secretary remains a
derived attention consumer. Dead age-based MCP cleanup and raw benchmark rows
are removed. Historical Tura Plans remain readable; new active Tura and
Switchyard routing are rejected.

### Direct regression and CI proof

Focused tests cover authority, freshness, race, outage, idempotency, cleanup,
replay, retention, and recovery gates. Existing conservative GitHub Actions
concurrency remains. New contract tests run in current repository workflows.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-backend-verification`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `fresh dedicated worktree from origin/main 187f28e492ae1c4726cdd2f7b5a261a2b8b6c695`; drafting workspace remains untouched
- Commit policy: `implementation commits only after task-local proof; lead checkpoint updates plan ledger in same commit; no commit while plan status is proposed`
- Preauthorized local actions: `edit listed repository files, add focused tests, remove only listed Project OS-owned active runtime surfaces, regenerate generated outputs through repository scripts, and run listed local checks`
- User-approval actions: `change plan status to active, push, create or update PR, merge, delete external runtime resources, delete unrelated workspace files, discard evidence, and delete worktrees`
- Parallel ownership: `none; reconciliation, acceptance, runtime retirement, and generated surfaces share contracts and execute sequentially`
- Sequential fallback: `Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7 → Task 8`
- Bootstrap: `after explicit approval, create the dedicated worktree from the recorded base, copy this approved plan to the same repository-relative path there, preserve the drafting copy unchanged, resolve Executor and Template Profile before activation, record the exact execution worktree path in Expected workspace and every task-ledger Workspace cell, change plan status proposed → active, then commit the initial coordination checkpoint before activating Task 1`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/durable-facts-runtime-retirement`
- Base commit: `187f28e492ae1c4726cdd2f7b5a261a2b8b6c695` (`origin/main`, verified 2026-10-10)
- Expected workspace: `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\durable-facts-runtime-retirement\project-OS-starter` on branch `codex/durable-facts-runtime-retirement`, created from `187f28e492ae1c4726cdd2f7b5a261a2b8b6c695`; drafting workspace and its untracked files remain untouched
- Next action: `Task 6 — remove active Tura/Switchyard surfaces and preserve history`
- Blockers: `Task 6 remains active: Switchyard surfaces and generated Tura guidance are not fully retired`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\durable-facts-runtime-retirement\project-OS-starter` | `codex` | none | inventory, baseline validators, preserved-untracked proof | `origin/main=187f28e492ae1c4726cdd2f7b5a261a2b8b6c695; validate_repo_contracts=0; validate_planning_lifecycle=0; focused tests=119 passed; unrelated drafting workspace preserved` |
| Task 2 | `completed` | `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\durable-facts-runtime-retirement\project-OS-starter` | `codex` | Task 1 | phase contract and reconciliation tests | `reconciliation/dispatch/acceptance/attempt tests=192 passed; integration identity fail-closed; incomplete phases do not advance; git diff --check=0` |
| Task 3 | `completed` | `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\durable-facts-runtime-retirement\project-OS-starter` | `codex` | Task 2 | GitHub identity/freshness and acceptance-release tests | `remote identity/source/review binding; CoS release and consumer retention tests; receipt/task-result retention changes; focused tests=377 passed` |
| Task 4 | `completed` | `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\durable-facts-runtime-retirement\project-OS-starter` | `codex` | Task 2 | launcher binding, lock race, resource retirement tests | `pane retirement requires immutable session/pane/agent/process binding and shared lock; absent pane with live identity remains unresolved; focused Herdr/dcode tests=421 passed` |
| Task 5 | `completed` | `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\durable-facts-runtime-retirement\project-OS-starter` | `codex` | Tasks 3, 4 | Secretary ownership, compaction, replay tests | `released controller required before delivery compaction; activation tombstone retained; Secretary focused tests=38 passed` |
| Task 6 | `active` | `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\durable-facts-runtime-retirement\project-OS-starter` | `codex` | Task 2 | Tura/Switchyard removal and historical compatibility tests | `new dcode-project Tura selection and Tura setup fail closed; historical helpers and Switchyard manager remain, so active-topology retirement is incomplete` |
| Task 7 | `completed` | `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\durable-facts-runtime-retirement\project-OS-starter` | `codex` | Tasks 3–6 | CI wiring, generated drift, retention checks | `workflow concurrency and focused contract tests added; benchmark summary omits raw rows/pairs; summary proof passed` |
| Task 8 | `pending` | `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\durable-facts-runtime-retirement\project-OS-starter` | `codex` | Tasks 1–7 | full verification, regression matrix, measurement summary | pending |

## Task Breakdown

### Task 1: Freeze repository truth and migration boundaries

**Purpose:**
- Establish exact active consumers, generated owners, tests, deletion boundaries,
  current base, and unrelated working-tree state before changing shared
  lifecycle contracts.

**Task Function:**
- Repository truth and migration-safety audit.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:**
- Durable ownership, historical compatibility, rollback safety,
  generated-source ownership.

**Required Skills:**
- `skill-refactoring-assessment`
- `skill-using-git-worktrees`

**Files And Symbols:**
- `scripts/manage_switchyard_runtime.py`,
`scripts/dcode_project.py`, `scripts/herdr_main_launcher.py`,
`scripts/herdr_parallel_dispatch.py`, `scripts/project_os_runtime/`,
`repo_config/`, `.agents/skills/`, `generated_agents/`, `tests/`,
`.github/workflows/`.

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: `run inventory, read source/tests/config, record current HEAD and origin/main, create isolated worktree, and run baseline validators`
- Stop for: `unrelated working-tree mutation, missing canonical source, unknown generated owner, or any request to delete historical Plans`

**Steps:**
1. Record `git status --short --untracked-files=all`, `git rev-parse HEAD`,
   `git rev-parse origin/main`, and exact untracked paths to preserve.
2. Classify every `tura`, `switchyard`, `stage_router`, and
   `project-delegate` reference as active source, active test/config, generated
   output, historical completed Plan, or unrelated text.
3. Trace callers and tests for `evaluate_acceptance`, `validate_task_result`,
   `parse_task_result`, `_build_assignment_result`, `_pane_ownership_lock`,
   `_terminate_codex_lane`, `_remove_role_views`, `_cleanup_stale_direct_mcp_runtimes`,
   `build_evidence_snapshot`, and `ControllerSessionAdapter`.
4. Run baseline `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`,
   `py -3 scripts/validate_planning_lifecycle.py --repo-root .`, and focused
   current lifecycle tests.
5. Record baseline failures without changing unrelated files.
6. Record rollback boundaries before destructive changes: identify implementation
   checkpoint commits and canonical generated-source owners. Code rollback
   requires controller/user authorization, reverts task-owned commits without
   resetting unrelated state, regenerates adapters from restored canonical
   sources, and reruns affected proof. Git rollback cannot restore retired
   processes or disposed evidence; keep evidence until Task 3 release gates
   pass and stop if recovery requires an unavailable artifact.

**Verification:** `git status --short --untracked-files=all`; focused `rg`
inventory; baseline validators complete and preserved paths remain unchanged.

**Exit Criteria:** Active and historical references have named owners and no
deletion target lacks a caller/test decision.

### Task 2: Add pure phase-specific reconciliation

**Purpose:**
- Replace global missing-evidence gating with a pure decision surface that
  distinguishes eligibility from completed state and keeps remote evidence
  outside runtime ownership.

**Task Function:**
- Runtime contract correction and boundary integration.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:**
- Dispatch independence, dependency readiness, checkpoint/candidate separation,
  remote outage handling, lifecycle phase gates.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:** Add `scripts/project_os_runtime/reconciliation.py` with
`RemotePrEvidence`, `ReconciliationInput`, `ReconciliationResult`, and
`reconcile`; update `scripts/project_os_runtime/plan_preparation.py`,
`scripts/project_os_runtime/acceptance.py::evaluate_acceptance`,
`scripts/herdr_parallel_dispatch.py::launch_preflight`,
`scripts/herdr_parallel_dispatch.py::run_lane`,
`scripts/project_os_runtime/attempt.py::derive_lifecycle_state`;
add `tests/test_project_os_reconciliation.py` and update focused dispatch and
acceptance tests.

**Dependencies:**
- Task 1.

**Authority:**
- Preauthorized local actions: `add pure dataclasses/functions, wire existing dispatch/acceptance/retirement boundaries, and add deterministic tests`
- Stop for: `new persistence, GitHub client/cache, workflow database, scheduler, or any mutation from reconciliation code`

**Steps:**
1. Define phase requirements exactly: dispatch requires valid Plan/task/checkpoint,
   `dependencies_ready=True`, workspace validity, and no conflicting active
   attempt; verify requires runtime attempt, attributable candidate, terminal
   Worker state, and published TaskResult; accept requires current proof and
   unchanged candidate; integrate requires CoS PASS and current remote facts;
   retire requires exact runtime ownership and settlement; prune requires
   canonical consequence, acceptance reference, and replay-retention expiry.
2. Keep `checkpoint_sha` as canonical Plan/Git coordination checkpoint and
   `lane_head_sha` as implementation candidate. Never require equality.
3. Treat absent `attempt_id` as dispatch-ready when other dispatch conditions
   pass. Treat unavailable GitHub as remote-action unavailable, not local
   dispatch failure.
4. Return separate `integration_eligible`, `integration_complete`,
   `retirement_eligible`, and `retirement_complete` fields with explicit next
   action and unresolved reasons.
5. Wire the same pure reconciler at dispatch, acceptance, and runtime
   finalization boundaries; Task 3 owns integration wiring because it binds
   controller-supplied GitHub evidence; do not add orchestration.

**Verification:** Tests prove dependency-ready local dispatch without GitHub,
absent attempt readiness, dependency blocking, `C != H` acceptance, green
remote checks without CoS PASS, merge eligibility without merged state, and
fresh-controller reconstruction from durable references.

**Exit Criteria:** No phase uses one global `missing` set or copied boolean as
its sole gate; reconciler has no filesystem, network, or persistence side
effect.

### Task 3: Bind GitHub facts and move evidence release behind CoS

**Purpose:**
- Ensure integration consumes current PR facts and evidence deletion requires
  downstream acceptance plus canonical consequence.

**Task Function:**
- Acceptance and remote-evidence contract correction.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:**
- PR identity, head-bound checks/reviews, Worker/CoS authority boundary,
  canonical-only retention, race-safe integration.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`

**Files And Symbols:** `scripts/project_os_runtime/reconciliation.py::RemotePrEvidence`,
`scripts/project_os_runtime/acceptance.py::evaluate_acceptance` and new
`authorize_evidence_release`, `scripts/project_os_runtime/results.py::validate_task_result`,
`parse_task_result`, `publish_task_result`, `scripts/dcode_project.py::main`,
`_publish_result_receipt`, `_settle_attempt`,
`scripts/herdr_main_launcher.py::_discard_deepagents_receipt`,
`tests/test_project_os_acceptance.py`, `tests/test_project_os_runtime.py`,
`tests/test_dcode_project.py`, `tests/test_herdr_main_launcher.py`.

**Dependencies:**
- Task 2.

**Authority:**
- Preauthorized local actions: `change evidence schemas and acceptance/release helpers, preserve legacy parsing, and add failure-path tests`
- Stop for: `Worker-derived acceptance deletion, stale remote snapshot persistence, credential ownership, or evidence unlink before canonical acceptance`

**Steps:**
1. Require remote evidence fields `repository_identity`, `pr_number`,
   `base_ref`, `base_sha`, `head_sha`, head-bound checks, review identity,
   reviewed head, mergeability, merged state, and `source_ref`.
2. Derive `review_valid` only when review belongs to exact PR and reviewed head
   equals current candidate and PR head; reject wrong PR with same head and old
   review with current PR.
3. Keep GitHub retrieval in existing controller/provider capability. Pass one
   ephemeral `RemotePrEvidence` snapshot into pure reconciliation; do not add
   runtime cache or GitHub client.
4. Make `validate_task_result` accept `accepted` only as legacy non-authoritative
   metadata. Force release authorization to ignore Worker `accepted=True`.
5. Add `authorize_evidence_release` binding `plan_ref`, `task_id`,
   `assignment_id`, `attempt_id`, accepted candidate SHA, and canonical
   acceptance checkpoint SHA. Task 1 inventories each evidence consumer and
   its authoritative release source. Require CoS PASS, current Plan/Git proof,
   canonical-consequence proof, and positive artifact-bound release evidence
   from every required consumer, including recovery consumers. Each consumer
   owns its retention-policy reference and expiry proof; no implicit TTL or
   inferred consent is permitted. Missing policy, unknown consumers, missing
   release evidence, or unresolved recovery need blocks disposal and preserves
   evidence. Revalidate consumer releases and retention proof immediately
   before unlinking exact-bound evidence; CoS PASS alone never authorizes
   disposal. Keep replay tombstones until their own consumer-owned release gate
   passes; payload release does not authorize tombstone deletion.
6. Keep terminal Worker cleanup separate: process/pane/role-view settlement may
   complete before CoS review; TaskResult and receipt remain until release
   authorization succeeds. Use GitHub `expected_head_sha` at merge.

**Verification:** Wrong repository/PR/base/head, stale review, green checks
without CoS PASS, Worker `accepted=True`, exact CoS release binding, missing
canonical consequence, unexpired retention, outstanding recovery, and
pending-release retention preserve TaskResult and receipt; expired retention
with every release gate satisfied permits exact-bound disposal.
Tests also prove missing consumer consent, unknown consumers, absent retention
policy, stale release binding, and payload-only release cannot authorize
evidence or replay-tombstone deletion.

**Exit Criteria:** Only post-acceptance controller path can release consumed
evidence; remote mutable facts are never persisted by runtime code.

### Task 4: Make Herdr and runtime retirement ownership-safe

**Purpose:**
- Retire exact runtime resources without dispatch/retirement races or false
  success from missing observations.

**Task Function:**
- Runtime ownership and cleanup correctness.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:**
- Immutable launcher binding, exclusive pane ownership, resource-specific
  retirement, truthful idempotency, MCP reporting.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`

**Files And Symbols:** `scripts/herdr_main_launcher.py::_build_assignment_result`,
`_pane_ownership_lock`, `_run_with_pane_ownership`, `_terminate_codex_lane`,
`scripts/herdr_parallel_dispatch.py::run_lane`,
`scripts/dcode_project.py::_remove_role_views`, `_role_views_lock`,
`_settle_attempt`, `_direct_mcp_runtime`, `main`,
`tests/test_herdr_main_launcher.py`, `tests/test_herdr_parallel_dispatch.py`,
`tests/test_dcode_project.py`, `tests/test_herdr_attempt_contract.py`.

**Dependencies:**
- Task 2.

**Authority:**
- Preauthorized local actions: `edit task-owned launcher/runtime cleanup and ownership code, use existing locks, and add deterministic process/cleanup seam tests`
- Stop for: `unrelated process termination, pane/session deletion without exact binding, uncertain descendant state, or external MCP deletion`

**Steps:**
1. Emit one immutable launcher-owned ownership record containing repository,
   plan/lane, assignment, attempt, session, pane, agent, worktree, and process
   identity. Retirement consumes validated record, not caller-redeclared IDs.
2. Acquire `_pane_ownership_lock` across inspect, validate, stop/close, and
   absence verification. Dispatch and retirement cannot own or reuse same pane
   concurrently.
3. If pane is absent, return already-retired only when recorded process is
   positively dead or prior verified retirement receipt exists. Otherwise return
   unresolved/recovery-required.
4. Aggregate retirement by resource: worker process, descendants, pane, session,
   worktree/role views, and MCP runtime. Set `lane_retired=True` only when all
   task-owned required resources are settled; preserve shared/default session
   without blocking lane retirement.
5. Make cleanup monotonic and idempotent: second cleanup returns completed or
   already-absent; uncertain residue returns unresolved with exact remaining
   paths; MCP deletion failure remains visible and separate from semantic task
   success.
6. Remove `_cleanup_stale_direct_mcp_runtimes` only after Task 1 confirms no
   caller; keep `_direct_mcp_runtime` owned cleanup and failure evidence.

**Verification:** Tests cover pane race, absent pane with live recorded process,
shared session preservation, uncertain cleanup, repeated cleanup, role-view
lock contention, descendant uncertainty, MCP deletion failure, and retirement
versus dispatch exclusivity.

**Exit Criteria:** Retirement cannot claim success from timeout, silence,
missing pane, or unverified cleanup.

### Task 5: Restore Secretary as derived attention consumer

**Purpose:**
- Remove runtime fact ownership from Secretary and finish safe compaction
  without replay or delivery leakage.

**Task Function:**
- Secretary ownership and replay/retention correction.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:**
- Source ownership, sparse communication, replay protection, delivery payload
  release, fresh-controller reconstruction.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:** `scripts/project_os_runtime/secretary_evidence.py::build_evidence_snapshot`,
`scripts/project_os_runtime/secretary_events.py::reconcile_event_hint`,
`coalesce_event_hints`, `scripts/project_os_runtime/secretary_adapter.py::ControllerSessionAdapter`,
`InMemoryControllerSessionJournal`, `release_session`,
`tests/test_secretary_evidence.py`, `tests/test_secretary_events.py`,
`tests/test_secretary_adapter.py`, `tests/test_secretary_receipts.py`,
`docs/operating_system/runtime/runtime-surfaces.md`,
`.agents/skills/skill-project-secretary/SKILL.md`.

**Dependencies:**
- Tasks 3 and 4.

**Authority:**
- Preauthorized local actions: `derive Secretary views from reconciled owner facts, prune released delivery payloads, retain replay tombstones, and add adapter/evidence tests`
- Stop for: `Secretary becoming acceptance, runtime, task-ledger, or cleanup authority, or deletion of replay identity before its retention gate`

**Steps:**
1. Stop deriving `attempt_id`, terminal state, or publication state from Plan
   copies. Consume reconciled runtime/Worker/CoS facts with explicit provenance.
2. Keep Secretary output to one attention delta per unresolved project issue;
   preserve `event_identity` and replay tombstone after delivery payload release.
3. Complete controller compaction: after controller release, remove delivery
   entries and payload bodies while retaining enough identity to reject replay.
4. Prove a compacted controller cannot replay released delivery and a fresh
   controller reconstructs required state from Plan, Git, GitHub, and unsettled
   runtime evidence.

**Verification:** Ownership matrix, compaction, duplicate replay, released
payload, and fresh-controller recovery tests pass; Secretary never changes
acceptance, dispatch, retirement, or Git state.

**Exit Criteria:** Secretary is derived attention only; release retains replay
identity but no unnecessary delivery payload.

### Task 6: Remove active Tura/Switchyard surfaces and preserve history

**Purpose:**
- Retire obsolete runtime topology without breaking historical Plan parsing or
  canonical generated surfaces.

**Task Function:**
- Runtime topology migration and compatibility cleanup.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:**
- Canonical-only retention, active-path removal, historical readability,
  generated-source discipline.

**Required Skills:**
- `skill-refactoring-assessment`
- `skill-code-standards`

**Files And Symbols:** `repo_config/planning_artifact_schema.yaml`,
`scripts/dcode_project.py::_resolve_executor`, `_tura_worker_paths`,
`_run_tura_worker`, `_tura_worker_task`, `_tura_worker_argv`,
`_tura_worker_environment`, `scripts/manage_switchyard_runtime.py`,
`scripts/setup_deepagents_runtime.ps1`,
`scripts/validate_planning_lifecycle.py::validate_execution_contract`,
`scripts/validate_planning_lifecycle.py::validate_git_coordination`,
`scripts/validate_repo_contracts.py`, `repo_config/switchyard-routing.toml`,
`tests/test_setup_deepagents_runtime_contract.py`,
`docs/operating_system/planning/planning-dispatch.md`,
`docs/operating_system/runtime/runtime-surfaces.md`,
`.agents/skills/skill-chief-of-staff/SKILL.md`,
`.agents/skills/skill-executing-plans/SKILL.md`, `tests/test_manage_switchyard_runtime.py`,
`tests/test_dcode_project.py`, `tests/test_validate_repo_contracts.py`,
`tests/test_validate_planning_lifecycle.py`.

**Dependencies:**
- Task 1 and Task 2.

**Authority:**
- Preauthorized local actions: `remove Project OS-owned active Tura/Switchyard code, validators, docs, and tests; retain parser compatibility for historical completed Plans; regenerate adapters only from canonical sources`
- Stop for: `deleting historical completed Plans, editing generated adapters directly, or removing Codex/DeepAgents launch paths`

**Steps:**
1. Reject new active Tura selection before launch and reject active Switchyard
   routing references in lifecycle validation.
2. Remove unused Tura worker dispatch/setup/provider code, Tura setup
   parameters, repository-owned provider configuration, and setup branches
   generating `project-delegate` wrappers,
   and Tura installation guidance after caller inventory proves no supported
   active caller. Preserve DeepAgents setup and read compatibility for completed
   and superseded historical Plans.
3. Remove obsolete Project OS-owned Switchyard manager/manifest/patch surfaces;
   retain only explicit historical references required for readability.
   Repository retirement does not authorize editing or deleting installed
   `$HOME/.local/bin/project-delegate.ps1`, `project-delegate.cmd`,
   `$HOME/.codex/auto.config.toml`, `$HOME/.switchyard/routes.toml`, or
   user-local provider configuration. Record installed-output owners and
   provide migration instructions; preserve these outputs unless separately
   approved with exact paths, ownership proof, retention gates, and rollback
   evidence. Do not run setup/deploy commands to retire user-local outputs.
4. Update canonical docs, skills, config, and validators first; run
   `py -3 scripts/sync_agent_adapters.py --all-platforms` and verify generated
   outputs rather than hand-editing them.

**Verification:** New Tura task rejected, historical Tura Plan readable, active
Switchyard routing rejected, Codex/DeepAgents focused tests pass, generated
surfaces have no drift.

**Exit Criteria:** No active supported path depends on Tura or Switchyard.

### Task 7: Wire CI and retention checks

**Purpose:**
- Make corrected contracts continuously enforceable while keeping GitHub Actions
  concurrency conservative and benchmark artifacts canonical-only.

**Task Function:**
- CI and maintained-documentation integration.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:**
- GitHub durable consequence, CI cancellation, retention, generated validation,
  raw benchmark removal.

**Required Skills:**
- `skill-code-standards`
- `skill-verification-before-completion`

**Files And Symbols:** `.github/workflows/repo-contracts.yml`,
`.github/workflows/runtime-contracts.yml`,
`scripts/benchmark_completion_monitoring.py`,
`tests/test_secretary_benchmark.py`, `artifacts/completion-monitoring/`,
`docs/operating_system/`, `README.md` when active references remain.

**Dependencies:**
- Tasks 3–6.

**Authority:**
- Preauthorized local actions: `add focused test invocations to existing workflows, preserve cancel-in-progress, remove raw benchmark JSON rows from Git, and update canonical docs`
- Stop for: `new workflow database, GitHub cache, workflow that bypasses required checks, or deletion of canonical summary evidence`

**Steps:**
1. Add reconciliation, evidence-release, retirement, Secretary compaction, and
   topology tests to existing workflow jobs.
2. Add workflow-specific concurrency to both contract workflows:
   ```yaml
   concurrency:
     group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
     cancel-in-progress: ${{ github.event_name == 'pull_request' }}
   ```
   Cancel superseded pull-request runs only, not main-branch push runs. Preserve
   required jobs and checks; leave Pages workflow concurrency unchanged.
3. Change `scripts/benchmark_completion_monitoring.py` to retain one summary
   with provenance, workload, environment, aggregate measurements, correctness,
   and explicit metric limitations while excluding raw `rows` and `pairs`;
   preserve the existing nested `correctness` object and integer mismatch
   counts.
   Add a regression proving summary-only output and preserved correctness
   checks. Remove raw benchmark runs from tracked artifacts.
4. Update operating-system docs and README only from canonical sources; run
   generated sync and drift validators.

**Verification:** Workflow YAML parses, focused CI commands exist, concurrency
settings remain present, no raw benchmark rows remain, summary is valid JSON,
and generated checks pass.

**Exit Criteria:** CI proves correctness gates without creating a second durable
status owner.

### Task 8: Final verification and measured follow-up

**Purpose:**
- Prove cross-task behavior, safe retention, generated parity, and measurement
  honesty before completion.

**Task Function:**
- Release-readiness verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:**
- All outcomes and required merge gates.

**Required Skills:** `skill-verification-before-completion`,
`skill-plan-document-reviewer`, `skill-requesting-code-review`.

**Files And Symbols:** All Task 1–7 targets; plan ledger and final proof.

**Dependencies:**
- Tasks 1–7.

**Authority:**
- Preauthorized local actions: `run full test and validator matrix, inspect diff/reference inventory, compare bounded before/after metrics, and record evidence in this plan`
- Stop for: `unrelated failures not isolated, destructive-cleanup uncertainty, generated drift, stale remote evidence, or any unchecked required gate`

**Steps:**
1. Run focused tests for reconciliation, acceptance, results, Herdr, dcode,
   Secretary, validators, and topology.
2. Run full `py -3 -m pytest -q` and all repository validators.
3. Execute required matrix: dependency-ready dispatch with GitHub unavailable;
   absent attempt; dependency block; `C != H`; wrong PR; stale review; Worker
   `accepted=True`; CoS release; green checks without CoS PASS; merge eligible
   but unmerged; shared session; uncertain cleanup; absent pane with live
   process; dispatch/retirement race; repeated cleanup; MCP failure; Secretary
   replay; fresh-controller recovery.
4. Re-run active-reference search without excluding Plans:
   `rg -n -i --glob '!generated_agents/**' 'tura|switchyard|stage_router|project-delegate' README.md repo_config scripts tests docs .agents`.
   Classify Plan matches by frontmatter status. Permit explicit completed or
   superseded history and intentional migration instructions; reject active
   routing or admission references. Verify generated output separately through
   sync and drift checks.
5. Measure only after correctness with identical workload and environment:
   coordination turns, handoffs, GitHub reads, Herdr commands, terminal-to-
   retirement latency, orphan resources, retained bytes, superseded CI minutes,
   recovery time, and destructive cleanup errors. Mark unavailable metrics
   unavailable; never infer zero from no observation.
6. Request independent implementation review against the exact final candidate
   SHA. A later candidate commit invalidates that review and requires a fresh
   review plus rerun of affected proof.
7. Apply `skill-verification-before-completion`; keep plan `active` until proof
   is `verified`, then transition to `completed` through the coordination rule.

**Verification:**
- `py -3 -m pytest -q`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- `py -3 scripts/validate_repo_contracts.py --repo-root .`
- `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- `py -3 scripts/build_starter_kit.py`
- `py -3 scripts/validate_starter_kit.py`
- `git diff --check`
- `py -3 scripts/benchmark_completion_monitoring.py --baseline-revision 187f28e492ae1c4726cdd2f7b5a261a2b8b6c695 --repetitions 3 --output artifacts/completion-monitoring/runtime-retirement-final.json`
- `rg -n -i --glob '!generated_agents/**' 'tura|switchyard|stage_router|project-delegate' README.md repo_config scripts tests docs .agents`
- `python -m json.tool artifacts/completion-monitoring/runtime-retirement-final.json`
- `py -3 -c "import json; p=json.load(open('artifacts/completion-monitoring/runtime-retirement-final.json', encoding='utf-8')); c=p['correctness']; assert c['all_outcomes_match'] is True; assert c['lifecycle_mismatches'] == 0; assert c['cleanup_mismatches'] == 0; assert c['reconciliation_mismatches'] == 0; assert 'rows' not in p and 'pairs' not in p"`

**Exit Criteria:** Every required gate has fresh proof, every unresolved item
has an explicit blocker, canonical/generated layers agree, and unrelated
untracked paths remain untouched.

## Verification

Final completion requires all Task 1–8 proof plus:

- no active Tura or Switchyard admission;
- historical completed Tura Plans remain readable;
- dispatch does not require GitHub or `attempt_id`;
- integration requires exact current PR/base/head/check/review facts and CoS PASS;
- retirement and evidence release remain separate decisions;
- uncertain cleanup remains unresolved;
- Secretary compaction blocks replay and releases delivery payload;
- no raw benchmark JSON rows or copied remote status owner remain;
- GitHub Actions retain conservative cancellation and required checks;
- independent implementation review passes against exact final candidate SHA;
- `skill-verification-before-completion` returns `verified`.

## Completion Criteria

1. Each fact has one owner and each consumer revalidates mutable evidence.
2. Controllers alone make semantic dispatch, acceptance, integration, and
   evidence-release decisions.
3. Runtime owners retire exact resources with positive, idempotent evidence.
4. Consumers authorize disposal only after canonical consequence and replay
   retention gates pass.
5. Git and GitHub preserve durable workflow and integration consequence.
6. Codex and DeepAgents remain supported; Tura and Switchyard active paths do
   not.
7. Full verification is fresh, reproducible, and recorded in this plan.
