---
layer: change
artifact_type: spec
status: active
template_id: detailed-specification
name: parallel-deepagents-dispatch
targets:
  - scripts/herdr_parallel_dispatch.py
  - scripts/herdr_main_launcher.py
  - scripts/dcode_project.py
  - scripts/deepagents_result_contract.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_dcode_project.py
  - docs/operating_system/runtime/runtime-surfaces.md
---

# Parallel DeepAgents Dispatch

## Goal and Problem

### Problem

- current behavior or opportunity: Herdr has bounded single-lane lifecycle evidence, but no contract for admitting and aggregating multiple independent DeepAgents lanes concurrently.
- affected users, systems, or maintainers: CoS lead controllers, Herdr launcher maintainers, `dcode-project` maintainers, and plan authors coordinating independent write-capable tasks.
- evidence: `_build_assignment_result()` already composes `delivery`, `execution`, `observation`, `task_result`, `cleanup`, and `performance`; DeepAgents receipts correlate by `attempt_id`; role-view ownership is exclusive per worktree; `--dry-run` stops before worker execution.
- consequence of no change: parallel launch could confuse process start with delivery, reuse stale receipts, retry uncertain workers, overwrite shared worktrees, erase sibling failures, or claim task acceptance without proof.

### Goal

- desired outcome: enable a bounded two-lane DeepAgents pilot using a foreground CoS lead controller, existing launcher/receipt contracts, isolated worktrees, and plan-ledger ownership.
- observable success: independent lanes run concurrently only when admission checks pass; every lane retains attempt-correlated lifecycle evidence; retries, cancellation, partial failure, cleanup uncertainty, and final integration remain explicit; no second supervisor or lifecycle ledger appears.

## Required Outcomes

### Outcome: Safe lane admission

- affected actor or system: CoS/task-plan coordinator before launch.
- required result: each lane has stable task identity, explicit write set, isolated worktree, exclusive Herdr pane binding, fixed shared contracts, no unresolved dependency on another lane, and isolated mutable test resources where required.
- success condition: unsafe or ambiguous lane sets are rejected before any write-capable launch.

### Outcome: Concrete foreground coordination

- affected actor or system: one CoS lead controller running the repository-owned foreground helper `scripts/herdr_parallel_dispatch.py`.
- required result: helper receives a dependency-ready lane descriptor file, starts at most two blocking `herdr_main_launcher.py` subprocesses with separate stdout/stderr streams, parses preparation and final assignment JSON per lane, and returns lane evidence plus child exit status to CoS.
- success condition: controller owns collection and interruption handling; CoS alone updates the plan ledger and accepts results; no launcher or worker writes coordination state.

### Outcome: Attempt-correlated evidence

- affected actor or system: Herdr launcher and `dcode-project`.
- required result: each lane has a stable plan task/lane identity; each launcher invocation gets its own generated `dispatch_id`; every retry keeps the plan identity and receives a unique `attempt_id`; hashes, grant binding, agent, pane, process evidence, receipt, and lifecycle sections remain correlated.
- success condition: a receipt from an older attempt cannot settle a replacement attempt; missing or uncertain evidence remains unknown.

### Outcome: Honest delivery and completion semantics

- affected actor or system: launcher result and CoS acceptance.
- required result: launcher start proves only that a dispatch attempt exists; runtime delivery acknowledgement proves runtime acceptance only when directly observed; worker receipt proves worker and cleanup facts; task acceptance requires task report, verification, and CoS decision.
- success condition: no launcher path invents `task_result.accepted: true`; runtime completion never substitutes for `PASS | FAIL | BLOCKED` acceptance.

### Outcome: Bounded parallel lifecycle

- affected actor or system: CoS coordinator and existing lane launchers.
- required result: at most two admitted or potentially active attempts consume capacity in the pilot; command transport, worker execution, and observation/receipt settlement use separate budgets; siblings continue after independent failure unless batch policy says otherwise.
- success condition: one lane can fail, timeout, cancel, or become uncertain without corrupting settled sibling evidence.

### Outcome: Safe retry, cancellation, and reconciliation

- affected actor or system: CoS coordinator, Herdr, and `dcode-project`.
- required result: uncertain delivery reconciles the same attempt; confirmed failure or timeout gets a new attempt only after worker, descendants, worktree, and task-owned resources are settled and partial changes are assessed; active worker cancellation is deferred in the pilot, so stop-admission and bounded timeout/reconciliation replace false cancellation confirmation.
- success condition: no duplicate worker, duplicate edit, stale receipt settlement, or destructive cleanup follows an uncertain observation.

### Outcome: Final combined-revision acceptance

- affected actor or system: designated integration reviewer and CoS.
- required result: final review and verification inspect the exact combined revision after lane integration, while preserving each lane's individual result and uncertainty.
- success condition: batch `PASS` requires every required lane plus final integration verification; conclusive required failure yields `FAIL`; unresolved evidence or ownership yields `BLOCKED`.

## Design Analysis

### Change Summary

- baseline reference: commit `c086339c08bb396d32be44a2b848b1ab473fa52c`, Herdr lifecycle evidence hardening.
- added, changed, or removed behavior summary: add admission, bounded concurrent coordination, attempt-safe aggregation, and pilot evidence around existing lane lifecycle records.
- intentionally unchanged behavior: existing process ownership checks, DeepAgents receipt schema, role-view lock, full auto-discovery eligible-set semantics, Codex executor control flow, and CoS acceptance authority.
- affected maintained contracts: Herdr assignment result composition, DeepAgents receipt correlation, plan-ledger lane ownership, runtime-surface ownership documentation, and focused launcher/receipt tests.

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
|---|---|---|---|---|
| Where does lifecycle evidence compose? | `_build_assignment_result()` emits delivery, execution, observation, task result, cleanup, performance, and compatibility fields. | `scripts/herdr_main_launcher.py` | high | Extend this boundary; do not add a second verdict layer. |
| How are DeepAgents results correlated? | Receipt parsing requires matching `attempt_id`; malformed, missing, or mismatched receipts remain unknown. | `scripts/deepagents_result_contract.py`, `scripts/herdr_main_launcher.py` | high | Retries require new attempt IDs and stale receipts must be rejected. |
| Who owns same-worktree role views? | `dcode-project` holds an exclusive role-view lock for one worktree attempt and publishes cleanup evidence. | `scripts/dcode_project.py` | high | Concurrent write lanes require separate worktrees. |
| What does dry-run prove? | Main dry-run emits resolved JSON and returns before launch. | `scripts/herdr_main_launcher.py`, `tests/test_herdr_main_launcher.py` | high | Dry-run proves resolution only, not worker concurrency or cleanup. |
| Who owns durable coordination? | Plan owns task/dependency/acceptance state; Git owns workspace and changes; runtime state is not recovery truth. | `docs/operating_system/rules/git-tracked-coordination-rule.md` | high | Batch aggregation remains a derived view over plan and lane evidence. |
| Does Herdr expose atomic correlated delivery? | Current APIs provide process/pane observations and prompt operations, but no proven atomic attempt/pane/process-generation conditional delivery primitive. | reviewed verdicts and current launcher code | medium | Do not assume stronger delivery semantics; retain unknown and reconciliation paths. |
| What do native waits prove? | Receipt-first launcher observation uses `pane wait-output` only as a bounded marker signal for unresolved attempts, followed by pull-based process and output proof; `agent wait` is a documented capability, not current launcher integration. | Herdr capability evidence and launcher behavior | high | Wait success or timeout never proves delivery, acceptance, cleanup, or safe retry. |

### Coordination Interface

The pilot uses one foreground CoS lead controller, not a new daemon or durable
registry.

Native waits are bounded observation signals only. Current launcher integration
reads the attempt-correlated receipt first. Confirmed receipts skip blocking
marker waits but still retain bounded pane and process probes; unresolved
receipts use one bounded `pane wait-output` observation before final receipt,
process/descendant, pane, cleanup, and reconciliation checks. `agent wait` remains
documented as a Herdr capability but is not wired into the launcher; CoS retains
final `PASS | FAIL | BLOCKED` acceptance authority.

| Interface item | Contract |
|---|---|
| Input | Dependency-ready lane descriptors: stable plan task/lane ID, task text/hash, executor/profile, repo/worktree, expected base, session/pane, allowed write set, fixed shared contracts, mutable-resource policy, and dependency status. |
| Launch | CoS invokes `py -3 scripts/herdr_parallel_dispatch.py --lanes-file <path> --max-concurrency 2`; helper starts each admitted lane as one blocking `py -3 scripts/herdr_main_launcher.py ...` subprocess with separate stdout/stderr capture. |
| Preparation output | First launcher JSON record: resolved target, generated `dispatch_id`, generated `attempt_id`, task/grant hashes, runtime binding, and target-discovery evidence. Preparation is not final assignment output and does not prove delivery or completion. |
| Final output | Final assignment JSON record, or explicit transport/launch failure record, keyed by lane ID and `attempt_id`; normalized `lifecycle_receipt` is retained in assignment evidence before any raw receipt deletion. |
| Controller result | Per-lane normalized evidence, child exit status, stream diagnostics, capacity state, and unresolved conditions on stdout as tagged JSONL. Helper does not update plan ledger or assign `PASS`, `FAIL`, or `BLOCKED`. |
| Interruption | Stop admitting new lanes; retain running or uncertain attempts; reconcile plan, Git, and runtime ownership before any replacement launch. |

### Runtime Grant And CoS Projection

Each admitted descriptor supplies explicit `grant_turns`,
`grant_wall_clock_seconds`, `grant_child_agents`, and `mcp_select` values.
Admission normalizes these values through the existing
`_normalize_runtime_grant()` contract, maps them to launcher CLI arguments, and
derives one `grant_digest`. Correlated preparation evidence is authoritative for
the normalized `runtime_grant` and digest; final assignment evidence must carry
the same digest. Conflicting top-level and nested MCP selectors reject admission;
no selector source wins silently. Child delegation remains policy-level scope,
not subtree-budget enforcement.

CoS projection is ephemeral and explicit. It maps only existing structured
owners: task/lane identity and task text, profile and executor, Git worktree and
expected base, allowed writes, dependencies and readiness, Herdr session/pane,
fixed contracts, mutable resources, and Runtime Grant fields. Missing or
ambiguous values reject admission. File-backed `--lanes-file` descriptors and
in-memory descriptors use the same `load_lane_descriptors_from_items()`
validation path. Markdown or prose is not an input source, and expected Git
identity remains distinct from observed Git identity.

### Identity and Evidence Lifetime

| Identity | Required meaning |
|---|---|
| Plan task/lane ID | Stable workflow identity across retries and separate launcher invocations. |
| `dispatch_id` | One launcher dispatch invocation, generated during current resolution; not assumed stable across retries. |
| `attempt_id` | Unique execution attempt; required for DeepAgents receipt matching and retry separation. |
| Worktree/pane binding | Exact assigned resources; mutable ownership is rechecked immediately before launch and before reuse. |

The pilot does not invent process-generation APIs. When generation evidence is
unavailable, use current composite ownership evidence: exact executable/path,
working directory, pane binding, PID/descendant records, attempt marker, and
attempt-correlated receipt. A PID alone never proves identity.

The retained evidence is normalized assignment JSON, including
`lifecycle_receipt`. Raw receipt files remain `dcode-project`-owned temporary
artifacts and may be deleted after confirmed settlement when recovery is not
required.

### Prototype and Validation Evidence

- prototype reference or `Not applicable: no UI or behavior prototype is required for runtime contract and orchestration changes`.
- UX approval or `Not applicable: no UX surface exists`.
- frozen prototype revision or reference or `Not applicable: no prototype exists`.
- design export evidence or `Not required: no design export is involved`.
- scenarios to validate: two independent lanes; one sibling failure; uncertain delivery; confirmed timeout; active worker still potentially live after observation expiry; controller interruption; lane A starts while lane B fails to start; deferred cancellation racing with successful completion; late old receipt; cleanup uncertainty; final combined revision.
- findings incorporated into approved behavior: delivery is separate from completion; observation is preserved; full discovery semantics remain; no optimistic aggregate result.
- rejected alternatives: universal early acknowledgement requirement; selected-pane-only auto-discovery; second lifecycle schema; background supervisor; durable runtime registry; broad concurrency rollout before pilot proof.

### Scope

- included behavior: lane admission; bounded concurrency of two; existing evidence composition; attempt-safe receipt settlement; timeout/retry/cancellation/reconciliation rules; sibling aggregation; pilot metrics and rollout gates.
- affected boundaries: CoS/task plan, Herdr launcher, `dcode-project`, Git worktree/branch state, test resource ownership, and final integration review.
- admissible cases: planned independent write-capable lanes with explicit isolation; read-only or fixed-baseline review lanes may run concurrently when their declared resources do not conflict.
- compatibility expectation: single-lane execution and existing executor-specific control flow remain valid; automatic discovery still reports the full validated eligible set.

### Non-Goals

- no second lifecycle schema, verdict layer, supervisor, durable runtime registry, reservation service, or new background process.
- no requirement that launcher start means delivery or task acceptance.
- no atomic conditional delivery API invented above current Herdr capability.
- no replacement of full auto-discovery with selected-pane-only probing.
- no concurrency above two in first rollout.
- no automatic destructive cleanup when ownership or retirement is uncertain.

### Requirements and Behavioral Contract

#### Requirement: Lane admission

- trigger or actor: CoS/task-plan coordinator before starting a parallel wave.
- preconditions: each lane names stable plan task/lane identity, executor, branch/worktree, pane binding, allowed write set, dependencies, fixed shared contracts, and mutable resource policy.
- required behavior: admit only dependency-ready lanes with disjoint write ownership, isolated worktrees, exclusive pane bindings, and no unresolved shared mutable resource.
- output or state change: derived admission result records admitted lanes, rejected lanes, reasons, and concurrency limit; the stable plan task/lane identity is not regenerated from runtime IDs; plan ledger remains the durable coordination source.
- failure behavior: reject the wave before write-capable launch and preserve rejection reason; do not partially launch an unsafe wave.
- observable acceptance: tests prove same-worktree, overlapping-write-set, unresolved-dependency, shared-resource, and duplicate-pane cases reject.

#### Requirement: Capacity and partial start

- trigger or actor: foreground CoS controller admitting or replacing lanes.
- preconditions: capacity limit is two; every candidate has an admission record.
- required behavior: starting, running, and potentially running attempts consume one slot; launcher exit, transport timeout, and observation expiry do not release a slot until retirement evidence is established; retries consume a slot under the same rule.
- output or state change: controller tracks occupied, retired, and uncertain slots per lane/attempt without durable runtime registry.
- failure behavior: controller stops new admission on interruption or capacity uncertainty; if lane A starts and lane B fails to start, A remains tracked under sibling policy and no atomic rollback is implied.
- observable acceptance: barrier tests prove a third attempt cannot start while two slots are occupied and partial-start tests preserve lane A evidence after lane B launch failure.

#### Requirement: Lifecycle evidence composition

- trigger or actor: each launcher invocation and result classifier.
- preconditions: one plan task/lane identity, one generated per-invocation `dispatch_id`, one unique `attempt_id`, bound agent/task/grant identity, and executor-specific evidence.
- required behavior: `_build_assignment_result()` remains the single composition boundary; derive compatibility `status`, `failure_kind`, and `reconciliation_required` consistently from lifecycle sections while preserving separate delivery, execution, observation, task-result, cleanup, and performance sections.
- output or state change: one lane result per attempt; batch aggregation consumes lane results without mutating their facts.
- failure behavior: retain known facts and mark unknown fields/reconciliation when evidence is incomplete.
- observable acceptance: builder tests show later errors do not erase prior identity or phase facts and compatibility fields agree with structured sections.

#### Requirement: Delivery, execution, and acceptance separation

- trigger or actor: launcher result consumer.
- preconditions: launcher may return before worker completion, especially for Codex; DeepAgents may settle through receipt and bounded observation.
- required behavior: distinguish dispatch attempt, runtime delivery acknowledgement, worker execution, observation, cleanup, task report, verification, and CoS acceptance.
- output or state change: `delivery` may remain `unknown`; launcher task acceptance remains `None` or `False`; batch verdict is `PASS`, `FAIL`, or `BLOCKED` only at CoS acceptance.
- failure behavior: missing acknowledgement, report, verification, or cleanup proof prevents optimistic acceptance.
- observable acceptance: tests reject launcher-start-as-delivery and worker-completion-as-task-acceptance shortcuts.

Runtime reporting completion is not CoS acceptance. `reported_completed` means
runtime reporting reached its terminal reporting state; `accepted: null` keeps
CoS acceptance pending. Launcher status may be `completed` while task-result
acceptance remains unresolved.

#### Requirement: Retirement and bounded observation

- trigger or actor: launcher completion observer and coordinator capacity tracker.
- required behavior: receipt confirmation precedes marker waiting; confirmed receipts skip blocking marker wait but retain one bounded pane read and process probe. Unresolved receipts receive one bounded marker wait with reserved time for receipt reread and fresh final probes. DeepAgents explicit `runtime_grant.wall_clock_seconds.requested` supplies completion observation budget; `native` uses the fixed `120s` default, and receipt grace remains separate.
- output or state change: marker observation is recorded as `observed`, `expired`, or `transport_failed`; interval expiry is distinct from transport failure; stale markers never settle a current attempt.
- retirement rule: missing or unknown `descendant_state`, ownership, cleanup, or task evidence never proves retirement. Capacity may retire only when ownership and cleanup are explicitly settled, even if task-result evidence remains unresolved.
- observable acceptance: regression proof covers receipt-aware ordering, stale-marker rejection, bounded timeout uncertainty, process-state change before final probe, and `reported_completed` with `accepted: null`.

#### Requirement: Retry and stale-receipt protection

- trigger or actor: coordinator handling timeout, failure, or uncertain result.
- preconditions: current attempt evidence and ownership state are available.
- required behavior: reconcile the same attempt for uncertain delivery; create a new `attempt_id` only after confirmed failure/timeout and settled ownership; parse receipts only when attempt correlation matches; keep uncertain attempts consuming capacity until retirement is proven.
- output or state change: retry result is a new lane attempt linked to same stable task identity; old result remains preserved.
- failure behavior: block retry when worker, descendant, worktree, or task-owned resource retirement is uncertain.
- observable acceptance: late receipt from attempt A cannot settle replacement attempt B; uncertain delivery cannot trigger blind resend.

#### Requirement: Cancellation and sibling aggregation

- trigger or actor: coordinator or batch policy.
- preconditions: lane result has a known attempt and owner.
- required behavior: pilot cancellation is stop-admission only; no active worker-cancel command is claimed. `dcode-project` remains worker/descendant/cleanup owner and its bounded timeout plus receipt evidence establish termination facts. Allow independent siblings to finish; aggregate without deleting successful or failed lane records.
- output or state change: per-lane facts remain intact; derived batch state is `PASS`, `FAIL`, or `BLOCKED` under explicit precedence rules.
- failure behavior: unresolved ownership, delivery, cancellation state, or cleanup keeps batch `BLOCKED`, even when another lane has a conclusive failure; the known failure remains preserved.
- observable acceptance: tests cover one failed sibling with one successful sibling, one unresolved sibling, lane A plus lane B launch failure, controller interruption, and deferred cancellation racing with completion without optimistic all-green output.

Aggregate precedence:

| Required lane and integration evidence | CoS decision |
|---|---|
| All required tasks accepted; exact combined revision and integration verification pass | `PASS` |
| Conclusive required task or integration failure; all relevant lifecycle and cleanup states settled | `FAIL` |
| Any unresolved ownership, delivery, deferred cancellation, cleanup, missing verification, or combined-revision state, even alongside known failure | `BLOCKED`, preserving known failure |

#### Requirement: Final integration evidence

- trigger or actor: designated integration reviewer after admitted lanes finish.
- preconditions: lane results, Git worktrees/branches, and exact combined revision are known.
- required behavior: run final review and verification against exact combined revision, not only initial baseline or individual lane revisions.
- output or state change: CoS records final acceptance separately from runtime summaries.
- failure behavior: conclusive integration failure yields `FAIL`; missing verification, missing combined revision, post-review lane change, or unresolved integration evidence yields `BLOCKED`.
- observable acceptance: pilot evidence names combined revision and passes final verification gates.

### Constraints and Alternatives

- constraint: current Herdr does not prove atomic conditional prompt delivery; retain bounded observation and reconciliation.
- constraint: same-worktree DeepAgents role views are intentionally exclusive; use isolated worktrees rather than weakening the lock.
- constraint: plan/Git are durable truth; runtime threads, receipts, and batch memory are not recovery state.
- alternative: selected-pane-only discovery
  - benefit: fewer probes.
  - trade-off: loses full eligible-set semantics and may miss ownership conflicts.
  - reason rejected: preserve current discovery contract.
- alternative: early `accepted: true` on worker completion
  - benefit: simpler aggregate output.
  - trade-off: conflates execution with task acceptance.
  - reason rejected: violates existing acceptance authority.
- alternative: new supervisor or persistent registry
  - benefit: centralized coordination.
  - trade-off: duplicates plan/runtime ownership and adds recovery state.
  - reason rejected: existing plan ledger and launcher evidence are sufficient for pilot.

## Design Decisions

### Decision: Reuse existing evidence contract

- context: two verdicts proposed consolidation and parallel dispatch.
- selected approach: preserve existing lane lifecycle sections and derive batch results from them; change `_build_assignment_result()` only where field derivation is inconsistent.
- rationale: one SSOT, existing tests, no migration of a second schema.
- alternatives considered: parallel lifecycle record and universal adapter framework.
- accepted trade-offs: executor-specific helper functions remain different behind common evidence meanings.
- affected owners and boundaries: Herdr result builder, DeepAgents classifier, CoS aggregator.

### Decision: Bounded two-lane pilot

- context: concurrency behavior is unproven; dry-run cannot prove worker lifecycle.
- selected approach: cap pilot at two admitted lanes, then expand only after measured evidence.
- rationale: limits contention, retry ambiguity, and cleanup blast radius.
- alternatives considered: unrestricted fan-out and selected-pane-only optimization.
- accepted trade-offs: lower initial throughput; broader rollout waits for evidence.
- affected owners and boundaries: CoS plan, Herdr launcher, Git worktrees, test resources.

### Decision: Separate budgets

- context: command transport, worker execution, and receipt observation have different failure meanings.
- selected approach: retain independent deadlines and classify expiry by budget; observation expiry never proves worker termination.
- rationale: prevents duplicate launches and unsafe cleanup.
- alternatives considered: one universal timeout.
- accepted trade-offs: more explicit result fields and tests.
- affected owners and boundaries: Herdr observation, `dcode-project` worker timeout, coordinator retry logic.

### Decision: Defer active worker cancellation

- context: current `dcode-project` owns worker and descendant termination internally, but no supported external cancellation operation is proven for the pilot.
- selected approach: controller interruption stops new admission and records a cancellation/defer condition; active workers run to bounded owner timeout or normal completion, then receipt and process evidence are reconciled.
- rationale: killing the launcher is not proof that the worker or descendants stopped.
- alternatives considered: force-kill launcher process, invent a new cancellation API, or weaken cleanup proof.
- accepted trade-offs: slower interruption response; no pilot claim of confirmed active cancellation.
- affected owners and boundaries: CoS controller, Herdr observation, `dcode-project` worker/descendant/cleanup owner.

### Compatibility, Migration, and Risk

- old behavior: one lane can execute with current launcher/receipt evidence; dry-run resolves without execution.
- new behavior: plan may admit a bounded independent lane set and aggregate results without changing single-lane semantics; `dispatch_id` remains per invocation and plan lane identity carries retry continuity.
- compatibility boundary: existing `dispatch_id`, `attempt_id`, receipt schema, lifecycle sections, process checks, and role-view lock remain authoritative.
- migration or backfill: no durable migration; existing plans continue as single-lane or sequential waves.
- rollout and rollback: mocked tests → dry-run resolution → sequential control → two harmless real lanes → separate approval for any expansion; disable parallel admission, stop new admission, and reconcile uncertain attempts if any gate fails.
- deprecation or consumer impact: no field removal; compatibility fields remain until existing consumers migrate, if ever.
- risk:
  - mitigation: disjoint worktrees, explicit admission, stale-attempt tests, bounded observation, sibling-preserving aggregation, exact combined-revision review.

## Invariants and Edge Cases

### Invariants

- stable plan task/lane identity survives retries; `dispatch_id` identifies one launcher invocation; each retry has a new `attempt_id`.
- one attempt identity binds delivery, execution, observation, task result, cleanup, and performance facts.
- launcher start never proves delivery; worker completion never proves task acceptance.
- old-attempt receipts never settle replacement attempts.
- same-worktree write-capable DeepAgents launches remain mutually exclusive.
- automatic discovery retains full validated eligible-set semantics.
- unknown ownership, cleanup, delivery, cancellation, or verification remains unknown and blocks unsafe retry or acceptance.
- one lane failure does not erase independent sibling evidence.
- final acceptance reviews exact combined revision.
- CoS/task plan owns dependencies, concurrency budget, aggregation, and acceptance; Herdr owns target binding and top-level lifecycle; `dcode-project` owns worker/descendant/role-view receipt facts; Git owns worktree/branch/base/change truth.

### Edge Cases

- empty or minimal input: zero lanes or one lane uses existing sequential behavior; no parallel coordinator state is created.
- normal and large input: pilot admits at most two lanes; larger sets remain queued or sequential until a later approved rollout.
- duplicate, missing, malformed, or unsupported data: reject duplicate lane IDs, pane bindings, worktrees, overlapping write sets, malformed receipts, and missing attempt IDs.
- retry, cancellation, timeout, partial failure, or concurrency: stop admission on interruption; reconcile uncertain delivery; new attempt only after settled ownership; active cancellation is deferred; preserve siblings; block uncertain cleanup.
- migration or mixed-version state: old single-lane results remain parseable; missing new optional batch metadata never upgrades uncertainty to success.
- generated-source consistency: runtime surface documentation remains aligned with canonical scripts; no generated agent surface changes unless a canonical skill is changed.
- security or accessibility boundary: no new credential path, external write, destructive cleanup, or access broadening.

## Validation Plan

### Backend Verification Claims

- direct boundary: exercise Herdr lane admission, launcher result composition, receipt parsing, and bounded observation through focused Python tests.
- important success and failure behavior: prove admitted independent lanes, rejected conflicts, delivery unknown, confirmed receipt, stale receipt, timeout, cancellation, partial failure, and combined-revision acceptance.
- final state or side effects: verify no duplicate workers, no role-view collision, no unsafe worktree cleanup, preserved per-lane results, and exact combined revision evidence.
- rollback, retry, duplicate, or idempotency behavior: prove same-attempt reconciliation, new-attempt retry, stale-receipt rejection, deferred cancellation, and capacity retention until retirement.
- canonical contract and conformance proof: `deepagents_result_contract.py`, Herdr builder, runtime-surface ownership rules, and plan ledger semantics agree.
- real dependencies requiring proof: two harmless real DeepAgents tasks in separate worktrees and panes after mock, dry-run, and sequential-control gates; no production task.
- representative-operation trace mechanism: capture launcher JSON, receipt JSON, process/ownership evidence, Git revisions, and final verification output for both pilot lanes.
- performance claim and threshold: before the pilot, run three paired sequential-control and parallel trials with identical prompts, profiles, limits, clean worktrees, and implementation revision; require parallel median wall time at least 20% lower, total model usage no more than 110% of sequential control, zero retries, zero duplicate attempts, zero cleanup failures, and positive overlap in every parallel trial. Missing cost telemetry blocks any cost-benefit claim and expansion.

### Acceptance Criterion: Admission preserves isolation

- setup or precondition: two candidate lanes with explicit worktrees, panes, write sets, dependencies, and resource policies.
- action: run admission validation.
- expected result: only dependency-ready, disjoint, isolated lanes are admitted; limit is two.
- failure condition: conflicting lanes admitted or unsafe wave partially launched.
- proof method: focused admission tests and dry-run JSON.
- expected evidence: deterministic admitted/rejected lane records and reasons.

### Acceptance Criterion: Evidence remains attempt-safe

- setup or precondition: attempt A times out or becomes uncertain; attempt B is created after ownership settlement.
- action: deliver late receipt for A while observing B.
- expected result: B remains governed by B evidence; A receipt is retained as stale/foreign evidence.
- failure condition: A receipt settles B or retry occurs before ownership settlement.
- proof method: receipt/parser and launcher tests.
- expected evidence: distinct attempt IDs, explicit reconciliation, no duplicate launch.

### Acceptance Criterion: Coordinator proves real concurrency

- setup or precondition: two admitted mock workers expose a start barrier and a release barrier; capacity limit is two.
- action: start both lanes, hold both at the barrier, attempt a third lane, then release workers in sequence.
- expected result: both workers start before either finishes; third lane remains unstarted while two attempts are occupied; lane output preserves preparation and final assignment records separately.
- failure condition: second worker starts only after first finishes, third lane starts early, or preparation output is treated as final assignment output.
- proof method: deterministic barrier test and controller stream/exit assertions.
- expected evidence: overlapping start interval, third-launch rejection, per-lane output framing, and distinct attempt IDs.

### Acceptance Criterion: Pilot meets declared cost and performance gate

- setup or precondition: three paired trials use identical harmless tasks, profiles, concurrency limit, clean worktrees, and recorded runtime implementation revision.
- action: run sequential control, then parallel pilot; capture elapsed intervals, model usage, retries, duplicate attempts, cleanup failures, and implementation/runtime paths.
- expected result: parallel median wall time is at least 20% lower; model usage is at most 110% of sequential control; overlap is positive in every parallel trial; retries, duplicates, and cleanup failures are zero.
- failure condition: any threshold misses, telemetry is unavailable, or runtime implementation cannot be proven.
- proof method: controller metrics plus independent review of launcher path, `dcode-project` wrapper/version, receipts, and Git revisions.
- expected evidence: reproducible paired-trial table and explicit expansion decision; pilot remains capped at two on failure.

### Acceptance Criterion: Aggregate verdict preserves uncertainty

- setup or precondition: two lanes produce success and unresolved cleanup, or success and conclusive failure.
- action: aggregate lane results and run final integration gate.
- expected result: unresolved state yields `BLOCKED`; conclusive required failure yields `FAIL`; `PASS` requires all required lane and integration proof.
- failure condition: aggregate reports optimistic all-green or discards sibling evidence.
- proof method: mocked batch tests plus final combined-revision review.
- expected evidence: per-lane records remain intact and batch decision cites exact proof.

## Completion Criteria

Specification is complete when:

1. verdict corrections are represented as explicit behavior, not implementation assumptions
2. lane identity, admission, ownership, delivery, execution, observation, cleanup, retry, cancellation, and aggregation contracts are unambiguous
3. existing lifecycle sections and acceptance authority remain the SSOT
4. full discovery semantics and same-worktree locking remain protected
5. pilot scope, rollout gates, rollback, and non-goals are explicit
6. every required outcome maps to executable validation intent
7. implementation plan can name exact files, symbols, commands, dependencies, and stop conditions
