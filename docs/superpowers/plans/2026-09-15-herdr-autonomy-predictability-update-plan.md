---
layer: change
artifact_type: plan
status: active
template_id: implementation-plan
contract_version: "1"
name: herdr-autonomy-predictability-update
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/herdr_parallel_dispatch.py
  - scripts/herdr_main_launcher.py
  - scripts/dcode_project.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_herdr_main_launcher.py
  - tests/test_dcode_project.py
  - tests/test_runtime_tool_resolution_contract.py
  - tests/test_skill_chief_of_staff.py
  - tests/test_native_personal_local_workflow.py
  - docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - .agents/skills/skill-chief-of-staff/SKILL.md
---

# Herdr Autonomy, Deadlines, And Capability Projection Update

## Goal

Make granted DeepAgents autonomy usable and predictable without widening
ownership, MCP access, concurrency, or runtime authority. Separate planning
targets from enforced attempt limits, preserve one timing anchor across launch
and observation, classify runtime completion independently from CoS acceptance,
retain timeout ownership until bounded reaping, and project only validated
task-specific capabilities.

## Implementation Outcomes

### Truthful lifecycle and grant evidence

`reported_completed` with settled execution and cleanup is runtime-resolved even
when `task_result.accepted` is `null`; CoS acceptance remains pending. Missing
grant binding is explicitly unverified and never implicitly matched. Timeout
results preserve partial streams, attempt/process identity, and reconciliation
ownership until the foreground owner proves reaping or records an unresolved
handoff.

### One bounded timing model

Each attempt resolves one effective worker budget before launch. The 1800-second
limit bounds the entire attempt, including launcher startup, worker execution,
receipt settlement, and final cleanup. The worker receives only the remaining
allowance after bounded setup reservation; observation receives only remaining
attempt time plus bounded receipt settlement. Confirmed terminal receipts bypass
execution waiting but retain final process/output probes. `native` is resolved by
the existing wrapper default, not copied into another module.

### CoS-owned continuation and capabilities

The dispatcher returns attempt evidence and settlement only. CoS evaluates
continuation within explicit plan authority and cumulative allowance, then
dispatches a new correlated attempt from an executable checkpoint; no live
deadline mutation or dispatcher retry controller is added. The cumulative
allowance is `cumulative_wall_clock_seconds` in the durable plan task
`Authority`; each attempt charges its allocated `wall_clock_seconds`, and unknown
usage is charged in full. Runtime Tool Resolution supplies validated task-specific
local capabilities, records effective selection, and fails before launch when
executor capability is insufficient. Child delegation remains policy permission
only; no unenforced child count, depth, or spend claim is added.

### Contract and regression proof

The active dispatch specification, CoS policy, planning dispatch, runtime tool
resolution guidance, implementation, and tests agree on the new contracts.
Proof covers late completion, CoS-owned continuation limits, missing grant
evidence, timeout launcher/worker ownership, receipt-first observation,
capability projection, child-agent policy, fresh-worktree checkpoints, and
duplicate test-name removal. No performance claim is made without paired
accepted-task measurements.

## Execution Approach

- Mode: `parallel-capable`
- Coordination: `git-tracked`
- Execution model: `plan-bound-execution via CoS`
- Lead controller: native Codex; sole writer of `Coordination State` and task ledger
- Required skills: `skill-chief-of-staff`, `skill-dispatching-parallel-agents`, `skill-plan-document-reviewer`, `skill-executing-plans`, `skill-backend-verification`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-verification-before-completion`, `skill-using-git-worktrees`
- Isolation: fresh native Git branch/worktree from `origin/main` at the recorded base; preserve current checkout untracked `.playwright-mcp/` and `db/`
- Commit policy: task-local checkpoint commits only after proof; lead integration commit requires fresh verification; no push or merge authority during implementation
- Preauthorized local actions: inspect and edit declared files, create declared isolated worktrees, run declared tests and validators, run bounded harmless runtime proof, and update this plan ledger
- User-approval actions: push, merge, branch deletion, worktree removal, runtime retirement outside declared task-owned proof, capability installation, authentication, external writes, and any allowance beyond plan authority
- Parallel ownership: Task 1 freezes shared contracts and red tests. Stage 1 runs Tasks 2–3 with at most two active lanes. Stage 2 runs Tasks 4–5 with at most two active lanes. Task 2 owns dispatcher lifecycle; Task 3 owns launcher timing; Task 4 owns the complete capability path across dispatcher, launcher, wrapper, tests, and runtime-tool guidance; Task 5 owns CoS/planning policy. No overlapping write paths run concurrently.
- Dependency revision: Tasks 2–5 start from Task 1’s accepted checkpoint revision, not the original base. Task 6 starts only after accepted Task 2–5 checkpoints.
- Sequential fallback: if worktree binding, capability evidence, or parallel independence fails, CoS rebinds affected lane to Codex or executes tasks sequentially without widening scope.

## Coordination State

- Coordination owner: `native Codex lead controller / CoS`
- Coordination mode: `plan-bound-execution`
- Coordination schema: `2`
- Branch: `codex/herdr-autonomy-predictability-update`
- Base commit: `60e11dd12fc186d40e2a0abad8b98984924b5e8f`
- Expected workspace: fresh checkout of `origin/main` at base; current feature checkout, `.playwright-mcp/`, `db/`, and existing stash remain preserved
- Next action: dispatch R2 runtime debugger, then rerun bounded DeepAgents evidence proof before Task 6 acceptance
- Blockers: Task 6 runtime acceptance blocked. Proof B returned `completion_evidence_missing` with worker exit `0`, confirmed cleanup, and pane output later showing report plus exact marker; R1 retry patch did not make this live path observable. Static verification remains green
- Runtime incident R1: closed for its original delayed-receipt unit case. Runtime incident R2: investigate live DeepAgents pane/result observation where wrapper completed at 19.3 seconds but launcher settled at about 61 seconds with `report_present: false` and `marker_present: false`, while later pane read showed `READY_RUNTIME_B`, `COMPLETED`, and the exact marker. Keep worker completion, launcher reaping, report receipt, marker observation, and terminal rendering separate

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | `.worktrees/herdr-autonomy-predictability-update-task1` | `codex` | none | R1 root cause, focused regression, launcher repair, and contract proof | `a407f7d` (cherry-picked from `9a08d34`); 36 focused tests passed; worktree clean; profile `normal` |
| Task 2 | `completed` | `.worktrees/herdr-autonomy-predictability-update-task2` | `codex` | Task 1 checkpoint `a407f7d` | dispatcher behavior and direct helper proof | `ae99cde` (lane `a066875`); 44 dispatcher tests passed; harmless timeout fake passed; diff clean; profile `normal` |
| Task 3 | `completed` | `.worktrees/herdr-autonomy-predictability-update-task3` | `codex` | Task 1 checkpoint `a407f7d` | launcher deadline, receipt, and observation proof | `41f0bec` (lane `0e044ec`); 151 launcher tests passed; Herdr help/schema checks passed; diff clean; profile `normal` |
| Task 4 | `completed` | `.worktrees/herdr-autonomy-predictability-update-task4` | `codex` | Tasks 2–3 checkpoints `ae99cde`, `41f0bec` | capability flow and pre-launch rejection proof | `a617fe9` + `57d26f6` (lane `eab6a4a` + `c6394b5`); 329 owned tests passed; compile and diff checks clean; profile `normal` |
| Task 5 | `completed` | `.worktrees/herdr-autonomy-predictability-update-task5` | `codex` | Tasks 2–3 checkpoints `ae99cde`, `41f0bec` | policy, planning, and generated-surface proof | `9dc586f` (lane `2cef769`); 40 policy tests passed; adapter sync and `--check` passed; profile `normal` |
| Task 6 | `active` | lead workspace | `codex` | Tasks 2–5 checkpoints | integrated verification and runtime trace | Stage 2 checkpoints integrated; static verification passed; runtime acceptance blocked by R2 |

CoS resolves executor and template profile independently through
`docs/operating_system/planning/planning-dispatch.md`. `deepagents` is eligible
only after host-Git/worktree binding, capability checks, and Runtime Grant
validation pass. A failed binding rebinds the task to `codex`; it does not widen
authority. Child delegation is allowed only when Task 5 policy gates pass and the
computed child scope is a strict subset.

## Review Of Source Verdict

The supplied verdict is directionally correct. Findings are grouped by root
cause and ordered by execution risk:

### P1: Runtime completion is conflated with CoS acceptance

`run_lane()` treats `task_result.accepted is None` as unresolved even when the
launcher reports `reported_completed` and execution/cleanup are settled. The
same function treats absent grant evidence as a successful match. These facts
can trigger unnecessary failure handling or accept authority that was never
proven. Task 2 fixes both at the shared classification boundary.

### P1: Timeout ownership can close pipes before reaping

`_finish_timed_out_process()` closes streams after a best-effort zero-time
drain, while `run_lane()` returns without retaining a live process owner. Late
output and same-attempt reconciliation can therefore be lost. The dispatcher
owns the launcher subprocess only; launcher reaping does not prove worker or
descendant retirement. Task 2 keeps collection and launcher reaping bounded,
preserves independently recoverable worker evidence, and names a real
reconciliation owner when settlement remains uncertain.

### P1: Attempt deadline starts too late

`_deepagents_completion_evidence()` creates its observation deadline after
`pane run` returns. Numeric grants can therefore be spent twice, while native
worker and observation defaults describe different budgets. Task 3 resolves one
attempt deadline before launch and derives observation from remaining time.

### P2: Fixed local capability projection blocks valid tasks

`scripts/dcode_project.py` hardcodes `--shell-allow-list git,py` and rejects
capability overrides. Existing Runtime Tool Resolution already owns capability
requirements and evidence, but the local adapter does not consume task-specific
structured selection. Task 4 adds the smallest validated projection path and a
pre-launch executor-capability gate.

### P2: Continuation and child delegation policy is too coarse

Current policy requires retirement and redispatch for every grant change and
defaults child delegation to deny without a bounded implementation-lane rule.
Task 5 separates planning target from enforced maximum, permits settled
continuation only inside cumulative plan authority, and permits child delegation
only for isolated implementation subtasks. No live deadline mutation or
unenforced child budget is advertised.

### P2: Duplicate test names suppress coverage

`tests/test_herdr_main_launcher.py` defines three wait-related test names twice;
later definitions replace earlier ones during module loading. Task 1 renames
the duplicate cases before green verification so coverage remains observable.

### P3: Performance and concurrency expansion remain deferred

The verdict correctly keeps concurrency expansion, streaming, Codex numeric
budgets, and performance claims outside this update. They require paired
accepted-task measurements or a runtime enforcement owner and remain explicit
follow-up work.

### Required plan corrections

The latest review also identified execution hazards in the draft plan. The
dispatcher must return settled attempt evidence, not decide continuation. The
1800-second limit must bound the whole attempt, including setup and settlement.
Capability requirements must use one frozen field and explicit flow across CoS,
admission, launcher, wrapper, and returned evidence. Continuation checkpoints
must be accepted Git commits with report and verification evidence, then used as
fresh-worktree bases. Task 1’s accepted revision is the dependency base for all
implementation lanes, and each wave has at most two active lanes.

## Task Breakdown

### Task 1: Lock updated contract and establish red proof

**Purpose:**
- Convert justified verdict findings into executable acceptance rules before production edits.

**Task Function:**
- Update the active dispatch specification and add focused failing tests; do not change production behavior.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: contract/test work needs ordinary repository context and lifecycle reasoning; no child delegation.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independently verify each red test targets one missing behavior and duplicate names are removed.

**Files And Symbols:**
- Update `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md` sections covering separate budgets, the whole-attempt 1800-second boundary, runtime completion, Runtime Grant evidence, timeout ownership, CoS-owned continuation, fresh-worktree checkpoints, capability flow, and acceptance criteria.
- Freeze structured capability field `local_capabilities` with normalized `selectors`, `purposes`, and `verification_commands`; define flow `CoS requirement → admission → launcher projection → wrapper validation → returned evidence`. A digest proves equality only; it does not prove authority.
- Define durable plan-task `Authority.cumulative_wall_clock_seconds`; charge each attempt’s allocated `wall_clock_seconds` in full when usage is unknown. Do not claim token or child-budget accounting.
- Define checkpoint as an inspected Git commit plus task hash, remaining-work report, and completed verification evidence. Continuation is not final task acceptance.
- Add focused tests in declared test files for lifecycle truth, absent grant evidence, timeout ownership, fake-clock deadline/allowance boundaries, capability flow, pre-launch rejection, policy, checkpoint identity, actual launcher JSON through dispatcher, and duplicate wait-test names. Do not add dispatcher continuation tests; CoS owns that decision.
- R1 exception: because the first Herdr attempt lost completion evidence after worker exit `0`, Task 1 may inspect and patch the shared launcher completion-evidence path in `scripts/herdr_main_launcher.py` and its focused tests. Task 3 retains deadline ownership after Task 1 acceptance; no overlapping launcher edits run concurrently.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-plan-document-reviewer`

**Authority:**
- Preauthorized local actions: edit the active spec, declared test files, and the R1 launcher completion-evidence owner only; run named focused test commands.
- Stop for: any contract change that requires a new result schema, live deadline mutation, durable runtime ledger, or authority beyond this plan.

**Verification:**
- `python -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_runtime_tool_resolution_contract.py tests/test_skill_chief_of_staff.py tests/test_native_personal_local_workflow.py`
- Expected: intended new tests fail for the missing production behavior; no unrelated collection or duplicate-name failure remains. The focused suite uses fake clocks for deadline and allowance boundaries and exercises actual launcher JSON through dispatcher classification.

**Exit Criteria:**
- Updated spec names exact fields, states, ownership, limits, and deferred boundaries; red tests fail only for declared missing behavior.

### Task 2: Correct dispatcher truth and timeout ownership

**Purpose:**
- Fix shared dispatcher classification and timeout handling at `run_lane()` rather than patching callers. Dispatcher returns attempt evidence and settlement; CoS owns continuation.

**Task Function:**
- Implement runtime-resolved versus acceptance-pending classification, strict grant evidence verification, and foreground timeout collection/reaping.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded Python lifecycle implementation with direct subprocess and evidence contracts.

**Files And Symbols:**
- Update `scripts/herdr_parallel_dispatch.py:_grant_evidence_matches` to reject missing preparation/assignment binding when the admitted lane has a Runtime Grant; preserve digest equality and explicit unverified failure state.
- Update `scripts/herdr_parallel_dispatch.py:run_lane` classification so settled `reported_completed` with `accepted: null` sets runtime `unresolved` false, capacity `retired`, and acceptance pending without inventing acceptance.
- Keep resource retirement dependent on explicit execution, descendant, cleanup, and reaping evidence; grant verification status must remain separately visible from CoS acceptance.
- Replace `_finish_timed_out_process` best-effort close behavior with bounded settlement: drain streams while pipes remain open, bound every `communicate()` and `wait()`, and close streams only after launcher reaping. Collection expiry never cancels the worker. Any launcher termination uses an explicit policy and preserves independently recoverable worker/descendant evidence. If worker retirement cannot be proven, return a real reconciliation owner and collection mechanism, `reconciliation_required`, occupied capacity, and no retry-safe state; PID alone is insufficient.
- Keep launcher rebind safe only before launch. An uncertain existing attempt must settle or enter named reconciliation ownership before any continuation or retry decision.
- Preserve sibling evidence and two-lane concurrency; do not add a retry engine or durable runtime ledger.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Authority:**
- Preauthorized local actions: edit `scripts/herdr_parallel_dispatch.py` and `tests/test_herdr_parallel_dispatch.py`; run dispatcher tests and harmless subprocess fakes.
- Stop for: live process handoff without supported ownership, missing structured continuation checkpoint, or any request to widen concurrency.

**Verification:**
- `python -m pytest -q tests/test_herdr_parallel_dispatch.py`
- Expected: runtime completion pending acceptance retires settled capacity; missing grant evidence is unverified; timeout output survives launcher reaping; worker retirement remains separate; uncertain attempts block retry; dispatcher never starts continuation.

**Exit Criteria:**
- Shared dispatcher boundary satisfies all Task 1 red cases and preserves independent sibling results.

### Task 3: Anchor launcher deadlines and reduce observation overhead

**Purpose:**
- Use one effective worker budget from launch through final observation.

**Task Function:**
- Move attempt deadline creation before `pane run`, derive remaining observation time, and preserve bounded receipt settlement.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: launcher lifecycle and clock-boundary change with existing helper coverage.

**Files And Symbols:**
- Update `scripts/herdr_main_launcher.py:_normalize_runtime_grant` and launch setup to resolve one whole-attempt deadline: the 1800-second limit includes setup, worker execution, receipt settlement, and final cleanup. Compute worker allowance only after bounded setup reservation; reject a grant that cannot fit. Resolve `native` through the existing wrapper default; do not copy `420` into launcher code.
- Update `_deepagents_completion_evidence` to receive the attempt start/deadline, use only remaining attempt allowance, and add bounded receipt settlement without restarting the worker budget or mutating a live deadline.
- Update `_deepagents_completion_snapshot` so unresolved attempts wait for the marker before the decisive final process/output probes; confirmed receipts skip blocking execution wait but still perform bounded final probes.
- Reserve bounded command transport and settlement overhead inside the whole-attempt limit. Record deadline, setup elapsed time, effective worker allowance, remaining budget, marker wait state, receipt state, and observation errors in existing evidence sections.
- Preserve attempt correlation, stale-marker rejection, receipt grace of `30` seconds, and no `agent wait` production integration.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Authority:**
- Preauthorized local actions: edit `scripts/herdr_main_launcher.py` and `tests/test_herdr_main_launcher.py`; run launcher unit tests and bounded Herdr help/schema checks.
- Stop for: unsupported runtime deadline mutation, removal of receipt grace, or any change that treats marker/wait success as acceptance.

**Verification:**
- `python -m pytest -q tests/test_herdr_main_launcher.py`
- Expected: a report after the planning target but before enforced maximum completes without a second full observation allowance; fake-clock tests prove setup/worker/settlement accounting; receipt-confirmed attempts skip blocking wait; final probes remain bounded. `agent wait` checks remain informational only.

**Exit Criteria:**
- Launcher emits one attempt-correlated timing model and retains existing lifecycle evidence separation.

### Task 4: Project validated task-specific local capabilities

**Purpose:**
- Replace fixed `git,py` shell exposure with least-privilege capability selection derived from structured task requirements.

**Task Function:**
- Implement the frozen `local_capabilities` path without adding a provider registry or enabling all tools globally. This is Stage 2 and consumes the accepted Stage 1 interfaces.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded adapter/configuration change with security and trust-boundary validation.

**Files And Symbols:**
- Update `scripts/dcode_project.py` wrapper validation to accept only normalized command-basename selectors: lowercase ASCII names matching `[a-z0-9][a-z0-9._+-]*`, with no path separators, whitespace, commas, shell metacharacters, `*`, `..`, environment assignments, or duplicate entries. Standalone wrapper calls retain the safe default and cannot claim CoS authority from an argument or digest.
- Update `scripts/herdr_main_launcher.py` to project frozen `local_capabilities` from the admitted task, and `scripts/herdr_parallel_dispatch.py` to validate admission and carry requested/effective evidence. The path is `CoS requirement → admission → launcher projection → wrapper validation → returned evidence`.
- Update `docs/operating_system/tooling/runtime-tool-resolution.md` to define the structured field, selector normalization, executor availability check, and evidence ownership. This document remains policy; executable normalization stays in launcher/wrapper code.
- Record requested/effective selectors, verification commands, source task hash, and digest in existing launcher evidence; digest equality proves equality only, not authority. Preserve fixed filesystem boundary behavior.
- Reject a lane before launch when required local capability is unavailable to selected executor; do not fall back to global allow-all.
- Keep MCP selection separate: no project MCP trust, no credential projection, no new durable capability registry.

**Required Skills:**
- `skill-central-config-layer`
- `skill-backend-verification`
- `skill-test-driven-development`

**Authority:**
- Preauthorized local actions: edit `scripts/dcode_project.py`, `scripts/herdr_main_launcher.py`, `scripts/herdr_parallel_dispatch.py`, `docs/operating_system/tooling/runtime-tool-resolution.md`, and their owned tests; run adapter and capability contract tests.
- Stop for: raw task-text parsing, unrestricted shell exposure, project MCP trust, credential movement, or installing a new dependency.

**Verification:**
- `python -m pytest -q tests/test_dcode_project.py tests/test_runtime_tool_resolution_contract.py`
- Expected: Node/npm-style verification requirements project only validated selectors; malformed, path-bearing, duplicate, or unavailable selectors block before worker launch; standalone wrapper defaults remain safe; effective selection and source task hash are recorded; MCP defaults remain unchanged.

**Exit Criteria:**
- Capability requirements, executor selection, launch projection, and evidence use one validated path.

### Task 5: Make CoS continuation and child delegation predictable

**Purpose:**
- Update durable policy so useful autonomy is preauthorized without confusing policy permission with runtime enforcement.

**Task Function:**
- Define planning target, enforced maximum, CoS-owned continuation, cumulative task allowance, executable checkpoint, and implementation-lane child delegation rules.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: policy and planning contract change with cross-surface consistency checks.

**Files And Symbols:**
- Update `.agents/skills/skill-chief-of-staff/SKILL.md` Adaptive Runtime Grant, bounded lane autonomy, and returns/retirement sections. CoS owns continuation decisions; dispatcher returns settlement only.
- Update `docs/operating_system/planning/planning-dispatch.md` Runtime Grant Boundary with identical terms: planning target prompts reassessment; enforced maximum controls one attempt; durable `Authority.cumulative_wall_clock_seconds` caps all attempts; each attempt charges allocated `wall_clock_seconds` in full when usage is unknown.
- Record continuation request fields as structured task result evidence: progress, remaining work, requested increase, reason, and checkpoint `{commit, task_sha256, remaining_work, verification}`. CoS continues only after prior attempt settlement and only when cumulative authority remains.
- Require each continuation to create a fresh worktree anchored to the accepted checkpoint commit. Preserve useful partial work without treating checkpoint acceptance as final task acceptance.
- Permit `delegation.child_agents: allow` only for isolated implementation subtasks with strict write-set subset, dependency readiness, and sufficient parent allowance; set `deny` for review, integration, and acceptance lanes. `deny` is mandatory for those lane types.
- State that live deadline mutation, enforceable child count/depth/spend, Codex numeric budgets, and concurrency expansion remain deferred.

**Required Skills:**
- `skill-chief-of-staff`
- `skill-plan-document-reviewer`
- `skill-backend-verification`

**Authority:**
- Preauthorized local actions: edit `.agents/skills/skill-chief-of-staff/SKILL.md`, `docs/operating_system/planning/planning-dispatch.md`, and their owned contract tests; run policy/documentation tests plus `python scripts/sync_agent_adapters.py --all-platforms` followed by its `--check` validation.
- Stop for: policy text that grants authority beyond plan lane authority, claims runtime enforcement without evidence, or generated-surface drift.

**Verification:**
- `python -m pytest -q tests/test_skill_chief_of_staff.py tests/test_native_personal_local_workflow.py`
- Expected: implementation lanes can receive explicit child-agent permission under bounded conditions; review/integration/acceptance lanes are mandatory `deny`; continuation requires settlement, cumulative seconds accounting, accepted checkpoint, and fresh-worktree rebinding.

**Exit Criteria:**
- CoS policy and planning dispatch describe one symmetric, fail-closed autonomy model.

### Task 6: Integrate and verify complete update

**Purpose:**
- Reconcile accepted lanes and prove behavior at direct dispatcher, launcher, adapter, policy, and runtime boundaries.

**Task Function:**
- Codex-only integration, specification reconciliation, fresh verification, and evidence review.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: integration and verification require controller authority; no delegated write lane.

**Files And Symbols:**
- Inspect all declared diffs and accept only Task 1–5 paths.
- Update the active specification only where implementation evidence requires exact wording reconciliation; do not modify historical completed plans.
- Confirm duplicate launcher test names are absent and generated surfaces remain aligned with canonical sources.

**Required Skills:**
- `skill-plan-document-reviewer`
- `skill-backend-verification`
- `skill-verification-before-completion`

**Authority:**
- Preauthorized local actions: integrate accepted task commits, update this plan ledger, run declared verification, and run one bounded harmless runtime proof.
- Stop for: unresolved scope overlap, stale base/HEAD, missing required evidence, failed cleanup/reaping proof, or performance claims without paired measurements.

**Verification:**
- `python -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- `python -m pytest -q tests/test_dcode_project.py tests/test_runtime_tool_resolution_contract.py tests/test_skill_chief_of_staff.py tests/test_native_personal_local_workflow.py`
- `python -m pytest -q`
- `python scripts/validate_repo_contracts.py`
- `python scripts/validate_planning_lifecycle.py --repo-root .`
- `python scripts/validate_template_required_sections.py --repo-root . --require-template-selection`
- `herdr --version`
- `herdr agent wait --help`
- `herdr pane wait-output --help`
- `herdr api schema --json | rg -n -F 'agent.wait'`
- `herdr api schema --json | rg -n -F 'pane.wait_for_output'`
- `git diff --check`
- `git status --short --branch`

**Runtime proof:**
- Run two bounded lanes with one report completing after its planning target but before its enforced maximum and one CoS-dispatched continuation from an accepted checkpoint.
- Capture launcher JSON, grant/capability evidence, attempt IDs, task hash/checkpoint, process identity, partial timeout streams, receipt, cleanup, descendant state, fresh-worktree base, and final capacity.
- Require runtime completion to be distinct from CoS acceptance, matching grant/capability evidence, no dispatcher-created continuation, no duplicate attempt before settlement, no cleanup failure, and no remaining live launcher or worker. If worker retirement is uncertain, require a named reconciliation owner and bounded collection mechanism.
- Treat missing cost telemetry as incomplete performance evidence; do not promote a latency, usage, or concurrency claim.

**Exit Criteria:**
- All required tests, validators, capability checks, and runtime proof pass; `skill-verification-before-completion` returns `verified`; no push, merge, branch deletion, worktree removal, or runtime retirement outside declared task-owned proof occurs without separate authorization.

## Verification

Final verification is serialized by the lead after accepted lane integration:

- focused dispatcher and launcher tests
- focused adapter, capability, and policy tests
- full repository suite
- repository, planning, template, and generated-surface validators
- `python scripts/sync_agent_adapters.py --all-platforms --check` after canonical CoS skill edits
- Herdr version/help/schema checks
- one bounded lifecycle runtime trace with CoS-owned continuation and fresh-worktree checkpoint proof
- final diff and Git state inspection

Backend evidence must prove direct boundary behavior, important failure paths,
final process/cleanup state, timeout ownership, grant binding, attempt identity,
capability selection, continuation limits, and acceptance separation. Runtime
trace proves lifecycle correctness only. Performance remains unqualified unless
paired accepted-task measurements meet an explicitly owned threshold.

## Completion Criteria

1. Planning target and enforced maximum are separate; completion beyond target does not terminate a valid attempt.
2. CoS, not dispatcher, decides continuation only after settled ownership; each new attempt preserves task/checkpoint identity, uses a fresh worktree, and stays within durable `Authority.cumulative_wall_clock_seconds`.
3. One effective whole-attempt deadline includes setup, worker execution, receipt settlement, and cleanup; `native` resolves through the wrapper default.
4. Settled `reported_completed` with `accepted: null` is runtime-resolved and acceptance-pending, not failure.
5. Missing grant binding is explicitly unverified and never implicitly matched.
6. Timeout collection keeps streams available until bounded launcher settlement; launcher reaping and worker retirement remain separate, and uncertainty records a real reconciliation owner and bounded collection mechanism without unsafe retry.
7. Task-specific local capabilities follow `CoS requirement → admission → launcher projection → wrapper validation → returned evidence`; unsupported or malformed selectors block before launch.
8. Child-agent permission remains policy-level, explicit, subset-bounded, and honest about unenforced budgets.
9. Duplicate test names are removed; focused, full, contract, planning, capability, Herdr, and Git checks pass.
10. One bounded harmless runtime trace proves process, receipt, ownership, grant, capability, cleanup, CoS-owned continuation, fresh-worktree checkpoint, and final state evidence.
11. `skill-verification-before-completion` returns `verified` before any status transition to `completed`.

## Deferred Follow-up

Keep executor-fitness reuse, streaming transport, live deadline mutation,
Codex `agent wait` integration, native mutation idempotency, enforceable child
budgets, durable runtime ledgers, concurrency expansion, and performance
qualification outside this plan.
