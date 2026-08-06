---
artifact_type: plan
template_id: implementation-plan
status: completed
layer: change
parent_spec: docs/superpowers/specs/2026-08-05-uniform-harness-execution-orchestrator.md
targets:
  - scripts/harness_task.py
  - repo_config/harness.yaml
  - agents/roles.yaml
  - docs/operating_system/procedures/managed-execution-adapter-contract.md
related_features:
  - managed-harness
  - codex-host-adapter
---

# SSOT Symmetric Harness Host Adapter Plan

## Goal

Make managed execution real without a second controller, route table, run
schema, or per-mode executor. Every admissible request uses one packet, lane
DAG, lifecycle engine, host-adapter effect protocol, evidence model, and
controller decision path.

An admissible request is one whose route permits its canonical topology, whose
packet and gates validate, and whose host adapter reports that topology
`enforced`. Every other request records `execution_mode_unavailable` or
`blocked`; no mode falls back or partially dispatches.

## Implementation Outcomes

- Immutable version-3 packets include user request, role-derived claim schema,
  lane DAG, packet-native tool bindings, workspace, checks, and gates.
- Host reports one verified execution record for each writer and validator lane;
  core persists it and rejects missing, ambient, mismatched, or validator-write
  evidence.
- Each enabled topology uses isolated writers, one materialized final workspace,
  same-workspace checks, fresh read-only validation, then explicit controller
  decision. Sequential and parallel remain unavailable until separately proven.
- Every managed request resolves `runtime_provider_id` once. Its immutable
  packet object contains canonical provider ID and contract version; adapter
  identity and every host evidence record match that object.

## Scope And Boundaries

- `project-OS-starter` remains canonical owner of policy, role contracts,
  packet/run semantics, lifecycle transitions, verification, and generated
  instructions.
- New private repository `codex-harness-host` owns only Codex App Server
  process control and translation of harness effects to host operations.
- Runtime providers are interchangeable effect executors. They never own
  routing, packet policy, run state, verification semantics, or controller
  decisions. `codex_app_server` is first provider; OpenHands remains a future
  provider candidate, not a special execution path or current dependency.
- `scripts/harness_task.py` stays core owner for first host proof. Do not add a
  package, second schema file, MCP policy copy, or alternate controller.
- Current uncommitted fail-closed waiver changes remain in scope and must be
  preserved. Do not revert or duplicate them.
- Generic CLI remains adapter-free. Its managed `run` operation must remain
  `execution_mode_unavailable` unless an injected host adapter exists.
- Autonomous prompt-classification heuristics and background daemon scheduling
  are excluded. Host-side activation guard is required before claiming managed
  execution enforcement; parallel production rollout remains excluded from
  first host proof.

## Canonical Model

| Fact | Single owner | Consumers |
| --- | --- | --- |
| Route, canonical topology, gates, retry policy | `repo_config/harness.yaml` | harness core, routing renderer, docs |
| Role claim shape and field constraints | `agents/roles.yaml` | harness core, host prompts |
| Request normalization, packets, lane DAG, transitions, evidence | `scripts/harness_task.py` | generic CLI, host adapter |
| Provider IDs, contract versions, and route compatibility | `repo_config/harness.yaml` | packet resolver, controller, host adapter |
| Runtime capability and Codex process state | private host adapter | harness core through `capabilities()` |
| Mutable run truth | `.harness/runs/<run-id>/run.json` | controller and verifier |
| Human guidance | canonical rules, skills, and generated adapters | people and agents |

Canonical topology names:

| Canonical topology | Legacy alias | Work lanes | Final-state node and validator |
| --- | --- | --- | --- |
| `single_work_lane` | `single_agent` | one `primary` lane | one `integrate` node, then one read-only `validate` lane |
| `sequential_work_lanes` | `sequential_agents` | dependency-ordered lanes | one `integrate` node, then one read-only `validate` lane |
| `parallel_work_lanes` | `parallel_lanes` | disjoint isolated lanes | one `integrate` node creates final state, then one read-only `validate` lane |

The terms describe topology, not count of total agents. `integrate` is a
controller-owned host effect: every managed topology starts from adapter-owned
isolated workspaces. Single and sequential topologies materialize their sole
final workspace; parallel workspaces materialize one merged final state or
fail. Each topology therefore has identical work/integrate/validate semantics.

Runtime-provider symmetry uses the same boundary. A route permits one or more
provider IDs; controller selects exactly one permitted ID before packet
creation. Packet stores that immutable selection. Adapter reports its own
provider ID and contract version; core rejects a mismatch before workspace
creation. Runtime capability is dynamic adapter evidence, not static policy.
No automatic provider fallback occurs: a different provider requires a
controller-created successor attempt, preserving the original packet.

## Execution Approach

- Mode: direct source-first implementation until private host adapter reports
  `single_work_lane: enforced`. Do not use managed subagent skill before that
  capability exists.
- Required skills: `skill-executing-plans`, `skill-code-standards`,
  `skill-test-driven-development`, `skill-backend-verification`,
  `skill-subagent-driven-development`, `skill-verification-before-completion`.
- Isolation: one writer in `project-OS-starter`. Private adapter work occurs in
  its own repository. No shared-write parallelism.
- Dependency discipline: use Python standard library (`asyncio`, `subprocess`,
  `json`) for first private adapter. Add no RPC, DAG, queue, or workflow
  dependency.
- Capability discipline: host reports only proven `enforced` modes. Unsupported
  topology remains unavailable even when route policy permits it.

## Task Breakdown

### Task 0: Prove Host Control And Enforcement Boundary

**Purpose:**
- Verify current Codex host can start actual work, preserve session/run identity,
  relay approvals/cancellation, and enforce writer/validator containment within
  adapter-owned isolated workspaces.

**Specification Coverage:**
- Controller classification and host capability intersection.
- No silent local fallback or false enforcement claim.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `docs/operating_system/provider_capabilities.yaml:providers.codex`
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md`
- Inspect: `scripts/deploy_agent_runtime.py`
- Create: `../codex-harness-host/docs/feasibility-report.md`
- Verify: private disposable Git repository

**Dependencies:**
- Codex host installation and private adapter repository location are available.

**Steps:**
- [x] Verify actual Codex App Server support for separate work and validator
  threads, final-result collection, cancellation, and approval events. Work,
  result collection, cancellation, approval request, and cancel relay passed.
- [x] Verify `UserPromptSubmit` and `PreToolUse` hook behavior against current
  generated Codex runtime. No repo-owned hook payload exists; global direct
  desktop-write interception is excluded from managed scope.
- [x] Verify host can enforce validator read-only execution against a deliberate
  write attempt. Native `read-only` sandbox denied a disposable agent write;
  raw `commandExecution` evidence records access denied and absent final file.
- [x] Verify host can enforce writer containment: a writer succeeds in its
  adapter-owned isolated workspace and a write outside that root fails.
  `probe_writer_containment.ps1` exited `0`; inside write exists, sibling
  escape remains absent, and raw host event records outside-workspace denial.
- [x] Record observed capability, command/version, evidence, and failed cases
  in one private feasibility report. Do not add a second capability registry.
- [x] Mark feasibility state: `single_work_lane` is eligible for private adapter
  implementation; `sequential_work_lanes` and `parallel_work_lanes` remain
  unavailable. Formal adapter capabilities stay unavailable until Task 4.

**Verification:**
- [x] Manual disposable-repository probes with captured host event logs.
- Expected: every required property has direct evidence or an explicit
  unavailable result.

**Exit Criteria:**
- Host feasibility result determines exact adapter capabilities and whether
  Task 5 can add enforced controller activation rather than manual invocation.

### Task 1: Freeze Canonical V3 Contract

**Purpose:**
- Define one versioned managed request and lane-DAG contract. Preserve version-2
  input through one explicit normalizer; do not maintain two execution paths.

**Specification Coverage:**
- One lifecycle for every execution mode.
- Immutable packet per attempt.
- Explicit lane plan, independent validator, and capability intersection.

**Required Skills:**
- `skill-central-config-layer`
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `agents/roles.yaml:roles.validate`
- Modify: `scripts/harness_task.py:MANAGED_VERSION`
- Modify: `scripts/harness_task.py:resolve_managed_packet`
- Modify: `scripts/harness_task.py:_route_packet`
- Modify: `scripts/harness_task.py:_normalize_lanes`
- Modify: `repo_config/harness.yaml:orchestration`
- Modify: `scripts/validate_harness_config.py:validate`
- Modify: `tests/test_harness_task.py`
- Modify: `tests/test_validate_harness_config.py`

**Dependencies:**
- Existing version-2 records remain immutable historical evidence.

**Steps:**
- [x] Add one request normalizer. It accepts version 2 only to map legacy mode
  aliases to canonical names, then produces version-3 packet data.
- [x] Require immutable `user_request` in every managed packet. Host renders
  its agent prompt from this packet field and role contract only.
- [x] Add non-writing `validate` role before packet normalization creates its
  required validator lane. It accepts every template and requires `summary`,
  `findings`, and `verdict`; Task 2 owns validator-criterion evidence.
- [x] Replace canonical configuration names with `single_work_lane`,
  `sequential_work_lanes`, and `parallel_work_lanes`; retain old names only as
  declared aliases in same topology object.
- [x] Add topology fields for work scheduling, workspace mode, maximum parallel
  writers, and required validator lane. Do not encode host capability in YAML.
- [x] Add `kind` (`work`, `integrate`, or `validate`) and
  `required_claim_kind` to normalized execution nodes. Packet appends exactly
  one non-agent `integrate` node dependent on every work lane, then one
  validator lane dependent on that node.
- [x] Reject duplicate aliases, ambiguous aliases, missing validator policy,
  validator with write capability, invalid dependencies, and topology fields
  unknown to validator.
- [x] Preserve generic CLI behavior: normalized request without injected host
  adapter reaches `execution_mode_unavailable` before any lane dispatch.

**Verification:**
- [x] `python -m pytest tests/test_harness_task.py tests/test_validate_harness_config.py -q`
- Expected: v2 alias normalizes once; v3 packets use only canonical topology;
  every topology packet contains one integration node and one non-writing
  validator lane.

**Exit Criteria:**
- One packet schema represents all topology cases. No function branches on a
  legacy mode name after request normalization.

### Task 1A: Add One Runtime-Provider Contract

**Purpose:**
- Make runtime selection explicit, immutable, and provider-neutral without
  creating provider-owned routing, lifecycle, or evidence models.

**Specification Coverage:**
- One protocol for many execution providers.
- Static provider policy distinct from live runtime capability.
- Symmetric provider substitution and fail-closed selection.

**Required Skills:**
- `skill-central-config-layer`
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `repo_config/harness.yaml:runtime_providers`
- Modify: `repo_config/harness.yaml:routes.*.runtime_providers`
- Modify: `repo_config/harness.yaml:routes.*.default_runtime_provider`
- Modify: `scripts/validate_harness_config.py:validate`
- Modify: `scripts/harness_task.py:resolve_managed_packet`
- Modify: `scripts/harness_task.py:_adapter_capabilities`
- Modify: `scripts/harness_task.py:_adapter_call`
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`
- Modify: `tests/test_harness_task.py:FakeAdapter`
- Modify: `tests/test_validate_harness_config.py`

**Dependencies:**
- Task 1 packet normalization remains the only request-to-packet path.

**Steps:**
- [x] Add one static `runtime_providers` registry to `harness.yaml`, keyed by
  provider ID. Each row has only `contract_version`. Do not copy dynamic mode,
  sandbox, workspace, tool, credential, or deployment facts from a host.
- [x] Require every managed route to name its allowed provider IDs and exactly
  one `default_runtime_provider` from that list. Controller chooses one
  permitted provider before packet creation; route default applies only when
  controller leaves provider unspecified. Reject unknown, duplicate, missing,
  or disallowed IDs deterministically.
- [x] Accept optional request `runtime_provider_id`; resolve route default only
  when it is absent. Store exactly one selected
  `runtime_provider: {provider_id, contract_version}` object in each immutable
  packet and successor attempt. A provider change requires controller-created
  successor attempt; never auto-fallback during dispatch or retry.
- [x] Require adapter `identity()` to return exactly
  `{provider_id, contract_version}` after the selected mode is `enforced` and
  before workspace preparation or lane dispatch. Reject identity mismatch
  before workspace preparation or lane dispatch. Carry exact selected provider object in tool-binding,
  execution, and check evidence; core rejects mismatch before acceptance.
- [x] Keep `capabilities()` runtime-only. It reports present enforcement for
  the selected provider; static registry never marks a mode enforced.
- [x] Add shared contract tests: default selection, explicit allowed selection,
  unknown/disallowed selection, adapter mismatch, evidence mismatch,
  unavailable capability, and successor-provider immutability. Reuse
  `FakeAdapter`; add no plugin loader.

**Verification:**
- [x] `python -m pytest tests/test_harness_task.py tests/test_validate_harness_config.py -q`
- Expected: every accepted packet names one permitted provider; invalid or
  mismatched provider blocks before workspace creation; all provider paths use
  same lane, evidence, verifier, and controller-decision shape.

**Exit Criteria:**
- A second provider can be added as configuration plus one conforming adapter;
  no controller, packet, lifecycle, or verifier fork is required.

### Task 2: Add Validator Role And Claim Evidence

**Purpose:**
- Make independent validator evidence machine-checkable instead of manual
  review prose or implementer self-attestation.

**Specification Coverage:**
- Agent dispatch and claim collection.
- Evidence-based verification.
- Review and approval stay separate.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `agents/roles.yaml:roles`
- Modify: `scripts/validate_harness_config.py:ROLE_FIELDS`
- Modify: `scripts/harness_task.py:_validate_managed_claim`
- Modify: `scripts/harness_task.py:_verify_managed`
- Modify: `tests/test_harness_task.py`
- Modify: `tests/test_validate_harness_config.py`

**Dependencies:**
- Task 1 packet exposes integration node, validator lane, and role.

**Steps:**
- [x] Add generic optional role field constraints. Configure validator
  `verdict` as exactly `pass` or `fail`; do not hard-code role name in Python.
- [x] Add `validator` acceptance criterion kind. It is proven only when the
  validator lane has a role-valid claim with `verdict: pass` after successful
  final-state materialization.
- [x] Record validator claim reference and verdict under attempt evidence.
  Implementer claims, `manual_evidence`, approval records, and local checks
  cannot satisfy this criterion.
- [x] Make all managed topology packets include validator criterion. Preserve
  existing `check`, `change_set`, `review`, and `manual` meanings for explicit
  non-validator criteria.

**Verification:**
- [x] `python -m pytest tests/test_harness_task.py tests/test_validate_harness_config.py -q`
- Expected: missing validator claim, invalid verdict, or `fail` verdict blocks
  acceptance; only independent `pass` claim proves validator criterion.

**Exit Criteria:**
- Validator evidence has one role-configured shape and one verifier path.

### Task 3: Replace Single-Lane Dispatch With Generic DAG Scheduler

**Purpose:**
- Use one scheduler for every topology. Only ready lanes dispatch; validators
  run after work lanes; parallelism is a scheduling limit, not a second engine.

**Specification Coverage:**
- Uniform lifecycle execution.
- Lane dependencies, workspace ownership, dispatch, claim collection, and
  cancellation.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/harness_task.py:_execute_attempt`
- Modify: `scripts/harness_task.py:_adapter_capabilities`
- Modify: `scripts/harness_task.py:_adapter_call`
- Modify: `scripts/harness_task.py:_validate_managed_claim`
- Modify: `scripts/harness_task.py:_record_failure`
- Modify: `tests/test_harness_task.py:FakeAdapter`
- Modify: `tests/test_harness_task.py`

**Dependencies:**
- Tasks 1 and 2 complete.

**Steps:**
- [x] Replace `lanes[0]` dispatch with one readiness loop over normalized DAG.
  Work and validator lanes become ready only when every dependency succeeds;
  integration node becomes ready after every work-lane claim.
- [x] Use same effect sequence for every lane: prepare workspace, dispatch,
  collect claim, validate claim, record claim, then release or cancel handle.
- [x] Use one `materialize_final_state` adapter effect for every integration
  node. Record returned final workspace identity as evidence before dispatching
  validator. Current-workspace modes return identity state; parallel modes
  return one integrated state or a common failure.
- [x] Dispatch every ready work lane before claim collection where topology
  permits concurrency. Limit writable lanes by topology maximum; validators
  never overlap unfinished dependencies or integration.
- [x] On dispatch, workspace, claim, or cancellation failure, cancel active
  handles, record one common failure outcome, and leave prior lane records
  immutable.
- [x] Verify only after all required lane claims exist. Preserve one state path:
  `planned → running → observed → verifying → awaiting_decision`.
- [x] Reject an adapter capability as `enforced` unless it explicitly lists the
  canonical topology. Alias names must never appear in capability response.

**Verification:**
- [x] `python -m pytest tests/test_harness_task.py -q`
- Expected: single, sequential, and parallel fake-adapter topologies use same
  scheduler; integration failure prevents validator dispatch; dependency
  failure prevents integration; cancellation runs for active handles; state
  history remains valid.

**Exit Criteria:**
- No orchestration-specific dispatch or final-state branch remains outside
  topology data and generic dependency scheduling.

### Task 4: Implement Codex App Server Provider Adapter

**Purpose:**
- Connect immutable packet effects to real Codex work as provider
  `codex_app_server`, without copying harness policy or lifecycle code.

**Specification Coverage:**
- Host adapter capability contract.
- Workspace preparation, agent dispatch, claim collection, cancellation.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Create: `../codex-harness-host/pyproject.toml`
- Create: `../codex-harness-host/src/codex_harness_host/adapter.py`
- Create: `../codex-harness-host/src/codex_harness_host/app_server.py`
- Create: `../codex-harness-host/src/codex_harness_host/claims.py`
- Create: `../codex-harness-host/src/codex_harness_host/activation_guard.py`
- Create: `../codex-harness-host/src/codex_harness_host/cli.py`
- Create: `../codex-harness-host/tests/test_adapter.py`
- Create: `../codex-harness-host/tests/test_claims.py`
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`

**Dependencies:**
- Task 0 feasibility report supports required properties.
- Task 3 generic scheduler complete.

**Steps:**
- [x] Create private repository. Keep it out of starter-kit manifest and public
  export configuration.
- [x] Implement stdlib-only JSON-RPC App Server client with `asyncio`,
  `subprocess`, and `json`. Keep protocol framing isolated in `app_server.py`.
- [x] Implement adapter methods from canonical contract. Adapter imports and
  calls `scripts/harness_task.py:run_managed`; it never reimplements packet
  resolution, transition, verification, or decisions.
- [x] Implement `identity()` and report the canonical runtime identity
  `{provider_id: "codex_app_server", contract_version: 1}`. Every host
  workspace, tool-binding, lane, command, check, and validator evidence record
  carries that same provider identity.
- [x] Implement `materialize_final_state`. It returns identity current state for
  one-workspace runs; it materializes one merge-checked final state for isolated
  work lanes; it returns common failure on integration conflict.
- [x] Implement `capabilities()` conservatively: report only
  `single_work_lane: enforced` after all feasibility checks pass. Report every
  other topology unavailable.
- [x] Prepare writer in requested workspace. Run validator in same final state
  with host-enforced read-only sandbox. If host cannot enforce that boundary,
  report topology unavailable; prompt wording alone is insufficient.
- [x] Render agent prompts only from packet and role contract. Require one JSON
  `claimed_result`; validate and normalize it in `claims.py` before returning.
- [x] Forward user approval and cancellation events. Never auto-accept,
  retry, waive, or alter `run.json`.
- [x] Require adapter-owned isolated workspaces for every managed writer. Prove
  host `workspace-write` allows in-root writes and rejects workspace escape;
  never claim global desktop/CLI write interception.

**Verification:**
- [x] `python -m pytest ../codex-harness-host/tests/test_adapter.py ../codex-harness-host/tests/test_claims.py -q`
- Expected: fake App Server proves effect translation, final-state
  materialization, JSON claim parsing, cancellation, workspace-containment
  decision, and unavailable capability fallback.
- [x] Manual local App Server smoke in a disposable Git repository.
- Expected: one writer, one final-state materialization, and one fresh
  validator thread run; validator cannot modify source; run record contains
  both claims and no policy duplication.

**Exit Criteria:**
- Private Codex provider runs one real `single_work_lane` attempt through
  canonical harness core and reports no unsupported capability as enforced.

### Task 5: Add Controller Entry Point, Guard, And Live Acceptance Proof

**Purpose:**
- Give controller one real managed command surface, activate guard after route
  selection, and prove acceptance requires fresh validator claim plus direct
  repository evidence.

**Specification Coverage:**
- Controller classification, controller-only decision, honest verification,
  explicit unavailable/waiver behavior.

**Required Skills:**
- `skill-subagent-driven-development`
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Create: `../codex-harness-host/tests/test_live_single_work_lane.py`
- Modify: `../codex-harness-host/src/codex_harness_host/cli.py`
- Modify: `scripts/harness_task.py:main` only if adapter CLI needs a stable
  import-safe entry point; keep generic CLI adapter-free.
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `.agents/skills/skill-subagent-driven-development/SKILL.md`
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`

**Dependencies:**
- Task 4 real host adapter proof passes.

**Steps:**
- [x] Add one host CLI command accepting harness root and version-3 request.
  It prints only managed result JSON and preserves controller decision as a
  separate explicit command.
- [x] Run only adapter-owned isolated workspaces. Ambient desktop or CLI threads
  remain source-first and unvalidated; never claim global write interception.
- [x] Add environment-gated live test. It creates temporary Git repo, supplies
  bounded request, runs host CLI, asserts writer and validator claims, then
  calls controller `accept` only after check plus validator evidence.
- [x] Add negative live scenarios: unavailable read-only validator capability;
  validator `fail`; final-state integration conflict; workspace escape;
  cancellation; explicit waiver. Each must not become accepted.
- [x] Update root instructions and subagent skill only after live proof. They
  must name actual host command/tool, not a future adapter.

**Verification:**
- [x] `CODEX_HARNESS_LIVE=1 python -m pytest ../codex-harness-host/tests/test_live_single_work_lane.py -q`
- Expected: real host lifecycle reaches `awaiting_decision`, then controller
  accepts only validated work.
- [x] `python -m pytest tests/test_harness_task.py -q`
- Expected: generic CLI remains unavailable and explicit waiver remains
  terminal `unvalidated`.

**Exit Criteria:**
- One real end-to-end managed run has packet, writer claim, final-state
  evidence, validator claim, direct check evidence, guarded source write
  rejection, and recorded controller acceptance.

### Task 6: Enable Further Topologies Without New Lifecycle Code

**Purpose:**
- Prove symmetry: new topology capability changes only lane plans and host
  workspace behavior, never controller or verifier protocol.

**Specification Coverage:**
- Controlled mode expansion.
- Sequential and parallel workspace isolation.

**Required Skills:**
- `skill-dispatching-parallel-agents`
- `skill-using-git-worktrees`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py`
- Modify: `../codex-harness-host/src/codex_harness_host/app_server.py`
- Modify: `../codex-harness-host/tests/test_adapter.py`
- Modify: `../codex-harness-host/tests/test_live_single_work_lane.py`
- Modify: `repo_config/harness.yaml:orchestration` only when capability proof
  requires a new canonical topology field.
- Modify: `scripts/harness_task.py` only for generic scheduler defect found by
  adapter proof; no topology-specific executor.

**Dependencies:**
- Task 5 live single-work-lane proof passes.

**Steps:**
- [x] Enable `sequential_work_lanes` only for linear dependency chains: one
  root, one successor per writer, one terminal. Prepare each successor as a
  fresh base clone materialized from its direct predecessor. Reject branches,
  joins, multiple roots, and missing predecessor state before dispatch.
- [x] Enable `parallel_work_lanes` only after host creates isolated base clones,
  materializes one fresh final base clone in deterministic lane-ID order, and
  rejects two actual writer changes to same path before validator dispatch.
- [x] Initially materialize only regular-file adds, modifications, deletions,
  and untracked files. Reject renames, copies, unmerged states, type changes,
  submodules, and symlinks; expand only with direct merge proof.
- [x] Add adversarial proof for invalid sequential chain, parallel same-path
  conflict, unsupported file state, failed integration with no validator
  dispatch, and validator source write attempt.
- [x] Run live accepted sequential then parallel topology smoke. Each proves
  writer isolation, packet-native tools, final-workspace checks, fresh
  read-only validator, exact provider identity, and explicit controller accept.
- [x] Keep capability unavailable when any invariant cannot be host-enforced.

**Verification:**
- [x] Fake-adapter matrix test over every canonical topology.
- Expected: same packet, evidence, outcome, and decision schema across modes.
- [x] Environment-gated live smoke for each newly enabled topology.
- Expected: mode-specific workspace behavior differs; lifecycle and acceptance
  protocol do not.

**Exit Criteria:**
- Adding a topology required no new controller state, run schema, evidence
  format, or acceptance path.

### Task 6A: Add Provider-Conformance Gate

**Purpose:**
- Make future runtime-provider admission a repeated proof operation, not a
  second controller integration or provider-specific exception.

**Specification Coverage:**
- One protocol for many providers.
- Packet-root tool enforcement, final-workspace checks, and fresh validator
  symmetry across provider implementations.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/harness_task.py` only for provider-neutral contract checks
- Modify: `tests/test_harness_task.py`
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`
- Modify: `docs/operating_system/provider_capabilities.yaml` only to label it
  generated-surface metadata, never managed-runtime capability truth

**Dependencies:**
- Task 1A provider selection and Task 5 live Codex provider proof pass.

**Steps:**
- [x] Add one reusable core adapter-conformance fixture. It accepts an adapter
  implementation and checks identity match, isolated writer root, all selected
  tool bindings rooted in packet workspace, final-workspace checks, separate
  read-only validator, host event evidence, cancellation, and unavailable-mode
  fail-closed behavior.
- [x] Keep test vectors provider-neutral. `codex_app_server` supplies first
  live implementation; a future OpenHands provider must run same vectors with
  no controller or verifier conditional.
- [x] Require candidate providers to prove a fresh final workspace validator
  and denied validator write. Docker mount semantics, UI history, prompt text,
  or implementer claims alone never satisfy conformance.
- [x] Keep provider absent from route policy until conformance passes. A failed
  candidate remains unavailable with friction evidence; no waiver upgrades it
  to managed acceptance.

**Verification:**
- [x] `python -m pytest tests/test_harness_task.py -q`
- [x] Environment-gated conformance smoke for every provider admitted to a
  managed route.
- Expected: provider differences appear only in host evidence values; packet,
  run state, criteria, verifier result, and controller decision remain equal.

**Exit Criteria:**
- Adding a conforming provider needs one adapter, one policy row, and the same
  conformance evidence; it needs no new core execution branch.

### Task 7: Reconcile Generated Surfaces And Starter Kit

**Purpose:**
- Ship canonical core and truthful guidance. Keep private host runtime out of
  clone-ready starter output.

**Specification Coverage:**
- SSOT, generated instructions, publication boundary, starter-kit parity.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-private-public-repo-governance`

**Files And Symbols:**
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `.agents/skills/skill-subagent-driven-development/SKILL.md`
- Modify: `repo_config/starter-kit-manifest.json` only for canonical contract
  additions.
- Generate: `AGENTS.md`
- Generate: `generated_agents/codex/**`
- Verify: `generated_exports/project-OS-starter-kit`

**Dependencies:**
- Tasks 1 through 6 completed or explicitly unavailable with recorded reason.

**Steps:**
- [x] Replace legacy names in human guidance with canonical names and document
  aliases only in compatibility section.
- [x] State exact live host command/tool only after Task 5. Do not claim
  automatic controller enforcement before it exists.
- [x] Document provider IDs, static-policy ownership, dynamic-capability
  ownership, and conformance admission in canonical contract guidance. Keep
  `provider_capabilities.yaml` out of runtime capability decisions.
- [x] Run adapter sync. Do not hand-edit generated output.
- [x] Build starter kit. Confirm harness core and contract ship; confirm private
  host source, credentials, runtime state, and provider-specific deployment
  artifacts do not ship.

**Verification:**
- [x] `python scripts/sync_agent_adapters.py --check`
- [x] `python scripts/validate_agent_runtime_drift.py --skip-deploy-check`
- [x] `python scripts/build_starter_kit.py`
- [x] `python scripts/validate_starter_kit.py`
- Expected: generated surfaces match canonical sources; kit contains no private
  host adapter or `.harness` state.

**Exit Criteria:**
- Starter users receive one truthful contract and no private runtime dependency.

### Task 8: Add SSOT Friction Learning Loop

**Purpose:**
- Turn repeated verified execution friction into controller-owned improvement
  candidates without autonomous policy, tool, skill, provider, or route mutation.

**Specification Coverage:**
- One friction fact store, symmetric evidence across every lane and topology,
  controller-owned improvement selection, and fresh-rerun-only learning.

**Required Skills:**
- `skill-improve-harness`
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `repo_config/harness.yaml:friction_policy`
- Modify: `scripts/validate_harness_config.py:validate`
- Modify: `scripts/harness_task.py` friction recording, report, resolution,
  and CLI commands
- Modify: `tests/test_harness_task.py`
- Modify: `tests/test_validate_harness_config.py`
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`
- Modify: `.agents/skills/skill-improve-harness/SKILL.md`
- Modify: `docs/operating_system/templates/harness-improvement-template.md`

**Dependencies:**
- Tasks 1 through 7 completed.

**Steps:**
- [x] Add one static `friction_policy` registry. It owns event schema version,
  distinct-run threshold, and rolling window only; it never stores observed
  runtime state or remediation decisions.
- [x] Write every new observed friction once to append-only
  `.harness/friction-events.jsonl`. Run attempts store event IDs only. Each
  event records run, attempt, route, provider, mode, lane kind, phase, source,
  code, evidence reference, timestamp, and deterministic fingerprint. Do not
  copy prompts, secrets, or raw command logs.
- [x] Route agent claim friction, adapter failure, failed check, integration,
  validator, cancellation, and decision friction through one normalizer. Lane
  and topology differences become event fields, never separate ledgers.
- [x] Add read-only `friction-report` command. It derives unresolved candidates
  only from canonical events, requires configured distinct runs inside rolling
  window, and emits no state change.
- [x] Add controller-only `friction-resolve` command. It accepts only an
  accepted `harness_improvement` run and appends immutable `resolution` event
  with `keep`, `revise`, `remove`, or `pending`. It never changes harness
  configuration or upgrades failed work.
- [x] Update contract, improvement skill, and artifact template. A candidate
  must name fingerprint, baseline event IDs, smallest change, and fresh
  representative rerun before controller records resolution.

**Verification:**
- [x] `python -m pytest tests/test_harness_task.py tests/test_validate_harness_config.py -q`
- [x] `python scripts/harness_task.py --repo-root . friction-report`
- [x] `python scripts/validate_harness_config.py --repo-root .`
- [x] `python scripts/validate_repo_contracts.py`
- Expected: one same-schema event stream covers every source; repeated events
  yield a candidate only at threshold; resolution requires accepted improvement
  evidence; no report or resolution mutates policy.

**Exit Criteria:**
- Repeated verified friction can trigger one controller-selected,
  independently-verified improvement experiment. Harness learning remains
  traceable, reversible, and policy-safe.

## Verification

- `python -m pytest tests/test_validate_harness_config.py tests/test_harness_task.py tests/test_render_harness_routing.py tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py -q`
- `python scripts/validate_harness_config.py --repo-root .`
- `python scripts/render_harness_routing.py --repo-root . --check`
- `python scripts/validate_repo_contracts.py`
- `python scripts/validate_agent_runtime_drift.py --skip-deploy-check`
- `python scripts/build_starter_kit.py`
- `python scripts/validate_starter_kit.py`
- `git diff --check`
- `CODEX_HARNESS_LIVE=1 python -m pytest ../codex-harness-host/tests/test_live_single_work_lane.py -q`

## Completion Criteria

Plan is ready for completion verification when:

1. canonical topology, alias normalization, and one immutable selected runtime
   provider produce one version-3 packet shape for every admissible request
2. every managed topology contains final-state integration plus a fresh
   non-writing validator lane, and validator `pass` evidence is required for
   acceptance
3. core scheduler handles every lane DAG without mode-specific lifecycle code
4. private host adapter uses canonical core rather than copied policy or state
   machine, reports only proven capabilities as enforced, and uses host guard
   for managed-selected source-write enforcement
5. unavailable, failed validation, scope escape, cancellation, and waiver
   cannot become accepted
6. sequential and parallel mode activation changes lane/workspace data only;
   their run record, evidence, decisions, and retries stay identical
7. generated instructions and starter kit are synchronized and exclude private
   host runtime
8. every route-admitted provider passes same conformance gate; live proof for
   every admitted topology and all final checks pass from fresh evidence
9. friction observations, derived candidates, and controller resolutions use
   one immutable event schema; no automatic harness mutation exists

The plan may be marked `completed` only when
`skill-verification-before-completion` returns `verified` from fresh evidence.

## Execution Record

- 2026-08-05 — blocked at Task 0 before core or private-adapter edits.
  `codex.exe` resolves only to
  `C:\Program Files\WindowsApps\OpenAI.Codex_26.730.7989.0_x64__2p2nqsd0c76g0\app\resources\codex.exe`.
  Both `codex --version` and `codex app-server --help` fail with Windows
  `Access is denied` from this execution environment. Direct Node process spawn
  of `codex.exe app-server --help` independently fails with `EPERM`.
- 2026-08-05 — no user App Execution Alias or alternate `.codex\bin` executable
  exists. No deployed `~/.codex/config.toml` or `~/.codex/hooks.json` exists to
  probe current hook/session behavior. Static provider capability metadata is
  not runtime proof.
- 2026-08-05 — external user-terminal proof: `codex --version` returns
  `codex-cli 0.146.1`; `codex app-server --help` lists local daemon, stdio
  proxy, TypeScript bindings, JSON Schema generation, and `ws://` listen
  transport. The executable is usable from normal user terminal but not from
  this agent sandbox.
- 2026-08-05 — Task 0 executed against user-started loopback App Server.
  Separate ephemeral threads, turn-result collection, and cancellation passed.
  `sandbox: "read-only"` denied an agent write in a disposable Git workspace.
  Approval cancel relay passed. User selected adapter-owned isolated workspace
  enforcement; global `UserPromptSubmit`/`PreToolUse` interception is out of
  scope. Writer containment remains unproven. See private
  `../codex-harness-host/docs/feasibility-report.md`. All managed topologies
  remain `unavailable` until that proof exists.
- 2026-08-06 — Provider-neutral runtime proof passed against loopback App
  Server. Run `provider-smoke-eba3306be3e540a1890a00de3413e188` selected
  immutable `codex_app_server:1`, completed writer, same-final-workspace
  checks, fresh read-only validator, and explicit controller acceptance.
  Adapter identity plus tool-binding, lane, command, and check evidence all
  matched packet provider. Core full suite (131), host suite (5), sync, drift,
  starter build, starter validation, and `git diff --check` passed. Sequential
  and parallel remain explicitly unavailable.
- 2026-08-06 — Host topology proof enabled all canonical modes. Host unit tests
  prove linear sequential inheritance, parallel isolated merge, same-path and
  rename rejection, bounded packet-tool evidence retry, and concurrent-ready
  dispatch. Accepted `sequential-smoke-4cc3ce1a819c40fc9e5417f04e1d7166`
  showed successor inheritance and shared final validation. Accepted
  `parallel-smoke-155836041f16413cb2f9d6dc21af17af` showed isolated writers,
  fresh integrated final state, check, read-only validator, and controller
  acceptance. No core topology branch or run-schema change was added.
- 2026-08-06 — Completion proof passed. `tests/test_live_single_work_lane.py`
  creates a temporary Git harness fixture, runs host CLI with one version-3
  request, requires writer and fresh read-only validator claims plus direct
  final-workspace checks, then records controller `accept`. Negative lifecycle
  coverage remains split by boundary: core tests reject unavailable validators,
  validator failure, integration conflict, cancellation, and waiver; live host
  probes prove validator read-only, writer containment, and approval relay.
  Fresh core suite (74), host suite (14 passed, 1 gated skip), live proof,
  config, generated-surface sync, runtime drift, contracts, starter build,
  starter validation, and `git diff --check` passed.
- 2026-08-06 — Task 8 completed. `repo_config/harness.yaml` now owns the
  friction event version, threshold, and window; `.harness/friction-events.jsonl`
  holds append-only observations and controller resolutions; attempts retain
  event IDs only. Fresh focused and full harness/config tests, read-only report,
  config, contracts, generated adapter drift, starter build, and starter
  validation passed. No command changes harness policy automatically.
