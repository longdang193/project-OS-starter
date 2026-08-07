---
artifact_type: spec
template_id: detailed-specification
status: active
layer: change
name: harness-invocation-delegation-protocol
targets:
  - packages/harness-core
  - repo_config/harness.yaml
  - agents/roles.yaml
  - docs/operating_system/procedures/managed-execution-adapter-contract.md
---

# Harness Invocation and Delegation Protocol

## Goal and Problem

### Problem

- current behavior: `harness-core` manages immutable attempt packets and a
  lane DAG, but controller-created lanes are its only first-class lifecycle
  units. Agent child work has no equivalent core-mediated admission path.
  Packet context is one free-text `user_request`; Codex host prompt renders it
  twice.
- affected users, systems, or maintainers: controllers, workers, validators,
  provider-host maintainers, and future provider implementations.
- evidence: core centrally resolves route tools, role, budget, workspace, and
  lanes. Host dispatch receives lane, packet, workspace, and claim schema.
  Core compatibility exposes independent request, packet-read, and host API
  sets rather than their relation.
- consequence of no change: delegation remains prompt policy, child context
  cost can grow with parent history, and provider compatibility gains special
  cases.

### Goal

- desired outcome: one execution-node lifecycle supports controller-created work,
  agent-requested child work, integration, checks, and validation through one
  scheduler, one evidence model, and one controller decision boundary.
  `AgentInvocation` is the only node kind that owns an immutable agent packet,
  provider turn, role, context projection, and claimed result.
- observable success: permitted child delegation behaves as controlled tool
  call with fresh bounded context, explicit capability intersection, bounded
  budget, isolated workspace, structured outcome, and independent
  verification. Denial creates typed evidence and no host turn.

## Required Outcomes

### Outcome: One execution-node lifecycle

- affected actor or system: core scheduler, controller, worker, validator, and
  provider host.
- required result: root work, controller-created lanes, delegated children,
  integration, checks, and validation are execution nodes in one graph.
  Agent work and validation are `AgentInvocation` nodes; integration and checks
  are deterministic nodes with same dependency, observation, timeout,
  cancellation, and controller-decision transitions.
- success condition: no separate child runner or validator lifecycle exists;
  deterministic host effects do not receive fake agent packets, roles, prompts,
  or claims.

### Outcome: Controlled delegation primitive

- affected actor or system: managed worker and provider host.
- required result: `harness.delegate` is packet-selected runtime tool. It
  submits structured child request to core; it never directly invokes platform
  subagent API.
- success condition: core accepts or denies every child request before host
  dispatch. Ambient native delegation is typed failure, not prompt warning.

### Outcome: Fresh bounded context

- affected actor or system: controller, worker, child worker, and provider
  host.
- required result: every invocation receives one immutable context projection,
  not parent transcript history.
- success condition: packet records one bounded context table: objective,
  selected facts, artifact references, and expected result. Provider renders
  projection once. `lane_input.instructions` does not exist as second prompt
  channel.
  Parent receives bounded child outcome and evidence references only.

### Outcome: Intent separate from power

- affected actor or system: policy author, role registry, core, and provider
  host.
- required result: role describes intent/result schema only; semantic
  capabilities describe permitted effects; host maps grants to native tools.
- success condition: changing role never grants write, search, check, or
  delegation authority. Child grants equal parent grant intersected with route
  and profile ceilings.

### Outcome: Symmetric provider boundary

- affected actor or system: Codex host and future provider hosts.
- required result: package owns typed adapter protocol and shared conformance
  contract for identity, workspaces, capabilities, dispatch, cancellation,
  claims, evidence, and delegation denial.
- success condition: provider passes same proof without core policy change.

### Outcome: Explicit protocol evolution

- affected actor or system: consumers, core, launcher, provider hosts, and
  historical run recovery.
- required result: core owns one relational compatibility matrix mapping
  request API, emitted packet API, readable packet APIs, host API, and feature
  set.
- success condition: packet API 4 dispatches only to host API 3. Historical
  packet API 3 stays readable through declared matrix row. No implicit
  downgrade, fallback, or host-local compatibility rule exists.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
|---|---|---|---|---|
| One lifecycle exists? | `run_managed()` resolves packet, schedules work/integration/validation, records evidence, then awaits controller decision. | `packages/harness-core/src/harness_core/managed.py` | high | Extend core; do not add executor. |
| Lanes graph-shaped? | Non-single modes validate DAG, writable-path disjointness, integration, and validator lanes. | `packages/harness-core/src/harness_core/managed.py` | high | Invocation graph replaces lane-only vocabulary. |
| Roles/effects partly separate? | Roles own write/result schema; routes select tools; packets resolve binding access. | `agents/roles.yaml`; `repo_config/harness.yaml` | high | Move effect authority into capabilities. |
| Host effect-only? | Contract owns workspace, dispatch, collect, cancel, checks, and binding proof. | `docs/operating_system/procedures/managed-execution-adapter-contract.md` | high | Preserve host effects only. |
| Child context bounded? | Packet has `user_request`; Codex host renders request twice. | `managed.py`; `codex-harness-host/adapter.py` | high | Add context projection. |
| Delegation enforced? | Instructions prohibit child spawning; packet has no delegation grant. | `AGENTS.md`; `repo_config/harness.yaml` | high | Add core entitlement and host proof. |
| APIs relational? | Core exposes independent API sets. | `packages/harness-core/src/harness_core/compatibility.py` | high | Add compatibility matrix. |

### Prototype and Validation Evidence

- prototype reference: Not applicable: backend protocol change.
- validated states: existing host proof covers isolated writer workspace,
  final-state materialization, selected tools, read-only validator, approval,
  timeout, and provider failure.
- incorporated finding: invocation must retain current workspace/tool/evidence
  boundaries; delegation cannot bypass them.
- rejected alternatives: prompt-only spawn prohibition, second orchestration
  service, agent-managed acceptance, parent-transcript forwarding,
  provider-specific route policy, and unbounded recursion.

### Scope

- included behavior: invocation graph and packet API 4; core-mediated child
  creation; bounded context/outcome projection; semantic capabilities and
  delegation profiles; host API 3 protocol/conformance; packet API 3 recovery.
- affected boundaries: core, launcher, `harness.yaml`, roles, provider adapter,
  run record, managed-execution guidance, starter kit, and backend proof.
- admissible cases: controller single/sequential/parallel work; read-only and
  isolated write child delegation; all authority denials; historical packet 3.
- compatibility expectation: request APIs 2/3 retain packet API 3 behavior.
  New features require request API 4, packet API 4, and host API 3.

### Non-Goals

- autonomous planner trees, unbounded recursive agents, or agent-managed
  retry/escalation/approval/acceptance;
- distributed queue, lease, heartbeat, scheduler service, or global controller
  lock;
- reimplementing provider sandbox, shell, MCP, approval, or editor in core;
- transcript persistence or default child artifact-content forwarding;
- workflow DSL beyond current single, sequential, and parallel scheduling.

### Requirements and Behavioral Contract

#### Requirement: Immutable invocation packet

- trigger or actor: controller creates root work or planned lane, or worker
  calls granted `harness.delegate`.
- preconditions: core admits request/host matrix row, route, provider identity,
  workspace mode, role, capability set, and delegation profile.
- required behavior: core creates one immutable packet with this normalized
  shape:

  ```json
  {
    "packet_api": 4,
    "invocation_id": "inv-2",
    "parent_invocation_id": "inv-1-or-null",
    "role": "investigate",
    "idempotency_key": "delegate-4d54...",
    "work_context": {
      "version": 1,
      "objective": "Find exact middleware callers",
      "facts": [{"id": "fact-1", "text": "...", "sha256": "..."}],
      "artifacts": [{"path": "src/auth.py", "base_commit": "...", "sha256": "..."}],
      "expected_result": {"kind": "claimed_result", "required_fields": ["summary", "findings"]},
      "digest": "..."
    },
    "capabilities": ["repo.read", "code.search"],
    "delegation": {
      "max_depth": 1,
      "max_children": 2,
      "max_concurrent_children": 1,
      "per_child_timeout_seconds": 120,
      "total_child_timeout_seconds": 240,
      "verification": "schema"
    },
    "budget": {"turn_timeout_seconds": 120},
    "workspace": {"mode": "isolated", "write_access": "read_only"},
    "expected_result": {"kind": "claimed_result", "required_fields": ["summary", "findings"]}
  }
  ```

- output or state change: `run.json` records immutable packet under an
  `AgentInvocation` node and mutable node state/evidence separately.
- failure behavior: malformed, oversized, unsafe, unsupported, or
  incompatible values return typed admission failure before workspace or host
  dispatch.
- observable acceptance: root, controller lane, delegated child, and validator
  agent packets differ only by normalized data and authority grants.

#### Requirement: Controlled `harness.delegate`

- trigger or actor: managed worker invokes packet-selected delegation tool with
  structured child request.
- preconditions: parent packet grants delegation; parent `AgentInvocation` is
  running; request has one stable `idempotency_key`; requested role, context,
  paths, capabilities, budget, and workspace are valid.
- required behavior: core admits one child only when:

  ```text
  child role         in profile.allowed_roles
  child capabilities subset of parent capabilities and profile ceiling
  child paths        subset of parent allowed paths
  child timeout      within profile per-child limit
  child reservation  fits parent total child-time allocation
  active children    within profile max_concurrent_children
  child depth        within profile max_depth
  child count        within profile max_children
  child workspace    matches profile isolation/write rule
  child result       matches selected role schema
  ```

- output or state change: core reserves budget atomically, creates child packet,
  and returns child invocation ID/status. Duplicate idempotency key returns the
  original child without second reservation or host turn. Parent remains
  `waiting_for_child` until child reaches terminal state.
- state behavior: child `awaiting_decision`, timeout, cancellation, or terminal
  failure pauses parent and attempt at controller decision boundary. Controller
  retry/approval/escalation creates successor attempt; parent never resumes a
  mutated child packet. Parent cancellation cancels active descendants; child
  terminal state releases unconsumed reservation exactly once.
- failure behavior: stable denial code such as `delegation_depth_exceeded`,
  `delegation_capability_exceeded`, `delegation_budget_exceeded`,
  `delegation_path_exceeded`, or `delegation_not_permitted`; no child workspace
  or provider turn exists.
- observable acceptance: controller-created and agent-requested children use
  same core admission, workspace, dispatch, claim, evidence, cancellation, and
  reservation transitions. Core exposes typed `delegate(request) ->
  DelegationResult`; provider host only relays request/result while parent turn
  waits.

#### Requirement: Context and outcome projection

- trigger or actor: core creates invocation packet or completes child.
- preconditions: facts/artifacts are safe repository references or bounded text
  accepted by policy.
- required behavior: `repo_config/harness.yaml` owns one context-policy table
  with objective byte limit, total fact byte limit, maximum fact count, maximum
  artifact count, and maximum outcome-summary bytes. Core validates references,
  binds artifact digest to packet base commit/workspace identity, computes one
  canonical context digest before host dispatch, and emits one invocation-local
  projection. Provider renders it once. Child outcome contains claim, selected
  verification status, evidence refs, changed-path summary, and bounded summary;
  it excludes raw provider transcript and unselected parent context.
- output or state change: packet stores context digest/references; run stores
  bounded outcome/evidence references.
- failure behavior: missing artifact, digest mismatch, oversized text, unsafe
  path, unsupported ref, or context budget overflow blocks before dispatch.
- observable acceptance: parent transcript cannot increase child prompt beyond
  configured projection limit.

#### Requirement: Semantic capabilities and profiles

- trigger or actor: policy author configures route or controller selects route.
- preconditions: capability names and profile references exist in
  `repo_config/harness.yaml`.
- required behavior: policy owns semantic capability catalog, reusable
  capability sets, delegation profiles, route defaults, and topology limits.
  Initial capabilities are `repo.read`, `repo.write`, `checks.run`,
  `code.search`, `docs.query`, and `harness.delegate`. Roles own intent and
  result schemas; roles do not grant capability.
- output or state change: packet records immutable semantic grants/profile.
  Host records native-binding evidence for exactly those capabilities.
- failure behavior: unknown capability/profile, provider missing required
  capability, workspace/profile conflict, or native tool outside grant blocks
  before or during dispatch with typed evidence. Roles never decide write
  authority.
- observable acceptance: same route can use different providers without core
  route-policy change; provider maps its own native tools.

#### Requirement: Host API 3 typed effect protocol

- trigger or actor: core admits packet API 4 against host API 3.
- preconditions: provider advertises host API 3 and selected semantic
  capabilities.
- required behavior: provider implements one typed effect boundary reusing
  current adapter operations:

  | Core operation | Applies to | Required result |
  | --- | --- | --- |
  | `prepare_workspace(node, packet)` | `AgentInvocation` | verified workspace identity/access |
  | `verify_tool_bindings(node, packet, workspace)` | `AgentInvocation` | selected capability binding evidence |
  | `dispatch_lane(node, packet, workspace, delegate_bridge)` | `AgentInvocation` | cancellable provider handle |
  | `collect_claim(handle)` / `collect_lane_evidence(...)` | `AgentInvocation` | bounded claim/evidence |
  | `cancel_lane(handle)` | active `AgentInvocation` | idempotent terminal cancellation observation |
  | `materialize_final_state(node, packet, workspaces)` | `integration` | final workspace observation |
  | `run_checks(packet, workspace)` | `check` | normalized check observations |

  `delegate_bridge` is present only when packet grants `harness.delegate`; it
  relays `delegate(request) -> DelegationResult` to core and blocks parent turn
  until child terminal outcome. Provider must expose no ambient native child
  spawn tool. If platform exposes one and reports use, host records typed
  `ambient_delegation_forbidden` evidence and cancels parent.
- output or state change: core records provider capability, workspace, tool,
  cancellation, claim, and evidence observations without provider-selected
  policy or decision.
- failure behavior: unavailable method, incompatible result, unproven tool
  absence, unexpected native spawn, or capability mismatch fails typed
  conformance/admission before accepted work.
- observable acceptance: same conformance fixture passes for every provider;
  host API 3 never needs route-specific core branch.

#### Requirement: Invocation graph and scheduler symmetry

- trigger or actor: core resolves root work, planned lanes, or accepted child.
- preconditions: every dependency is another execution node in same attempt;
  concurrent writers have disjoint paths and isolated workspaces.
- required behavior: single, sequential, and parallel modes select scheduling
  limits over one execution-node graph. `AgentInvocation` nodes dispatch through
  provider and produce claims. `integration` and `check` nodes call deterministic
  host effects and produce normalized observations. Validator is an
  `AgentInvocation` with no write or delegation capability.
- output or state change: parent waits for child terminal outcome; graph
  failure follows existing cancellation/controller-decision policy.
- failure behavior: cycle, missing dependency, overlap, unsupported concurrent
  write, validator write/delegation, or missing final workspace blocks attempt.
- observable acceptance: topology changes data/scheduler limits, never
  lifecycle implementation or acceptance authority.

## Design Decisions

### Decision: Execution node is sole scheduler unit

- context: lanes, validators, integration, checks, and future delegated
  children must obey same lifecycle and proof rules without pretending every
  deterministic effect is an agent turn.
- selected approach: every scheduled unit is an `ExecutionNode`; root has no
  parent. `AgentInvocation` extends this node for worker/validator provider
  turns. `integration` and `check` remain deterministic node kinds.
- rationale: one graph/state machine prevents special runner paths while reuse
  of existing host effects avoids fake prompts, roles, claims, and packets.
- alternatives considered: retain lanes plus separate child-agent records;
  create generic orchestration service.
- accepted trade-offs: packet/run migration and provider adapter update.
- affected owners and boundaries: core owns graph/state; policy owns route and
  profile data; host owns effects; controller owns final decision.

### Decision: Delegation is core-mediated native tool

- context: instruction-only child-spawn prohibition is weak enforcement.
- selected approach: packet grants or withholds `harness.delegate`; native tool
  submits structured request to core and receives typed result.
- rationale: delegation becomes symmetric with controller lane creation while
  retaining bounded authority.
- alternatives considered: direct platform subagent tool, role spawn prompts,
  unrestricted child agents.
- accepted trade-offs: host must prove native child-spawn tool absent or
  unexposed for profiles without delegation. Runtime denial is additional proof
  only when provider emits observable native child-spawn events.
- affected owners and boundaries: core validates; host exposes/denies native
  tool; roles do not grant delegation.

### Decision: Context table replaces transcript inheritance

- context: current request is unconstrained and duplicated in host prompt.
- selected approach: policy owns one context-limit table; core validates one
  work-context table and per-invocation projection with digest-backed artifact
  refs bound to packet base commit/workspace identity.
- rationale: fresh context lowers token cost and makes replay/audit stable.
- alternatives considered: parent transcript copy; host-owned prompt trimming.
- accepted trade-offs: controller/agent must name needed facts/artifacts. No
  free-form `lane_input.instructions` survives beside normalized objective and
  expected-result schema.
- affected owners and boundaries: core owns schema/limits; host renders once;
  run stores bounded outcome/reference data.

### Decision: Semantic capabilities precede native tool bindings

- context: route policy currently contains native host kinds.
- selected approach: policy grants semantic capabilities and workspace profile;
  provider maps to native tools and reports binding evidence. Role registry v2
  owns only accepted templates and result schema; it has no `writes` field.
- rationale: same route works across providers without policy duplication.
- alternatives considered: retain host-kind route entries; provider branches in
  core.
- accepted trade-offs: adapter conformance surface expands.
- affected owners and boundaries: policy owns capability semantics and write
  authority; roles own intent/result schema; host owns mapping; packet stores
  grants; evidence stores resolved bindings.

### Decision: Delegation uses run-owned reservations and child profiles

- context: immutable parent packets cannot safely track reservations, and one
  turn timeout cannot bound serial or parallel children.
- selected approach: immutable delegation profile carries depth, count,
  concurrency, per-child timeout, total child-time ceiling, allowed roles,
  workspace rule, and child verification mode (`none`, `schema`, `checks`, or
  `validator`). Mutable run state owns idempotency-key mapping and reservation
  ledger; core reserves before child creation and releases once at child
  terminal state.
- rationale: same profile/ledger admits controller and agent child work without
  timing races or duplicate turns.
- alternatives considered: parent-local counters; host-local budget tracking;
  unrestricted recursive planner tree.
- accepted trade-offs: total budget is time allocation, not wall-clock promise.
- affected owners and boundaries: policy owns reusable profile defaults; packet
  owns immutable selected profile; run owns reservation state; host only reports
  observation.

### Decision: Child claims remain provisional

- context: delegated research, edits, and reviews have different useful local
  proof levels, but controller acceptance remains run-level authority.
- selected approach: profile selects child proof floor. `none` stores claim;
  `schema` validates claim shape; `checks` records selected checks; `validator`
  dispatches fresh read-only child validator. Every child outcome remains
  provisional until final fresh validator and controller acceptance.
- rationale: avoids mandatory validator turns for read-only facts while keeping
  independent final verification unchanged.
- alternatives considered: final validator only with no child proof; validator
  per child unconditionally.
- accepted trade-offs: profile author chooses bounded local proof.
- affected owners and boundaries: policy owns profile; core schedules proof;
  host performs selected effect; controller owns final acceptance.

### Decision: Compatibility is one relational matrix

- context: independent API sets cannot express feature-compatible packet/host
  pairs.
- selected approach: core owns rows mapping request API, packet API, host API,
  readable packet APIs, and required features:

  | Profile | Request APIs | Emitted packet API | Dispatch host API | Required features |
  | --- | --- | --- | --- | --- |
   | legacy dispatch | 2, 3 | 3 | 2 | lanes, tool bindings, terminal observation v1 |
   | legacy recovery | none | none | 3 read-only | inspect packet/run API 3 evidence only |
   | invocation | 4 | 4 | 3 | context v1, semantic capabilities, delegation profiles, execution-node graph |

  Host API 3 declares readable packet APIs 3 and 4, but it dispatches packet
  API 4 only. Host API 2 dispatches packet API 3 only. Core derives all
  admission/read/feature checks from matrix.
- rationale: one source prevents partial host upgrades and hidden fallbacks.
- alternatives considered: separate constants plus host-local checks; package
  version-only compatibility.
- accepted trade-offs: protocol changes require explicit profile and host
  conformance release.
- affected owners and boundaries: core owns matrix; consumer selects request
  API; host advertises capability; launcher reports package absence only.

### Compatibility, Migration, and Risk

- old behavior: request APIs 2/3 emit packet API 3; host API 2 dispatches lane
  packets; child delegation is instruction-prohibited; routes own native tool
  bindings.
- new behavior: request API 4 emits invocation packet API 4 and requires host
  API 3; capability/delegation/context are immutable packet facts.
- compatibility boundary: API 3 is legacy and receives no delegation/context
  features. API 4 never downgrades to API 3 or host API 2.
- migration or backfill: API 4 emits run-record API 2. Core reads run-record
  API 1 and packet API 3 unchanged. Host API 3 may inspect this historical
  state but cannot dispatch it; controller must select legacy host API 2 or
  create successor API 4 attempt. Consumers upgrade package/host lockfiles,
  host API advertisement, and `harness_core.request_api` together before
  selecting API 4 routes.
- rollout and rollback: release host API 3 conformance before consumer API 4.
  Roll back consumer policy only before new API 4 run; never mutate packet or
  attempt already created.
- deprecation or consumer impact: bridge scripts remain package launchers; new
  automation uses package/host entrypoints. Legacy removal needs future matrix
  release.
- risk:
  - provider exposes ambient child-spawn tool.
    - mitigation: host denies/unexposes it, records tool-use evidence, and
      fails conformance when profile forbids delegation.
  - context refs drift from workspace content.
    - mitigation: core validates safe paths and digests before dispatch.
  - children exhaust parent time.
    - mitigation: core reserves child allocation from immutable parent budget.
  - semantic/native mapping differs by provider.
    - mitigation: shared adapter conformance and packet binding proof.

## Invariants and Edge Cases

### Invariants

- Every root, lane, child, integration, check, and validator has one mutable
  execution-node record. Only worker and validator `AgentInvocation` nodes have
  immutable agent packets and provider dispatch.
- Controller alone records accept, retry, escalation, approval, waiver, and
  block decisions.
- Child capability/path/budget/depth/count/workspace authority never exceeds
  parent grant and profile ceiling.
- Roles describe intent/result schema; capabilities plus workspace profile grant
  effects.
- Provider host cannot select route policy, alter authority, or accept work.
- Validator is fresh, read-only, has no delegation, reads final workspace, and
  remains separate from provisional child proof.
- Packet API 4 never dispatches through host API 2. No fallback mutates packet,
  run, or evidence.
- Raw parent/child/provider transcripts are not persisted in packet, run, or
  terminal observation.

### Edge Cases

- empty input: root objective, role, result schema, and explicit capability set
  remain required; `none` delegation profile is valid.
- large input: core rejects context beyond byte/count limits; it never silently
  truncates semantic facts.
- invalid data: duplicate invocation/dependency/fact/artifact/capability/profile
  fails typed admission.
- retry, cancellation, timeout, partial failure, concurrency: duplicate child
  request returns original invocation; parent cancellation cascades only to
  active children; child terminal release is exactly once; child decision-needed
  outcome pauses parent at controller boundary; terminal observation stays
  normalized; concurrent writers require disjoint paths/isolated workspaces;
  controller successor preserves old evidence.
- mixed versions: run-record API 1/packet API 3 stays immutable/readable;
  host API 3 inspection is read-only; packet API 4 cannot dispatch through host
  API 2; unknown matrix row blocks without rewrite.
- generated sources: canonical policy/rule/skill changes precede generated
  adapters, runtime deployment, and starter-kit rebuild.
- security: child cannot widen paths, writes, tools, workspace, budget, or
  delegation; host cannot expose ambient unselected MCP/delegation tools.

## Validation Plan

### Backend Verification Claims

- direct boundary: core validates invocation packet, delegation request,
  context projection, capability intersection, compatibility matrix, and typed
  denial without provider dispatch.
- important success and failure behavior: root/controller/agent child and
  validator use same lifecycle; permitted read-only/write child cases complete
  through integration/verification; every denied authority axis returns typed
  code.
- final state or side effects: `run.json` preserves immutable packets,
  parent/child relation, bounded outcome, evidence refs, and controller-only
  decisions; workspaces remain contained.
- rollback, retry, duplicate, or idempotency behavior: duplicate delegation
  cannot create duplicate child; cancellation/timeout preserve terminal
  evidence; retry/escalation creates successor without mutation; policy
  rollback never rewrites packet API 4 data.
- canonical contract and conformance proof: shared core adapter conformance
  proves provider identity, host API compatibility, semantic binding,
  delegation denial, read-only validator, workspace containment, and terminal
  observation.
- real dependencies requiring proof: live Codex App Server proof covers
  selected tool use, `harness.delegate` availability/denial, model identity,
  sandbox access, child outcome, and fresh validator.
- representative-operation trace mechanism: run-owned invocation evidence,
  bounded terminal observation, and host tool-binding evidence.
- performance claim and threshold: Not applicable: no latency improvement is
  claimed. Context proof measures bounded input size only.

### Acceptance Criterion: One symmetric lifecycle

- setup or precondition: compatible API 4 consumer and host API 3 provider.
- action: create root work, controller lane, delegated child, integration,
  check, and validator.
- expected result: each is execution node using same state/evidence contract;
  only `AgentInvocation` nodes use agent packet/provider claim. Deterministic
  nodes use shared normalized observations.
- failure condition: any unit bypasses execution-node lifecycle, or deterministic
  node receives fake agent packet/role/claim.
- proof method: core graph/state tests and provider conformance evidence.
- expected evidence: packets, state histories, claims, bindings, workspace IDs,
  and validator result.

### Acceptance Criterion: Delegation is bounded and enforced

- setup or precondition: profile permitting one read-only research child and
  profile forbidding delegation.
- action: request allowed child twice with same idempotency key, then excess
  depth/count/concurrency/capability/budget/path/write child and ambient native
  spawn.
- expected result: allowed child gets derived grant/context; forbidden cases
  deny or fail before unauthorized child work.
- failure condition: child widens authority, host dispatches ungranted child,
  or prompt-only warning is sole control.
- proof method: core admission tests and live/provider tool-use traces.
- expected evidence: reservation ledger, one child turn for duplicate request,
  typed denial/no child turn for admission denial, or terminal enforcement
  evidence for ambient tool violation.

### Acceptance Criterion: Fresh context remains bounded

- setup or precondition: parent has large transcript-like data; child needs
  selected facts/artifacts only.
- action: create child context projection.
- expected result: prompt contains one projection within limits; unselected
  parent text absent; artifact digests match workspace.
- failure condition: duplicate rendering, transcript inheritance, silent
  truncation, or digest mismatch.
- proof method: packet/prompt rendering tests and provider capture proof.
- expected evidence: context metadata/digest, rendered prompt assertion, and
  bounded child outcome.

### Acceptance Criterion: Parent/child lifecycle is recoverable

- setup or precondition: parent `AgentInvocation` has one permitted child,
  finite child reservation, and provider delegate bridge.
- action: dispatch child; exercise success, duplicate request, timeout,
  cancellation, and `awaiting_decision` outcome.
- expected result: parent waits only for original child; reservation releases
  once; terminal child result resumes or pauses parent through declared state;
  controller alone creates successor after decision-required outcome.
- failure condition: duplicate child turn, lost reservation, parent continues
  after paused child, mutation of child packet, or host records controller
  decision.
- proof method: core state-machine/reservation tests and host bridge fixture.
- expected evidence: node histories, idempotency mapping, reservation ledger,
  terminal observations, and controller-decision record.

### Acceptance Criterion: Provider neutrality and migration

- setup or precondition: host API 3 adapter, candidate adapter fixture, legacy
  packet API 3 data, and API 4 request/host fixtures.
- action: run shared conformance; inspect packet 3 through host API 3; attempt
  packet-3 dispatch through host API 3; dispatch API 4 with host API 2 then
  host API 3.
- expected result: providers need no core route branch; packet 3 stays readable
  but host API 3 rejects its dispatch; API 4/host 2 blocks before dispatch;
  API 4/host 3 proceeds with features.
- failure condition: native provider authorization enters route policy,
  fallback/downgrade occurs, or historical evidence changes.
- proof method: core compatibility tests, launcher tests, host preflight, and
  shared conformance suite.
- expected evidence: selected compatibility profile, typed failure or dispatch
  record, conformance report, and unchanged historical packet digest.

## Completion Criteria

Specification is complete when:

1. one execution-node contract covers every admissible scheduled unit and one
   `AgentInvocation` contract covers every provider turn
2. delegation, context, capabilities, budgets, and structured outcomes have
   one authoritative owner and explicit denial behavior
3. host effects and controller decisions remain separated from core policy
4. packet/host/request compatibility and legacy migration are explicit
5. invariants cover recursive delegation, workspace containment, verification,
   cancellation, concurrency, and historical packets
6. every required outcome maps to backend and provider conformance proof
7. implementation sequencing remains for separate approved plan
