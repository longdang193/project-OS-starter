---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: normal-coordination-result-and-resource-convergence
targets:
  - scripts/secretary_live_runtime.py
  - scripts/herdr_main_launcher.py
  - scripts/project_os_runtime/secretary_adapter.py
  - scripts/project_os_runtime/secretary_evidence.py
  - scripts/benchmark_secretary_architecture.py
  - tests/test_secretary_live_runtime.py
  - tests/test_herdr_main_launcher.py
  - tests/test_secretary_adapter.py
  - tests/test_secretary_evidence.py
  - tests/test_secretary_benchmark.py
  - tests/test_skill_chief_of_staff.py
  - tests/test_skill_project_secretary.py
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - .agents/skills/skill-project-secretary/SKILL.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - .github/workflows/runtime-contracts.yml
  - generated_agents/codex/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/codex/skills/skill-project-secretary/SKILL.md
  - generated_agents/claude/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/claude/skills/skill-project-secretary/SKILL.md
  - generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/antigravity/skills/skill-project-secretary/SKILL.md
---

# Normal Coordination Result and Resource Convergence

## Verdict Review

The supplied verdict is directionally correct and should be implemented as a
narrow correctness and convergence pass, not another architecture expansion.
The current source already separates normal/probe concerns in part, preserves
runtime safety facts, and has Secretary result, resource, and observability
fields. The remaining work is to make those facts useful on the normal path
without treating optional evidence as universal admission.

The implementation must preserve this invariant:

> An unavailable capability blocks only the action or claim that depends on it.
> It must not prevent Secretary or CoS from understanding the request,
> returning the strongest useful answer supported by current evidence, or
> selecting another independently safe path.

The verdict is corrected in four ways before execution:

1. A launcher exit, idle observation, output-character count, or cleanup state
   is not itself a semantic Secretary result. Normal result reporting requires
   an attributable, unambiguous response payload or retrievable response
   reference; missing optional structured receipts must not erase that result.
2. Resource facts are monotonic and exception-safe. `unknown` may later become
   `removed`; an agent that is gone while its workspace remains open is
   quarantined, not falsely settled; an exception after ownership begins still
   returns the resource state.
3. CoS repository wording is narrowed by claim type. Direct advice may be
   useful with an uncertain or absent exact SHA; an exact repository audit or
   mutation still requires exact Git binding.
4. The benchmark must stop claiming live performance from canned deterministic
   values. Deterministic contract scenarios remain useful for correctness, but
   production-path instrumentation is required for latency, calls, retries,
   messages, and residual resources, with sample-size-aware reporting.

No new receipt schema, workflow database, lifecycle registry, sweeper, generic
retry manager, or orchestration layer is justified. Git, Plan, and GitHub
remain durable truth; runtime receipts and provider telemetry remain bounded
evidence; reporting must not become an execution gate.

## Goal

Make ordinary Secretary coordination return a normal useful result whenever a
safe attributable response exists, while ensuring cleanup and owned-resource
facts converge monotonically and remain truthful through partial failure.

Keep the target architecture explicit:

- Secretary decides **where attention belongs**.
- CoS decides **what the workstream should do next**.
- Workers decide **how to execute their bounded task**.
- Middleware handles **how an authorized action reaches a runtime and how its
  result comes back**.
- Runtime owners handle **process and resource safety**.
- Git/Plan/GitHub preserve **durable truth**.
- Reporting answers **what we can observe and measure**.

None of these layers may impersonate another layer.

## Implementation Outcomes

### Truthful normal Secretary results

`secretary_live_runtime` distinguishes semantic response capture from idle,
launcher, receipt, and provider observations. It correlates valid assignment,
attempt, run, task, repository, plan, and session identity without accepting
conflicting same-type identifiers. A normal invocation can report a useful
result when structured receipt/provider evidence is unavailable; the strict
probe path remains strict for claims that require complete proof.

### Monotonic resource and cleanup evidence

The existing launcher-owned agent and workspace lifecycle reports every
resource acquired after an exception or partial cleanup. Cleanup evidence can
progress from `unknown` to verified `removed`; it never regresses a verified
terminal state. If process removal succeeds but workspace closure fails, the
resource is quarantined and only dependent reuse/retry is constrained.

### Precise CoS repository claims

CoS and planning documentation distinguish direct advisory reasoning from
exact repository audits and mutation. Missing Herdr, provider, receipt, or
exact SHA evidence limits only the associated action or claim; it does not
make the semantic role unavailable.

### Measured benchmark evidence

The Secretary benchmark retains deterministic scenario correctness coverage but
adds real production-path instrumentation for time to first useful answer,
supported latency percentiles, subprocess/Herdr/provider/model/message/retry
counts, false-block classification, and remaining owned resources. CI runs
the deterministic contract suite and validates that live metrics are labeled
as observed, unavailable, or not attempted rather than fabricated.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-backend-verification`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve all unrelated dirty and untracked files
- Commit policy: `no commits during execution`
- Preauthorized local actions: `inspect declared source/tests/docs/config, make additive edits only in declared plan-owned files, regenerate only the declared generated adapter destinations from canonical skill sources, run declared focused tests, contract validators, adapter checks, benchmark probes, and diff checks`
- User-approval actions: `push, merge, publication, destructive recovery, worktree deletion, cleanup outside the plan-owned files, and changes to unrelated dirty work`
- Parallel ownership: `none; runtime, docs, tests, benchmark, and generated surfaces share one contract`
- Sequential fallback: `baseline and caller inventory → result/correlation → resource convergence → CoS wording → benchmark/CI → generated-surface sync and final verification`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `current checkout; do not change branch or absorb unrelated work`
- Base commit: `c528be95423b82cb58278448e2e9b4161d25852c`
- Expected workspace: `preserve the existing dirty/untracked workspace, including `.github/workflows/runtime-contracts.yml`, `scripts/benchmark_secretary_architecture.py`, `tests/test_secretary_benchmark.py`, `scripts/herdr_parallel_dispatch.py`, `scripts/project_os_runtime/acceptance.py`, `scripts/project_os_runtime/reconciliation.py`, `scripts/validate_repo_contracts.py`, the existing plan files, `.playwright-mcp/`, `db/`, `a`, `b`, `diff.patch`, `temp_evidence.json`, `test2.txt`, `test_out.txt`, `scripts/benchmark_dispatch.py`, `tests/fixtures/dispatcher_benchmark/`, and `tests/test_benchmark_dispatch.py`; plan edits to overlapping files are additive to the pre-task content and must not replace or stage unrelated hunks`
- Next action: `none; implementation and verification complete`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | source/caller inventory and baseline focused tests | `99 passed`; shared caller inventory complete; unrelated dirty files preserved |
| Task 2 | `completed` | current | `codex` | Task 1 | normal response, identity, and strict-probe matrix | `2 new regressions plus 73 focused tests passed`; normal result no longer depends on structured receipt |
| Task 3 | `completed` | current | `codex` | Task 2 | cleanup convergence and exception-path matrix | `5 Secretary + 16 launcher + 1 reconciliation focused tests passed`; close failure is quarantined and recovery-required |
| Task 4 | `completed` | current | `codex` | Tasks 2, 3 | CoS advisory versus exact-audit wording tests | `36 skill contract tests passed`; canonical sources synchronized and drift check passed |
| Task 5 | `completed` | current | `codex` | Tasks 2, 3, 4 | measured benchmark, CI labels, and final validators | `89 runtime/benchmark tests passed`; 780-row deterministic benchmark validated; validators passed; no live/provider sample available so performance metrics remain not_attempted |

## Task Breakdown

### Task 1: Freeze source truth and current behavior

**Purpose:**
- Establish the exact shared callers, current result/resource fields, and
  baseline evidence before changing behavior.

**Task Function:**
- Build the implementation boundary and preserve unrelated workspace state.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `lead Codex controller owns the source-first baseline and no delegated benefit is needed`

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: `single lead controller owns source-first baseline validation`

**Specification Coverage:**
- Verdict goals 1–4; no optional capability may become a universal normal-path
  preflight; no new lifecycle system.

**Required Skills:**
- `skill-executing-plans`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py::_observe_submitted_codex`, `_release_codex_agent`, `_completion_observed`, `_launcher_identity_matches`, `_launcher_facts_match`, `sanitize_launcher_result`, `run_smoke`
- Inspect: `scripts/project_os_runtime/secretary_adapter.py::ControllerSessionAdapter`, `InMemoryControllerSessionAdapter`, `matches_binding`
- Inspect: `scripts/project_os_runtime/secretary_evidence.py::build_evidence_snapshot`
- Inspect: `scripts/benchmark_secretary_architecture.py::ContractMetric`, `run_contract_benchmark`
- Inspect: all focused Secretary/CoS tests and `.github/workflows/runtime-contracts.yml`
- Verify: `git status --short --untracked-files=all`, current callers, and baseline focused tests

**Dependencies:**
- None. Do not stage, rewrite, or delete existing dirty/untracked files.

**Authority:**
- Preauthorized local actions: `read declared source, tests, docs, config, history, and run baseline checks without modifying unrelated files`
- Stop for: `missing symbol, changed base/branch, or evidence that the requested behavior is already owned by another active plan`

**Steps:**
- [x] Step 1: Record exact callers and current result/resource state transitions.
- [x] Step 2: Run the focused baseline tests and capture failures without fixing unrelated defects.
- [x] Step 3: Confirm whether any shared reconciliation module, rather than the
  Secretary wrapper, owns the resource state that must change.

**Verification:**
- [x] `py -B -m pytest tests/test_secretary_live_runtime.py tests/test_secretary_adapter.py tests/test_secretary_evidence.py tests/test_secretary_benchmark.py tests/test_skill_chief_of_staff.py tests/test_skill_project_secretary.py`
- Expected: baseline result is recorded; unrelated pre-existing failures are
  identified and excluded from scope.

**Exit Criteria:**
- Exact edit set, caller set, and baseline behavior are recorded in the active
  plan evidence before implementation edits begin.

### Task 2: Make normal result capture and identity correlation truthful

**Purpose:**
- Return `reported`/useful normal results when an attributable semantic response
  exists, while preserving strict proof requirements for probe-only claims.

**Task Function:**
- Repair the shared capture and correlation boundary, not individual callers.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: `bounded runtime correctness work with moderate reasoning depth and localized risk`

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: `focused runtime tests plus direct boundary verification`

**Specification Coverage:**
- Idle plus output chars without semantic response is `unavailable`.
- A captured attributable response is `reported`.
- Distinct valid assignment/attempt IDs are not ambiguous.
- Conflicting same-type IDs are ambiguous/correlation failure.
- Missing structured receipt or provider database has zero normal-result impact.
- Ambiguous delivery must not cause duplicate launch.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/secretary_live_runtime.py::_completion_observed`, `_launcher_identity_matches`, `_launcher_facts_match`, `select_launcher_payload`, `sanitize_launcher_result`, and the smallest existing normal/probe entry-point split needed after Task 1
- Inspect/modify only if required by the shared contract: `scripts/project_os_runtime/secretary_adapter.py::CommunicationEnvelope`, delivery/replay correlation, and `matches_binding`
- Verify: `tests/test_secretary_live_runtime.py`, `tests/test_secretary_adapter.py`, `tests/test_secretary_receipts.py`

**Dependencies:**
- Task 1 source and caller inventory complete.

**Authority:**
- Preauthorized local actions: `edit only the listed runtime/adapter symbols and focused tests; run direct launcher-boundary tests and safe local probes without external writes`
- Stop for: `new receipt schema, provider migration, duplicate lifecycle authority, or any change that makes optional telemetry mandatory for normal reasoning`

**Steps:**
- [x] Step 1: Add failing focused tests for the response/identity matrix.
- [x] Step 2: Trace the shared caller path from launcher payload selection through
  sanitization and runtime snapshot validation; patch the root correlation rule.
- [x] Step 3: Keep strict receipt/provider validation on the strict probe path,
  but prevent its absence from overwriting an already correlated normal result.
- [x] Step 4: Prove ambiguous delivery is reported without a second launch or
  duplicate effect.

**Verification:**
- [x] `py -B -m pytest tests/test_secretary_live_runtime.py -k "completion_observed or launcher_identity or launcher_facts or normal_result or structured_receipt or provider_telemetry"`
- [x] `py -B -m pytest tests/test_secretary_adapter.py -k "binding or delivery or replay"`
- [x] Assertions cover idle plus output chars → `unavailable`, captured attributable
  response → `reported`, distinct IDs → non-ambiguous, conflicting same-type IDs
  → correlation failure, missing receipt/provider DB → normal result preserved, and
  ambiguous delivery → no duplicate effect.
- Expected: normal result remains useful and attributable; strict probe remains
  blocked only for claims requiring unavailable proof; conflicting IDs fail
  closed without duplicate execution.

**Exit Criteria:**
- The same shared correlation behavior is used by every existing caller, and
  focused regression tests cover both positive and negative identity cases.

### Task 3: Make cleanup and resource evidence converge monotonically

**Purpose:**
- Ensure every owned resource has truthful final or recoverable state through
  normal completion, uncertain cleanup, workspace-close failure, and exceptions.

**Task Function:**
- Harden the existing launcher/resource settlement path without adding a
  sweeper or retry manager.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: `runtime/resource correctness requires focused debugging and direct boundary proof`

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: `exception-path and cleanup-state regression proof`

**Specification Coverage:**
- Cleanup `unknown` may later become verified `removed` and then settled.
- Agent removed while workspace close fails becomes quarantined.
- Runtime exception after resource ownership begins still returns resource state.
- Uncertain cleanup blocks only dependent reuse/retry and preserves unrelated
  results.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/secretary_live_runtime.py::_release_codex_agent`, `_observe_submitted_codex`, `run_smoke`, and the existing result/error serialization path
- Modify: `scripts/herdr_main_launcher.py::_terminate_codex_lane_unlocked`, `retire_lane`, and the existing cleanup/resource result path
- Inspect/modify only if Task 1 proves it is the shared owner: `scripts/project_os_runtime/reconciliation.py::reconcile` and related resource/settlement facts
- Verify: `tests/test_secretary_live_runtime.py`, `tests/test_herdr_main_launcher.py`, `tests/test_reconciliation.py`, and any existing launcher cleanup tests
- Document if needed: `docs/operating_system/procedures/runtime-adapter-procedure.md`, `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- Task 1 complete; Task 2 identity semantics must not be regressed.

**Authority:**
- Preauthorized local actions: `edit declared cleanup/resource symbols and focused tests; use deterministic transport fakes and bounded local process probes only`
- Stop for: `global cleanup infrastructure, destructive process termination outside the owned attempt, or a resource-state change that weakens runtime-owner safety`

**Steps:**
- [x] Step 1: Add failing tests for unknown-to-removed convergence, agent-removed/workspace-close-failed quarantine, and exception-after-ownership.
- [x] Step 2: Patch the shared cleanup/finalization path so cleanup evidence is
  monotonic and serialized even when observation or release raises.
- [x] Step 3: Confirm dependent reuse/retry is the only behavior constrained by
  quarantine; unrelated semantic results remain returned.
- [x] Step 4: Update only the minimum runtime procedure wording needed to match
  the source and tests.

**Verification:**
- [x] `py -B -m pytest tests/test_secretary_live_runtime.py -k "release_codex_agent or observe_submitted_codex or cleanup or exception"`
- [x] `py -B -m pytest tests/test_herdr_main_launcher.py -k "terminate_codex_lane or retire_lane"`
- [x] `py -B -m pytest tests/test_reconciliation.py -k "resource or settlement or quarantine"` when Task 1 identifies reconciliation as the shared owner.
- [x] Direct boundary exercise with transport outcomes `removed`, `unknown`, and
  workspace-close failure; assert unknown → removed convergence, quarantine on
  workspace-close failure, and serialized resource state after an exception.
- Expected: no owned resource disappears from the returned result; terminal
  removal is never downgraded; quarantine is explicit and scoped.

**Exit Criteria:**
- Cleanup state is truthful on success, timeout, exception, replay, and partial
  failure, with regression proof at the shared caller boundary.

### Task 4: Narrow CoS repository-snapshot claims by action type

**Purpose:**
- Let direct CoS reasoning answer useful questions with uncertainty while
  keeping exact Git binding mandatory for exact audits and mutations.

**Task Function:**
- Reconcile semantic-role documentation and tests with the runtime evidence
  boundary established in Tasks 2–3.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: `documentation/contract change with focused semantic tests; no new executable`

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: `skill and planning contract tests`

**Specification Coverage:**
- Direct CoS advisory without exact SHA returns a useful answer with explicit
  uncertainty.
- Exact repository audit requires exact Git binding.
- Missing Herdr in direct CoS does not prevent answering or selecting an
  independently safe path.
- Managed Secretary without Herdr is unavailable only as a managed path; the
  semantic Secretary role remains usable.

**Required Skills:**
- `skill-chief-of-staff`, `skill-project-secretary`, `skill-code-standards`

**Files And Symbols:**
- Modify: `.agents/skills/skill-chief-of-staff/SKILL.md`, `.agents/skills/skill-project-secretary/SKILL.md`, `docs/operating_system/planning/planning-dispatch.md`
- Modify only if current procedure language is stale: `docs/operating_system/procedures/runtime-adapter-procedure.md`, `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: `tests/test_skill_chief_of_staff.py`, `tests/test_skill_project_secretary.py`, and planning-dispatch contract tests

**Dependencies:**
- Tasks 2–3 establish the result/resource facts and failure vocabulary.

**Authority:**
- Preauthorized local actions: `edit canonical skill and planning documentation plus focused contract tests; run the writer sync for declared generated destinations and then run generated-surface checks`
- Stop for: `adding a CoS executable, changing Git/Plan/GitHub ownership, or weakening exact-audit/mutation gates`

**Steps:**
- [x] Step 1: Add or update tests that distinguish advisory reasoning, exact
  audit, governed mutation, and managed Secretary runtime availability.
- [x] Step 2: Remove only stale blanket wording that makes optional runtime
  capability a semantic preflight.
- [x] Step 3: Preserve exact repository, plan, authority, settlement, acceptance,
  and GitHub evidence requirements where the action consumes them.
- [x] Step 4: Run `py -3 scripts/sync_agent_adapters.py --all-platforms` to write
  only the declared `generated_agents/codex/skills/`,
  `generated_agents/claude/skills/`, and
  `generated_agents/antigravity/skills/` destinations; stop if it proposes
  unrelated drift, deletion, or changes outside those destinations.
- [x] Step 5: Run the no-write drift check after regeneration.

**Verification:**
- [x] `py -B -m pytest tests/test_skill_chief_of_staff.py tests/test_skill_project_secretary.py`
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `py -3 scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-11-19-46-normal-coordination-result-and-resource-convergence-plan.md`
- [x] Named assertions cover advisory without exact SHA, exact audit requiring
  exact binding, missing Herdr direct CoS usefulness, and managed Secretary
  unavailability without semantic-role failure.
- Expected: semantic roles remain directly useful; exact claims remain strict;
  generated surfaces match canonical skill sources.

**Exit Criteria:**
- Documentation and tests express the same action-scoped capability boundary,
  with no second coordination authority or runtime registry.

### Task 5: Replace canned benchmark metrics with measured production-path evidence

**Purpose:**
- Preserve deterministic correctness scenarios while making performance and
  operational claims honest, reproducible, and CI-visible.

**Task Function:**
- Instrument the existing Secretary path and report only metrics supported by
  the sample and evidence source.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: `measurement and CI scope are bounded; no performance redesign`

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: `benchmark contract tests and CI validation`

**Specification Coverage:**
- Measure time to first useful answer; p50/p95/p99 only when sample size
  supports them; subprocess, Herdr, provider, model-turn, message, retry, false
  block, and remaining-resource metrics.
- Never label deterministic fakes as live or claim statistically meaningful
  improvements from tiny samples.

**Required Skills:**
- `skill-backend-verification`, `skill-performance-optimization`, `skill-code-standards`, `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `scripts/benchmark_secretary_architecture.py::ContractMetric`, `_metric`, `run_contract_benchmark`, and the existing CLI output path
- Modify: `tests/test_secretary_benchmark.py`
- Modify only if the current workflow lacks the needed command: `.github/workflows/runtime-contracts.yml`
- Verify: `scripts/secretary_live_runtime.py` instrumentation is sourced from the
  production path, not duplicated benchmark constants

**Dependencies:**
- Tasks 2–4 complete so benchmark labels and resource/result fields are stable.

**Authority:**
- Preauthorized local actions: `edit benchmark/test/CI surfaces, run deterministic and bounded local production-path measurements, and record unavailable metrics honestly`
- Stop for: `new telemetry database, external provider writes, claims of production statistical significance from insufficient samples, or unrelated CI changes`

**Steps:**
- [x] Step 1: Add failing tests that reject `live=True` or latency/token claims
  when evidence provenance is deterministic-fake or sample size is insufficient.
- [x] Step 2: Attach measurements to the existing production-path boundaries and
  expose `measured`, `unavailable`, and `not_attempted` states.
- [x] Step 3: Keep deterministic scenario correctness assertions and add the
  normal/probe/resource verification matrix as bounded cases.
- [x] Step 4: Add or adjust the CI command so the benchmark and contract tests
  run without requiring Herdr, provider DB, or live credentials.

**Verification:**
- [x] `py -B -m pytest tests/test_secretary_benchmark.py tests/test_secretary_live_runtime.py tests/test_secretary_adapter.py tests/test_secretary_evidence.py tests/test_secretary_receipts.py`
- [x] `py -B scripts/benchmark_secretary_architecture.py 30`
- [x] Inspect the command output: deterministic contract rows
  remain `evidence_provenance=deterministic-fake`, `live=false`, and
  `latency_ms/token_usage` are unavailable unless an exercised production-path
  measurement explicitly supplies them; measured rows carry their source and
  sample count.
- [x] Percentiles are emitted only when `sample_count >= 20`; otherwise the
  percentile field is `unavailable` with an explicit insufficient-sample reason.
- [x] CI workflow command succeeds in the no-live-capability environment.
- [x] Bounded production-path measurement output labels every metric with its
  provenance and sample support.
- Expected: correctness is deterministic and repeatable; performance claims are
  measured or explicitly unavailable; CI does not turn optional infrastructure
  into a normal semantic gate.

**Exit Criteria:**
- The benchmark no longer contains unsupported canned performance claims and
  CI proves the supported contract matrix.

## Verification

Run fresh final proof only after all tasks are complete:

- `py -B -m pytest tests/test_secretary_live_runtime.py tests/test_secretary_adapter.py tests/test_secretary_evidence.py tests/test_secretary_receipts.py tests/test_secretary_benchmark.py tests/test_reconciliation.py tests/test_skill_chief_of_staff.py tests/test_skill_project_secretary.py`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- `git diff --check`
- Run the repository-supported runtime-contract CI command locally when
  available; otherwise record the unavailable runner and rely on the exact
  focused command above.
- Run bounded live probes only when existing credentials/capabilities are
  already available; treat missing Herdr/provider/receipt evidence as an
  observed capability limitation, not a failed normal semantic result.

Execution note: no live/provider capability was used in this run. The benchmark
reports deterministic contract correctness and explicit
`measurement_status=not_attempted`; it does not claim production latency,
token usage, or percentile performance.

The final backend evidence must identify the direct launcher/runtime boundary,
success and important failure paths, final resource state, quarantine/retry
disposition, identity/correlation proof, and one representative trace from
request through result and cleanup. Browser or MCP evidence cannot substitute
for this backend proof.

## Completion Criteria

The plan is ready for completion verification when:

1. normal Secretary results are useful and attributable without universal
   receipt/provider/Herdr preflight;
2. strict probe claims remain blocked when their required proof is unavailable;
3. cleanup/resource evidence is monotonic, exception-safe, and explicit about
   quarantine;
4. CoS wording distinguishes advisory reasoning from exact repository claims;
5. deterministic correctness tests and measured benchmark output agree with
   source behavior;
6. canonical skill changes are synchronized to generated adapters and all
   declared validators/checks are fresh;
7. no unrelated dirty or untracked workspace file is staged, rewritten, deleted,
   or treated as evidence for this plan;
8. deviations, deferred GitHub administration, live-capability limitations,
   and remaining risks are recorded in the plan evidence.

## Non-Goals and Stop Conditions

- No new receipt schema, lifecycle database, registry, sweeper, or generic retry
  manager.
- No GitHub branch-rule mutation in this plan.
- No provider installation, authentication, data-access widening, or external
  writes without separate approval.
- No promotion of provider telemetry into Secretary-native result or acceptance
  truth.
- Stop and revise the plan if implementation discovers that the needed behavior
  belongs to a different shared owner, requires a durable schema migration, or
  changes Plan/Git/GitHub authority boundaries.

## Rollback and Risk

Keep changes localized to the existing runtime/adapter boundary and preserve
the strict probe path. If a normal-path change weakens identity or cleanup
proof, revert that task’s checkpoint and retain the deterministic regression
test as the failing guard. If a live capability is absent, report the exact
unavailable evidence and continue with source, deterministic, and bounded local
boundary proof; do not fabricate a live result.
