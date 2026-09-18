---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: runtime-boundary-authority-follow-up
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/project_os_runtime/admission.py
  - scripts/project_os_runtime/capabilities.py
  - scripts/project_os_runtime/lane.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/validate_repo_contracts.py
  - tests/test_project_os_runtime.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_validate_repo_contracts.py
  - tests/test_dcode_project.py
  - tests/test_deploy_agent_runtime.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
  - .agents/skills/skill-deepagents-executing-plans/SKILL.md
  - README.md
  - docs/architecture.md
  - docs/pipeline.md
  - generated_agents/codex/skills/skill-deepagents-executing-plans/SKILL.md
  - generated_agents/claude/skills/skill-deepagents-executing-plans/SKILL.md
  - generated_agents/antigravity/skills/skill-deepagents-executing-plans/SKILL.md
  - generated_exports/project-OS-starter-kit/
---

# Runtime Boundary Authority Follow-up

## Review Basis

Reviewed pasted verdict against exact `origin/main` at
`045c5f05ae35a972b31a488e6435137bd15bbf6c`.

Native source, validator, workflow, and focused test inspection confirm the
material findings. DeepAgents delegation is not required for this review:
current repository evidence directly proves the drift. Use DeepAgents only for
an independent implementation audit if execution encounters unresolved receipt
or compatibility ambiguity.

## Verdict

Verdict is **accepted with corrections**. PR #34 centralized semantic helpers,
but did not make the boundary authoritative end-to-end. The follow-up is one
bounded refactor, not a new orchestration system.

## Justified Findings

### P0 — Ownership SSOT contradicts itself

`docs/operating_system/runtime/runtime-surfaces.md` correctly assigns lifecycle
semantics to `scripts/project_os_runtime/`, but its Policy section still says
Herdr owns top-level lane/session/pane lifecycle. `repo-governance.md` repeats
the stale launcher ownership. `scripts/validate_repo_contracts.py` requires
that stale sentence, so green validation currently protects contradiction.

Preserve: Plan plus Git and CoS own workflow truth and acceptance; Herdr owns
transport, target resolution, and observation; `dcode-project` owns worker
execution, deadlines, descendants, cleanup, receipts, and attempt resources.

Smallest correction: make `runtime-surfaces.md` the implementation-level
ownership SSOT, make secondary docs link to it, and change validation from exact
prose pins to canonical-source and structural checks.

### P0 — Canonical dispatcher boundary stops at admission output

`_admit_lanes()` prepares lanes and records `AdmissionResult`, then immediately
projects them back through `legacy_admission_lists()`. `run_lane()` still accepts
generic mappings and can call `_bind_requested_grant()` again. Dispatcher-local
capability comparators duplicate `project_os_runtime/capabilities.py`.

Preserve: legacy descriptor input and compatibility output at explicit edges;
bounded scheduling, executor pools, Herdr invocation, event delivery, and
existing receipt wire formats.

Smallest correction: normalize raw descriptors once, carry immutable
`PreparedLane` plus canonical `AdmissionResult` through scheduling and launch,
and keep legacy projection only at ingress/serialization boundaries.

### P1 — Capability policy and execution guidance split one contract

`runtime-adapter-procedure.md` describes explicit Herdr MCP selection, then later
says `dcode-project` does not translate Codex `mcp_servers`. The statement is
correct for direct worker authority but unclear beside the approved Herdr
projection. `skill-deepagents-executing-plans` places a direct
`dcode-project --role` example immediately after coordinated Herdr guidance.

Smallest correction: publish one capability table covering task requirements,
default `git,py`, explicit local capabilities, approved MCP selection, worker
PATH checks, task-text authority, and approval/sandbox boundaries. Label direct
execution personal-local only; point coordinated execution to the dispatcher.

### P1 — Deployment contract is stronger than current prose and validator pins

Runtime deployment code and tests now distinguish preflight, no-op, marker-owned
replacement, mixed-root exact updates, per-bundle rollback, partial success, and
external backups. Runtime guidance still needs that contract stated explicitly.
Validator guidance also pins implementation names and exact ownership prose
instead of enforcing AST boundaries, behavior tests, and a small SSOT reference.

Smallest correction: document the observed deployment guarantees, remove stale
implementation/prose requirements, and retain existing deployment behavior and
tests without adding global transactions or cross-bundle rollback.

### P2 — Admission, lifecycle, and acceptance states blur

`README.md` says admission or evidence failure enters `BLOCKED`, while the
architecture workflow and planning docs use `BLOCKED` for multiple layers.
`herdr_parallel_dispatch.py:main()` returns nonzero for rejected lanes and
unresolved executed results, but not for blocked or deferred-only batches.

Smallest correction: define separate namespaces and document CLI behavior:
admission (`ADMITTED|DEFERRED|BLOCKED|REJECTED`), runtime facts
(`settled|unresolved|recovery-required`), and CoS acceptance
(`PASS|FAIL|BLOCKED`). Make rejected, blocked, and unresolved outcomes nonzero;
choose and document whether all-deferred is normal scheduling output or nonzero.

## Goal

Make one executable semantic core, one runtime ownership map, thin operational
guidance, and validators that enforce structure and behavior instead of copied
implementation prose.

## Implementation Outcomes

### Canonical runtime boundary

`PreparedLane`, `AdmissionResult`, capability semantics, budget containment,
settlement, lifecycle, and eligibility have one production owner. Dispatcher
and launcher consume prepared facts without rebinding or reclassifying them.

### Consistent documentation and validation

Runtime ownership, timeout ownership, capability projection, deployment
guarantees, and state namespaces agree across canonical docs, governance,
active spec, skill guidance, README, pipeline, and architecture source.
Validators check maintained sources and AST/behavior contracts without pinning
obsolete prose or compatibility-shim ownership.

### Regression and publication proof

Focused tests prove ingress normalization, immutable lane flow, capability
matching, admission exclusivity, CLI exit semantics, deployment guarantees, and
validator behavior. Generated adapters and starter-kit output are regenerated
only after canonical sources change and pass drift/kit validation.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: dedicated worktree from `origin/main`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed canonical files, add focused tests, run declared validators, regenerate derived adapters/kit, and run bounded local probes
- User-approval actions: DeepAgents execution, push, merge, publication, destructive recovery, and cleanup
- Parallel ownership: none; shared core and docs require ordered integration
- Sequential fallback: Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/runtime-boundary-authority`
- Base commit: `045c5f05ae35a972b31a488e6435137bd15bbf6c`
- Expected workspace: `dedicated clean worktree; unrelated parent artifacts preserved`
- Next action: none; implementation and verification complete
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | dedicated worktree | `codex` | none | ownership/timeout docs and doc checks | docs patched; runtime tests passed; validator stale-pin failure deferred to Task 4 |
| Task 2 | `completed` | dedicated worktree | `codex` | Task 1 | PreparedLane/AdmissionResult end-to-end tests | 68 focused tests passed |
| Task 3 | `completed` | dedicated worktree | `codex` | Task 1 | capability projection and skill guidance tests/checks | 25 contract/workflow tests passed |
| Task 4 | `completed` | dedicated worktree | `codex` | Task 1 | deployment and validator regression suite | 59 validator/deployment tests passed; adapter drift fixed by sync |
| Task 5 | `completed` | dedicated worktree | `codex` | Tasks 2–4 | state namespace and CLI exit tests | 73 focused runtime/dispatcher tests passed |
| Task 6 | `completed` | dedicated worktree | `codex` | Task 5 | adapter, kit, repo, and live-probe evidence | 506 focused tests; 79 repository contract tests; planning lifecycle, repo/config, adapter drift, starter-kit, and `git diff --check` validation passed; deployed launcher and local dispatcher `--help` passed; `dcode-project --help` refused as expected; Herdr exact-pane dry-run returned structured `BLOCKED` because server was unavailable (`server_not_running`); no production DeepAgents run performed |

## Task Breakdown

### Task 1: Canonical ownership and timeout guidance

**Purpose:** Remove contradictory ownership maps and make timeout behavior
executor-specific.

**Template Profile:**
- Controller-selected: `normal`

**Files:**

- `docs/operating_system/runtime/runtime-surfaces.md`
- `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- `docs/operating_system/planning/planning-dispatch.md`
- `docs/operating_system/governance/repo-governance.md`
- `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md`

**Changes:** Assign semantics to `project_os_runtime`, worker execution and
cleanup to `dcode-project`, and Herdr to transport/observation. State that
DeepAgents deadlines terminate and clean up in `dcode-project`; Herdr
observation expiry returns unresolved evidence; CoS reconciles before retry or
worktree cleanup. Replace governance/spec duplicate ownership tables with links
to `runtime-surfaces.md`; preserve completed plans as historical evidence.

**Authority:**
- Preauthorized local actions: edit listed docs and run focused doc checks.
- Stop for: ownership conflict with source/tests or a required decision about timeout/retirement semantics.

### Task 2: PreparedLane and AdmissionResult production boundary

**Purpose:** Make canonical preparation and admission facts the only internal
dispatcher representation.

**Template Profile:**
- Controller-selected: `normal`

**Files:**

- `scripts/project_os_runtime/admission.py`
- `scripts/project_os_runtime/lane.py`
- `scripts/herdr_parallel_dispatch.py`
- `tests/test_project_os_runtime.py`
- `tests/test_herdr_parallel_dispatch.py`

**Changes:** Add pure admission classification helpers to existing
`project_os_runtime/admission.py` for duplicate IDs, dependency state,
worktree/pane/write/resource conflicts, fixed-contract equality, and supplied
capacity facts. Core validates/classifies supplied facts, creates
`AdmissionResult`, and owns state taxonomy and exclusivity; it does not observe
live occupancy, choose execution order, or schedule lanes. Dispatcher observes
occupied slots, owns ordering/concurrency, retains the executor pool, and
supplies capacity facts. Plan/CoS owns dependency truth; runtime classifies the
supplied `dependency_ready` fact. Normalize legacy descriptors once at ingress;
validate one exclusive state per lane; carry immutable `PreparedLane` and
result/reason facts through launch. Remove `_bind_requested_grant()` after all
callers migrate. Keep compatibility projection only at loader/serializer edges
and preserve missing-ID, duplicate-ID, deferred-capacity, and rejection
behavior.

**Proof:** focused tests assert one preparation call, immutable internal lanes,
stable reasons, no duplicate classification, compatibility projection, and
launcher command generation from prepared facts.

**Authority:**
- Preauthorized local actions: edit listed runtime/test files and run focused pytest.
- Stop for: a consumer requiring raw mutable descriptors below ingress or a wire-format change not covered by an explicit compatibility decision.

### Task 3: One capability policy and DeepAgents guidance

**Purpose:** Remove contradictory capability wording without moving authority
across layers.

**Template Profile:**
- Controller-selected: `normal`

**Files:**

- `scripts/project_os_runtime/capabilities.py`
- `scripts/herdr_parallel_dispatch.py`
- `tests/test_project_os_runtime.py`
  - `tests/test_herdr_parallel_dispatch.py`
  - `docs/operating_system/tooling/runtime-tool-resolution.md`
  - `docs/operating_system/procedures/runtime-adapter-procedure.md`
  - `.agents/skills/skill-deepagents-executing-plans/SKILL.md`
  - `tests/test_runtime_tool_resolution_contract.py`
  - `tests/test_skill_deepagents_executing_plans.py`
  - `tests/test_native_personal_local_workflow.py`

**Changes:** Keep complete capability-policy SSOT in
`docs/operating_system/tooling/runtime-tool-resolution.md`, including task
requirements, default `git,py`, explicit local capabilities, approved MCP
selection, worker PATH checks, task-text authority, and approval/sandbox
boundaries. Make `runtime-adapter-procedure.md` an operational projection that
references that SSOT, and make `skill-deepagents-executing-plans` method
guidance that references it. Reuse the shared capability matcher for
preparation and worker evidence. Keep normalization/defaults in
`capabilities.py`, executable PATH availability in `dcode-project`, explicit
MCP selection in Herdr projection, and task text out of authority. Mark direct
`dcode-project` examples personal-local only; coordinated work references the
canonical dispatcher procedure.

**Proof:** capability tests cover empty/default, explicit selection, mismatch,
worker-unavailable, digest, and validated-availability cases. Contract tests
prove the tooling document owns the complete policy, secondary surfaces
reference that SSOT, and no contradictory capability claims remain; do not rely
on one textual occurrence.

**Authority:**
- Preauthorized local actions: edit listed runtime/docs/test files and run focused capability tests.
- Stop for: an MCP or PATH behavior change that requires provider credentials or an external runtime decision.

### Task 4: Deployment contract and validator simplification

**Purpose:** Align prose and structural checks with deployed behavior.

**Template Profile:**
- Controller-selected: `normal`

**Files:**

- `scripts/validate_repo_contracts.py`
- `tests/test_validate_repo_contracts.py`
- `tests/test_deploy_agent_runtime.py`
- `docs/operating_system/runtime/runtime-surfaces.md`

**Changes:** State preflight/no-op, marker-owned replacement, mixed-root exact
updates, per-bundle rollback, retained partial success, and external backups.
Remove exact requirements for `ADMISSION_RESULTS` ownership and the stale Herdr
lifecycle sentence. Retain AST dependency checks, behavior tests, canonical
runtime-source existence, and maintained secondary-document references.

**Proof:** validator tests reject forbidden imports and missing canonical
references, accept the corrected ownership text, and deployment tests retain
backup, rollback, mixed-root, and stale-scan coverage.

**Authority:**
- Preauthorized local actions: edit listed validator/docs/tests and run declared validation commands.
- Stop for: any deployment behavior regression or validator relaxation that removes structural/behavior enforcement rather than only stale prose pins.

### Task 5: State namespaces and dispatcher CLI contract

**Purpose:** Make admission, lifecycle, and CoS acceptance states distinct and
observable.

**Template Profile:**
- Controller-selected: `normal`

**Files:**

- `scripts/herdr_parallel_dispatch.py`
- `tests/test_herdr_parallel_dispatch.py`
- `README.md`
  - `docs/architecture.md`
  - `docs/pipeline.md`

**Changes:** Define the three state namespaces in canonical prose. Update
dispatcher `main()` so rejected, blocked, and unresolved results return
nonzero. Treat all-deferred batches as normal scheduling output with exit `0`
and document that choice; no admitted execution plus unresolved result remains
nonzero. Keep guided-story workflow and architecture HTML/SVG regeneration out
of this plan; those generated artifacts remain untouched until a separate
Archify task provides an executable delivery path.

**Proof:** subprocess or direct-main tests cover admitted success, rejected,
blocked, deferred-only, and unresolved execution outcomes; workflow semantic
checks and README/pipeline references use the separate namespaces.

**Authority:**
- Preauthorized local actions: edit listed CLI/docs/test files and run bounded local verification.
- Stop for: an unresolved product decision about deferred exit semantics.

### Task 6: Derived surfaces and final verification

**Purpose:** Prove canonical changes, generated surfaces, and kit output remain
aligned.

**Template Profile:**
- Controller-selected: `normal`

**Files:**

- generated adapter outputs selected by `scripts/sync_agent_adapters.py`
- `generated_exports/project-OS-starter-kit/`

**Changes:** Run adapter sync after canonical sources change; never hand-edit
generated mirrors. Keep starter kit derived from `repo_config/starter-kit-manifest.json`
and build it at `generated_exports/project-OS-starter-kit`. Generated paths are
derived targets selected by those canonical sync/build commands; do not hand-edit
them.

**Proof:** run focused suites, full repo contract/config validation, adapter
drift check, starter-kit build/validation, `git diff --check`, deployed-layout
help probes, and conditional live Herdr proof. Record exact outputs before
completion.

**Authority:**
- Preauthorized local actions: regenerate declared derived surfaces and run declared local verification.
- Stop for: generated drift, kit forbidden-path failure, or unrelated dirty-state mutation. If Herdr is available and its live probe fails, stop; if unavailable, record unavailable evidence and do not run production DeepAgents.

**Completion record:**
- Generated adapters synced from canonical sources; adapter drift check passed.
- Starter kit built and validated at `generated_exports/project-OS-starter-kit`.
- Final focused suite passed: `506 passed`.
- Repository contract suite passed: `79 passed`.
- Planning lifecycle, repository/config, starter-kit, adapter-drift, and `git diff --check` validation passed.
- Deployed launcher `--help` and local dispatcher `--help` with `PYTHONPATH` cleared passed.
- `dcode-project --help` produced expected refusal behavior.
- Herdr exact-pane dry-run returned structured `BLOCKED` with `server_not_running`; Herdr live service was unavailable, so no production or credentialed DeepAgents run occurred.

## Verification

Run after each relevant task:

```powershell
py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_herdr_parallel_dispatch.py tests/test_validate_repo_contracts.py
```

Run final proof:

```powershell
py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_deepagents_result_contract.py tests/test_herdr_attempt_contract.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_deploy_agent_runtime.py tests/test_validate_repo_contracts.py tests/test_starter_kit_generation.py
py -3 scripts/validate_repo_contracts.py --repo-root .
py -3 scripts/validate_repo_config.py --repo-root .
py -3 scripts/sync_agent_adapters.py --all-platforms --check
py -3 scripts/build_starter_kit.py --repo-root . --output-root generated_exports
py -3 scripts/validate_starter_kit.py --repo-root . --output-root generated_exports
git diff --check
```

If Herdr is available, live proof must use a temporary isolated Herdr workspace:
launcher dry-run with exact pane target, deployed launcher and dispatcher
`--help` with `PYTHONPATH` cleared, and documented `dcode-project` refusal
behavior. If Herdr is unavailable, record that limitation; do not run
production or credentialed DeepAgents. Deployed-layout probes and local tests
remain required in either case.

## Completion Criteria

- `runtime-surfaces.md` is the only detailed implementation ownership map.
- No active validator requires stale Herdr lifecycle prose or shim ownership.
- Dispatcher internal paths use prepared lanes, canonical admission facts, and
  shared capability semantics exactly once.
- Capability, timeout, deployment, and state documentation agree with code.
- Admission, lifecycle, and acceptance state tests pass, including CLI exit
  behavior for blocked, deferred, rejected, and unresolved cases.
- Generated adapters are current; starter-kit build and validation pass.
- Focused tests, repository validators, config validation, drift checks, and
  deployed-layout probes pass with no unrelated files changed. Herdr live proof
  passes when Herdr is available; otherwise its unavailability is recorded and
  no production DeepAgents run is performed.
- Completed plans remain untouched as historical evidence.

## Non-Goals

- No new scheduler, durable registry, transaction log, global rollback system,
  runtime service, or protocol.
- No removal of `herdr_attempt_contract.py` or `deepagents_result_contract.py`
  without consumer proof; retain them as compatibility surfaces.
- No change to raw worker receipt wire format, Herdr transport semantics,
  provider credentials, MCP approval policy, or starter-kit publication policy.
- No cleanup of unrelated parent artifacts, databases, browser state, or
  existing generated outputs outside the declared kit path.
