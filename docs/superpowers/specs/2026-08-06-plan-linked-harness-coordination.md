---
artifact_type: spec
template_id: detailed-specification
status: active
layer: change
related_spec: docs/superpowers/specs/2026-08-05-uniform-harness-execution-orchestrator.md
---

# Plan-Linked Harness Coordination

## Goal and Problem

### Problem

- current behavior or opportunity: specifications define approved behavior and
  implementation plans define tasks, while managed packets and `run.json`
  define one execution lifecycle. No contract binds a managed run to one plan
  task or defines how a controller hands coordination-heavy work to a later
  session.
- affected users, systems, or maintainers: controller agents, human reviewers,
  host adapters, and maintainers resuming multi-session, sequential-lane, or
  parallel-lane changes.
- evidence: managed runs preserve immutable packets, attempts, evidence, and
  controller decisions; plans preserve task order and handoff prose. Neither
  currently names the other as authoritative coordination context.
- consequence of no change: a later controller must infer intended task,
  ownership, base revision, and recovery state from prose and runtime files.
  Concurrent coordination can select overlapping changes without one explicit
  conflict rule.

### Goal

- desired outcome: one active implementation plan becomes durable coordination
  truth for coordination-heavy work. Every managed execution packet binds to
  one immutable plan task and normalized coordination manifest. `run.json`
  remains runtime, evidence, and handoff truth.
- observable success: a fresh controller session can read one active plan,
  identify next admissible task, create or continue only a valid managed run,
  and record verified progress without reconstructing coordination from chat
  history or creating a second scheduler.

## Required Outcomes

### Outcome: Plan-owned coordination manifest

- affected actor or system: plan author, controller, plan validator, and
  packet resolver.
- required result: a coordination-heavy implementation plan contains one
  machine-readable, Git-tracked manifest in its frontmatter. The plan file
  remains the sole durable source for coordination task IDs, dependencies,
  requested topology, target branch, and planned write ownership.
- success condition: every referenced `plan_task_id` resolves to exactly one
  manifest task, and prose task sections reference that ID instead of copying
  coordination fields.

### Outcome: Immutable plan-to-packet binding

- affected actor or system: controller, harness core, and host adapter.
- required result: every coordinated managed packet contains `plan_ref`,
  `plan_task_id`, and `plan_digest`. Packet resolution
  rejects absent, malformed, changed, inactive, or incompatible plan context
  before workspace preparation or dispatch.
- success condition: a run attempt remains attributable to normalized manifest
  bytes, task, and existing packet `base_commit`. A manifest change creates a
  successor attempt; prior packet and evidence remain immutable.

### Outcome: Session-safe handoff and recovery

- affected actor or system: controller agents and human maintainers.
- required result: controller derives task state from packets linked by
  `plan_ref` and `plan_task_id`. Runtime state, managed run identity, concise
  handoff, host handles, claims, logs, and evidence remain only in `run.json`.
- success condition: an interrupted session never claims resume of an unknown
  host turn. Controller either continues a planned packet whose plan binding is
  still valid or creates a successor attempt from active plan state.

### Outcome: Symmetric topology coordination

- affected actor or system: all `single_work_lane`,
  `sequential_work_lanes`, and `parallel_work_lanes` requests.
- required result: every topology consumes same plan-task contract, packet
  binding, run lifecycle, handoff rules, and controller decisions. Topology
  changes only lane/workspace data.
- success condition: no topology receives a separate planner, plan format,
  run registry, or acceptance path.

### Outcome: Bounded conflict control

- affected actor or system: controllers starting coordinated tasks.
- required result: first version serializes controller task activation for one
  active plan and target branch. Ordered tasks may reuse paths only after
  dependencies complete. Parallel lanes remain subject to existing disjoint-path
  and isolated-workspace rules.
- success condition: one controller detects overlap before dispatch from plan
  manifests. Simultaneous controller activation is unavailable until explicit
  concurrency protocol exists; no lease, heartbeat, distributed lock, or global
  job scheduler is required for first version.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
|---|---|---|---|---|
| Where do approved behavior and task order live? | Specifications own behavior; plans own exact tasks, dependencies, execution approach, and verification. | `.agents/skills/skill-spec-drafting/SKILL.md`; `docs/operating_system/planning/planning-dispatch.md` | high | Keep plan as durable coordination source; do not create a coordination database. |
| Where does one managed execution live? | Immutable packet and mutable `run.json` own attempts, evidence, and controller decisions. | `scripts/harness_task.py`; `docs/operating_system/procedures/managed-execution-adapter-contract.md` | high | Preserve `run.json` as execution-only truth. |
| Which topologies already exist? | Policy defines canonical single, sequential, and parallel work-lane modes with isolated workspaces and validator role. | `repo_config/harness.yaml` | high | Add one plan-task interface for all topologies. |
| How does retry work? | Controller creates successor packet/attempt; earlier packet remains unchanged. | `scripts/harness_task.py:apply_controller_decision` | high | Plan changes or interrupted work must use same successor rule. |
| What is current handoff guidance? | Active plan or user response contains last task, repository state, evidence, next action, and blockers. | `.agents/skills/skill-executing-plans/SKILL.md` | high | Make plan handoff fields structured for coordinated work; keep prose concise. |

### Prototype and Validation Evidence

- prototype reference or `Not applicable: no UI or runtime prototype is needed`.
- validated scenarios and states: existing managed topology proof establishes
  isolated writer, final-state integration, fresh read-only validation, and
  controller acceptance boundaries.
- findings incorporated into approved behavior: coordination must link to those
  boundaries rather than introduce a second executor or acceptance path.
- rejected alternatives: a lease/heartbeat service, a separate coordination
  database, a global scheduler, host-turn resume claims, and per-topology plan
  formats.

### Scope

- included behavior:
  - optional plan coordination manifest for coordination-heavy implementation
    plans;
  - stable plan task IDs and plan-to-packet binding;
  - derived task state, run-owned compact handoff record, and controller
    pre-dispatch conflict check;
  - plan/template/skill/AGENTS guidance, validation, generated adapters, and
    starter-kit synchronization.
- affected boundaries: plan drafting, plan execution, managed packet resolution,
  run lifecycle, controller decisions, routing guidance, and plan validation.
- admissible cases:
  - ordinary local work without coordination manifest;
  - one controller across multiple sessions;
  - one task in `single_work_lane`;
  - dependency-ordered tasks in `sequential_work_lanes`;
  - disjoint concurrent tasks/lanes in `parallel_work_lanes`.
- compatibility expectation: existing specifications, non-coordinated plans,
  unmanaged source-first work, and historical runs remain valid.

### Non-Goals

- distributed lock, lease, heartbeat, global queue, background scheduler, or
  automatic work claiming;
- simultaneous controller task activation or dispatch for same active plan and
  target branch;
- resuming an interrupted host thread or claiming host process persistence;
- replacing Git plan history, `run.json`, friction ledger, host adapter, or
  controller decision authority;
- automatic routing, conflict resolution, retry, policy mutation, or acceptance.

### Requirements and Behavioral Contract

#### Requirement: Coordination manifest

- trigger or actor: author marks implementation plan as coordination-heavy.
- preconditions: plan uses `artifact_type: plan`; plan is in repository and
  is Git-tracked and names canonical target branch/base reference.
- required behavior: plan frontmatter contains zero or one `coordination`
  object; its presence enables coordinated execution. Unknown fields fail.
  Its normalized YAML shape is:

  ```yaml
  coordination:
    target_branch: main
    base_ref: HEAD
    tasks:
      - id: task-1
        depends_on: []
        execution_mode: single_work_lane
        planned_write_paths: [scripts/**]
  ```

  `target_branch` and `base_ref` are non-empty strings. `tasks` is a non-empty
  list. Every task `id` is a unique non-empty ASCII slug; `depends_on` is a
  list of distinct task IDs; `execution_mode` is one canonical topology name;
  `planned_write_paths` is a non-empty list of safe repository-relative
  patterns. Dependencies must exist and be acyclic.
- output or state change: each prose Task section names one `Coordination ID`.
  Its task body owns purpose, files, steps, verification, and exit criteria;
  it does not copy manifest dependencies, topology, or paths.
- failure behavior: invalid, duplicate, unknown, cyclic, or legacy topology
  fields make plan invalid for managed coordination. Controller does not
  dispatch a packet from it.
- observable acceptance: validator maps every manifest task to one prose task
  and verifies canonical topology names, safe paths, and acyclic dependencies.

#### Requirement: Derived plan-task lifecycle

- trigger or actor: controller starts, blocks, hands off, or completes a
  coordination task.
- preconditions: plan status is `active`; task dependencies are completed;
  controller selected route and topology are admitted by route policy and host
  capability.
- required behavior: controller derives task state from packets with matching
  `plan_ref` and `plan_task_id`: `ready` has completed dependencies and no
  active/terminal run; `active` has one planned, running, observed, verifying,
  or awaiting-decision run; `blocked` has latest terminal blocked or
  unvalidated run; `done` has latest accepted run. Handoff contains last
  verified fact, next action, blocker or decision, and timestamp in that run.
- output or state change: controller writes run lifecycle and handoff evidence.
  It updates plan prose/checklists only after task becomes terminal. Agents
  return claims only and never mutate plan or run coordination state.
- failure behavior: unavailable execution mode, failed check, failed validator,
  approval wait, conflict, or interrupted host work leaves task `blocked` or
  `active` with explicit next action; it cannot become `done`.
- observable acceptance: new controller session reads plan and matching runs,
  then selects only one ready task or reports recorded blocker.

#### Requirement: Packet binding and continuation

- trigger or actor: controller resolves coordinated managed request.
- preconditions: manifest task is ready or active for that controller,
  dependencies are done, planned paths are allowed, and no active conflicting
  task exists.
- required behavior: resolver copies repository-relative `plan_ref`, stable
  `plan_task_id`, and SHA-256 `plan_digest` of normalized `coordination`
  object into immutable packet. Existing packet `base_commit` remains sole
  resolved code-base identity.
- output or state change: run attempt records packet only; run-level execution
  state owns handoff and does not copy plan manifest fields.
- failure behavior: changed digest, changed packet base commit, inactive plan,
  incomplete dependency, or overlap blocks dispatch. Controller may amend plan
  and create successor attempt; it never overwrites prior packet.
- observable acceptance: same planned packet may continue after a new session
  only when tracked plan, normalized digest, and packet base commit still match;
  all other recovery creates new attempt.

#### Requirement: Conflict and topology symmetry

- trigger or actor: controller chooses task whose requested topology allows
  concurrent work.
- preconditions: plan manifest contains task ownership and dependencies.
- required behavior: one controller serializes task activation for active plan
  and target branch. It compares paths before each dispatch. A task may reuse
  dependency paths only after dependencies are `done`. `parallel_work_lanes`
  additionally requires disjoint lane paths and isolated workspaces;
  sequential work uses declared order; single work uses one task/lane.
- output or state change: packet contains standard canonical topology and lane
  DAG. No coordination-specific executor runs.
- failure behavior: ambiguous overlap, cyclic dependency, noncanonical mode,
  concurrent controller activation, or host mode unavailable blocks or follows
  existing controller waiver rule; no automatic downgrade occurs.
- observable acceptance: equivalent failures produce same controller outcome
  shape across all three topologies.

#### Requirement: Backward compatibility

- trigger or actor: controller executes plan or task without coordination
  manifest.
- preconditions: ordinary source-first or existing managed request.
- required behavior: current plan/specification lifecycle and managed packet
  contract remain unchanged. Controller may execute local reversible work
  without plan linkage.
- output or state change: no new mandatory metadata for historical plans,
  uncoordinated plans, or non-managed runs.
- failure behavior: omitted optional manifest never makes ordinary work invalid.
- observable acceptance: existing plan, harness, and starter-kit tests pass
  without adding coordination fields to legacy fixtures.

### Constraints and Alternatives

- constraint: one authoritative owner per fact; no duplicated task state in
  plan and `run.json`.
- alternative: add standalone SQLite/JSON coordination registry.
  - benefit: machine-native querying and potential distributed locks.
  - trade-off: second mutable truth, migration, runtime dependency, and
    reconciliation burden.
  - reason accepted or rejected: rejected. Git-tracked active plan is enough
    for first coordination layer.
- alternative: add lease, heartbeat, and automatic stale-run recovery now.
  - benefit: supports untrusted concurrent controllers and crash recovery.
  - trade-off: scheduler semantics, expiry races, clock rules, and new service
    owner.
  - reason accepted or rejected: rejected. Successor attempts and explicit
    controller handoff cover admissible first-version recovery.
- alternative: create separate plan formats per orchestration topology.
  - benefit: topology-specific prose.
  - trade-off: duplicated ownership, validation, and lifecycle logic.
  - reason accepted or rejected: rejected. One manifest parameterizes topology.

## Design Decisions

### Decision: Plan is coordination SSOT

- context: multi-session work needs durable, reviewable intent and ownership;
  managed runs need durable technical evidence.
- selected approach: implementation plan owns immutable coordination manifest,
  dependencies, and work ownership. Immutable packet owns resolved plan binding.
  `run.json` owns attempts, derived task state, handoff, host evidence,
  verification, and controller decision history.
- rationale: each fact has one writable owner and human review remains Git
  native.
- alternatives considered: runtime registry; duplicated task state in run;
  chat-only handoff.
- accepted trade-offs: controllers scan active plan manifests before dispatch;
  first version admits one serialized controller decision writer only.
- affected owners and boundaries: plans, packet resolver, run lifecycle,
  controller, plan validator, generated instructions.

### Decision: Coordination metadata is optional and structured

- context: local reversible work must remain cheap; coordination fields must be
  parseable when required.
- selected approach: only coordination-heavy Git-tracked plans declare
  `coordination` in frontmatter. Manifest owns mechanical fields and produces
  normalized digest; prose Task sections reference task IDs and own human
  implementation detail.
- rationale: one plan file remains SSOT without duplicate human/machine task
  descriptions.
- alternatives considered: require manifest for every plan; parse headings as
  schema; sidecar manifest file.
- accepted trade-offs: plan authors maintain stable task IDs for coordinated
  work.
- affected owners and boundaries: plan template, planning validator, writing
  plans skill, executing plans skill.

### Decision: Fresh successor replaces unsafe resume

- context: host process/thread durability cannot be inferred after session loss
  or plan/base change.
- selected approach: only a still-planned packet with matching plan digest and
  existing packet base commit can continue. Any interrupted, manifest-changed,
  failed, or ambiguous work uses explicit controller decision and successor
  attempt.
- rationale: preserves immutable evidence and avoids false host-resume claims.
- alternatives considered: resume arbitrary host turn; rebind old packet to
  edited plan; silent rerun.
- accepted trade-offs: recovery may require redispatching work.
- affected owners and boundaries: controller, packet resolver, host adapter,
  run lifecycle.

### Decision: Controller activation stays serialized

- context: safe simultaneous controller activation requires atomic reservation,
  which first version deliberately excludes.
- selected approach: one controller serializes task activation for each active
  plan/target branch. It compares manifest paths before dispatch. Parallelism
  remains packet-internal through existing isolated-lane contract.
- rationale: handles multi-session handoff without a false cross-controller
  safety claim or new distributed state.
- alternatives considered: global path lock; auto-merge; rely only on Git
  conflicts; compare-and-set concurrency protocol.
- accepted trade-offs: simultaneous controllers are blocked. Explicit
  concurrency design is required before admitting them.
- affected owners and boundaries: controller preflight, plan validator,
  `parallel_work_lanes` admission.

### Compatibility, Migration, and Risk

- old behavior: plans and managed packets are independent; handoff is prose;
  all managed requests omit plan binding.
- new behavior: coordination-heavy plan tasks bind managed packets through
  normalized manifest digest. Task state and handoff derive from linked runs.
  Ordinary work remains unchanged.
- compatibility boundary: manifest is opt-in. Existing plans and run records
  require no backfill.
- migration or backfill: none. New or deliberately upgraded active plans use
  manifest; historical plans remain historical.
- rollout and rollback: introduce parser/validator in advisory read-only mode,
  prove representative single/sequential/parallel paths, then enforce only for
  manifest-enabled managed requests. Disable before dispatch by removing
  manifest from new plan; never rewrite historical packet/run evidence.
- deprecation or consumer impact: replace legacy topology aliases in plan
  template guidance with canonical names. Alias input remains governed by
  existing packet compatibility rules.
- risk:
  - risk: manifest duplicates prose or becomes stale.
  - mitigation: validator requires one task-ID reference and rejects duplicated
    mechanical coordination fields in prose templates.
  - risk: controller derives task completion from stale or ambiguous runs.
  - mitigation: resolver requires one current matching run; validator blocks
    multiple current runs and requires latest accepted evidence before `done`.
  - risk: conflict policy blocks safe independent work.
  - mitigation: manifest opt-in; use separate worktree/plan only with explicit
    target branch and disjoint paths.

## Invariants and Edge Cases

### Invariants

- One coordination-heavy task has one Git-tracked active plan, one stable task
  ID, and one serialized controller decision writer.
- Plan owns immutable coordination manifest; packet owns resolved plan binding;
  `run.json` owns derived task state, handoff, and execution/evidence state;
  `harness.yaml` owns static route policy.
- Every coordinated packet references exactly one plan task and exact plan
  normalized-manifest digest plus existing packet base commit.
- Prior attempts, packets, claims, evidence, decisions, and friction event IDs
  remain immutable.
- Equivalent single, sequential, and parallel cases use one lifecycle and
  validator boundary. Topology only changes lane/workspace data.
- No agent accepts work, mutates plan state, auto-resolves conflict, or claims
  host-session resume.
- A task is `done` only with linked accepted managed evidence; `unvalidated`,
  blocked, failed, or waived runs cannot satisfy it.

### Edge Cases

- empty or minimal input: no coordination manifest means existing source-first
  or unmanaged plan process continues unchanged.
- normal and large input: manifest supports many dependency-ordered tasks; no
  fixed worker-count or global queue is introduced.
- duplicate, missing, malformed, or unsupported data: duplicate task IDs,
  missing prose reference, unsafe path, unknown dependency, cycle, invalid
  status, invalid digest, inactive plan, legacy mode, or unknown run ID fails
  before dispatch.
- retry, cancellation, timeout, partial failure, or concurrency: cancellation
  and friction remain normal run evidence; controller records handoff in run
  and uses successor attempt. One controller serializes task activation;
  parallel lanes remain packet-internal and disjoint.
- migration or mixed-version state: manifest-disabled plans use legacy process;
  manifest-enabled plans require new resolver/validator. Historical run files
  remain readable.
- generated-source consistency: canonical template, skills, root AGENTS source,
  generated adapters, and starter kit synchronize after guidance changes.
- security or accessibility boundary: repository-relative safe paths only;
  no plan field authorizes external workspace access, elevated tools, approval,
  or private host data.

## Validation Plan

### Backend Verification Claims

- direct boundary: plan manifest parser/validator, packet resolver, run
  lifecycle, controller decision, and plan-task state updater.
- important success and failure behavior: prove manifest-enabled task dispatch,
  same-packet continuation, successor after plan/base change, dependency order,
  path conflict block, linked accepted completion, and legacy plan pass-through.
- final state or side effects: derived task state has only permitted outcomes;
  packet binding is immutable; `run.json` preserves evidence and handoff; no
  second coordination store is written.
- rollback, retry, duplicate, or idempotency behavior: repeated controller
  request for same active task returns existing valid planned attempt or blocks;
  retry/scope/manifest changes create exactly one successor; `done` derives
  only from same task's latest accepted run ID.
- canonical contract and conformance proof: harness config, plan template,
  plan validator, roles, generated agent adapters, and starter kit validate.
- real dependencies requiring proof: host adapter must prove all selected
  topology modes as existing managed contract requires; no new external service
  dependency is introduced.
- representative-operation trace mechanism: packet plan binding, `run.json`
  state history/handoff, host evidence, controller decisions, and friction
  events.
- performance claim and threshold: Not applicable: no background scheduler or
  throughput claim. Parser/preflight must remain foreground and bounded by
  active-plan manifest size.

### Acceptance Criterion: Plan-task binding

- setup or precondition: Git-tracked active plan with one valid coordination
  manifest task and resolved existing packet base commit.
- action: controller resolves managed packet for task.
- expected result: packet contains plan path, task ID, normalized manifest
  digest, and existing base commit; run attempt links only through immutable
  packet.
- failure condition: packet accepts absent or changed plan context.
- proof method: direct resolver/run-record tests.
- expected evidence: packet and run JSON assertions plus automated output.

### Acceptance Criterion: Multi-session handoff

- setup or precondition: task has valid planned managed packet and controller
  session ends before dispatch or after recorded blocked outcome.
- action: fresh controller reads plan and run state.
- expected result: controller continues only matching planned packet; otherwise
  reads run-owned handoff and creates successor attempt after decision.
- failure condition: controller resumes unknown host handle or overwrites prior
  packet/evidence.
- proof method: direct lifecycle tests with changed plan digest/base commit.
- expected evidence: immutable first attempt, successor attempt, and run
  handoff record.

### Acceptance Criterion: Symmetric topology coordination

- setup or precondition: three valid manifest tasks request canonical single,
  sequential, and parallel topology under route and host capability.
- action: resolve and execute representative managed runs.
- expected result: each packet has same plan binding shape; each ends through
  standard integrate/validate/controller path.
- failure condition: any mode uses separate planner, state format, or bypasses
  read-only validator.
- proof method: parameterized core tests plus existing host conformance/live
  proof where host behavior is affected.
- expected evidence: normalized packet/run evidence and test output.

### Acceptance Criterion: Conflict control and compatibility

- setup or precondition: one controller considers dependency-ordered tasks with
  reused or disjoint planned paths; one legacy plan lacks manifest.
- action: controller preflights each ready task.
- expected result: reused paths admit only after dependency is done, packet
  internal parallel paths remain disjoint, and legacy plan retains existing
  behavior.
- failure condition: simultaneous controller activation, unsafe packet-internal
  dispatch, or new mandatory metadata for ordinary work.
- proof method: manifest validator and controller preflight tests.
- expected evidence: blocker/packet outputs and unchanged legacy fixtures.

## Completion Criteria

Specification is complete when:

1. coordination ownership across plan, packet, `run.json`, and static policy is
   explicit and non-duplicated
2. plan manifest, task state, packet binding, successor recovery, and conflict
   semantics are unambiguous
3. all canonical topologies use same coordination and verification semantics
4. non-goals exclude unapproved scheduler, lock, and host-resume behavior
5. compatibility and migration preserve legacy plans and managed runs
6. every required outcome maps to direct validation intent
7. implementation sequencing remains outside this specification
