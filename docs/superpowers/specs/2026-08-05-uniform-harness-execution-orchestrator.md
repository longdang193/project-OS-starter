---
artifact_type: spec
template_id: detailed-specification
status: active
layer: change
---

# Uniform Harness Execution Orchestrator

## Goal and Problem

### Problem

- current behavior: `scripts/harness_task.py` resolves task packets through
  `repo_config/harness.yaml` and independently verifies a returned claim, but
  no component owns dispatch, workspace preparation, claim collection, retry,
  escalation, approval resume, and final decision as one lifecycle.
- affected users, systems, or maintainers: controller implementations and all
  task routes using the repository harness.
- evidence: `resolve_task()` emits a packet and `verify_task()` verifies a
  claim, while CLI exposes only `preflight` and `verify`.
- consequence of no change: each controller recreates orchestration glue,
  causing divergent workspace, retry, approval, evidence, and failure behavior.

### Goal

- desired outcome: one packet-driven executor owns deterministic lifecycle
  stages while controller retains classification and final decision authority.
- observable success: every supported execution mode follows the same lifecycle
  and produces one reproducible run record with explicit evidence and decision.

## Required Outcomes

### Outcome: Uniform lifecycle execution

- affected actor or system: controller and harness executor.
- required result: one `run` operation performs preflight, authorization,
  workspace preparation, dispatch, claim collection, verification, and decision
  handling in one ordered lifecycle.
- success condition: no route-specific execution pipeline owns separate state,
  evidence, retry, or approval semantics.

### Outcome: Reproducible run authority

- affected actor or system: controller, agents, reviewers, and auditors.
- required result: each execution has one canonical run record containing the
  request, immutable per-attempt packet snapshots, lanes, claims, evidence,
  frictions, decisions, and state history.
- success condition: a maintainer can identify what was authorized, attempted,
  verified, and decided without reconciling competing lifecycle files.

### Outcome: Honest verification

- affected actor or system: verifier and controller.
- required result: every acceptance criterion has explicit evidence or remains
  unresolved for review; absence of a generic blocker never proves a criterion.
- success condition: automated evidence, review evidence, and approval evidence
  are distinguishable in the run record and final decision.

### Outcome: Controlled mode expansion

- affected actor or system: controller and execution-mode handlers.
- required result: first release executes `single_agent`; later sequential and
  parallel modes use the same lifecycle and run schema when their handlers are
  implemented and verified.
- success condition: unsupported modes block before dispatch and never silently
  downgrade to `single_agent`.

### Outcome: Provider-neutral managed execution

- affected actor or system: controller, harness core, and runtime providers.
- required result: static route policy selects one provider ID and contract
  version into immutable packet state; adapter identity and host evidence must
  match it before managed work or acceptance.
- success condition: adding a conforming provider changes static policy and one
  adapter only; no provider fallback, route-specific lifecycle, verifier, or
  controller path exists.

### Outcome: Bounded runtime and actionable timeout recovery

- affected actor or system: controller, harness core, runtime providers, and
  maintainers.
- required result: static route policy resolves one immutable execution budget
  into each packet; every lane in every topology consumes that same packet
  budget and records structured timeout evidence before controller decides the
  next action.
- success condition: no host CLI flag, hidden provider default, or route-local
  branch can change a packet timeout; a timeout never silently resubmits a
  request or consumes a retry without a recorded controller decision.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
|---|---|---|---|---|
| Where route policy lives | Routes select template, role, rules, skills, tools, workspace, checks, gates, and permitted modes. | `repo_config/harness.yaml` | high | Keep static execution policy canonical in this file. |
| What the harness currently owns | `resolve_task()` returns a packet; `verify_task()` checks diff scope, gates, state transition, and configured checks. | `scripts/harness_task.py` | high | Extend existing owner with lifecycle execution; do not create a second harness. |
| Where role contracts live | Roles define write capability, accepted templates, result kind, and required fields. | `agents/roles.yaml` | high | Keep role contract separate from routing policy. |
| Current verification limitation | Every acceptance criterion is marked proven whenever no blocker exists. | `scripts/harness_task.py` | high | Replace implicit success with criterion-specific evidence. |
| Current authorization limitation | Claim payload can declare `approved_gates`; verifier trusts that value. | `scripts/harness_task.py` | high | Controller-issued approval records must replace agent-declared approval. |
| Current change-set limitation | Changed-path collection uses tracked Git diff only. | `scripts/harness_task.py` | high | Define a complete immutable change-set snapshot, including untracked paths. |
| Current orchestration policy | Sequential and parallel modes declare review and workspace requirements but no executor provisions or dispatches them. | `repo_config/harness.yaml` | high | Treat mode policy and implemented mode capability as separate facts. |

### Prototype and Validation Evidence

- prototype reference: Not applicable. Direction was approved from source and
  harness-test evidence; no UI or external prototype applies.
- validated scenarios and states: packet selection, state-transition rejection,
  scope escape, approval gate, failed check, and evidence-file output have
  focused automated coverage.
- findings incorporated into approved behavior: approval is authorization, not
  semantic review; `allowed_paths` is maximum scope, not planned write intent;
  packet snapshots must be immutable per attempt rather than per whole run.
- rejected alternatives: per-route runners, a persistent scheduler or daemon,
  and a separate prompt-policy layer.

### Scope

- included behavior: a `run` lifecycle operation, per-run record, immutable
  attempt packets, common decisions, evidence-based criteria, common pre/post
  gate evaluation, and single-agent execution first.
- affected boundaries: `scripts/harness_task.py`, harness policy, task/claim
  contracts, role-result validation, local `.harness/` run artifacts, and
  controller-to-agent dispatch adapter.
- admissible cases: a requested mode is admissible only when route policy allows
  it and an executor handler for that mode is registered and verified.
- compatibility expectation: existing standalone `preflight` and `verify`
  behavior remains available while `run` becomes the lifecycle owner.

### Non-Goals

- natural-language task classification inside the Python harness.
- a background daemon, queue, scheduler, or distributed worker pool.
- automatic policy mutation from friction records.
- silently changing route, template, tool set, workspace, or execution mode
  during an attempt.
- a provider-independent hard sandbox where the selected platform cannot impose
  tool restrictions.
- parallel execution in the first executable slice.

### Requirements and Behavioral Contract

#### Requirement: Controller classification and preflight

- trigger or actor: controller receives a user request and chooses task type,
  desired execution mode, allowed scope, planned write paths, and acceptance
  criteria.
- preconditions: task request is structurally valid and names a configured
  route.
- required behavior: executor validates policy and resolves one packet before
  any workspace change or agent dispatch.
- output or state change: run state advances from `classified` to `planned`; a
  packet snapshot is recorded for the attempt.
- failure behavior: invalid route, unsafe paths, unavailable mode, missing role,
  or unavailable required capability returns a machine-readable block decision
  and performs no dispatch.
- observable acceptance: packet records immutable `user_request`, template,
  role, rules, skills, tools, workspace, checks, gates, mode, allowed paths,
  and base reference.

#### Requirement: One lifecycle for every execution mode

- trigger or actor: executor receives a planned attempt with an admissible mode.
- preconditions: packet preflight passed and required authorization is present.
- required behavior: execute this order for every mode: authorize, prepare
  workspace, dispatch lanes, collect claims, verify, emit outcome, obtain
  controller decision, apply transition, and persist.
- output or state change: lifecycle transitions use common run states and common
  decision objects; mode only changes lane count, workspace strategy, and review
  requirement.
- failure behavior: unsupported mode returns `block` with
  `execution_mode_unavailable`; no fallback mode is selected.
- observable acceptance: a single-agent attempt has one lane; later sequential
  and parallel attempts use the same outer record and decision protocol.

#### Requirement: Immutable packet per attempt

- trigger or actor: controller retries or escalates a run.
- preconditions: previous attempt has a recorded decision.
- required behavior: controller creates a successor attempt and preflights a
  new packet snapshot; prior attempt packet, claim, evidence, and decision stay
  unchanged.
- output or state change: successor attempt is `planned` before dispatch.
- failure behavior: changing a packet in place is invalid and blocks run
  continuation until a successor attempt is created.
- observable acceptance: escalation from `single_agent` to `parallel_lanes`,
  when parallel support exists, creates a later attempt rather than mutating
  attempt one.

#### Requirement: New-run and continuation symmetry

- trigger or actor: controller starts a managed run or resumes a `planned`
  attempt.
- preconditions: a new request has no existing run record, or an existing run
  ID resolves to exactly one `planned` active attempt.
- required behavior: one provider entrypoint accepts exactly one input form:
  request creates a new run; run ID continues the existing packet with no
  request resubmission. Continuation reuses the active immutable packet and
  never creates a duplicate initial attempt.
- output or state change: continuation dispatches the already planned attempt;
  new-run creation records attempt one before any host dispatch.
- failure behavior: a request for an existing run ID, a continuation request
  that differs from stored request, or a non-`planned` run blocks without
  workspace preparation.
- observable acceptance: `--request` and `--run-id` are mutually exclusive;
  a controller can resume a retry-created planned attempt without creating a
  successor run.

#### Requirement: Immutable execution budget

- trigger or actor: harness core resolves a managed packet.
- preconditions: route and selected orchestration mode are valid.
- required behavior: `repo_config/harness.yaml` owns named bounded execution-
  budget profiles, each route's initial profile, and each profile's permitted
  timeout decisions plus optional named escalation target. Core validates them
  and writes one normalized `execution_budget` object into packet state,
  including profile identity, `turn_timeout_seconds`, permitted timeout
  decisions, and only one policy-named successor profile. Host consumes this
  resolved value for every work, integration, validation, and check operation.
- output or state change: packet and host evidence identify the exact timeout
  budget used by each lane.
- failure behavior: missing, malformed, out-of-policy, or host-unenforceable
  budget blocks before dispatch. No provider CLI timeout override, fallback
  default, or in-place packet mutation is permitted.
- observable acceptance: `single_work_lane`, `sequential_work_lanes`, and
  `parallel_work_lanes` use identical budget resolution and evidence shape.

#### Requirement: Timeout evidence and controller recovery

- trigger or actor: provider reaches a packet turn timeout or terminally
  interrupts a timed-out turn.
- preconditions: host has a dispatched packet lane.
- required behavior: host returns normalized timeout evidence containing lane
  ID, configured timeout, elapsed time, terminal status, event-trace summary,
  last observed tool call, and completed command count. Core records it under
  the active attempt and exposes an explicit timeout outcome to controller.
- output or state change: run remains decision-pending; controller records
  `block`, or `escalate` only through packet-named successor budget profile.
  Timeout never causes automatic retry or acceptance.
- failure behavior: missing terminal-interrupt proof or incomplete timeout
  evidence blocks the run and remains distinguishable from a generic dispatch
  failure.
- observable acceptance: maintainers can classify a timeout as prompt stall,
  productive budget exhaustion, or hung command from one run record.

#### Requirement: Explicit lane plan

- trigger or actor: controller requests a managed execution mode.
- preconditions: selected mode is admissible for the route and executor.
- required behavior: packet records a normalized lane plan. Each lane has stable
  `lane_id`, role, allowed paths, dependency IDs, workspace requirement, and
  write capability. `single_agent` normalizes to one `primary` lane.
- output or state change: sequential lanes execute in declared dependency order;
  parallel writable lanes have no unresolved dependencies and disjoint allowed
  paths.
- failure behavior: duplicate lane ID, unknown dependency, dependency cycle, or
  overlapping writable paths blocks before workspace preparation.
- observable acceptance: later execution modes add lane data, not a separate
  lifecycle or a route-specific runner.

#### Requirement: Workspace preparation and lane ownership

- trigger or actor: executor begins an authorized attempt.
- preconditions: mode capability is available.
- required behavior: every host-managed writable lane provisions an
  adapter-owned isolated workspace. The adapter dispatches writers only in that
  workspace and must prove their sandbox cannot write outside it. Parallel
  writable lanes require disjoint allowed paths and isolated workspaces.
  Ambient desktop or CLI threads outside the adapter are source-first,
  unvalidated work; they are never part of a managed run.
- output or state change: each lane records workspace kind, stable path or
  worktree identity, role, allowed paths, and attempts.
- failure behavior: unavailable workspace capability, dirty-conflict policy, or
  overlapping writable paths blocks before dispatch.

### Outcome: Uniform multi-lane final state

- affected actor or system: host adapter final-state effects.
- required result: `sequential_work_lanes` permits only one linear work-lane
  dependency chain. Each successor receives a fresh base clone with direct
  predecessor changes materialized. `parallel_work_lanes` materializes isolated
  writer changes into one fresh base clone in lane-ID order, rejecting same
  actual changed paths.
- success condition: all successful modes run checks and one fresh read-only
  validator against the same final workspace. Unsupported file states or failed
  integration stop before checks or validator dispatch.
- initial support: regular-file adds, modifications, deletions, and untracked
  regular files. Renames, copies, unmerged entries, type changes, submodules,
  and symlinks fail closed until direct proof expands support.
- observable acceptance: any managed writer using controller source workspace,
  or escaping its adapter-owned workspace, blocks the run. Validators use the
  final isolated state with a host-enforced read-only sandbox.

#### Requirement: Agent dispatch and claim collection

- trigger or actor: executor dispatches an authorized lane.
- preconditions: packet, workspace, selected template, role contract, and
  required platform capability are available.
- required behavior: a host dispatch adapter receives lane ID, immutable packet,
  workspace identity, timeout, and cancellation token; it returns either one
  normalized `claimed_result` or normalized dispatch failure. Agent prompt is
  rendered from packet and role contract; prompt is derived presentation, never
  a policy source. Agent returns only a `claimed_result` matching role-required
  fields.
- output or state change: lane claim is attached to its attempt in the run
  record; state advances from `running` to `observed` after all required lane
  claims arrive.
- failure behavior: dispatch error, missing claim, invalid result kind, or
  missing required fields produces a common decision without accepting work.
- observable acceptance: agents never write the shared run record and never
  spawn child agents.

#### Requirement: Complete change-set snapshot

- trigger or actor: executor begins verification for an observed attempt.
- preconditions: attempt packet has a base reference resolved to an immutable
  commit ID before dispatch.
- required behavior: controller derives actual changed paths from tracked added,
  modified, deleted, renamed, and staged changes against that commit plus
  untracked nonignored paths. It records path and change kind in attempt
  evidence; agent-reported `changed_files` is advisory only.
- output or state change: scope and post-execution gate evaluation consume this
  recorded snapshot.
- failure behavior: unresolved base commit, malformed path, or incomplete
  change-set collection blocks acceptance.
- observable acceptance: an untracked file outside allowed scope cannot bypass
  scope or protected-path checks.

#### Requirement: Evidence-based verification

- trigger or actor: executor collects an observed attempt.
- preconditions: claims are structurally valid.
- required behavior: verifier evaluates actual changed paths, configured checks,
  gates, transitions, and one evidence declaration per acceptance criterion.
- output or state change: each criterion stores `proven`, `failed`, or
  `review_required` with evidence reference; state advances through `verifying`.
- failure behavior: missing evidence declaration, failed evidence, scope escape,
  unapproved protected change, or failed configured check prevents acceptance.
- observable acceptance: no criterion is auto-proven solely because unrelated
  checks passed.

#### Requirement: Common gate engine

- trigger or actor: executor preflights a write-capable attempt and verifies an
  observed attempt.
- preconditions: route defines approval gates or defaults apply.
- required behavior: one path-matching mechanism evaluates gate policy twice:
  first against `planned_write_paths`, then against actual changed paths.
  Only controller-issued approval records may satisfy a gate; agents cannot
  declare approvals in claims.
- output or state change: unapproved planned protected paths request approval
  before dispatch; unapproved actual protected paths prevent acceptance after
  execution.
- failure behavior: `planned_write_paths` is required for new write-capable
  managed-run requests. Legacy standalone tasks retain existing post-change
  gate behavior.
- observable acceptance: `allowed_paths` remains authorization maximum and is
  never reused as planned-write input.

#### Requirement: Uniform decision protocol

- trigger or actor: preflight, authorization, workspace, dispatch, collection,
  verification, or review cannot continue normally.
- preconditions: run has an active attempt.
- required behavior: executor emits one machine-readable outcome with reason,
  evidence references, and allowed decisions. Controller records one decision
  object with `kind`, `next_state`, and optional successor-attempt instruction.
- output or state change: supported kinds are `accept`, `retry`, `escalate`,
  `request_approval`, and `block`.
- failure behavior: unknown kind or invalid state transition blocks the run.
- observable acceptance: controller handles every failure source through the
  same decision shape without route-specific branches; executor never accepts,
  retries, escalates, or approves autonomously.

#### Requirement: Bounded retries and approval resume

- trigger or actor: controller receives retry, escalation, approval, or block
  outcome.
- preconditions: static route policy names one retry policy.
- required behavior: harness policy owns maximum attempts, retryable reasons,
  escalation after exhaustion, and approval-resume rules. Approval record binds
  gate, approver identity, approved path scope, attempt ID, and issuance time.
- output or state change: retry or escalation creates a successor planned
  attempt; approval resume creates a successor planned attempt only when its
  record matches requested scope and gate.
- failure behavior: exhausted retry budget, invalid controller decision, stale
  approval, or decision outside allowed outcome blocks the run.
- observable acceptance: no agent claim can bypass a gate or create unbounded
  retry loop.

#### Requirement: Friction capture without autonomous mutation

- trigger or actor: agent, workspace, tool, or verifier reports degraded or
  blocked progress.
- preconditions: friction has a normalized category and source attempt or lane.
- required behavior: executor records friction in the run record and includes
  it in decision evidence. Harness policy does not change during the run.
- output or state change: friction is classified as informational, retryable,
  escalating, or blocking by the common decision protocol.
- failure behavior: malformed friction is rejected from the claim; repeated
  verified friction may later enter the separate harness-improvement route.
- observable acceptance: a non-blocking observation does not fail unrelated
  verification merely because it exists.

### Constraints and Alternatives

- constraint: static policy and mutable execution history have different owners.
- alternative: per-route runners.
  - benefit: direct short-term implementation.
  - trade-off: duplicated state, evidence, and failure semantics.
  - reason rejected: violates symmetry and creates policy drift.
- alternative: daemon or scheduler.
  - benefit: asynchronous queueing and background workers.
  - trade-off: durable service, worker, queue, and recovery complexity.
  - reason rejected: one foreground lifecycle command meets current need.
- alternative: separate prompt-policy templates.
  - benefit: provider-specific wording.
  - trade-off: packet and prompt can conflict.
  - reason rejected: prompts must render resolved packet only.

## Design Decisions

### Decision: Controller decides; executor applies deterministic transitions

- context: controller must retain final authority, while every lifecycle stage
  needs uniform machine-readable handling.
- selected approach: verifier and executor emit an outcome containing evidence,
  reason, and allowed decisions. Controller records the decision; executor
  validates and applies only that recorded decision.
- rationale: prevents automatic retries, escalation, acceptance, or approval
  from bypassing controller authority while preserving one decision protocol.
- state contract:

  | Current state | Event or decision | Next state |
  |---|---|---|
  | `classified` | valid preflight | `planned` |
  | `planned` | authorized dispatch | `running` |
  | `running` | complete claims | `observed` |
  | `running` | dispatch interruption | `blocked` |
  | `observed` | verification starts | `verifying` |
  | `verifying` | outcome requires controller decision | `awaiting_decision` |
  | `awaiting_decision` | `accept` | `accepted` |
  | `awaiting_decision` | `retry` or `escalate` | `planned` for successor attempt |
  | `awaiting_decision` | `request_approval` or `block` | `blocked` |
  | `blocked` | matching controller approval resume | `planned` for successor attempt |

- alternatives considered: executor choosing decisions; controller-specific
  failure branches.
- accepted trade-offs: controller integration must submit explicit decisions.
- affected owners and boundaries: controller adapter, state policy, run writer,
  verifier, and CLI/API response contract.

### Decision: Dispatch adapter capability contract

- context: Python harness code cannot assume every host runtime can spawn an
  agent, create isolated workspaces, cancel work, or enforce selected tools.
- selected approach: host provides one dispatch adapter with stable operations:
  `capabilities`, `prepare_workspace`, `dispatch_lane`, `cancel_lane`, and
  `collect_claim`. Capabilities declare supported execution modes, workspace
  modes, tool-control level (`enforced`, `advisory`, or `unavailable`), timeout,
  and cancellation support.
- rationale: route policy remains provider-neutral while preflight truthfully
  intersects policy with executable host capability.
- alternatives considered: Python directly invoking provider-specific tools;
  treating prompt wording as hard tool enforcement.
- accepted trade-offs: first release requires a concrete host adapter or a
  deterministic block; fake adapter remains test-only.
- affected owners and boundaries: host controller integration, executor,
  capability registry, packet, and run evidence.

### Decision: Change-set and approval records are controller-owned evidence

- context: agent claims and tracked Git diff alone cannot safely prove protected
  scope or complete changed paths.
- selected approach: controller resolves base commit before dispatch, writes one
  immutable change-set snapshot after execution, and writes approvals outside
  agent claims. Approval record contains gate, approver identity, path scope,
  attempt ID, issuance time, and optional expiry.
- rationale: prevents untracked-file scope escape and agent-forged approval.
- alternatives considered: trusting `changed_files` or `approved_gates` from
  claim payload.
- accepted trade-offs: controller performs extra Git inspection and approval
  records contain audit metadata.
- affected owners and boundaries: change-set collector, gate engine, controller,
  run record, and verifier.

### Decision: Lane plan and retry policy are explicit policy data

- context: later modes need lane topology and bounded recovery without new
  lifecycle branches.
- selected approach: managed request names a lane plan and route names one retry
  policy. Lane plan owns lane IDs, roles, dependencies, and intended writable
  scope; retry policy owns attempt limit, retryable reasons, and exhaustion
  outcome.
- rationale: parallelism and recovery differ by data, not duplicated runner
  logic.
- alternatives considered: inferring lanes from agent output; hard-coding retry
  limits in controller prompts.
- accepted trade-offs: managed requests carry more structured metadata.
- affected owners and boundaries: task schema, harness policy, preflight,
  controller, and tests.

### Decision: Runtime budget is policy-resolved packet data

- context: a fixed host timeout can hide prompt stalls, productive long-running
  work, and hung commands behind one generic dispatch failure.
- selected approach: `repo_config/harness.yaml` owns named bounded execution-
  budget profiles, each route's initial profile, and each profile's permitted
  timeout decisions and optional named escalation target. Packet resolution
  freezes one resolved `execution_budget`, including profile identity and its
  optional successor profile; every host lane consumes it and returns
  normalized timeout evidence.
- rationale: timeout behavior differs by configured data, not provider CLI
  flags, topology branches, or undocumented deployment defaults.
- alternatives considered: one host-wide hard-coded timeout; arbitrary CLI
  timeout override; automatic retry after timeout.
- accepted trade-offs: policy and packet schema gain one small object and
  profile transition; hosts must reject a budget they cannot enforce. A
  controller cannot invent an arbitrary larger timeout.
- affected owners and boundaries: harness policy, packet resolver, host
  adapter, run evidence, controller, and conformance tests.

### Decision: Continuation reuses planned packet identity

- context: retry decisions create a planned successor attempt, but resubmitting
  its original request creates a duplicate-run conflict instead of dispatching
  that attempt.
- selected approach: provider CLI has mutually exclusive new-run request and
  continuation run-ID inputs. Continuation calls the core with `request=None`
  and the existing run ID; core alone validates active planned state.
- rationale: new work and continuation remain one symmetric boundary while run
  authority and immutable packet identity stay in core.
- alternatives considered: host recreating request from `run.json`; a separate
  resume runner; silently creating a new run ID.
- accepted trade-offs: controllers must retain run IDs and choose an explicit
  decision before a later attempt exists.
- affected owners and boundaries: provider CLI, harness core, controller,
  run record, and deployment procedure.

### Decision: Static policy, role contract, and run state have separate SSOTs

- context: routing policy, role requirements, and one execution's mutable state
  change at different rates and must not be duplicated.
- selected approach: `repo_config/harness.yaml` owns static route policy;
  `agents/roles.yaml` owns role contract; `.harness/runs/<run-id>/run.json`
  owns one run's mutable record.
- rationale: one owner per fact preserves reproducibility without placing
  mutable state in policy or repeating route details in roles.
- alternatives considered: one giant configuration file; packet, claim, and
  evidence files with independent authority.
- accepted trade-offs: run record is a larger structured document and requires
  atomic controller-only writes.
- affected owners and boundaries: harness policy, role catalog, executor, and
  local ignored `.harness/` artifacts.

### Decision: Attempt packets are immutable; run contains attempts

- context: retries and escalations may need new template, role, mode, scope, or
  review policy while prior authorization must remain auditable.
- selected approach: every attempt stores its own immutable packet snapshot;
  top-level run stores request, state history, and ordered attempts.
- rationale: preserves original authorization and enables mode escalation
  without mutating history.
- alternatives considered: one mutable packet per run; one independent file per
  attempt stage.
- accepted trade-offs: run consumers read the active attempt rather than a
  top-level packet field.
- affected owners and boundaries: controller preflight, executor, verifier, and
  run-artifact reader.

### Decision: Policy permission and executor capability are distinct

- context: a route can permit a mode before local runtime has its tested handler.
- selected approach: route policy determines whether a mode is allowed; executor
  capability registry determines whether it is implemented. A mode runs only at
  their intersection.
- rationale: avoids configuration claiming behavior unavailable in current
  runtime while preserving future route policy.
- alternatives considered: silently downgrade modes; remove all future modes
  from policy until implementation.
- accepted trade-offs: preflight can return `execution_mode_unavailable`.
- affected owners and boundaries: harness policy, executor capability registry,
  controller, and tests.

### Decision: Managed enforcement is adapter-owned workspace containment

- context: current Codex runtime can enforce per-thread sandboxes and relay
  approvals, but exposes no repository-owned global hook that can intercept
  unrelated desktop or CLI threads.
- selected approach: managed authority covers only lanes created by the host
  adapter. Every managed writer receives an adapter-owned isolated workspace
  with host `workspace-write` sandbox; every validator receives the materialized
  final workspace with host `read-only` sandbox. Ambient threads remain outside
  the managed lifecycle and are source-first, unvalidated work.
- rationale: native, directly testable containment is enforceable now; a global
  hook claim is not.
- alternatives considered: require `UserPromptSubmit`/`PreToolUse` global
  session binding; accept unmanaged ambient work as managed; prompt-only write
  restrictions.
- accepted trade-offs: harness cannot stop a user from running an unrelated
  desktop or CLI agent. It can never accept that work as part of a managed run.
- affected owners and boundaries: host adapter, workspace preparation,
  integration, packet evidence, and feasibility tests.

### Decision: Controller is sole run-record writer

- context: parallel lanes cannot safely mutate one shared JSON record.
- selected approach: agents return claims to controller; controller validates and
  atomically persists every run update with ordered state history.
- rationale: preserves one run SSOT and avoids concurrent-write corruption.
- alternatives considered: agents writing lane JSON files; shared writable
  `run.json`.
- accepted trade-offs: controller must collect complete claims before persistence.
- affected owners and boundaries: dispatch adapter, agent protocol, local run
  artifact writer.

### Decision: Review and approval are different evidence paths

- context: human permission to touch protected policy differs from a reviewer
  judging semantic behavior.
- selected approach: approval gates authorize actions; semantic criteria use
  reviewer or manual-review evidence. Neither substitutes for the other.
- rationale: prevents protected-path permission from falsely proving product
  quality and prevents semantic uncertainty from authorizing protected changes.
- alternatives considered: treating all semantic uncertainty as approval.
- accepted trade-offs: some tasks require a review step before acceptance.
- affected owners and boundaries: criteria schema, review roles, approval gate
  records, and controller decision.

### Compatibility, Migration, and Risk

- old behavior: controller separately invokes `preflight`, dispatches work, and
  invokes `verify`; version-1 task criteria are plain strings, approval data is
  claim-supplied, and verify may auto-prove criteria after no blockers.
- new behavior: `run` owns orchestration; managed-run requests use typed
  evidence criteria and planned write paths; standalone commands remain usable.
- compatibility boundary: existing version-1 `preflight` and `verify` inputs
  remain supported. Version-1 criteria cannot be auto-accepted by managed run
  without explicit review evidence, and version-1 claim approvals never satisfy
  managed-run gates.
- migration or backfill: Not applicable to repository data. Controllers migrate
  request producers to typed criteria and `planned_write_paths` before relying
  on managed execution.
- rollout and rollback: enable only `single_agent` capability first; retain
  standalone commands as rollback path until managed-run evidence is stable.
- deprecation or consumer impact: no immediate removal of existing CLI commands
  or packet fields.
- risk:
  - provider cannot hard-restrict selected tools.
    - mitigation: dispatch adapter applies host sandbox containment to its own
      workspace, records direct write/escape evidence, and verifier never
      claims global desktop enforcement.
  - interrupted write corrupts run history.
    - mitigation: controller writes atomically and validates record before each
      transition.
  - retry loops waste tokens.
    - mitigation: policy defines bounded retry count and escalation/block
      decision after exhaustion.

## Invariants and Edge Cases

### Invariants

- every dispatched lane has one validated immutable packet snapshot.
- every managed writable lane runs only in its adapter-owned isolated workspace;
  ambient threads have no managed run authority.
- controller alone writes run state and performs accept, retry, escalate, and
  approval-resume transitions.
- no mode silently changes or falls back after preflight.
- every changed path is checked against allowed scope and post-execution gates.
- every automated acceptance claim cites declared evidence.
- approval authorization never proves semantic review; semantic review never
  grants protected-path authorization.
- generated prompts and adapter surfaces never become policy SSOTs.
- friction recording never mutates harness policy during an active run.
- every packet-selected lane receives the same immutable execution budget;
  providers cannot add a hidden timeout override or fallback default.
- timeout evidence distinguishes terminal timeout from generic dispatch failure;
  controller records the next decision before any successor attempt exists.
- a timeout permits `escalate` only when current packet names one valid
  successor budget profile. `retry` never substitutes for timeout escalation;
  controller creates one successor packet only after explicit escalation.
- continuation dispatches only an existing `planned` attempt and never
  resubmits its stored request.

### Edge Cases

- empty or minimal input: missing task type, criteria, base reference, planned
  write paths for managed write work, or mode produces preflight block.
- normal and large input: one run may contain multiple attempts and lanes;
  record size remains bounded by truncated command output and referenced artifact
  paths rather than unbounded raw logs.
- duplicate, missing, malformed, or unsupported data: duplicate run ID, invalid
  decision, invalid claim, forged approval, unknown check, unknown evidence
  kind, invalid lane graph, retry-policy mismatch, and unknown mode block
  without dispatch.
- retry, cancellation, timeout, partial failure, or concurrency: cancellation,
  timeout, missing lane claim, or partial parallel failure records decision and
  preserves completed lane evidence. Timeout records configured budget and
  terminal trace summary. An explicit escalation can create one successor only
  through the packet-named budget profile; retry creates successor attempt only
  after explicit retry-policy-permitted controller decision.
- migration or mixed-version state: legacy standalone version-1 requests remain
  valid; managed runs require typed criteria before automatic acceptance.
- generated-source consistency: canonical policy, roles, skills, and rules are
  edited at source and adapter synchronization runs before managed execution.
- security boundary: task-provided criteria can select only configured checks;
  task input cannot supply arbitrary shell commands or escape workspace paths;
  claims cannot supply approvals; change-set collection includes untracked
  nonignored paths.

## Validation Plan

### Backend Verification Claims

- direct boundary: JSON request, packet, run record, claim, evidence, and
  decision schemas reject malformed and unsafe input.
- important success and failure behavior: prove single-agent success, failed
  check, invalid claim, unsupported mode, scope escape, pre-gate approval,
  post-gate approval, review-required criterion, retry, escalation, and
  interrupted-run recovery, continuation of a planned attempt, and timeout
  evidence with terminal interruption.
- final state or side effects: verify atomic `run.json`, immutable prior
  attempts, workspace cleanup or preservation policy, and no dispatch before a
  blocking preflight or gate decision.
- rollback, retry, duplicate, or idempotency behavior: rerunning an interrupted
  operation resumes or blocks from recorded state without duplicating accepted
  side effects; retry creates one successor attempt.
- canonical contract and conformance proof: validate harness policy references,
  role contracts, request/claim/run schemas, and generated adapter drift.
- real dependencies requiring proof: platform dispatch and workspace worktree
  behavior require representative integration proof when handlers are added.
- representative-operation trace mechanism: per-run state history, lane claims,
  command evidence, decisions, friction records, and timeout trace summary in
  `run.json`.
- performance claim and threshold: packet budget bounds each foreground turn;
  timeouts require evidence-based classification before a controller selects a
  packet-named higher permitted budget or a smaller task slice.

### Acceptance Criterion: Single lifecycle owner

- setup or precondition: valid managed-run request for supported `single_agent`.
- action: execute run through an agent claim and verification.
- expected result: one run record contains packet, one lane, claim, evidence,
  decision, and ordered transitions through accepted or blocked state.
- failure condition: controller needs a route-specific runner or separate
  lifecycle authority to finish task.
- proof method: direct harness test with fake dispatch and check runners.
- expected evidence: validated run record and automated test output.

### Acceptance Criterion: Policy and capability intersection

- setup or precondition: route permits a mode without registered executor
  handler.
- action: preflight managed run for that mode.
- expected result: no workspace or agent is created; decision is
  `block/execution_mode_unavailable`.
- failure condition: executor silently runs another mode.
- proof method: direct harness test with dispatch spy.
- expected evidence: no dispatch call and recorded blocking decision.

### Acceptance Criterion: Immutable escalation

- setup or precondition: first attempt completes with escalation decision.
- action: controller starts successor attempt with a different permitted mode or
  template.
- expected result: attempt one packet and evidence remain unchanged; attempt two
  has separate packet and lane set.
- failure condition: original packet is overwritten.
- proof method: direct run-record transition test.
- expected evidence: before/after record comparison.

### Acceptance Criterion: Symmetric budget and continuation

- setup or precondition: routes permitting each supported topology and a run
  with a controller-escalated `planned` attempt using packet-named successor
  budget profile.
- action: resolve packets, dispatch through conforming host test adapter, then
  continue the planned run by ID.
- expected result: every lane receives the packet budget; continuation uses the
  existing attempt without request resubmission or duplicate run creation.
  Prior packet remains unchanged; successor receives only the static,
  packet-named profile.
- failure condition: host changes the budget, CLI accepts both inputs, or core
  creates another attempt before controller decision.
- proof method: parameterized core tests, host adapter conformance tests, and
  one live App Server continuation proof.
- expected evidence: immutable packet comparison, host lane evidence, and one
  `run.json` continuation record.

### Acceptance Criterion: Actionable timeout evidence

- setup or precondition: host turn reaches configured packet timeout and
  terminal interruption completes.
- action: collect timeout failure through core lifecycle.
- expected result: active attempt remains decision-pending with configured
  budget, elapsed time, terminal status, event summary, last tool call, and
  completed command count.
- failure condition: timeout is recorded as opaque generic failure, silently
  retries, or accepts work.
- proof method: deterministic host timeout test plus core transition test.
- expected evidence: normalized timeout object in `run.json` and controller
  decision options constrained by packet policy.

### Acceptance Criterion: Honest criteria and review separation

- setup or precondition: one command criterion, one file or diff criterion,
  and one semantic review criterion.
- action: run verification with automated evidence passing and review absent.
- expected result: automated criteria are proven; semantic criterion is
  `review_required`; run cannot accept until reviewer evidence exists.
- failure condition: no blocker marks all criteria proven or approval substitutes
  for review.
- proof method: direct verifier tests.
- expected evidence: criterion-level verification results and decision.

### Acceptance Criterion: Symmetric gates

- setup or precondition: protected path appears in planned write paths or actual
  Git diff.
- action: evaluate authorization before dispatch and verification after claim.
- expected result: shared matcher produces approval decision before dispatch and
  prevents acceptance after unapproved actual protected change.
- failure condition: separate path-policy logic yields divergent results.
- proof method: parameterized gate-engine tests with same patterns and both
  inputs.
- expected evidence: matching blocker or approval-decision records.

## Completion Criteria

Specification is complete when:

1. one run lifecycle, run authority, per-attempt packet immutability, criteria
   evidence, gate semantics, decision protocol, and mode admissibility are
   explicit
2. static policy, role contract, and mutable run state have one named owner
3. approval, review, retry, escalation, and blocked behavior are distinguished
4. first-slice and later-mode compatibility boundaries are explicit
5. every required outcome maps to direct validation intent
6. no unresolved design question requires an implementation-time policy choice
7. timeout, continuation, and deployment-freshness behavior have one named
   owner and direct proof intent
8. implementation sequencing remains outside this specification
