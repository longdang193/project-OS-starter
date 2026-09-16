---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: herdr-attempt-contracts-and-settlement
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/herdr_attempt_contract.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/herdr_main_launcher.py
  - scripts/dcode_project.py
  - tests/test_herdr_attempt_contract.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_herdr_main_launcher.py
  - tests/test_dcode_project.py
  - tests/test_runtime_tool_resolution_contract.py
  - docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
---

# Herdr Attempt Contracts And Terminal Settlement

## Review Disposition

The attached verdict is correct on five material defects:

1. Canonical grant, capability, digest, and budget rules are missing.
2. The `1800`-second watchdog is not compositional with worker timeout and settlement.
3. Post-terminal report collection can spend the full observation window polling after execution already ended.
4. Timeout collection does not prove who owns a still-live launcher process.
5. Test-only validation helpers bypass production contracts and create competing semantics.

Refinements:

- Grant normalization is not duplicated verbatim: `scripts/herdr_parallel_dispatch.py` imports private launcher code. The fix is still required because private cross-module coupling prevents one contract owner.
- Capability availability belongs to `scripts/dcode_project.py`, using the worker wrapper environment. Dispatcher admission validates selector shape and canonical values; it must not claim worker-environment availability from controller `PATH`.
- Empty capability selection must report the wrapper's actual fallback `git,py`, or Project OS must pass that effective list explicitly. `effective: []` is not truthful when the worker receives `git,py`.
- Keep `MAX_CONCURRENCY = 2`. This update targets correctness and avoidable observation cost, not throughput.
- The previous draft was internally stale: `status: active` conflicted with a completed ledger and “Next action: none”. This draft is `proposed` and contains no completion claim.

## Goal

Make one Herdr attempt truthful and bounded across admission, launcher setup,
worker execution, receipt settlement, output collection, and CoS handoff while
preserving current ownership boundaries.

## Non-Goals

- No scheduler, durable runtime ledger, provider registry, streaming transport, or second supervisor.
- No dispatcher-owned continuation or retry controller.
- No live mutation of deadlines after launch.
- No child-agent token, depth, or spend enforcement.
- No concurrency increase or performance claim without paired accepted-task measurements.

## Execution Approach

- Mode: inline sequential
- Coordination: git-tracked
- Required skills: `skill-chief-of-staff`, `skill-executing-plans`, `skill-backend-verification`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-verification-before-completion`, and `skill-using-git-worktrees`.
- Shared-write rule: Tasks 1–3 serialize because the new contract module and launcher evidence shape are shared by dispatcher, launcher, wrapper, and tests. Task 4 follows implementation.
- Commit policy: no push, merge, branch deletion, worktree removal, capability installation, authentication, or external runtime write. Lane commits remain unauthorized until user grants Git disposition; CoS records task proof in this plan.
- Isolation: use `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter\.worktrees\herdr-attempt-contracts-and-settlement` on branch `codex/herdr-attempt-contracts-and-settlement`; preserve main-checkout `.playwright-mcp/` and `db/`.
- Stop for: contract ambiguity, inability to prove launcher collection ownership, failed cleanup/reaping evidence, stale base, or performance claims without paired measurements.

## Invariants

- Plan and CoS own authority, dependencies, cumulative allowance, continuation, and acceptance.
- Dispatcher owns admission, launcher process collection, and capacity retention until launcher settlement is proven.
- Launcher owns Herdr binding, attempt timing, observation, and result composition.
- `dcode-project` owns worker execution, descendants, cleanup, and lifecycle receipt.
- One pure contract module owns normalization, defaults, digests, constants, and budget arithmetic. It performs no Herdr calls, process inspection, executable lookup, or provider discovery.
- Raw requested values remain available for explanation. Comparisons use canonical effective values and digests.
- Runtime completion remains distinct from CoS acceptance.
- No result claims launcher retirement while a live launcher handle remains without an explicit supported collection owner.
- Plan lifecycle is `proposed -> active -> completed`; implementation starts only after approval, and execution owner records `completed` only after fresh verification.

## Implementation Outcomes

- One pure shared contract module owns canonical grant, capability, digest, default, and budget rules.
- `native` remains capped by the shared `420`-second default, remaining authorized task allowance, and remaining whole-attempt time after settlement reserve.
- Stable grant binding and dynamic effective budget evidence remain separate.
- Dispatcher-owned launcher collection preserves late output and occupied capacity through explicit handoff until reaping is proven.
- Terminal settlement is conditional and preserves uncertainty when Herdr observation cannot correlate exit evidence.
- Worker capability receipts distinguish requested, passed, and validated values through `attempt_id`.

## Task Breakdown

Task 1: Add canonical pure attempt contracts.
Task 2: Integrate dispatcher and launcher timing, evidence, and ownership.
Task 3: Make terminal settlement event-driven and worker capability evidence truthful.
Task 4: Align frozen contracts and verify lifecycle boundaries.

## Coordination State

- Coordination schema: `2`
- Coordination owner: native Codex CoS controller.
- Coordination mode: `plan-bound-execution`.
- Repository: `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter`.
- Base commit: `ff89ae5ec3bf1cfe8846591c755d95a43b85af5b`.
- Branch: `codex/herdr-attempt-contracts-and-settlement`.
- Expected workspace: `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter\.worktrees\herdr-attempt-contracts-and-settlement`.
- Lane branch: `codex/herdr-attempt-contracts-and-settlement`.
- Lane worktree: `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter\.worktrees\herdr-attempt-contracts-and-settlement`.
- Preserved unrelated main-checkout paths: `.playwright-mcp/`, `db/`.
- Next action: none; branch disposition remains unauthorized.
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | shared lane worktree | `deepagents` | none | pure contract module and focused tests | Herdr retry confirmed; `20 passed`; runtime allowlist regression integrated and `143 passed` across Task 1 plus `dcode_project` tests |
| Task 2 | `completed` | shared lane worktree | `deepagents` | Task 1 | dispatcher/launcher timing, binding, collector proof | Task 2A accepted by Herdr evidence-only closeout; Task 2B fixed collector handles and timeout ownership; combined focused suite `327 passed`; `git diff --check` passed |
| Task 3 | `completed` | shared lane worktree | `deepagents` | Task 2 | terminal decision table and wrapper receipt proof | Herdr worker timed out after partial patch; cleanup and descendant termination confirmed. CoS integration retained scoped changes, fixed three test-contract defects, and verified launcher/wrapper/dispatcher suite `331 passed` |
| Task 4 | `completed` | shared lane worktree | `codex` | Tasks 1–3 | docs reconciliation, full verification, runtime proof | Frozen spec and runtime-tool guidance reconciled; focused suite `360 passed`; full suite `638 passed`; repository, planning, template, adapter, Herdr, Git, and test-name checks passed. Success probe completed with worker exit `0`, marker observed, receipt confirmed, cleanup removed, descendants terminated. Timeout probe ended `worker_failed` with receipt confirmed, cleanup removed, descendants terminated, and no unsafe retry. |

### Task 1: Add canonical pure attempt contracts

**Purpose:** Establish one source of truth for grant, capability, digest, and budget semantics.

**Task Function:** Contract design and focused unit implementation.

**Template Profile:**
- Controller-selected: `high`

**Specification Coverage:** Whole-attempt deadline, canonical local capabilities, grant binding, and truthful effective evidence.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`.

**Dependencies:** Current `main` at `ff89ae5ec3bf1cfe8846591c755d95a43b85af5b`; no prior implementation task.

**Authority:**
- Preauthorized local actions: inspect current contract consumers; add `scripts/herdr_attempt_contract.py`; add focused tests; run task-local checks.
- Stop for: an existing canonical owner, runtime/process access required by pure functions, scope expansion, or base/HEAD drift.

**Steps:**

1. Extract pure parsing, normalization, digest, default, and budget rules from current dispatcher/launcher behavior.
2. Add the shared module with explicit raw/requested and canonical/effective outputs.
3. Add boundary tests for casing, defaults, invalid selectors, digest stability, and budget fit.

**Files And Symbols:**

- Add `scripts/herdr_attempt_contract.py`.
- Add `tests/test_herdr_attempt_contract.py`.

**Changes:**

- Add pure functions for runtime-grant normalization, local-capability normalization, effective default resolution, stable grant-binding digest construction, capability digest construction, and whole-attempt budget arithmetic. Leave consumer removal to Tasks 2–3.
- Define `1800` seconds as the whole-attempt ceiling and define the shared `420`-second `native` default used by direct wrapper and Project OS launches. Keep the existing `git,py` wrapper fallback in one named constant.
- Define budget output fields for requested worker seconds, effective worker seconds, setup elapsed seconds, remaining authorized task seconds, remaining attempt seconds, and reserved terminal settlement seconds.
- Resolve `native` as `min(420, remaining authorized task allowance, remaining attempt time - settlement reserve)`. Keep explicit numeric grants strict; reject when they cannot fit. Do not silently expand cumulative task authority.
- Keep stable grant-binding digest inputs limited to canonical requested authority and task identity. Exclude effective worker time, setup elapsed time, remaining time, and settlement deadlines from that digest.
- Compare `lane_id`, `task_sha256`, and `attempt_id` as separate identity fields; stable digest inputs are executor, requested turns, requested wall-clock grant, MCP selection, and child-agent authority.
- Keep all functions deterministic and injectable through numeric arguments. No `time.monotonic()`, `shutil.which()`, subprocess calls, or Herdr calls in this module.

**Proof:**

- `Node` normalizes to `node` before digest comparison.
- Duplicate, malformed, empty, and unsafe capability selectors fail deterministically.
- Empty capability request resolves to the declared wrapper fallback for evidence purposes.
- `native` never exceeds `420`, remaining authorized task allowance, or remaining attempt time after reserve.
- Strict numeric grants reject when setup plus settlement reserve leaves insufficient time.
- Grant and capability digests are stable for equivalent canonical inputs and differ for changed effective inputs.

**Exit:**

- New module has focused tests and no runtime dependencies beyond the standard library.
- Existing modules can import the shared functions without circular imports.

### Task 2: Integrate dispatcher and launcher timing, evidence, and ownership

**Purpose:** Bind dispatcher and launcher behavior to the shared contract and make launcher collection ownership explicit.

**Task Function:** Backend lifecycle integration and failure-path repair.

**Template Profile:**
- Controller-selected: `high`

**Specification Coverage:** Admission, attempt identity, grant evidence, timeout ownership, and no unsafe retry before settlement.

**Required Skills:** `skill-backend-verification`, `skill-systematic-debugging`, `skill-test-driven-development`.

**Dependencies:** Task 1 accepted focused tests and module import.

**Authority:**
- Preauthorized local actions: modify listed dispatcher/launcher symbols and tests; run focused tests; create task-owned collector evidence.
- Stop for: live launcher without reaping or explicit handoff, ownership overlap, scope expansion, or base/HEAD drift.

**Steps:**

1. Redirect dispatcher and launcher imports to the shared contract module.
2. Replace raw dictionary equality with canonical evidence comparison.
3. Resolve and record worker budget immediately before launch.
4. Rework timeout collection so launcher pipes and reaping remain dispatcher-owned until settlement.
5. Run focused dispatcher and launcher regressions before moving to wrapper changes.

**Files And Symbols:**

- Modify `scripts/herdr_parallel_dispatch.py`.
- Modify `scripts/herdr_main_launcher.py`.
- Modify `tests/test_herdr_parallel_dispatch.py`.
- Modify `tests/test_herdr_main_launcher.py`.

**Changes:**

- Replace dispatcher and launcher imports of private `_normalize_runtime_grant()` with the shared contract module.
- Remove dispatcher-local grant and capability digest implementations, `TIMEOUT_OWNER`, and unused pseudo-contract helpers after caller search. Audit and remove only helpers with no production caller: `validate_plan_authority()`, `validate_git_checkpoint()`, `attempt_expired()`, `validate_acceptance()`, `dispatch_launcher_record()`, and `validate_local_capabilities()`.
- Make `_bind_requested_grant()` preserve raw request fields while storing canonical requested authority and effective capability evidence. Forward the effective capability list explicitly for Project OS launches.
- Make `_grant_evidence_matches()` perform two checks: stable requested grant/task binding and effective budget containment. Do not compare dynamic effective budget, elapsed, remaining, or settlement fields through the stable grant digest.
- Resolve the worker timeout immediately before `pane run`, after setup cost is known. Pass the resolved timeout explicitly to `dcode-project`.
- Keep strict numeric grants strict and cap `native` at the shared `420` default plus both authority/deadline limits.
- Record requested, effective, elapsed, remaining-authority, remaining-attempt, and reserve values in a separate attempt-budget evidence object.
- Use one concrete launcher collection mechanism: dispatcher creates `tempfile.mkdtemp(prefix=f"herdr-launcher-{lane_id}-")`, opens `stdout.log`, `stderr.log`, and `handoff.json` before `Popen`, retains the `Popen` handle and file handles in a dispatcher-owned collector, drains output into those files, and parses files after reaping. On collection expiry, a non-daemon dispatcher collector retains the handle, writes `handoff.json` with owner, PID, paths, attempt ID, and capacity state, and returns unresolved evidence with capacity occupied. The collector directory remains until reaping or explicit reconciliation cleanup. Capacity releases only after that collector proves reaping and final evidence; no retry uses the lane before then.
- Keep launcher reaping separate from worker descendant retirement. Do not convert worker cleanup uncertainty into launcher retirement.

**Proof:**

- End-to-end dispatcher tests cover `Node` versus `node`, empty/default capability evidence, mismatched grant digest, and strict-versus-native budget admission.
- Timeout tests prove file-backed streams remain recoverable through settlement, the dispatcher collector owns live launchers after collection expiry, and unresolved capacity remains occupied until ownership is settled.
- A fake live launcher returns only explicit collector handoff metadata; a settled result requires proven reaping.
- A nonzero setup-time test proves dynamic budget evidence is validated for containment, not stable-digest equality.
- Production path test exercises `_admit_lanes() -> run_lane() -> launcher JSON -> grant/capability validation`.

**Exit:**

- Dispatcher owns launcher collection; `dcode-project` remains worker/descendant owner.
- No dispatcher continuation, retry, or acceptance decision appears.

### Task 3: Make terminal settlement event-driven and worker capability evidence truthful

**Purpose:** Stop post-terminal polling waste and make capability evidence reflect the worker environment.

**Task Function:** Observation-path and wrapper boundary implementation.

**Template Profile:**
- Controller-selected: `high`

**Specification Coverage:** Fresh process evidence, bounded terminal settlement, worker capability validation, cleanup receipt.

**Required Skills:** `skill-backend-verification`, `skill-systematic-debugging`, `skill-test-driven-development`.

**Dependencies:** Task 2 accepted evidence shape and timeout ownership.

**Authority:**
- Preauthorized local actions: modify launcher/wrapper observation and capability paths plus tests; run focused tests; run bounded harmless evidence probes.
- Stop for: streaming, registries, scheduler behavior, inability to preserve uncertainty when native Herdr wait lacks correlated exit evidence, or scope/base drift.

**Steps:**

1. Start terminal settlement from first confirmed terminal evidence.
2. Reorder marker wait, process-info, and final pane read operations.
3. Validate shell capabilities against wrapper `PATH` before worker start.
4. Emit actual effective shell allow-list and preserve existing receipt/cleanup behavior.
5. Run focused observation, timeout, capability, and cleanup regressions.

**Files And Symbols:**

- Modify `scripts/herdr_main_launcher.py`.
- Modify `scripts/dcode_project.py`.
- Modify `tests/test_herdr_main_launcher.py`.
- Modify `tests/test_dcode_project.py`.

**Changes:**

- Start one terminal-settlement deadline at first correlated terminal receipt or explicit correlated worker-exit evidence: `min(first_terminal_observation + reserve, whole_attempt_deadline)`. Process absence, silence, or an uncorrelated native wait signal never proves terminal execution.
- Use conditional settlement: complete terminal receipt/report skips marker wait; terminal success with missing marker/report performs one bounded report-settlement wait; terminal failure collects failure evidence immediately; an already observed marker skips repeated waiting; lost process visibility preserves uncertainty.
- After a required wait, collect fresh `pane process-info` and one bounded final `pane read`. Native waits provide observation signals, not atomic marker/process ordering.
- Preserve final receipt, marker, report hash, process state, and observation error when report evidence remains missing. Do not add streaming infrastructure unless this native path still loses reports under a measured live probe.
- Keep direct wrapper invocation and Project OS `native` default at shared `420` seconds. Project OS launches pass resolved effective timeout; explicit numeric grants remain authoritative when admissible.
- Validate requested shell capabilities in `dcode_project.py` against the exact child environment `PATH` and working directory after `_extract_local_capabilities()`. Reject unavailable capabilities before worker creation.
- Extend the existing `--result-file` receipt boundary with an attempt-correlated `capabilities` object containing distinct `requested`, `passed_to_worker`, `validated_available`, `digest`, and `validation_error` fields. Publish validation failure before worker creation when `--result-file` and `--attempt-id` are present; otherwise fail closed on stderr and nonzero exit.
- Launcher reads that receipt by `attempt_id`, copies validated capability evidence into `assignment.local_capabilities`, and dispatcher verifies receipt/assignment evidence against the canonical requested and effective values. Never treat launcher projection alone as worker validation.
- Preserve existing worker process-tree termination, cleanup receipt, and result-file correlation by `attempt_id`.

**Proof:**

- Completion tests cover the conditional settlement table, one terminal deadline, no repeated marker wait, fresh process evidence after required wait, and uncertainty when visibility is lost.
- Receipt-first success with missing report settles within the terminal reserve and does not produce a 1-Hz full-snapshot loop.
- Stale or uncorrelated process evidence cannot establish terminal execution.
- Wrapper tests cover `Node -> node`, absent selection -> `git,py`, explicit unavailable capability under a worker-only `PATH`, and successful capability evidence.
- Receipt tests prove `requested`, `passed_to_worker`, and `validated_available` remain distinct and correlate by `attempt_id` through wrapper -> launcher -> dispatcher.
- Timeout tests continue to prove descendant termination and cleanup facts.

**Exit:**

- Terminal settlement no longer consumes the full unused execution observation window and never assumes atomic Herdr ordering.
- Capability evidence describes what worker received and validated, not merely what launcher requested.

### Task 4: Align frozen contracts and verify real lifecycle boundaries

**Purpose:** Reconcile frozen documentation with implementation and produce fresh integration/runtime proof.

**Task Function:** Contract documentation, regression integration, and final verification.

**Template Profile:**
- Controller-selected: `high`

**Specification Coverage:** Frozen lifecycle ownership, deadline semantics, capability evidence, completion-versus-acceptance separation.

**Required Skills:** `skill-backend-verification`, `skill-verification-before-completion`.

**Dependencies:** Tasks 1–3 accepted; no unresolved launcher ownership or capability evidence defects.

**Authority:**
- Preauthorized local actions: edit named canonical docs/tests; run declared validators and bounded harmless runtime evidence probes; record task evidence in this plan.
- Stop for: external writes, authentication, installation, runtime retirement outside declared attempt, failed required proof, or plan/Git identity mismatch. Execution owner sets `active` before implementation and `completed` only after `verified` evidence.

**Steps:**

1. Reconcile only stale frozen-contract, runtime-grant, and runtime-tool-resolution wording.
2. Detect duplicate launcher test names and rename only confirmed collisions without dropping behavioral coverage; current head contains two `test_deepagents_snapshot_rejects_stale_marker_output()` definitions.
3. Run focused tests, full suite, validators, Herdr checks, and Git checks.
4. Run bounded harmless success and timeout lifecycle traces.
5. Set plan status `active` before implementation; set `completed` only after verification returns `verified`.

**Files And Symbols:**

- Modify `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md` only where the frozen contract contradicts the implementation above.
- Modify `docs/operating_system/tooling/runtime-tool-resolution.md` for worker-environment capability evidence and freshness rules.
- Modify `tests/test_runtime_tool_resolution_contract.py` only for changed documentation contract assertions.
- Modify `tests/test_herdr_parallel_dispatch.py`, `tests/test_herdr_main_launcher.py`, and `tests/test_dcode_project.py` for integrated regression coverage.

**Changes:**

- State that the `1800`-second boundary includes setup, resolved worker time, terminal settlement, output collection, cleanup, and launcher reaping.
- State that strict numeric worker grants block when the whole-attempt budget cannot fit; `native` is capped by shared `420` default, remaining authorized task allowance, and remaining attempt time after reserve.
- State that stable grant binding covers requested authority/task identity while dynamic effective budget is separate evidence.
- State that local capability availability is proven by the worker wrapper environment, while dispatcher evidence compares canonical effective selections.
- State the dispatcher-owned collector and file-backed late-output handoff, including occupied capacity until reaping is proven.
- State that runtime completion is not CoS acceptance and that CoS alone decides continuation after ownership settlement.
- Remove stale wording that implies controller `PATH` proves worker capability availability or that observation expiry/native wait proves retirement.
- Verify duplicate launcher test names are absent and both stale-marker cases remain covered under distinct names.

**Verification:**

- `python -m pytest -q tests/test_herdr_attempt_contract.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_runtime_tool_resolution_contract.py`
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

- Run one bounded harmless lane whose report completes after its planning target but before its enforced maximum, with nonzero setup time and `native` effective budget capped at `420`.
- Capture launcher JSON showing stable grant binding, separate attempt budget, receipt-correlated capability evidence, conditional marker wait, fresh process evidence, receipt, cleanup, and launcher reaping.
- Run one bounded timeout lane and prove file-backed late output, dispatcher collector ownership, occupied capacity, worker cleanup, descendant retirement, and no unsafe retry.
- If continuation is exercised, CoS dispatches it from an accepted checkpoint; dispatcher emits no continuation.
- Do not claim latency or usage improvement without paired accepted-task measurements with identical workload, profile, concurrency, and runtime revision.

**Exit:**

- Focused and full tests pass.
- Contract, planning, Herdr, Git, and runtime boundary checks pass.
- Runtime evidence distinguishes completion, acceptance, launcher reaping, worker retirement, and capability validation.
- Plan moves `proposed -> active` at implementation start and `active -> completed` only after final verification produces fresh evidence.

## Verification

- `python -m pytest -q tests/test_herdr_attempt_contract.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_runtime_tool_resolution_contract.py`
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

## Completion Criteria

1. Tasks 1–3 pass focused proof and Task 4 passes full verification.
2. Plan, specification, runtime-tool guidance, implementation, and tests agree on native budget, stable grant binding, collection ownership, terminal settlement, and capability receipt contracts.
3. No live launcher or worker remains unowned after declared runtime proof; uncertainty remains explicit when retirement is not proven.
4. CoS accepts task evidence independently from Herdr status and records `completed` only after `skill-verification-before-completion` returns `verified`.

## Deferred Follow-Up

Keep executor-fitness reuse, streaming transport, live deadline mutation, Codex
`agent wait` integration, native mutation idempotency, enforceable child
budgets, durable runtime ledgers, concurrency expansion, and performance
qualification outside this update.
