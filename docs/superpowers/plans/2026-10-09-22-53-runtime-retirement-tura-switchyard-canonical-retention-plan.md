---
layer: change
artifact_type: plan
status: active
template_id: implementation-plan
contract_version: "1"
name: runtime-retirement-tura-switchyard-canonical-retention
targets:
  - repo_config/planning_artifact_schema.yaml
  - scripts/dcode_project.py
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/project_os_runtime/reconciliation.py
  - scripts/project_os_runtime/results.py
  - scripts/project_os_runtime/secretary_evidence.py
  - scripts/project_os_runtime/secretary_receipts.py
  - scripts/project_os_runtime/secretary_events.py
  - scripts/project_os_runtime/secretary_adapter.py
  - .github/workflows/repo-contracts.yml
  - .github/workflows/runtime-contracts.yml
  - docs/operating_system/
  - .agents/skills/
  - generated_agents/
  - tests/
---

# Runtime Retirement, Tura/Switchyard Removal, Canonical-Only Retention

## Goal

Retire Project OS-owned Tura and Switchyard execution paths, leave Codex and
DeepAgents as active executors, make Herdr and each resource owner perform
idempotent retirement with positive ownership evidence, and retain operational
evidence only until its canonical consequence is recorded.

Review disposition: verdict accepted with repository-specific corrections.
Drafting workspace remains `codex/9router-security-overlay-099` at
`04f7c70e6854341dd3ffaabe83687f4af4405cf8`; it is not an execution base.
`git ls-remote origin refs/heads/main` verified current `main` as
`187f28e492ae1c4726cdd2f7b5a261a2b8b6c695`. Execution must create a dedicated
migration branch/worktree from that SHA. Current code already has
`_discard_deepagents_receipt()` and `_terminate_codex_lane()`. The plan keeps
historical receipt compatibility, preserves serialized cleanup `unverified`,
binds freshness to Git checkpoints and PR head SHAs, and adds no central
cleanup service or workflow database.

## Implementation Outcomes

### Active runtime topology is Codex plus DeepAgents

Planning schema, executor selection, launcher setup, runtime procedures,
skills, README, validators, tests, and generated adapters no longer advertise
or admit Tura. Project OS-owned Switchyard routing files, validators, docs, and
patch evidence are removed. Completed historical plans remain readable and are
not rewritten.

### Durable truth has one authoritative owner

Plan/spec owns scope, task dependencies, and acceptance criteria. Git owns
repository contents, ancestry, worktrees, and checkpoint commits. PR head SHA
owns the implementation candidate. GitHub owns PR state, checks, reviews, and
merge mechanics. CoS owns semantic acceptance recorded in a Plan checkpoint.
Runtime owners own only temporary attempts, settlement, and retirement evidence.
Secretary routes non-reconstructible attention and never becomes a second task
ledger or acceptance authority.

### Reconciliation is derived and read-only

Existing Plan/Git/GitHub/runtime owners expose one read-only reconciliation
boundary that returns current task, dependency, Git, PR/head, check/review,
runtime, contradiction, missing-evidence, next-action, and authorized-owner
facts. It stores nothing and never trusts copied `head_matches`, `ci_passed`,
`review_valid`, or `mergeable` claims at consequential action boundaries.

Stable references are `plan_ref`, `task_id`, `checkpoint_sha`, `lane_head_sha`,
and `attempt_id`. Existing `plan_revision` remains a content digest until all
consumers can derive Plan content from Git; it is not reinterpreted as a Git
SHA.

### Lifecycle and retention are separate decisions

Execution, Verification, Acceptance, Integration, and Retirement remain
distinct. A terminal Worker with published `TaskResult` may retire before CoS
acceptance, but evidence remains until consumed and canonical consequence is
recorded. PR merge never proves Herdr or worktree retirement. Operational state
is retained only for live concurrency, idempotency, duplicate suppression,
ownership, incomplete-action recovery, or unconsumed evidence.

### GitHub Actions remain canonical proof

PR checks and reviews remain GitHub-owned. Superseded PR runs are cancelled
where safe; broad runtime suites remain enabled; no path-based suite skipping,
CI status files, or copied PR/check/review ledgers are added. Optional Git
commit trailers remain deferred P2 work, not an initial migration dependency.

### Resource retirement has one shared result vocabulary and exact ownership

DeepAgents attempt directories, direct MCP runtime directories, Herdr panes and
agents, and task-owned sessions expose explicit `removed`, `preserved`, or
semantic `unresolved` outcomes with reasons. Serialized receipt cleanup state
remains `unverified`; readers interpret it as unresolved/not proven. Unknown ownership, shared resources,
transport uncertainty, active recovery, and unreleased work preserve resources.
Repeated retirement is idempotent. Worktree deletion remains separate and stays
under `skill-finishing-a-development-branch`.

### Canonical evidence outlives disposable runtime evidence

Lifecycle receipts, TaskResult records, Secretary session entries, Docket
obligations, and raw runtime artifacts are deleted or compacted only after
settlement, acceptance, canonical Plan/Git consequence, and recovery needs are
proven. Existing Docket contract remains documentation-only because no
production Docket loader exists in this repository.

### Cleanup changes have direct regression and operational proof

Focused tests cover success, failure, idempotency, ownership mismatch, shared
resources, transport uncertainty, receipt retention, historical-plan
compatibility, and stale-reference rejection. Repository, generated-adapter,
starter-kit, and runtime validation pass. Before/after cleanup metrics are
captured at baseline and final revisions; each metric is marked
`MEASURED`, `UNAVAILABLE`, or `NOT_APPLICABLE`.

## Review Notes

- Pasted recommendation cites stale repository state; execution must bind to the
  current Git base recorded below.
- Recommendation names `_discard_deepagents_receipt()` accurately, but its
  current `rmdir()` behavior silently leaves a directory when sibling
  `task-result.json` remains. Fix ownership sequencing in the Herdr launcher;
  do not let independent consumers delete sibling evidence.
- Do not perform an `unverified` → `unresolved` serialized wire migration.
  Retain `unverified` in current and historical receipts; use semantic
  `unresolved` only in derived retirement views unless a versioned receipt
  schema is later approved.
- Recommendation says “canonical only” but does not define retention gates.
  Tasks below make settlement, acceptance, canonical consequence, and recovery
  the explicit gates.
- Current working tree has unrelated untracked `.playwright-mcp/`, `db/`, and
  `temp_evidence.json`; execution must preserve them.
- Do not delete user-owned `$HOME/.switchyard`, `$CODEX_HOME/auto.config.toml`,
  or other external runtime files. Remove only repository-owned producers and
  validators.
- Adopt five bounded migration waves: A topology simplification, B Git/GitHub
  reconciliation plus handoffs, C cleanup plus runtime retirement, D Secretary
  retention, and E canonical-state plus Actions convergence.
- One fact gets one durable owner. Reconciliation is read-only and discarded
  after each decision; no `status.json`, workflow DB, durable Herdr DB,
  duplicate ledger, cleanup daemon, or event bus is introduced.
- Handoffs pass stable references and outcome/evidence pointers, not copied
  mutable status. Receivers re-read Plan, Git, GitHub, and runtime owners.
- Consequential actions revalidate current PR head, checks, reviews,
  mergeability, dirty state, and runtime ownership. GitHub unavailability is
  `REMOTE_EVIDENCE_UNAVAILABLE`, never PASS.
- Docket retains only non-reconstructible obligations. Durable human/project
  blockers may move to GitHub Issues, but promotion removes duplicate Docket
  state and never creates one Issue per Plan task.
- Generic reconciliation belongs in a neutral pure runtime module, not in
  `secretary_*`; Secretary and CoS consume its ephemeral view.
- GitHub reads come from existing controller capability as an ephemeral remote
  snapshot. No new GitHub client, credential owner, cache, or persistence.
- Historical Tura remains parseable for completed/superseded Plans; active
  lifecycle validation rejects it before dispatch.
- This migration uses ordinary single-lead execution. CoS and Secretary are
  systems under test, not orchestration owners for their own surgery.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-plan-document-reviewer`, `skill-using-git-worktrees`, `skill-verification-before-completion`
- Isolation: `fresh dedicated worktree per migration wave, created from the newly merged predecessor; the approved Plan is copied into each fresh worktree before activation and remains the only coordination artifact`
- Commit policy: `no speculative coordination commits; implementation branches may commit within granted lane authority; lead creates one coordination checkpoint after each accepted migration wave; no commit changes task state without accepted proof`
- Preauthorized local actions: `edit listed canonical files, delete only listed Project OS-owned runtime files, regenerate generated adapters and starter-kit outputs through repository scripts, run listed local tests and validators, inspect Git state, and record bounded runtime metrics`
- User-approval actions: `push, merge, publication, external runtime deletion, destructive recovery, discard of unrelated untracked files, worktree deletion, and commits`
- Parallel ownership: `none`; canonical schema, docs, skills, generated projections, validators, and shared runtime contracts require ordered writes
- Sequential fallback: `Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7 → Task 8 → Task 9`
- Activation gate: `lead changes frontmatter status proposed → active in fresh migration worktree before Task 1; no task executes while status is proposed`
- Controller: `ordinary single-lead Git-tracked execution; CoS and Secretary are modified/tested systems, not migration orchestrators`
- Migration waves: `PR A = Task 2; PR B = Tasks 3–4; PR C = Tasks 5–6; PR D = Task 7; PR E = Task 8; Task 1 = rebase/baseline; Task 9 = final integration`
- Wave base rule: `each PR starts from newly merged predecessor; do not maintain five implementation branches simultaneously`
- Bootstrap rule: `fetch the recorded base SHA if absent locally; copy this approved Plan from the drafting workspace into the fresh worktree before changing status to active; record the copy and exact controller checkpoint transfer in the first accepted checkpoint`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/runtime-retirement-migration` created at activation
- Base commit: `187f28e492ae1c4726cdd2f7b5a261a2b8b6c695` (`origin/main`, verified 2026-10-09)
- Expected workspace: `fresh dedicated worktree from base; preserve unrelated untracked .playwright-mcp/, db/, temp_evidence.json, and this plan; do not reset or clean drafting workspace`
- Next action: `Task 9 — re-run final verification after review fixes`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | `rg` inventory and baseline validators | `baseline benchmark; active-reference inventory; repo-contract preflight passed` |
| Task 2 | `completed` | current | `codex` | Task 1 | topology deletion and supported-executor tests | `267 focused tests; topology files deleted; generated adapters synchronized` |
| Task 3 | `completed` | current | `codex` | Task 2 | read-only reconciliation and freshness tests | `reconciliation boundary; 8 focused tests; remote-unavailable fail-closed behavior` |
| Task 4 | `completed` | current | `codex` | Task 3 | reference-handoff and lifecycle tests | `reference projection; receipt-release guard; focused lifecycle suites passed` |
| Task 5 | `completed` | current | `codex` | Task 2 | cleanup contract, release trigger, and receipt lifecycle tests | `structured MCP/capture cleanup; exact release binding; 222 focused tests` |
| Task 6 | `completed` | current | `codex` | Task 5 | direct Herdr retirement boundary tests | `owner-checked idempotent retire_lane; mismatch/absent-pane tests; full Herdr suite passed` |
| Task 7 | `completed` | current | `codex` | Tasks 4, 6 | Secretary/Docket retention tests | `released-journal compaction with replay tombstones; Docket contract retained` |
| Task 8 | `completed` | current | `codex` | Task 7 | copied-state removal and GitHub Actions concurrency | `canonical retention policy; PR concurrency; no active retired-runtime references` |
| Task 9 | `active` | current | `codex` | Tasks 1-8 | full validator, generated drift, starter-kit, regression gates, and metrics | `review fixes applied; final verification pending` |

## Task Breakdown

### Task 1: Freeze active and historical surface inventory

**Purpose:**
- Establish exact current consumers, generated owners, test contracts, and
  deletion boundaries before changing shared runtime topology.

**Task Function:**
- Repository truth and migration-safety audit.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `repository-wide scope and deletion risk require controller selection at activation`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `baseline inspection is deterministic`

**Specification Coverage:**
- Reconcile recommendation against current source, tests, validators, Git base,
  generated surfaces, and unrelated workspace changes.

**Required Skills:**
- `skill-refactoring-assessment`
- `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: `repo_config/planning_artifact_schema.yaml:executor.shared`
- Inspect: `scripts/dcode_project.py:_resolve_executor`, `_tura_worker_paths`, `_run_tura_worker`, `_direct_mcp_runtime`
- Inspect: `scripts/herdr_main_launcher.py:_discard_deepagents_receipt`, `_terminate_codex_lane`, `_main_body`
- Inspect: `scripts/herdr_parallel_dispatch.py:run_lane`
- Inspect: `scripts/project_os_runtime/results.py:CLEANUP_STATES`, receipt parsers
- Inspect: `scripts/validate_repo_contracts.py`, `scripts/validate_planning_lifecycle.py`
- Inspect: `.agents/skills/`, `docs/operating_system/`, `README.md`, `tests/`
- Verify: `git status --short --untracked-files=all`

**Dependencies:**
- Current repository state and pasted recommendation.

**Authority:**
- Preauthorized local actions: `read files, run repository searches and baseline validators, and update this plan's evidence only`
- Stop for: `unknown active consumer, unexpected generated owner, or any need to delete unrelated workspace content`

**Steps:**
- [x] Step 1: Create/select dedicated migration worktree from
  `187f28e492ae1c4726cdd2f7b5a261a2b8b6c695`, record clean `git status`,
  `HEAD`, branch, and untracked paths, and leave drafting workspace untouched.
- [x] Step 2: Classify every Tura, Switchyard, `stage_router`, and
  `project-delegate` reference as active source, generated projection,
  validation/test contract, historical completed artifact, or external runtime
  reference.
- [x] Step 3: Confirm canonical sources under `.agents/skills/`,
  `docs/operating_system/`, `repo_config/`, and `agents/`; mark
  `generated_agents/` and `.agents/rules/` as derived outputs.
- [x] Step 4: Run baseline `py -3 scripts/validate_repo_contracts.py --repo-root . --fast` and
  `py -3 scripts/benchmark_completion_monitoring.py --baseline-revision 187f28e492ae1c4726cdd2f7b5a261a2b8b6c695 --repetitions 3 --output artifacts/completion-monitoring/runtime-retirement-baseline.json`; record validator and metric results before modification.
- [x] Step 5: Mark each requested metric `MEASURED`, `UNAVAILABLE`, or
  `NOT_APPLICABLE`; do not invent values or use prior reports as baseline.

**Verification:**
- [x] `rg -n -i --glob '!docs/superpowers/plans/**' --glob '!generated_agents/**' 'tura|switchyard|stage_router|project-delegate' .`
- Expected: `complete active-reference inventory exists; historical and generated references are separately classified`.
- [x] `git status --short --untracked-files=all`
- Expected: `only preserved workspace paths, this Plan, and declared baseline artifact output appear`.
- [x] `python -m json.tool artifacts/completion-monitoring/runtime-retirement-baseline.json`
- Expected: `baseline artifact records base revision, repeated cases, and comparable measurement inputs`.

**Exit Criteria:**
- Exact active write/delete set, generated refresh path, historical exceptions,
  and baseline validator result are recorded in the execution evidence.

### Task 2: PR A — Simplify execution topology

**Purpose:**
- Remove Project OS-owned Switchyard routing and Tura execution while leaving
  Codex and DeepAgents as the only active executors.

**Task Function:**
- Execution-topology retirement and compatibility convergence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `bounded deletion with validator, launcher, and documentation consumers`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `task-local topology tests provide direct contract proof`

**Specification Coverage:**
- Verdict PR A: remove Stage Router, auto-routing config, Project OS-generated
  route ownership, Tura setup/dispatch/configuration, validator invocation, and
  patch evidence while preserving historical completed Plans.

**Required Skills:**
- `skill-refactoring-assessment`
- `skill-code-standards`

**Files And Symbols:**
- Delete: `repo_config/switchyard-routing.toml`
- Delete: `scripts/manage_switchyard_runtime.py`
- Delete: `tests/test_manage_switchyard_runtime.py`
- Delete: `docs/operating_system/runtime/switchyard/README.md`
- Delete: `docs/operating_system/runtime/switchyard/decision-evidence.patch`
- Modify: `repo_config/planning_artifact_schema.yaml:artifacts.plan.executor.shared` only after legacy parser compatibility is proven
- Modify: `scripts/project_os_runtime/plan_preparation.py:parse_plan`, `load_plan`, and executor compatibility handling
- Modify: `scripts/dcode_project.py:_resolve_executor`, Tura worker helpers, and executor dispatch in `main`
- Modify: `scripts/setup_deepagents_runtime.ps1:TuraExecutable`, `TuraProviderConfig`, and `project-delegate` generation
- Modify: `scripts/validate_planning_lifecycle.py` active executor diagnostics
- Modify: `scripts/validate_repo_contracts.py` Switchyard subprocess-step construction
- Modify: `tests/test_validate_repo_contracts.py` expected validation-step assertions
- Modify: `.github/workflows/repo-contracts.yml`, `.github/workflows/runtime-contracts.yml` obsolete Switchyard/Tura test and job references
- Modify: active executor/runtime docs, README, template, and canonical skills
- Modify: `tests/test_dcode_project.py`, `tests/test_validate_planning_lifecycle.py`, `tests/test_native_personal_local_workflow.py`, `tests/test_skill_chief_of_staff.py`, `tests/test_validate_template_required_sections.py`
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md` Switchyard sections
- Modify: `docs/operating_system/governance/repo-governance.md` active `repo_config/` inventory
- Verify: `repo_config/starter-kit-manifest.json`, generated outputs, and repository-wide stale-reference search

**Dependencies:**
- Task 1 inventory confirms all deleted files are Project OS-owned and separates historical Tura references from active contracts.

**Authority:**
- Preauthorized local actions: `delete only listed repository-owned Switchyard files, edit listed topology/config/docs/tests, and run focused checks`
- Stop for: `any requested deletion under $HOME, $CODEX_HOME, .switchyard, or another external runtime root`

**Steps:**
- [x] Step 1: Remove the manifest, manager, tests, runtime docs, and decision-evidence patch; remove only Project OS-owned Switchyard generated runtime producers.
- [x] Step 2: Keep low-level parser compatibility for legacy `tura`; reject
  `tura` for `new`, `proposed`, and `active` Plans in lifecycle validation, and
  accept `tura` for completed/superseded historical Plans without rewriting them.
- [x] Step 3: Remove Tura dispatch, setup, provider, environment,
  `project-delegate`, active docs, and active tests.
- [x] Step 4: Preserve Codex and DeepAgents launch, receipt publication,
  role-view cleanup, and settlement behavior; do not edit generated files directly.
- [x] Step 5: Add regression assertions that active validation no longer invokes
  Switchyard or Tura, historical Plans remain readable, and starter-kit
  manifests do not require deleted surfaces.
- [x] Step 6: Remove obsolete CI invocations in the PR A workflows, regenerate
  affected adapters from canonical sources, and run the adapter drift and
  repository-contract gates before handing PR A to the next wave. Task 9 still
  performs the final full regeneration and drift check.

**Verification:**
- [x] `py -3 -m pytest tests/test_validate_repo_contracts.py tests/test_dcode_project.py tests/test_validate_planning_lifecycle.py tests/test_native_personal_local_workflow.py tests/test_skill_chief_of_staff.py tests/test_validate_template_required_sections.py -q`
- Expected: `Switchyard/Tura active paths fail closed; Codex and DeepAgents paths pass; historical plans remain readable`.
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check` and
  `py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- Expected: `PR A generated surfaces have no drift before wave handoff`.
- [x] `rg -n -i --glob '!docs/superpowers/plans/**' --glob '!generated_agents/**' 'switchyard|stage_router' repo_config scripts tests docs README.md`
- Expected: `no active Project OS-owned Switchyard or Tura executable reference remains; only approved historical compatibility text remains`.

**Exit Criteria:**
- Repository no longer creates, validates, documents, or tests Project OS-owned
  Switchyard routing or Tura execution; external runtime deletion remains
  unperformed and historical Plans remain readable.

### Task 3: PR B — Reconcile Git and GitHub as durable truth

**Purpose:**
- Make Plan, Git, GitHub, CoS, and runtime ownership explicit, then derive a
  read-only current evidence view without adding a state store.

**Task Function:**
- Durable-owner matrix, checkpoint freshness, and action-boundary reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `cross-layer evidence semantics with stale-state risk`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `focused evidence and planning tests cover behavior`

**Specification Coverage:**
- Verdict P0/P1 and PR B: one authoritative owner per fact, stable identity
  references, Git checkpoint binding, PR-head freshness, dirty-state handling,
  and read-only reconciliation. GitHub data arrives as an ephemeral snapshot
  from existing controller capability; this task adds no GitHub client.

**Required Skills:**
- `skill-central-config-layer`
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/plan_preparation.py:prepare_task`, `prepare_plan_lanes`, and Plan digest/checkpoint handling
- Add: `scripts/project_os_runtime/reconciliation.py:LocalEvidence`, `RemotePrEvidence`, `RuntimeEvidence`, `EvidenceSnapshot`, `Contradiction`, `MissingEvidence`, `Eligibility`, and pure `reconcile`
- Modify: `scripts/project_os_runtime/secretary_evidence.py:EvidenceSnapshot`, `build_evidence_snapshot` as Secretary-facing compatibility projection only
- Modify: `scripts/project_os_runtime/secretary_receipts.py:build_live_receipt`, `validate_live_receipt`
- Modify: `scripts/project_os_runtime/secretary_events.py:ReconciliationEvidence`, `reconcile_event_hint`
- Modify: `scripts/herdr_parallel_dispatch.py:run_lane`, `runtime_completion_is_not_acceptance`
- Modify: `docs/operating_system/rules/git-tracked-coordination-rule.md`, `docs/operating_system/runtime/runtime-surfaces.md`, and `docs/operating_system/planning/planning-dispatch.md`
- Add: `tests/test_reconciliation.py`
- Modify: `tests/test_plan_preparation.py`, `tests/test_secretary_evidence.py`, `tests/test_secretary_receipts.py`, `tests/test_secretary_live_runtime.py`, `tests/test_git_lane_lifecycle.py`

**Dependencies:**
- Task 2 topology simplification; no reconciliation code may preserve retired Tura/Switchyard paths.

**Authority:**
- Preauthorized local actions: `edit listed neutral reconciliation/evidence owners/docs/tests and run focused local checks without remote writes or new credential access`
- Stop for: `ambiguous ownership, historical-plan rewrite request, credential/config writes outside repository, or any GitHub mutation`

**Steps:**
- [x] Step 1: Define owner/reference fields as `plan_ref`, `task_id`, `checkpoint_sha`, `lane_head_sha`, and `attempt_id`; keep `plan_revision` as content digest until consumers can derive Plan content from Git.
- [x] Step 2: Add neutral pure `reconciliation.py` composition over Plan/Git local evidence, an ephemeral controller-supplied `RemotePrEvidence` snapshot, and runtime evidence; keep Secretary modules as consumers/adapters, not owners.
- [x] Step 3: Have controller capability retrieve current PR head, checks, reviews, mergeability, and availability once per reconciliation cycle; if unsupported, return `REMOTE_EVIDENCE_UNAVAILABLE` and stop the consequential action.
- [x] Step 4: Revalidate current `git rev-parse HEAD`, dirty state, and runtime ownership before consequential actions; bind dirty verification to explicit input digest or checkpoint.
- [x] Step 5: Represent GitHub outage as `REMOTE_EVIDENCE_UNAVAILABLE`; never infer PASS from stale or missing remote evidence.
- [x] Step 6: Cover lifecycle phases `Execution`, `Verification`, `Acceptance`, `Integration`, and `Retirement` without collapsing them into `completed`.

**Verification:**
- [x] `py -3 -m pytest tests/test_plan_preparation.py tests/test_secretary_evidence.py tests/test_secretary_receipts.py tests/test_secretary_live_runtime.py tests/test_git_lane_lifecycle.py -q`
- Expected: `fresh references reconstruct current state; stale checkpoint, changed PR head, dirty unbound input, unsupported GitHub read, and unavailable GitHub fail closed`.
- [x] `rg -n 'plan_ref|task_id|checkpoint_sha|lane_head_sha|attempt_id|REMOTE_EVIDENCE_UNAVAILABLE' scripts tests docs`
- Expected: `stable identity and remote-unavailable contracts have one canonical owner and no copied status ledger`.

**Exit Criteria:**
- Read-only reconciliation reconstructs current state from authoritative owners,
  rejects stale evidence, and persists nothing.

### Task 4: PR B — Replace copied status with reference-based handoffs

**Purpose:**
- Slim Worker→CoS and CoS→Secretary payloads to stable references, outcome,
  evidence pointers, blocker, and runtime settlement facts.

**Task Function:**
- Handoff contract reduction and lifecycle-boundary enforcement.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `cross-owner contract migration with compatibility risk`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `direct receipt, event, and lifecycle tests provide proof`

**Specification Coverage:**
- Verdict P0/P1 and PR B: reference-only handoffs, receiver-side derivation,
  Worker retirement after TaskResult publication, and no routine Secretary noise.

**Required Skills:**
- `skill-central-config-layer`
- `skill-backend-verification`
- `skill-project-secretary`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/secretary_receipts.py:build_live_receipt`, `validate_live_receipt`
- Modify: `scripts/project_os_runtime/secretary_events.py:EventHint`, `ReconciliationEvidence`, `reconcile_event_hint`
- Modify: `scripts/project_os_runtime/secretary_adapter.py:CommunicationEnvelope`, `ControllerSessionAdapter`
- Modify: `scripts/herdr_parallel_dispatch.py:run_lane`, terminal publication and acceptance boundary
- Modify: `scripts/herdr_main_launcher.py:_discard_deepagents_receipt` and its
  producer-side evidence-release caller
- Modify: `tests/test_secretary_evidence.py`, `tests/test_secretary_receipts.py`, `tests/test_secretary_live_runtime.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_git_lane_lifecycle.py`
- Verify: `.agents/skills/skill-project-secretary/SKILL.md`, `docs/operating_system/planning/planning-dispatch.md`

**Dependencies:**
- Task 3 read-only reconciliation and freshness contract.

**Authority:**
- Preauthorized local actions: `edit listed handoff/receipt/event owners and focused tests; run local contract checks without remote writes`
- Stop for: `loss of replay/idempotency proof, acceptance authority moving to Worker or Secretary, or any durable duplicate status store`

**Steps:**
- [x] Step 1: Reduce Worker→CoS payload to `task_ref`, `candidate_ref`, outcome,
  evidence refs, and blocker; use `candidate_ref.commit_sha` for committed
  work or `candidate_ref.checkpoint_sha` plus `working_tree_digest` for dirty
  work; keep runtime receipt separate with assignment, attempt, execution,
  cleanup, and settlement fields.
- [x] Step 2: Reduce CoS→Secretary payload to accepted cross-workstream
  consequence; suppress routine progress, commits, retries, checks, cleanup,
  and local acceptance with no project-level attention.
- [x] Step 3: Let receiver fetch Plan/Git/GitHub/runtime facts from references;
  upstream mutable status fields never authorize action.
- [x] Step 4: Permit Worker retirement after valid TaskResult publication while
  retaining TaskResult until CoS acceptance and canonical Plan consequence.
  Move the producer-side deletion guard into PR B: the named caller is
  `scripts/herdr_main_launcher.py:_discard_deepagents_receipt`, and it may call
  `release_attempt_evidence(assignment_id, attempt_id, accepted_checkpoint_sha)`
  only after verifying TaskResult consumption, settlement persistence, and the
  accepted checkpoint. A crash or retry between guard evaluation and deletion
  leaves evidence retained and makes the next invocation retry-safe; no
  `rmdir()` may delete a directory containing unconsumed sibling evidence.
- [x] Step 5: Keep Secretary optional and preserve duplicate-delivery replay
  protection across release and compaction.

**Verification:**
- [x] `py -3 -m pytest tests/test_secretary_evidence.py tests/test_secretary_receipts.py tests/test_secretary_live_runtime.py tests/test_herdr_parallel_dispatch.py tests/test_git_lane_lifecycle.py -q`
- Expected: `reference-only handoffs reconstruct state, terminal Worker may retire before CoS decision, pending evidence remains retained, and replay remains duplicate-safe`.
- [x] Include the new `tests/test_reconciliation.py` in PR B focused proof.
- Expected: `read-only reconciliation and reference handoffs pass together before PR B handoff`.
- [x] Contract inspection of `.agents/skills/skill-project-secretary/SKILL.md`
- Expected: `Secretary remains attention/routing only and has no acceptance or task-ledger authority`.

**Exit Criteria:**
- Handoffs carry references rather than copied mutable status; lifecycle phases
  and evidence retention gates are explicit and regression-tested.

### Task 5: PR C — Converge cleanup result and evidence-consumption contracts

**Purpose:**
- Make evidence disposal explicit and resource-specific without adding a
  generic cleanup service.

**Task Function:**
- Lifecycle retention contract and producer-owned cleanup correction.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `backend lifecycle semantics and compatibility migration`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `backend tests are the acceptance proof`

**Specification Coverage:**
- Verdict sections on cleanup and PR C: DeepAgents attempt-directory
  lifecycle, direct MCP cleanup visibility, explicit retention gates, and
  shared result vocabulary.

**Required Skills:**
- `skill-backend-verification`
- `skill-disposable-artifact-cleanup`
- `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/results.py:CLEANUP_STATES`, receipt parser compatibility, result normalization
- Modify: `scripts/project_os_runtime/attempt.py:settlement_decision`, `_normalize_settlement_evidence`, and intended `release_attempt_evidence`
- Modify: `scripts/dcode_project.py:_direct_mcp_runtime`, `_cleanup_stale_direct_mcp_runtimes`, receipt/task-result publication paths
- Modify: `scripts/herdr_main_launcher.py:_discard_deepagents_receipt`, `_read_deepagents_task_result`, result finalization in `_main_body`
- Modify: `scripts/herdr_parallel_dispatch.py:run_lane` cleanup/capture finalization
- Modify: `tests/test_dcode_project.py`, `tests/test_deepagents_result_contract.py`, `tests/test_herdr_main_launcher.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_project_os_runtime.py`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md` retention and cleanup contract

**Dependencies:**
- Task 2 topology simplification; current receipt schema and cleanup-state inventory.

**Authority:**
- Preauthorized local actions: `edit listed runtime contract and tests, add bounded cleanup-result fields, and run direct temporary-directory/process-boundary tests`
- Stop for: `deleting receipt or TaskResult before consumer/acceptance gates are represented, changing lock-path ownership, or introducing a new persistent registry`

**Steps:**
- [x] Step 1: Keep serialized receipt cleanup state `unverified` for current and
  historical records; expose semantic `unresolved` only in derived views and
  never silently change the externally consumed enum.
- [x] Step 2: Make one attempt-directory owner decide removal only after
  lifecycle receipt consumption, TaskResult consumption, settlement persistence,
  and recovery eligibility are all proven. Keep sibling files when any gate is
  incomplete.
- [x] Step 3: Add producer-owned `release_attempt_evidence(assignment_id,
  attempt_id, accepted_checkpoint_sha)`; verify assignment, attempt, Plan,
  repository, and accepted checkpoint binding before marking exact attempt
  evidence releasable.
- [x] Step 4: Replace direct MCP `ignore_errors=True` cleanup with structured
  outcome reporting; failed deletion becomes visible and recoverable without
  changing semantic task success.
- [x] Step 5: Keep role-view cleanup separate from MCP runtime cleanup and keep
  lock release owned by the lock handle, never by stale-path deletion.
- [x] Step 6: Add tests for retained TaskResult, accepted-checkpoint release,
  stale/mismatched release binding, accepted-result cleanup,
  deletion failure, malformed/foreign receipts, and idempotent repeated cleanup.

**Verification:**
- [x] `py -3 -m pytest tests/test_dcode_project.py tests/test_deepagents_result_contract.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py -q`
- Expected: `direct cleanup boundaries emit truthful state; no early evidence deletion; serialized unverified receipts remain readable`.
- [x] Temporary-directory boundary probe through the focused tests
- Expected: `attempt directory disappears only after both evidence consumers release it; MCP deletion failure reports unresolved/preserved rather than false removed`.

**Exit Criteria:**
- Cleanup contract is explicit, owner-local, idempotent, backward-compatible
  for historical receipts, and covered by fresh backend tests.

### Task 6: PR C — Add idempotent Herdr lane retirement and bounded reconciliation

**Purpose:**
- Provide one supported Herdr/launcher retirement operation that verifies exact
  ownership before stopping workers, closing panes/agents, or removing empty
  task-owned sessions.

**Task Function:**
- Runtime resource retirement and startup reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `high-risk process/resource ownership and transport uncertainty`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `direct Herdr boundary tests are required`

**Specification Coverage:**
- Recommendation sections 2, 6–9, 12–13 and PR C: exact ownership,
  idempotency, preservation on uncertainty, task-owned session removal, and
  bounded startup reconciliation.

**Required Skills:**
- `skill-backend-verification`
- `skill-disposable-artifact-cleanup`

**Files And Symbols:**
- Modify: `scripts/herdr_main_launcher.py:_terminate_codex_lane`, new owner-local `retire_lane` operation, ownership/result serialization, CLI integration if required by existing launcher contract
- Modify: `scripts/herdr_parallel_dispatch.py:run_lane`, settlement/reconciliation handoff
- Modify: `scripts/owned_process.py:run_owned_process` only where retirement proof requires existing process-tree evidence
- Modify: `scripts/project_os_runtime/attempt.py:settlement_decision` only where cleanup state must remain occupied until retirement proof
- Modify: `tests/test_herdr_main_launcher.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_owned_process.py`, `tests/test_project_os_runtime.py`
- Verify: `docs/operating_system/procedures/runtime-adapter-procedure.md`, `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- Task 5 cleanup vocabulary and evidence gates.

**Authority:**
- Preauthorized local actions: `edit Herdr owner code/tests and run mocked Herdr/process boundary tests using exact task-owned identities`
- Stop for: `identity mismatch, shared/default session, pane reuse, uncertain process ownership, transport timeout, reconciliation_required=true, or any worktree deletion request`

**Steps:**
- [x] Step 1: Define `retire_lane(bound_attempt)` around existing launcher
  termination/verification helpers; require repository, plan/lane, assignment,
  attempt, session, pane/agent, worktree, and process identity where present.
- [x] Step 2: Freeze further dispatch, capture required evidence, stop only
  task-owned worker/agent descendants, verify process retirement, then remove
  task-owned pane/agent.
- [x] Step 3: Initially retire only positively owned process, agent, and pane.
  Inspect enclosing session but do not delete it unless
  `session_created_by_this_attempt`, `session_is_empty`, and
  `no_external_consumer` are all proven; otherwise preserve it.
- [x] Step 4: Return structured per-resource `removed`, `preserved`, or
  `unresolved` outcomes with reason and recovery-required fields. Repeated calls
  on already-absent owned resources return successful idempotent results.
- [x] Step 5: Add bounded startup reconciliation for exact previously recorded
  resources only; never infer ownership from age, silence, empty output, or a
  stale path.
- [x] Step 6: Keep worktree disposition outside retirement and hand exact
  cleanup authority to `skill-finishing-a-development-branch`.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_owned_process.py tests/test_project_os_runtime.py -q`
- Expected: `settled Codex and DeepAgents lanes retire owned process/agent/pane resources; shared, reused, uncertain, and transport-failed resources are preserved or unresolved; session deletion occurs only with creation provenance; second retirement is idempotent`.
- [x] Mocked Herdr boundary matrix for pane/process/session operations
- Expected: `no blind retry/delete and no cleanup claim without positive retirement evidence`.

**Exit Criteria:**
- Herdr has one owner-local, idempotent retirement operation wired to terminal
  lane settlement and bounded reconciliation, with no generic resource manager.

### Task 7: PR D — Compact Secretary operational retention after canonical consequence

**Purpose:**
- Remove consumed Secretary/session evidence only after canonical workflow
  consequence is recorded, without turning Secretary into workflow truth.

**Task Function:**
- Operational journal retention convergence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `state-retention semantics cross Secretary and acceptance boundaries`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `InMemoryControllerSessionJournal` tests cover current implementation

**Specification Coverage:**
- Verdict Secretary sections and PR D: journal compaction, consumed
  receipt/TaskResult pruning, Git/GitHub reconciliation, and Docket discharge
  handling.

**Required Skills:**
- `skill-project-secretary`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/secretary_adapter.py:ControllerSessionJournal`, `InMemoryControllerSessionJournal`, `release_controller`, `release_session`
- Modify: `tests/test_secretary_adapter.py`, `tests/test_secretary_events.py`, `tests/test_secretary_docket.py`
- Modify: `.agents/skills/skill-project-secretary/SKILL.md`
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `docs/operating_system/templates/secretary-docket.yaml`
- Modify: `scripts/project_os_runtime/secretary_evidence.py:build_evidence_snapshot`
- Verify: `docs/operating_system/governance/repo-governance.md`

**Dependencies:**
- Task 4 handoff/reconciliation contract and Task 6 retirement result.

**Authority:**
- Preauthorized local actions: `edit Secretary journal contract/docs/tests and add only bounded compaction of released, consumed entries`
- Stop for: `any attempt to make Secretary accept work, settle attempts, own Plan/Git truth, or add a persistent Docket/runtime database`

**Steps:**
- [x] Step 1: Keep Secretary as attention/routing surface; document that Plan,
  Git, accepted decisions, source, and tests remain canonical.
- [x] Step 2: Read Plan/Git and relevant GitHub facts on activation, derive
  changed project attention, route one bounded consequence, then release the
  session; do not persist another project-state representation.
- [x] Step 3: Add journal compaction for released controller/session entries
  whose deliveries and activation receipts are no longer needed for replay or
  recovery; retain replay tombstones when duplicate side effects must remain
  prevented.
- [x] Step 4: Mark consumed lifecycle receipts and TaskResult records eligible
  for producer-owned deletion only after acceptance/canonical consequence.
- [x] Step 5: Keep Docket documentation-only behavior because no production
  Docket loader exists; define discharged-entry removal as sole-writer behavior
  and promote durable human/project blockers to GitHub Issues only when an
  existing owner cannot reconstruct them; remove duplicate Docket state after
  promotion and never create one Issue per Plan task.
- [x] Step 6: Add tests proving release does not erase unresolved obligations,
  replay protection survives compaction, and discharged entries are removable
  only after canonical evidence exists.

**Verification:**
- [x] `py -3 -m pytest tests/test_secretary_adapter.py tests/test_secretary_events.py tests/test_secretary_docket.py -q`
- Expected: `released operational state compacts only after replay/recovery gates; Secretary never becomes acceptance or plan authority`.
- [x] Contract inspection of `docs/operating_system/templates/secretary-docket.yaml`
- Expected: `Docket contains only unresolved non-reconstructible attention and has no duplicate plan/attempt lifecycle fields`.

**Exit Criteria:**
- Secretary retention is bounded, replay-safe, canonical-state-independent, and
  does not introduce a new runtime or coordination database.

### Task 8: PR E — Converge canonical policy and Actions concurrency

**Purpose:**
- Establish canonical retention policy, remove obsolete copied status fields,
  and add safe PR-run cancellation without destructive artifact pruning.

**Task Function:**
- Canonical policy and low-risk CI convergence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `policy convergence with explicit deferral of destructive cleanup`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `tracked-file inventory and plan review are sufficient`

**Specification Coverage:**
- Verdict retention sections and PR E: one canonical retention policy, obsolete
  copied-state removal, GitHub Actions concurrency, no cleanup daemon/registry/
  event bus/TTL sweeper, and no copied CI status. Bulk raw-artifact pruning and
  path-based CI filtering are P2 follow-up work.

**Required Skills:**
- `skill-disposable-artifact-cleanup`
- `skill-plan-document-reviewer`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `artifacts/completion-monitoring/`, `artifacts/runtime-observation/`, `artifacts/worker-contract-benchmark/`
- Modify: this migration Plan, deletion/PR evidence, or stable fixture manifest
  when recording retention conclusions; never edit old completed Plans solely for
  this migration
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`, `docs/operating_system/governance/repo-governance.md`, and relevant cleanup skill references
- Modify: `.github/workflows/repo-contracts.yml`, `.github/workflows/runtime-contracts.yml`
- Modify: `docs/operating_system/rules/git-tracked-coordination-rule.md`
- Verify: `docs/superpowers/plans/` historical Tura references remain readable

**Dependencies:**
- Task 7 complete and its evidence is accepted.

**Authority:**
- Preauthorized local actions: `classify tracked artifacts, update current policy/docs, remove obsolete copied status fields, and add workflow concurrency without bulk artifact deletion or path-based suite skipping`
- Stop for: `artifact used by a fixture, benchmark, compatibility test, required acceptance proof, unresolved recovery, or any request to edit historical Plans`

**Steps:**
- [x] Step 1: Classify every tracked runtime artifact as canonical, required
  regression/benchmark fixture, compatibility evidence, required acceptance
  evidence, or redundant raw observation.
- [x] Step 2: Record retention result, limitation, and revision in this
  migration Plan, the deletion commit/PR, or a stable fixture manifest; do not
  edit old completed Plans. If deletion would make one unintelligible, retain
  the artifact.
- [x] Step 3: Do not bulk-delete tracked raw artifacts in this migration;
  produce a P2 candidate list and retain benchmark inputs and fixtures.
- [x] Step 4: Add one canonical Resource Retirement and Retention Contract to
  operating-system docs, referenced by owners without duplicating mechanics.
- [x] Step 5: Add PR workflow concurrency that cancels superseded runs and keep
  GitHub check results canonical without status files. Preserve broad runtime
  suites; do not add path-based skipping in this migration.
- [x] Step 6: Remove copied branch/head, PR, CI, review, and checkpoint fields
  only after Tasks 3–7 consumers read Git/GitHub owners directly; defer optional
  commit trailers, raw artifact pruning, and CI path filtering to P2.
- [x] Step 7: Confirm no forbidden subsystem was added: cleanup daemon, periodic
  sweeper, global resource registry, persistent Herdr database, generic delete
  service, TTL deletion, LLM cleanup agent, heartbeat infrastructure, duplicate
  settlement ledger, or cleanup event bus.

**Verification:**
- [x] `git ls-files artifacts docs/superpowers/plans | sort`
- Expected: `retention decisions are classified without destructive pruning; current Plan or fixture manifest owns each new conclusion`.
- [x] Repository search for forbidden subsystem names and duplicate cleanup contracts
- Expected: `no new central cleanup architecture or second source of truth exists`.

**Exit Criteria:**
- Repository retention policy has one canonical owner per fact, raw evidence is
  bounded, and historical plans are preserved as historical evidence.

### Task 9: Regenerate projections, run final verification, and measure

**Purpose:**
- Reconcile canonical edits with generated adapters, starter-kit outputs,
  focused tests, repository validators, and operational measurements.

**Task Function:**
- Final integration, generated-surface reconciliation, and acceptance evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `broad cross-surface verification with no new implementation`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `repository validators and focused tests are authoritative`

**Specification Coverage:**
- Verdict regression gates, measurement list, final target flow, and all
  implementation outcomes.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-executing-plans`
- `skill-backend-verification`

**Files And Symbols:**
- Modify through generator only: `generated_agents/`, `.agents/rules/`, and starter-kit outputs
- Verify: `scripts/sync_agent_adapters.py`, `scripts/validate_agent_runtime_drift.py`, `scripts/build_starter_kit.py`, `scripts/validate_starter_kit.py`
- Verify: `scripts/validate_repo_contracts.py`, `scripts/validate_planning_lifecycle.py`
- Verify: focused test files named in Tasks 2–8, `tests/test_reconciliation.py`, and full `tests/`
- Verify: `.github/workflows/repo-contracts.yml`, `.github/workflows/runtime-contracts.yml` concurrency and job-scope declarations

**Dependencies:**
- Tasks 1 through 8 complete with accepted task-local proof.

**Authority:**
- Preauthorized local actions: `run generators, validators, focused/full tests, git diff checks, stale-reference searches, and bounded before/after measurement commands`
- Stop for: `generated drift with unclear canonical owner, failed required proof, unrelated diff, external publication, or any request to clean unrelated untracked paths`

**Steps:**
- [x] Step 1: Regenerate all managed adapters from canonical sources with
  `py -3 scripts/sync_agent_adapters.py --all-platforms`.
- [x] Step 2: Run focused tests for Tura/Switchyard removal, cleanup, Herdr,
  Secretary, planning lifecycle, and generated metadata.
- [x] Step 3: Run repository contract, planning, agent-runtime-drift, starter-kit,
  and `git diff --check` validation.
- [x] Step 4: Run final `py -3 scripts/benchmark_completion_monitoring.py --baseline-revision 187f28e492ae1c4726cdd2f7b5a261a2b8b6c695 --repetitions 3 --output artifacts/completion-monitoring/runtime-retirement-final.json` with the same workload and environment as Task 1; compare against the baseline artifact and record only metrics this benchmark or named regression probes can observe.
  manual handoffs/task, manager turns/task, status-reconstruction turns,
  Git commands/transition, GitHub API calls/transition, terminal-to-CoS time,
  terminal-to-retirement time, and any retained-resource/bytes values exposed
  by the benchmark. Mark every unsupported metric, including CI minutes/merged
  PR, stale-evidence incidents, fresh-controller recovery time, and incorrect
  destructive cleanup, `UNAVAILABLE` unless a named probe supplies direct
  evidence. Prove destructive-cleanup safety through the ownership/failure
  regression tests; never infer a measured zero from absent observations.
- [x] Step 5: Execute regression matrix: fresh controller recovers from Git and
  GitHub; old checkpoint dispatch is rejected; changed PR head invalidates old
  review; GitHub outage is unavailable not PASS; terminal Worker with TaskResult
  may retire before CoS; pending TaskResult is retained; committed consequence
  makes consumed evidence prunable; merged PR still requires runtime retirement;
  repeated Herdr retirement is idempotent; shared/default session is preserved;
  MCP deletion failure is unresolved; Secretary replay prevents duplicates; new
  Tura is rejected; historical Tura Plan is readable; active Switchyard routing
  is rejected; obsolete PR runs cancel where configured.
- [x] Step 6: Re-run active-reference search excluding only historical completed
  plans and generated output that is confirmed synchronized; inspect remaining
  matches manually.
- [x] Step 7: Apply `skill-verification-before-completion`; keep Plan status
  `active` until fresh proof returns `verified`, then change status to
  `completed` through the approved coordination transition.

**Verification:**
- [x] `py -3 -m pytest -q`
- Expected: `full suite passes, or every unrelated pre-existing failure is recorded without weakening scope`.
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: `generated adapters have no drift`.
- [x] `py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- Expected: `canonical/generated runtime metadata agrees`.
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- Expected: `repository contracts pass with no active Tura/Switchyard requirement`.
- [x] `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- Expected: `all active Git-tracked plans satisfy current task-ledger and authority contracts`.
- [x] `py -3 scripts/build_starter_kit.py`
- Expected: `starter-kit build succeeds from current manifest`.
- [x] `py -3 scripts/validate_starter_kit.py`
- Expected: `starter-kit output contains no retired active runtime surface`.
- [x] `git diff --check`
- Expected: `no whitespace errors`.
- [x] `python -m json.tool artifacts/completion-monitoring/runtime-retirement-final.json`
- Expected: `final artifact is comparable with Task 1 baseline and records metric availability status`.
- [x] Regression matrix from Task 9 Step 5
- Expected: `all listed stale-reference, lifecycle, ownership, outage, idempotency, retention, and CI-concurrency gates pass`.

**Exit Criteria:**
- Canonical sources, tests, docs, validators, generated adapters, starter-kit
  outputs, runtime proof, and measurements agree; no required task remains
  unresolved; unrelated untracked workspace state remains untouched.

## Execution Evidence

- Worktree: `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\runtime-retirement-migration\project-OS-starter`
- Branch: `codex/runtime-retirement-migration`; base: `187f28e492ae1c4726cdd2f7b5a261a2b8b6c695`
- Review: first independent `review-1` pass found four P1 trust-boundary defects;
  retirement ownership, evidence preservation, release-only compaction, and
  checkpoint/dependency gates were patched; corrected-head review pending.
- Focused proof: `239 passed`; post-fix full suite: `1066 passed, 1 skipped`.
- Contract proof: adapter sync check, runtime drift validation, repository contracts,
  planning lifecycle, starter-kit build/validation, and `git diff --check` passed.
- Runtime proof: final deterministic benchmark outcomes match baseline across all
  cases after review fixes; production cleanup and receipt-publication metrics
  remain unavailable by design because benchmark harness is synthetic.
- Active-reference proof: only negative assertions in tests and historical Plan
  text retain retired names; current source, docs, config, and generated runtime
  surfaces contain no active Tura/Switchyard/project-delegate reference.
- Preserved: drafting checkout untracked `.playwright-mcp/`, `db/`,
  `temp_evidence.json`, and plan; no external runtime path or worktree was deleted.
- Deferred by approved scope: live GitHub mutation/read proof, bulk raw-artifact
  pruning, path-based CI filtering, commit trailers, and final Git disposition.

## Verification

- `py -3 -m pytest -q`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- `py -3 scripts/build_starter_kit.py`
- `py -3 scripts/validate_starter_kit.py`
- `git diff --check`
- `rg -n 'concurrency:|cancel-in-progress|benchmark|runtime' .github/workflows/repo-contracts.yml .github/workflows/runtime-contracts.yml`
- `rg -n -i --glob '!docs/superpowers/plans/**' --glob '!generated_agents/**' 'tura|switchyard|stage_router|project-delegate|TURA_PROVIDER_CONFIG|TURA_PROJECT_ROOT' README.md repo_config scripts tests docs .agents`
- `py -3 scripts/benchmark_completion_monitoring.py --baseline-revision 187f28e492ae1c4726cdd2f7b5a261a2b8b6c695 --repetitions 3 --output artifacts/completion-monitoring/runtime-retirement-final.json`
- Review measurement output using identical before/after workload and environment.

## Completion Criteria

The plan is ready for completion verification when:

1. Switchyard and Tura active surfaces are removed or rejected, while historical
   completed plans remain readable.
2. Codex and DeepAgents paths retain direct focused proof.
3. Git/GitHub reconciliation is read-only, freshness-bound, and has no copied
   durable status owner; reference handoffs preserve lifecycle and replay gates.
4. Cleanup states, receipt retention, Herdr retirement, Secretary compaction,
   GitHub Actions convergence, and artifact retention have explicit owners and
   no central cleanup service.
5. Every task-local verification item has fresh evidence recorded in the plan.
6. Canonical docs/config/skills changed before generated outputs, and generated
   outputs pass drift checks.
7. Full repository validation, regression matrix, and baseline/final measurements
   are complete, with failures, deviations, unavailable metrics, and deferrals
   recorded.
8. Plan lifecycle follows `proposed → active → completed`: lead activates before
   Task 1, keeps status `active` through migration, and changes to `completed`
   only after `skill-verification-before-completion` returns `verified`.
