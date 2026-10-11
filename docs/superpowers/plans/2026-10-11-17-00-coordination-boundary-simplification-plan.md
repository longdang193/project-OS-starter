---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: coordination-boundary-simplification
targets:
  - .agents/skills/skill-project-secretary/SKILL.md
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - scripts/secretary_live_runtime.py
  - scripts/secretary_evidence_adapter.py
  - scripts/benchmark_secretary_architecture.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_evidence_adapter.py
  - tests/test_secretary_benchmark.py
  - tests/test_skill_project_secretary.py
  - tests/test_skill_chief_of_staff.py
  - tests/test_native_personal_local_workflow.py
  - .github/workflows/runtime-contracts.yml
---

# Coordination Boundary Simplification

## Verdict Review

The supplied verdict is implementation-ready after these justified corrections:

1. **Separate usefulness from proof completeness.** A launcher exit, idle observation, or cleanup result does not prove a useful Secretary result. A normal invocation requires an attributable final response whose payload or reference is retrievable and whose identity is unambiguous. Missing observability must not erase a correlated result.
2. **Simplify CoS as a semantic role, not another CLI.** Direct CoS reasoning and recommendation run in the active lead session without requiring a plan or Herdr. Governed mutation, parallel work, acceptance, retry, settlement, and integration still use the existing plan/runtime gates. No `cos run` launcher is added.
3. **Keep normal Secretary `run` read-only for repository implementation.** A request such as “fix this” routes from Secretary to CoS and an authorized Worker or governed execution path; Secretary itself does not edit the repository.
4. **Separate runtime paths structurally.** Add `run_normal` and preserve a strict `run_probe` path, with `smoke` only as a compatibility alias to `probe`; do not grow one flag-heavy `run_smoke` function.
5. **Fix the PR #80 attribution conflict independently.** A matching provider session must not promote run/attempt economics when launcher and provider identifiers contradict each other or when no authoritative run/attempt relationship exists. This is a reporting defect, not an execution gate.
6. **Do not create a second lifecycle system.** Reuse existing launcher execution, task-result, cleanup, settlement, acceptance, and reconciliation facts. Add only a thin value normalization boundary where the current Secretary wrapper lacks a stable invocation result.

The plan therefore broadens the next change from a Secretary-only invocation patch to a coordination-boundary simplification while preserving proven runtime safety and durable-truth rules.

## Goal

Make Secretary and CoS directly usable for ordinary attention, analysis, and recommendation without universal plan, Herdr, provider, or receipt preflight, while keeping stronger assurance mandatory for the specific action that needs it.

The target rule is:

> Strict where safety depends on the fact; flexible where variability is harmless; optional where the fact is diagnostic only.

The implementation must preserve the ownership model:

- Secretary decides **where attention belongs**.
- CoS decides **what the workstream should do next**.
- Workers decide **how to execute their bounded task**.
- Middleware handles **how an authorized action reaches a runtime and how its result comes back**.
- Runtime owners handle **process and resource safety**.
- Git, Plan, and GitHub preserve **durable truth**.
- Reporting answers **what can be observed and measured**.

No layer may impersonate another layer.

## Implementation Outcomes

### Minimal semantic coordination contracts

`skill-project-secretary` and `skill-chief-of-staff` describe directly usable semantic roles with symmetric input/output contracts.

Secretary consumes an objective, project context, available evidence, and constraints, then returns status, attention/result, affected workstreams, evidence references, and a next action. CoS consumes an objective, workstream context, available evidence, and constraints, then returns status, decision/result, evidence references, and a next action. Direct CoS is an in-session semantic role for analysis, recommendation, routing, continuation, and escalation; it is not a new executable.

Neither contract requires a full runtime receipt, provider telemetry, plan binding, native Codex, Herdr, or multi-lane topology for read-only attention or recommendation. The former advisory exact-commit-only and PR/research/specification/incident prohibitions are removed as blanket restrictions; the requested action determines assurance. Plan binding, runtime grants, settlement proof, acceptance proof, and GitHub policy remain required only when the selected next action consumes them. Governed multi-writer execution still requires an approved plan and isolated ownership.

### Thin invocation boundary

The existing Secretary live wrapper gains a normal invocation path separate from the strict capability-probe path.

Normal invocation returns a small correlated result with independent facts:

```text
invocation_id
execution: completed | failed | interrupted | unknown
result: reported | unavailable | ambiguous
resource: settled | quarantined | unresolved
observability: available | unavailable | inconclusive
started_at
finished_at
evidence_refs
  reporting: optional provider evidence and attribution
```

`invocation_id` is created and owned by invocation middleware for this direct call only. It is ephemeral correlation, is not an `attempt_id` or plan run ID, and grants no workflow authority. The normal path does not require the strict Secretary receipt or query the 9router database. Existing strict behavior remains available as `probe`, with `smoke` as a compatibility alias.

A correlated final task result is required before returning `result: reported`, and the final payload or a retrievable reference must be available with unambiguous correlation. A status flag without accessible semantic content is not enough. Launcher exit code, pane idle state, character counts, or cleanup alone must never be promoted into semantic completion. `execution: failed` with `result: reported` is valid when a correlated failure result was received; result availability is independent from execution success.

### Progressive assurance

Existing checks become mandatory at the consuming action rather than at every coordination entry point:

| Requested action | Required assurance |
| --- | --- |
| Secretary status or prioritization | Canonical project/workstream evidence readable |
| CoS blocker analysis or recommendation | Relevant workstream evidence |
| One read-only Worker | Runtime delivery and bounded-task correlation |
| One mutating Worker | Scope, ownership, and cleanup mechanism |
| Parallel writers | Approved plan, dependencies, isolated ownership |
| Retry uncertain work | Prior ownership and settlement proof |
| Accept candidate | Candidate identity, criteria, and verification |
| Reuse runtime resource | Settlement proof |
| Merge | GitHub checks, review policy, and integration evidence |
| Claim token/cost economics | Reporting attribution evidence |

Missing optional receipts, provider telemetry, token data, or cost data do not block ordinary coordination.

### Reporting stays a sidecar

Provider observation remains read-only and independently classified. The normal Secretary/CoS invocation path performs zero provider database queries unless reporting is explicitly requested. Missing or ambiguous provider evidence only limits attribution and economics claims.

The PR #80 attribution issue is corrected so run/attempt promotion requires:

- a valid structured receipt;
- an exact provider-session bridge;
- complete provider coverage;
- a conflict-free launcher/provider identifier join; and
- an authoritative run or attempt relationship.

A session match without an authoritative run/attempt relationship remains session/request attribution only and never becomes run/attempt attribution merely because a receipt binds the same session; session reuse is possible. It never becomes an execution blocker. The adapter's compatibility `readiness` field is probe-only (`probe_readiness` semantics), not a generic Secretary state; if compatible, expose `probe_readiness` as the principal field and retain `readiness` only as a deprecated projection.

### Safety remains narrow and strong

The change preserves worktree identity, write-set isolation, dependency proof, attempt correlation, ambiguous-delivery protection, cancellation, cleanup or quarantine, settlement before retry/reuse, immutable candidate identity, CoS acceptance, evidence-release safety, and Git/GitHub integration proof.

It does not add a new orchestration service, persistence layer, event bus, WorkerResult v2, Secretary ledger, CoS-to-CoS mesh, lifecycle taxonomy, or upstream 9router mutation.

## Target Architecture

```text
                         User
                           │
              ┌────────────┴────────────┐
              │                         │
          Secretary                    CoS
      project attention         workstream decisions
              │                         │
              └──────────┬──────────────┘
                         ▼
                 Execution Selection
             direct / bounded / governed
                         │
                         ▼
                  Thin Middleware
             binding / delivery / result
             timeout / cancel / cleanup
                         │
                         ▼
                 Runtime / Workers
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
       Git / Plan               Reporting sidecar
    durable truth              receipts / telemetry
    acceptance proof           economics / probes
```

### Ownership table

| Layer | Owns | Must not own |
| --- | --- | --- |
| User/API | Intent and requested outcome | Runtime mechanics |
| Secretary | Project attention, priority, cross-workstream coordination, user synthesis | Acceptance, cleanup, telemetry |
| CoS | Workstream analysis, assignment, continuation, escalation, semantic acceptance | Project-wide priority, provider economics |
| Execution selection | Direct vs bounded vs governed choice | Acceptance |
| Middleware/runtime adapter | Binding, delivery, result correlation, timeout/cancel, resource handling, normalization | Project reasoning, acceptance, economics |
| Worker/runtime owner | Execution, task-local evidence, process/descendant lifecycle | Canonical project truth |
| Git/Plan/GitHub | Durable work, dependencies, accepted consequences, integration policy | Process liveness |
| Reporting/probes | Receipts, telemetry, attribution, economics, benchmarks | Ordinary coordination admission |

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`, `skill-using-git-worktrees`
- Isolation: `required clean task-specific worktree from 874924c5a21952e200d3a4ed9a70738584da3813`; the current dirty checkout remains untouched
- Commit policy: `proof-gated local checkpoint commits` after Task 1, Tasks 2–4, Task 5, and Task 6; push, PR creation/update, and merge remain user-approval actions
- Preauthorized local actions: edit listed canonical sources and tests, regenerate tracked adapters from canonical sources, run focused and final local verification, run bounded read-only capability probes, and preserve probe artifacts outside the repository
- User-approval actions: create or delete worktrees, commit, push, open or update a PR, merge, publish generated exports, destructive cleanup, and external runtime writes
- Parallel ownership: `none`; shared skill, runtime, and documentation surfaces require one sequential owner
- Sequential fallback: baseline clean worktree, fix reporting attribution, define semantic contracts, implement normal invocation, detach reporting, update CoS/Secretary guidance, add variability benchmark, regenerate adapters, run final proof

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/coordination-boundary-simplification`
- Base commit: `874924c5a21952e200d3a4ed9a70738584da3813`
- Expected workspace: `clean isolated worktree from the PR #80 merge commit`; the current `main` checkout contains unrelated preserved changes and is not an execution workspace
- Next action: none; implementation and final proof complete
- Blockers: none

## Execution Evidence

- Normal live invocation returned `result.state=reported` with a correlated Herdr reference and no provider telemetry field; cleanup remained uncertain, so `resource.state=quarantined` and reuse stayed blocked.
- The bounded strict probe completed transport and workspace cleanup but remained `BLOCKED_CAPABILITY` because `secretary_runtime_receipt` was unavailable; provider observation was inconclusive with no usage rows. This is optional probe evidence, not a normal coordination blocker.
- A transient final-read timeout was reproduced and fixed by retrying terminal observations with errors; an interruption race was fixed by treating an already-retired Herdr agent as removed after verification.

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated | `codex` | none | focused contract tests and source review | `51 passed` in `tests/test_skill_project_secretary.py`, `tests/test_skill_chief_of_staff.py`, and `tests/test_native_personal_local_workflow.py`; checkpoint commit |
| Task 2 | `completed` | isolated | `codex` | Task 1 | `12 passed` in `tests/test_secretary_evidence_adapter.py` | conflicting run/attempt identifiers remain unpromoted; checkpoint commit |
| Task 3 | `completed` | isolated | `codex` | Task 1 | normal invocation result and safety tests | `46 passed` runtime tests; normal result normalization covers unavailable, reported failure, ambiguity, and cleanup quarantine |
| Task 4 | `completed` | isolated | `codex` | Tasks 2-3 | run/probe separation and zero normal-path provider queries | `69 passed` runtime, adapter, and benchmark tests; `run` has no provider observer; `probe_readiness` is probe-only |
| Task 5 | `completed` | isolated | `codex` | Tasks 1-4 | variability benchmark and scenario tests | six paired deterministic scenarios; `py -B scripts/benchmark_secretary_architecture.py 1` emits no live/latency claims |
| Task 6 | `completed` | isolated | `codex` | Tasks 1-5 | generated-surface drift and full repository proof | `352 passed` focused; `1210 passed, 2 skipped` full suite; planning, repo-contract, adapter-drift, and diff checks passed |

## Task Breakdown

### Task 1: Establish semantic coordination contracts

**Purpose:**
- Narrow Secretary and CoS entry contracts to semantic coordination and apply progressive assurance without weakening governed execution.

**Task Function:**
- Reconcile canonical role contracts, planning dispatch, and runtime guidance against the target ownership architecture.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared canonical documentation and test ownership must remain sequential.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused source and contract tests are sufficient for this documentation-and-contract task.

**Specification Coverage:**
- Secretary chooses project attention; CoS chooses the next workstream action; Workers choose implementation details; neither coordination role owns runtime, reporting, or durable truth.
- Direct Secretary and direct/advisory CoS reasoning, recommendation, routing, continuation, and escalation do not require a complete plan-bound execution topology, native Codex, or Herdr.
- CoS reasoning/coordination is distinct from CoS-governed execution. A plan is not required to reason or recommend; an approved plan remains required before governed multi-writer or other plan-bound mutation.
- CoS remains an in-session semantic role in the active lead session for this delivery; do not add a `cos run` executable or a second middleware surface.
- Remove blanket exclusions for PR, release, incident, specification, research, and cross-repository advisory analysis. Apply assurance based on the selected action instead.
- Strong assurance is required only for the action that consumes it.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-project-secretary/SKILL.md`
- Inspect: `.agents/skills/skill-chief-of-staff/SKILL.md`
- Inspect: `docs/operating_system/planning/planning-dispatch.md`
- Inspect: `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Modify: `.agents/skills/skill-project-secretary/SKILL.md`
- Modify: `.agents/skills/skill-chief-of-staff/SKILL.md`
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: `tests/test_skill_project_secretary.py`, `tests/test_skill_chief_of_staff.py`, `tests/test_native_personal_local_workflow.py`

**Dependencies:**
- PR #80 is merged at base commit `874924c5a21952e200d3a4ed9a70738584da3813`.

**Authority:**
- Preauthorized local actions: modify only the listed canonical skills, planning/runtime docs, and their focused tests; run local contract checks.
- Stop for: any request to change acceptance, reconciliation, Git/Plan state, generated output ownership, or runtime lifecycle semantics beyond the stated progressive-assurance rules.

**Steps:**
- [x] Step 1: Replace universal Secretary/CoS preflight language with explicit direct/advisory versus plan-bound execution modes.
- [x] Step 2: Add the progressive-assurance matrix and the symmetric Secretary/CoS semantic input/output contracts.
- [x] Step 3: State that receipts, telemetry, idle state, and provider evidence are supporting facts, not ordinary coordination admission or acceptance authority; state that normal Secretary `run` is read-only for repository implementation and routes implementation requests to CoS and an authorized execution path.
- [x] Step 4: Add focused assertions for direct Secretary use, direct/advisory CoS use without a plan or Herdr, the removal of blanket advisory exclusions, and preservation of plan-bound safety rules.

**Verification:**
- [x] `py -B -m pytest tests/test_skill_project_secretary.py tests/test_skill_chief_of_staff.py tests/test_native_personal_local_workflow.py -q`
- Expected: existing safety assertions remain green and new direct/advisory contract assertions pass.

**Exit Criteria:**
- Canonical role and planning documents express the target architecture without requiring a new lifecycle state machine or ledger.

### Task 2: Correct provider attribution promotion

**Purpose:**
- Prevent contradictory launcher/provider identifiers from being promoted to run- or attempt-attributed economics.

**Task Function:**
- Patch the existing reporting projection boundary and prove the conflict cases with focused regression tests.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small shared reporting fix with clear ownership and low execution ambiguity.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused adapter tests and direct source inspection.

**Specification Coverage:**
- Session attribution remains reportable when proven.
- Run/attempt attribution requires a conflict-free join, exact session bridge, complete coverage, and validated receipt.
- Reporting classification never becomes execution admission or acceptance.

**Required Skills:**
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/secretary_evidence_adapter.py:_join_provider_usage`
- Inspect: `scripts/secretary_evidence_adapter.py:_provider_usage`
- Modify: `scripts/secretary_evidence_adapter.py:_provider_usage`
- Verify: `tests/test_secretary_evidence_adapter.py`

**Dependencies:**
- Task 1 defines the lower-attribution and non-blocking reporting contract.

**Authority:**
- Preauthorized local actions: modify only the reporting adapter and focused adapter tests; run the targeted test module.
- Stop for: any change to provider storage, provider schema, acceptance inputs, retry policy, or runtime execution behavior.

**Steps:**
- [x] Step 1: Add failing cases for conflicting `run_id`, conflicting `attempt_id`, and matching session with no authoritative run/attempt relationship.
- [x] Step 2: Require `join.state == "matched"` and a conflict-free identifier relationship before setting `secretary_attributed`.
- [x] Step 3: Preserve lower proven attribution and `partial-unattributed` economics when the stronger join fails; when the receipt and provider share only session `S` and the provider has no authoritative run/attempt identifier, retain session attribution only unless an independent mapping proves membership in `R`.
- [x] Step 4: Verify that adapter output remains sanitized and non-blocking.

**Verification:**
- [x] `py -B -m pytest tests/test_secretary_evidence_adapter.py -q`
- Expected: contradictory identifiers never produce `secretary_attributed == True`; session/request evidence remains available.

**Exit Criteria:**
- PR #80's attribution promotion defect is fixed without changing execution, acceptance, cleanup, or settlement behavior.

### Task 3: Add the thin normal invocation result

**Purpose:**
- Make the existing Secretary runtime wrapper return a correlated useful result without requiring the strict experimental receipt.

**Task Function:**
- Implement the smallest normal invocation path on top of existing launcher task-result and cleanup evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: runtime-boundary change with material safety and backend contract implications.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct boundary tests, failure-path tests, cleanup/resource assertions, and existing launcher contract tests.

**Specification Coverage:**
- Normal invocation requires a correlated final response, not exit code, idle, pane text hash, or cleanup alone.
- Normal Secretary `run` is coordination/read-only with respect to repository implementation. It may inspect, reason, prioritize, route, contact CoS, and summarize, but it must not interpret an implementation request as permission for Secretary itself to edit the repository.
- `result: reported` requires a correlated final result, retrievable payload or reference, and unambiguous identity; a task-result status without semantic content is insufficient.
- Execution, result, resource, and observability are independent fields; reporting is optional sidecar evidence.
- `execution: failed`, `result: reported`, and `resource: settled` is valid when a correlated failure result was received.
- Cleanup uncertainty preserves the result but quarantines or leaves the resource unresolved; it does not authorize reuse or retry.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:SecretaryLaunchRequest`
- Inspect: `scripts/secretary_live_runtime.py:run_smoke`
- Inspect: `scripts/secretary_live_runtime.py:_build_codex_runtime_snapshot`
- Inspect: `scripts/herdr_main_launcher.py:_main_body`
- Modify: `scripts/secretary_live_runtime.py:main`
- Add or extract: `scripts/secretary_live_runtime.py:run_normal`
- Add or extract: `scripts/secretary_live_runtime.py:run_probe`
- Preserve: `scripts/secretary_live_runtime.py:run_smoke` as a compatibility alias to `run_probe`; do not add normal/probe/telemetry flags to this function
- Modify: `scripts/secretary_live_runtime.py` with a minimal `_normalize_invocation_outcome` helper in the existing middleware module
- Verify: `tests/test_secretary_live_runtime.py`, `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 1 establishes semantic result and progressive-assurance rules.
- Existing launcher task-result, execution, observation, and cleanup facts remain authoritative.

**Authority:**
- Preauthorized local actions: modify the existing live wrapper and focused runtime tests; read launcher code; run local direct-boundary tests.
- Stop for: inability to obtain a correlated final result from existing launcher evidence without inferring from pane text, or any need to weaken cancellation, cleanup, settlement, or worktree checks.

**Steps:**
- [x] Step 1: Add a normal `run` entry path with only task, cwd, and runtime selection; derive the exact Git worktree root and current `HEAD` with `git rev-parse`, use current `HEAD` as the read-only `expected_base` anchor when no plan-bound mutation is requested, and require an explicit accepted base for plan-bound or mutating work.
- [x] Step 2: Use a separate lightweight invocation request for normal `run` and preserve the strict `SecretaryLaunchRequest` shape for capability probing; do not synthesize plan, attempt, run, session, model, or controller facts in normal mode.
- [x] Step 3: Implement `run_normal` and keep strict probing in `run_probe`; keep `run_smoke` as a compatibility alias rather than adding behavior flags to the strict path.
- [x] Step 4: Normalize existing launcher evidence into independent `execution`, `result`, `resource`, `observability`, timestamps, evidence references, and optional reporting.
- [x] Step 5: Map `reported_completed` and `reported_failed` task results to `result: reported` only when the correlated payload or retrievable reference exists and identity is unambiguous; map missing or conflicting final results to `unavailable` or `ambiguous`.
- [x] Step 6: Prove that `execution: failed` can coexist with `result: reported` when a failure result is received, without turning result availability into execution success.
- [x] Step 7: Prove that `idle`, launcher exit `0`, and cleanup alone cannot produce `result: reported`.
- [x] Step 8: Prove that a reported result survives a missing receipt or quarantined resource, while retry/reuse remains blocked by unresolved resource ownership.

**Verification:**
- [x] `py -B -m pytest tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py -q`
- Expected: correlated results are returned without strict receipts; absent or ambiguous results are not reported as completed; safety failures remain blocking for the affected action.

**Exit Criteria:**
- Normal Secretary invocation has a stable, minimal result contract and does not require the capability-probe receipt.
- Normal Secretary cannot become an implementation executor merely because `run` accepts a task string.

### Task 4: Separate normal run, capability probe, and reporting

**Purpose:**
- Remove provider reporting and strict receipt collection from the normal invocation path while preserving probe and reporting tools.

**Task Function:**
- Split command routing and evidence collection by purpose without deleting the existing strict probe contract.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded runtime/reporting separation with focused regression proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: mock-boundary tests and one bounded live capability probe when the runtime is available.

**Specification Coverage:**
- `run` answers whether Secretary returned a correlated useful result.
- `probe`/`smoke` answers whether complete runtime/receipt/telemetry capability can be proven.
- 9router is required only by the reporting/probe path, never by ordinary Secretary or CoS reasoning.
- Adapter `probe_readiness` is explicitly probe-only. If the compatibility `readiness` field remains, it is a deprecated projection and cannot become a generic Secretary blocker.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_observe_provider_telemetry`
- Inspect: `scripts/secretary_live_runtime.py:main`
- Inspect: `scripts/secretary_evidence_adapter.py:build_evidence_bundle`
- Modify: `scripts/secretary_live_runtime.py:main`
- Modify: `scripts/secretary_live_runtime.py:run_normal` and `scripts/secretary_live_runtime.py:run_probe` as separate paths
- Preserve: `scripts/secretary_live_runtime.py:run_smoke` as a strict-probe compatibility alias only
- Modify: `scripts/secretary_evidence_adapter.py:build_evidence_bundle` only for optional sidecar classification, not normal invocation
- Verify: `tests/test_secretary_live_runtime.py`, `tests/test_secretary_evidence_adapter.py`, `.github/workflows/runtime-contracts.yml`

**Dependencies:**
- Task 2 supplies conflict-safe attribution.
- Task 3 supplies the normal invocation outcome.

**Authority:**
- Preauthorized local actions: modify only the live wrapper, reporting adapter, and their tests/workflow entries; run mocked provider-boundary checks and bounded read-only probes.
- Stop for: any provider database write, normal-path provider query, removal of strict probe coverage, promotion of optional telemetry into result/acceptance state, or a requirement for a new session registry, durable invocation ledger, controller lifecycle, retry manager, dispatcher, or generic `ExecutionOutcome` persistence subsystem.

**Steps:**
- [x] Step 1: Add `run` and `probe` command semantics; retain `smoke` as an alias for the strict probe.
- [x] Step 2: Ensure normal `run` does not call `_observe_provider_telemetry` or require `validate_live_receipt`.
- [x] Step 3: Keep provider observation in the explicit reporting/probe path with independent availability, attribution, and coverage; expose `probe_readiness` as the principal probe field where compatible and retain `readiness` only as a deprecated projection.
- [x] Step 4: Add a test that counts provider observer calls and asserts zero on normal `run`.
- [x] Step 5: Run one bounded live probe and preserve its sanitized artifact as capability evidence only; do not make probe success a normal invocation gate.

**Verification:**
- [x] `py -B -m pytest tests/test_secretary_live_runtime.py tests/test_secretary_evidence_adapter.py -q`
- [x] `py -B scripts/secretary_live_runtime.py probe --help`
- Expected: normal run has zero provider queries; strict probe remains available; provider failure changes only reporting evidence.

**Exit Criteria:**
- Normal coordination no longer waits on or fails because of 9router, token, cost, or complete receipt evidence.

### Task 5: Add variability-focused coordination benchmark

**Purpose:**
- Measure coordination usability and prove degraded behavior without promoting the contract-fake session adapter into production middleware; do not claim real latency improvement from the deterministic benchmark.

**Task Function:**
- Extend the existing deterministic Secretary architecture benchmark with progressive-assurance scenarios and explicit independent outcomes.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic benchmark and test changes have no shared runtime mutation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: benchmark test assertions and final report inspection.

**Specification Coverage:**
- Useful results survive optional observability failure.
- Cleanup uncertainty affects resource reuse, not result preservation.
- Ambiguous results do not trigger duplicate retries.
- Parallel writers escalate to governed plan-bound execution.
- Two workstreams route through Secretary without a CoS-to-CoS mesh.

**Required Skills:**
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/benchmark_secretary_architecture.py:SCENARIOS`
- Inspect: `scripts/benchmark_secretary_architecture.py:ContractMetric`
- Modify: `scripts/benchmark_secretary_architecture.py:SCENARIOS`
- Modify: `scripts/benchmark_secretary_architecture.py:ContractMetric`
- Modify: `scripts/benchmark_secretary_architecture.py:run_contract_benchmark`
- Verify: `tests/test_secretary_benchmark.py`
- Verify: `.github/workflows/runtime-contracts.yml`

**Dependencies:**
- Tasks 1–4 define the outcome fields and assurance rules being measured.

**Authority:**
- Preauthorized local actions: modify only the deterministic benchmark, its tests, and the existing CI test list; run offline benchmark commands.
- Stop for: any live provider dependency, new persistence, new orchestration service, or benchmark that claims live economics without attribution evidence.

**Steps:**
- [x] Step 1: Add six deterministic architectural scenarios: direct Secretary; advisory CoS without a plan; managed Secretary without receipt/provider; ambiguous result; cleanup quarantine; and multi-workstream escalation.
- [x] Step 2: Leave attribution conflict to `tests/test_secretary_evidence_adapter.py`, retry/settlement to existing attempt/reconciliation tests, and parallel-writer requirements to existing plan/dispatcher tests; do not create another lifecycle test framework.
- [x] Step 3: Record mandatory inputs, preflight count, provider query count, messages, duplicate effects, blocker classification, and semantic outcome. Treat any time-to-first-result value as optional measurement only, not CI evidence for p50/p95 latency improvement.
- [x] Step 4: Assert that normal coordination has zero provider queries and that optional evidence failures do not become global blockers.
- [x] Step 5: Preserve the existing `ControllerSessionAdapter` as a deterministic contract fixture only; do not make it a middleware dependency.

**Verification:**
- [x] `py -B scripts/benchmark_secretary_architecture.py 1`
- [x] `py -B -m pytest tests/test_secretary_benchmark.py -q`
- Expected: all scenarios produce deterministic paired results, safety invariants remain true, and degraded outcomes retain the strongest proven fact.

**Exit Criteria:**
- The benchmark demonstrates fewer mandatory facts and fewer false blockers without weakening duplicate, retry, cleanup, acceptance, or integration safety.
- The deterministic benchmark makes structural usability claims only; any live latency measurement is separately labeled optional and is not a CI acceptance gate.

### Task 6: Regenerate canonical adapters and run final proof

**Purpose:**
- Reconcile generated skill surfaces, repository contracts, behavioral tests, and plan evidence with the simplified architecture.

**Task Function:**
- Perform final source-to-generated synchronization and fresh cross-surface verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final sequential reconciliation and verification.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository validators, full test suite, and final source review.

**Specification Coverage:**
- Canonical skills remain the only authored source.
- Generated adapters have no drift.
- Acceptance, reconciliation, cleanup, settlement, Git, Plan, and GitHub ownership remain unchanged outside the intended boundary.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-project-secretary/SKILL.md`
- Inspect: `.agents/skills/skill-chief-of-staff/SKILL.md`
- Inspect: `scripts/secretary_live_runtime.py`
- Inspect: `scripts/secretary_evidence_adapter.py`
- Verify: `generated_agents/antigravity/skills/skill-project-secretary/SKILL.md`
- Verify: `generated_agents/claude/skills/skill-project-secretary/SKILL.md`
- Verify: `generated_agents/codex/skills/skill-project-secretary/SKILL.md`
- Verify: `generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md`
- Verify: `generated_agents/claude/skills/skill-chief-of-staff/SKILL.md`
- Verify: `generated_agents/codex/skills/skill-chief-of-staff/SKILL.md`

**Dependencies:**
- Tasks 1–5 complete with focused proof accepted by the lead controller.

**Authority:**
- Preauthorized local actions: regenerate tracked adapters from canonical skills and run declared validators/tests; do not edit generated files directly.
- Stop for: generated drift caused by an unrelated source, failed contract validation, changed acceptance/reconciliation semantics, or unrecorded scope expansion.

**Steps:**
- [x] Step 1: Run `py -B scripts/sync_agent_adapters.py --all-platforms`.
- [x] Step 2: Run `py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`.
- [x] Step 3: Run `py -B scripts/validate_repo_contracts.py --repo-root . --fast`.
- [x] Step 4: Run `py -B scripts/validate_planning_lifecycle.py`.
- [x] Step 5: Run the focused contract, runtime, benchmark, and acceptance/reconciliation tests.
- [x] Step 6: Run the full test suite and `git diff --check`.
- [x] Step 7: Record any unavailable live probe capability as reporting evidence, never as normal coordination failure.

**Verification:**
- [x] `py -B -m pytest tests/test_skill_project_secretary.py tests/test_skill_chief_of_staff.py tests/test_native_personal_local_workflow.py tests/test_secretary_evidence_adapter.py tests/test_secretary_live_runtime.py tests/test_secretary_benchmark.py tests/test_herdr_main_launcher.py tests/test_project_os_reconciliation.py tests/test_reconciliation.py -q` (`352 passed`)
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --fast`
- [x] `py -B scripts/validate_planning_lifecycle.py`
- [x] `py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- [x] `py -B -m pytest -q` (`1210 passed, 2 skipped`)
- [x] `git diff --check`
- Expected: all required checks pass; no generated drift; no provider query on normal invocation; acceptance and lifecycle safety remain unchanged.

**Exit Criteria:**
- The implementation, canonical docs, generated adapters, tests, benchmarks, and verification evidence all express the same coordination boundaries.

## Verification

Final artifact-level verification must prove:

- normal Secretary and advisory CoS paths are usable without plan-bound runtime proof when their requested action is read-only reasoning or recommendation;
- direct CoS is usable in-session without a plan, Herdr, native Codex qualification, or a new `cos run` launcher when only analysis, recommendation, routing, continuation, or escalation is requested;
- normal Secretary `run` remains read-only for repository implementation and routes implementation requests to CoS and an authorized Worker or governed path;
- normal runtime invocation returns a correlated result when one exists even if strict receipt or provider evidence is unavailable;
- `result: reported` requires retrievable correlated content with unambiguous identity, while a correlated failure result may coexist with `execution: failed`;
- no correlated final result is reported as semantic completion;
- cleanup uncertainty preserves the result but prevents unsafe reuse or retry;
- normal invocation performs zero provider database queries;
- strict probe/reporting paths remain available and correctly classified;
- contradictory provider identifiers never produce run/attempt attribution;
- CoS plan-bound mutation, acceptance, retry, settlement, and integration gates remain intact;
- no new session registry, durable invocation ledger, controller lifecycle, retry manager, dispatcher, or generic outcome persistence subsystem is introduced;
- Secretary remains optional and does not become a mandatory hop;
- deterministic benchmark results make structural usability claims only, with live latency measurement optional and separate from CI acceptance;
- generated skill adapters match canonical sources.

## Completion Criteria

The plan is ready for completion verification when:

1. all six tasks have completed with task-local proof recorded;
2. the simplified semantic contracts and progressive-assurance matrix are present in canonical sources;
3. normal and probe invocation paths are distinct and tested;
4. the PR #80 attribution conflict is fixed and covered by regression tests;
5. normal invocation has no provider database dependency;
6. runtime, cleanup, retry, acceptance, and integration safety invariants remain proven;
7. the variability benchmark reports the requested usability metrics;
8. generated adapters and repository contracts validate without drift;
9. full tests and `git diff --check` pass;
10. any live capability limitation is recorded as optional observability evidence rather than promoted into a coordination failure;
11. scope deviations, blocked capabilities, and deferred work are recorded in the plan before status changes to `completed`.

The plan was explicitly approved for execution; completion is recorded only after the required implementation and verification evidence above passed.

