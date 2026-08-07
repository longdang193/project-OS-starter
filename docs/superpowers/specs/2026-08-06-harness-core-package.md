---
artifact_type: spec
template_id: detailed-specification
status: active
layer: change
related_specs:
  - docs/superpowers/specs/2026-08-05-uniform-harness-execution-orchestrator.md
  - docs/superpowers/specs/2026-08-06-plan-linked-harness-coordination.md
---

# Harness Core Package

## Goal and Problem

### Problem

- current behavior: starter and consumer repositories contain editable copies
  of harness packet resolution, plan coordination, and validation scripts.
  `codex-harness-host` dynamically loads the copy at the selected harness root.
- affected users, systems, or maintainers: every consumer repository,
  controller, provider host, and maintainer updating harness behavior.
- evidence: a consumer copy lacked plan-task `allowed_paths` derivation even
  after canonical starter code had the contract. Host preflight passed because
  it correctly loaded the stale consumer copy.
- consequence of no change: each core fix requires synchronized manual edits,
  tests, kit rebuilds, and consumer deployments. Drift can block managed work
  late with a misleading configuration error.

### Goal

- desired outcome: one versioned Python package owns executable harness-core
  behavior for direct CLI and every provider host. A separate launcher owns
  only package-availability reporting. Consumer repositories own repository
  data and required request-protocol policy.
- observable success: an admissible consumer, route, topology, and provider
  resolves and executes through the same core API. A protocol mismatch or
  unavailable package blocks before packet creation with a precise typed result.

## Required Outcomes

### Outcome: One executable core

- affected actor or system: starter maintainers, consumer repositories, direct
  CLI, and provider hosts.
- required result: packet resolution, plan coordination, lifecycle execution,
  validation, and status commands exist in one `harness-core` package.
- success condition: no consumer-local script contains an independent core
  implementation or diverges in packet, plan, scope, run-state, or validation
  semantics.

### Outcome: Symmetric entrypoints

- affected actor or system: direct CLI, `codex-harness-host`, and future
  conforming provider hosts.
- required result: all entrypoints invoke the same package API with repository
  root and provider adapter as inputs.
- success condition: no entrypoint dynamically imports executable core code
  from a consumer repository, and no provider reimplements route selection,
  plan parsing, scope derivation, run transitions, or controller decisions.

### Outcome: Consumer data ownership

- affected actor or system: each harness consumer repository.
- required result: each consumer retains ownership of its route policy, roles,
  rules, skills, plans, requested work, and mutable `.harness` records.
- success condition: core release changes do not copy consumer policy or plans
  into another repository, and package code never owns consumer-specific facts.

### Outcome: Explicit compatibility admission

- affected actor or system: controller, core package, and provider host.
- required result: `pyproject.toml` and lockfiles declare PEP 440 package
  dependency compatibility. Consumer policy declares one required integer
  request API. Core exposes one immutable compatibility matrix and package
  release. Host preflight and direct CLI evaluate shared protocol admission
  before packet creation.
- success condition: an unsupported request API blocks as
  `harness_core_request_api_incompatible`; an absent or unloadable package
  blocks as launcher-owned `harness_core_environment_unavailable`. Neither path
  falls back to copied scripts, dynamic imports, implicit upgrades, or partial
  dispatch.

### Outcome: Preserved plan authorization contract

- affected actor or system: plan author, packet resolver, validator, and host.
- required result: plan task explicitly owns `allowed_paths` and
  `planned_write_paths`; core derives both for plan-linked requests.
- success condition: `planned_write_paths` is always a subset of
  `allowed_paths`; authorization is never inferred from planned writes.

### Outcome: Reduced release management

- affected actor or system: harness maintainers and consumer maintainers.
- required result: a core behavior update is built, tested, released, and
  installed once per runtime environment rather than copied into every
  consumer repository.
- success condition: a consumer adopts a compatible release by policy and
  runtime installation; it does not receive a hand-edited core source tree.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
|---|---|---|---|---|
| Where packet and plan behavior lives | Consumer copies of `harness_task.py` and `plan_coordination.py` resolve packets and coordination manifests. | Current starter and consumer harness sources | high | Move executable behavior to one package. |
| How provider host selects core | Host dynamically loads `<harness-root>/scripts/harness_task.py`. | `codex-harness-host` CLI loader | high | Replace dynamic target-core loading with package import. |
| What consumer-specific data exists | Route policy, required request API, roles, plans, rules, skills, workspace roots, and `.harness` state are repository-local. | Harness policy and plan contracts | high | Keep these as package inputs, never package-owned copies. |
| What must remain uniform | Single, sequential, and parallel work modes share packet and run contracts. | Execution-orchestrator and plan-link specs | high | Version admission and core API apply identically to every topology. |
| Why copied source is unsafe | A stale target copy caused a missing `allowed_paths` failure before packet creation. | Reproduced target resolution failure | high | Compatibility must fail early and name release mismatch. |

### Prototype and Validation Evidence

- prototype reference: Not applicable. This is backend/runtime architecture.
- validated scenarios and states: direct packet resolution, plan-linked scope
  derivation, consumer configuration validation, and host conformance tests
  exist as current proof boundaries.
- findings incorporated into approved behavior: generated consumer copies
  still require per-repository update management; package runtime is selected
  as final SSOT.
- rejected alternatives:
  - generated copied core plus hashes: preserves source ownership but retains
    per-consumer deployment and stale-copy management.
  - host-derived authorization: violates plan/policy ownership and creates
    provider-specific behavior.
  - deriving `allowed_paths` from `planned_write_paths`: narrows or corrupts
    authorization for read-only and broader-authorized tasks.

### Scope

- included behavior: core package API and CLI; host/core boundary; consumer
  core compatibility declaration; packet core identity; migration bridge;
  package-level validation and provider conformance.
- affected boundaries: starter kit contents, consumer harness entrypoints,
  provider-host loading, plan-linked resolution, configuration validation, and
  run/packet evidence.
- admissible cases:
  - direct CLI validation and status operations;
  - managed execution through any conforming provider;
  - `single_work_lane`, `sequential_work_lanes`, and
    `parallel_work_lanes`;
  - plan-linked and non-plan-linked requests;
  - consumer policy whose required request API is supported by core;
  - explicit unsupported request API, unsupported host API, or unavailable core
    environment.
- compatibility expectation: existing policy, role, plan, packet, run, tool,
  workspace, verification, and controller-decision contracts retain current
  behavior unless this specification explicitly changes ownership or early
  compatibility failure.

### Non-Goals

- automatic package upgrade or network download during managed execution;
- a distributed package registry, scheduler, lock service, or host queue;
- changing controller authority, provider selection, packet schema semantics,
  or core work-mode behavior beyond shared loading and compatibility admission;
- package ownership of consumer plans, policies, skills, roles, product code,
  credentials, or `.harness` records;
- retaining independently executable legacy consumer core scripts after
  migration completion.

### Requirements and Behavioral Contract

#### Requirement: Package API

- trigger or actor: direct CLI or conforming provider host starts a harness
  operation.
- preconditions: launcher loaded `harness-core` and consumer repository root
  exists.
- required behavior: package exposes one public operation equivalent to
  `run_managed(repo_root, request, adapter, run_id=None)` and package-owned
  operations for packet resolution, configuration validation, plan status,
  handoff, controller decision, and verification.
- output or state change: operations use only consumer-root inputs and create
  or update only authorized consumer `.harness` records.
- failure behavior: malformed inputs and core errors preserve existing typed
  failure semantics; no operation imports consumer Python core code.
- observable acceptance: direct CLI and provider-host calls produce identical
  packet normalization and run-state outcomes for equal inputs.

#### Requirement: Protocol compatibility declaration

- trigger or actor: direct CLI or host preflight addresses a consumer root.
- preconditions: consumer `repo_config/harness.yaml` exists and launcher loaded
  core.
- required behavior: policy declares `harness_core.request_api` as one positive
  integer. Package evaluates it against `SUPPORTED_REQUEST_APIS` before request
  resolution, packet creation, workspace preparation, or dispatch. Package
  evaluates adapter `host_api` against `SUPPORTED_HOST_APIS` before host
  dispatch.
- output or state change: compatibility result records package release, required
  request API, selected packet API, host API when applicable, and result.
- failure behavior: missing or malformed policy value returns
  `harness_core_request_api_invalid`; unsupported request API returns
  `harness_core_request_api_incompatible`; unsupported host API returns
  `harness_core_host_api_incompatible`. Each creates no packet, attempt,
  workspace, writer, validator, or product change. Package absence remains the
  launcher-owned environment failure.
- observable acceptance: direct CLI and every provider host report same protocol
  result for same consumer policy, package matrix, and adapter API.

#### Requirement: Launcher environment boundary

- trigger or actor: direct CLI or provider host begins a core operation.
- preconditions: separately installed `harness-core-launcher` command/library
  is available to that entrypoint.
- required behavior: launcher imports the installed `harness-core` package and
  invokes its public API only after import succeeds. Launcher owns no route,
  plan, policy, packet, lifecycle, or controller logic.
- output or state change: unavailable or unloadable core returns one typed
  result with `failure_class: environment`, code
  `harness_core_environment_unavailable`, and no actual package identity.
- failure behavior: launcher creates no consumer run, packet, attempt,
  workspace, writer, validator, or product change. It never loads consumer
  Python code as fallback.
- observable acceptance: direct launcher and every provider host emit the same
  environment failure shape for a missing or unloadable core.

#### Requirement: Core identity evidence

- trigger or actor: core resolves a managed packet or runs a direct operation.
- preconditions: compatibility admission passed.
- required behavior: immutable packet records exact package release, request
  API, `CURRENT_PACKET_API`, and host API when applicable. Run-level evidence
  records protocol admission result and package identity.
- output or state change: historical packets remain attributable to exact core
  behavior even after later package upgrades.
- failure behavior: absent identity is a core error and blocks packet creation.
- observable acceptance: packet and host evidence show same core identity.

#### Requirement: Host adapter boundary

- trigger or actor: provider host receives a managed request or planned run ID.
- preconditions: host advertises provider identity, integer `host_api`, and
  enforced capabilities.
- required behavior: host imports compatible package, constructs only its
  adapter, passes consumer root and request/run ID to package API, and records
  adapter evidence returned by package lifecycle.
- output or state change: host has no target-core loader and no copy of plan or
  packet policy logic.
- failure behavior: an unsupported host API fails package admission. Host never
  substitutes another core, alters authorization, or silently downgrades
  execution mode.
- observable acceptance: two conforming hosts receive same core packet for
  same consumer request; only provider evidence differs.

#### Requirement: Deterministic admission order

- trigger or actor: direct launcher or provider host receives an operation.
- preconditions: entrypoint has a consumer root; a host adapter can expose its
  static `host_api` without contacting provider runtime.
- required behavior: every entrypoint applies this order: launcher package-load;
  policy request-API parse and package matrix admission; host-API admission when
  an adapter exists; provider runtime preflight/capability check; full policy,
  request, plan, and packet resolution; workspace preparation; dispatch.
- output or state change: the first failed stage returns its typed result. Core
  compatibility failures occur before provider runtime connection attempts.
- failure behavior: malformed policy is a protocol-policy failure; unavailable
  package is launcher environment failure; unavailable provider runtime is a
  separate host-preflight failure only after package and protocol admission.
- observable acceptance: equal direct and host inputs produce equal launcher and
  protocol results before host-specific runtime evidence can differ.

#### Requirement: Plan scope derivation

- trigger or actor: a plan-linked managed request contains `plan_ref` and
  `plan_task_id`.
- preconditions: active Git-tracked plan and compatible core.
- required behavior: core resolves canonical mode, base ref, `allowed_paths`,
  and `planned_write_paths` from manifest task; request values may match but
  may not conflict.
- output or state change: immutable packet contains normalized task binding,
  digest, explicit authorization scope, and planned paths.
- failure behavior: missing task scope, unsafe path, duplicate path, planned
  path outside allowed scope, changed digest, or conflicting request value
  blocks before packet creation.
- observable acceptance: a task with empty planned writes and non-empty scope
  remains valid where role and route permit no writes.

#### Requirement: Package CLI

- trigger or actor: maintainer runs installed package command against a
  consumer root.
- preconditions: launcher loaded package; repository root path supplied.
- required behavior: one CLI exposes validation, plan status, handoff, packet
  inspection, and explicitly unavailable generic managed execution where no
  provider adapter exists.
- output or state change: CLI uses same core API as hosts; it never embeds an
  alternate resolver or copies consumer core scripts.
- failure behavior: provider-required managed execution reports unavailable
  mode rather than claiming dispatch. Package absence is reported by launcher,
  not by package CLI.
- observable acceptance: CLI output and provider preflight share compatibility
  and core identity fields.

## Design Decisions

### Decision: Package runtime is executable SSOT

- context: copied scripts created behavior drift despite canonical starter
  source and successful host preflight.
- selected approach: release one `harness-core` Python package. Starter owns
  package source, package tests, release metadata, and starter-kit consumer
  configuration templates. Installed package owns executable core behavior.
- rationale: one import path and release eliminate per-consumer core code
  copying while retaining consumer-root data ownership.
- alternatives considered: generated copies, dynamic consumer imports, and
  host-owned policy logic.
- accepted trade-offs: runtime environment must install a compatible package;
  package release is an explicit operational dependency.
- affected owners and boundaries: starter owns code/release; consumer owns
  data/compatibility policy; host owns adapter only.

### Decision: Package dependencies and runtime APIs stay separate

- context: package release compatibility and runtime protocol compatibility are
  different facts and must not share one version field.
- selected approach: `pyproject.toml` and lockfiles own PEP 440 dependency
  compatibility for package, launcher, and host installation. Consumer policy
  owns one integer `harness_core.request_api`. Package owns the sole runtime
  compatibility matrix:

  ```python
  SUPPORTED_REQUEST_APIS = {2, 3}
  SUPPORTED_PACKET_READ_APIS = {3}
  CURRENT_PACKET_API = 3
  SUPPORTED_HOST_APIS = {2}
  ```

- rationale: dependency resolvers decide installability; core decides runtime
  protocol behavior. Hosts and consumers consume matrix results and never copy
  matrix values.
- alternatives considered: one overloaded version range, per-consumer copied
  version files, host-hardcoded protocol policy, and automatic package upgrades.
- accepted trade-offs: consumers update requested integer deliberately when
  their request contract changes; package release remains an explicit runtime
  dependency.
- affected owners and boundaries: package metadata/lockfiles own PEP 440;
  policy owns required request API; package owns protocol matrix and evaluation;
  packets record selected identities.

### Decision: Separate launcher owns package-unavailable failure

- context: package code cannot report its own absence, but every entrypoint
  needs an observable no-side-effect environment failure.
- selected approach: separate `harness-core-launcher` imports core for direct
  CLI and provider hosts. It emits one typed environment result on missing or
  unloadable package, then delegates without interpreting consumer semantics.
- rationale: preserves one executable core without pretending an absent import
  can run package code.
- alternatives considered: raw Python import error, consumer-local fallback,
  launcher-owned packet resolver, or dynamic target-core import.
- accepted trade-offs: launcher is a small operational dependency and must be
  installed with host/direct entrypoints.
- affected owners and boundaries: launcher owns availability result only;
  package owns all executable harness semantics.

### Decision: Provider hosts import package, never consumer executable code

- context: dynamic target script loading made host correctness depend on every
  consumer copy.
- selected approach: host imports `harness-core` and passes a provider adapter
  into package API.
- rationale: same core runs for all providers and consumer repositories;
  provider-neutral boundary remains narrow and testable.
- alternatives considered: retain target script loader, embed core separately
  in each provider, or pass policy semantics to adapters.
- accepted trade-offs: host/package API compatibility is an explicit release
  contract and must be tested.
- affected owners and boundaries: host owns transport/workspace/tool adapter;
  package owns lifecycle and policy interpretation.

### Decision: Legacy scripts are one-way migration shims only

- context: existing consumers may reference `scripts/harness_task.py` during
  adoption.
- selected approach: any retained script delegates directly to installed
  package CLI/API and contains no resolver, parser, validation, or lifecycle
  implementation. Package absence fails explicitly.
- rationale: temporary compatibility does not reintroduce a second executable
  core.
- alternatives considered: indefinitely maintain copied scripts or require all
  consumers to cut over atomically without bridge.
- accepted trade-offs: transitional shim remains an extra entrypoint but not an
  independent behavior owner.
- affected owners and boundaries: package remains code SSOT; consumer shim is
  generated/deprecated transport only.

### Compatibility, Migration, and Risk

- old behavior: provider host dynamically imports consumer executable core;
  starter kit copies core scripts and tests into consumers.
- new behavior: package executes core for all entrypoints; consumers carry data
  and compatible API range, not editable core implementations.
- compatibility boundary: existing core scripts may delegate only during
  migration. A consumer becomes package-only after its policy declares
  `harness_core.request_api`, package validation passes, and no independent core
  implementation remains. Missing field is an explicit protocol-policy failure,
  never an implicit default.
- migration or backfill: package preserves current public packet/run behavior;
  it records core identity on newly created packets. Existing immutable packets
  remain historical evidence and are not rewritten. Unversioned historical
  packets are unreadable for continuation; unfinished runs require a controller
  successor attempt from original request/plan data.
- rollout and rollback: install prior compatible package release centrally and
  retain consumer policy range. Rollback never copies old core source into a
  consumer.
- deprecation or consumer impact: copied scripts and tests leave starter kit
  required contents after all supported consumers use package entrypoints.
- risk:
  - package unavailable: launcher emits explicit environment block; no packet
    or workspace side effect.
  - unsupported request or host API: package emits explicit protocol block; no
    packet or workspace side effect.
  - package/host API drift: provider conformance gate blocks host admission.
  - mixed migration state: shim delegates or fails; it never runs legacy logic.
  - stale policy range: validation names required and actual values before
    dispatch.

## Invariants and Edge Cases

### Invariants

- one package owns executable packet, plan, validation, lifecycle, and run
  semantics.
- PEP 440 metadata/lockfiles own package dependency compatibility; one consumer
  policy owns required request API and repository route policy.
- one package compatibility matrix owns supported request APIs, packet-read
  APIs, current packet API, and host APIs.
- one plan manifest task owns `allowed_paths` and `planned_write_paths`.
- `planned_write_paths` is a subset of `allowed_paths`; equality is permitted
  only when author intentionally chooses narrow authorization.
- all direct CLI and provider-host entrypoints call same package behavior.
- host adapter never mutates route policy, authorization scope, mode, core
  identity, packet, or controller decision.
- core identity is immutable in packet evidence; later upgrades do not rewrite
  history.
- launcher environment failure and package protocol incompatibility fail before
  packet creation and cannot be waived into managed acceptance.

### Edge Cases

- empty planned writes: valid only with non-empty explicit allowed scope and a
  route/role that permits no writes.
- missing or malformed `harness_core.request_api`: protocol-policy failure
  before packet creation.
- absent or unloadable package: launcher-owned environment failure from direct
  CLI, Codex host, and every future provider host.
- unsupported request or host API: package-owned protocol failure from direct
  CLI, Codex host, and every future provider host.
- plan-linked request sends static fields: equal values are accepted; conflicts
  block; absent values derive from plan.
- package upgrade during an active run: continuation requires `packet_api` in
  `SUPPORTED_PACKET_READ_APIS`, matching existing `planned` state, and existing
  plan digest/base rules. An unversioned or unreadable packet blocks; controller
  creates a successor according to existing policy.
- host unavailable: launcher availability and package protocol admission run
  first. Provider runtime preflight then remains separate and blocks dispatch.
- legacy shim present with package unavailable: explicit package-unavailable
  failure; no fallback to retained local logic.
- future provider: admissible only after it imports compatible package and
  passes existing packet, workspace, tool-binding, validator, and controller
  conformance proof.

## Validation Plan

### Backend Verification Claims

- direct boundary: package API resolves equivalent direct and host-managed
  requests from a real temporary consumer root.
- important success and failure behavior: compatible package resolves packets;
  launcher environment failure, malformed request API, unsupported request API,
  unsupported host API, stale shim, and scope conflict block before packet
  creation.
- final state or side effects: packet records exact core identity; failed
  compatibility leaves no run, attempt, workspace, writer, validator, or
  product change.
- rollback, retry, duplicate, or idempotency behavior: existing planned runs
  retain immutable identity; only packet API `3` remains readable; core upgrade
  never silently resubmits or mutates prior packets.
- canonical contract and conformance proof: every provider host imports same
  package API and passes existing enforced-mode, workspace, tool, validator,
  and controller-decision conformance tests.
- real dependencies requiring proof: installed package metadata and host
  runtime environment.
- representative-operation trace mechanism: one direct CLI and one live
  provider-host run record capture core release/API identity.
- performance claim and threshold: Not applicable. No latency target changes.

### Acceptance Criterion: One core identity across entrypoints

- setup or precondition: compatible package, one temporary consumer root, and
  one conforming test host.
- action: resolve equal managed requests through package CLI and host adapter.
- expected result: packet content and core identity match; only provider
  transport evidence differs.
- failure condition: host dynamically loads consumer core or returns different
  packet authorization, mode, plan binding, or run transition.
- proof method: direct package API test and host conformance test.
- expected evidence: equal normalized packet fields and one recorded core
  identity.

### Acceptance Criterion: Early environment and protocol block

- setup or precondition: one missing package environment, one malformed request
  API policy, one unsupported request API, and one unsupported host API.
- action: run direct launcher/validation and provider preflight for each case.
- expected result: missing package returns launcher
  `harness_core_environment_unavailable`; remaining cases return their named
  package protocol failures. None creates a packet or workspace.
- failure condition: raw import error, later parser error, dynamic local-core
  fallback, inconsistent direct/host result, or writer/validator dispatch.
- proof method: parameterized launcher, package, and host tests.
- expected evidence: typed result, package/matrix identity where available, and
  absence of run artifacts.

### Acceptance Criterion: Deterministic host failure precedence

- setup or precondition: one host with unavailable provider runtime and a
  consumer policy requiring unsupported request API; then same host with a
  supported request API.
- action: invoke provider-host preflight for both requests.
- expected result: unsupported request API returns package protocol failure
  without provider connection attempt; supported request API reaches and returns
  host-preflight failure.
- failure condition: host connection error masks package incompatibility or
  direct and host protocol results diverge.
- proof method: adapter spy plus parameterized direct/package/host tests.
- expected evidence: ordered call trace and absence of run artifacts.

### Acceptance Criterion: Plan scope remains explicit

- setup or precondition: active Git-tracked plan task with non-empty allowed
  scope and either non-empty or empty planned writes.
- action: resolve plan-linked request without request-local static scope.
- expected result: packet derives explicit task scope and planned paths;
  planned path outside scope and caller conflict block.
- failure condition: core derives authorization from planned paths or accepts a
  task missing explicit scope.
- proof method: package parser/resolver tests across every work topology.
- expected evidence: normalized packet, immutable digest, and deterministic
  failure records.

### Acceptance Criterion: Consumer no longer owns executable core

- setup or precondition: migrated consumer starter kit and installed package.
- action: run package validation, inspect entrypoint, and invoke provider host.
- expected result: consumer contains only policy/data plus optional delegating
  shim; no independent packet or plan implementation executes.
- failure condition: copied resolver remains required or host imports consumer
  executable core.
- proof method: starter-kit contract test and host loader test.
- expected evidence: kit manifest, shim delegation proof, and host package
  import evidence.

## Completion Criteria

Specification is complete when:

1. package, consumer, and host ownership boundaries are explicit and non-overlapping
2. every admissible entrypoint and topology uses one core API
3. PEP 440 dependency compatibility, integer protocol matrix, consumer request
   API, host API, and packet identity contracts are explicit
4. copied-core migration, package-unavailable launcher behavior, rollback,
   mixed-version behavior, packet continuation, and legacy shim boundaries are
   defined
5. explicit plan authorization remains separate from planned writes
6. early failure behavior preserves no-side-effect managed execution semantics
7. every required outcome maps to observable package, host, and consumer proof
8. implementation sequencing remains outside this specification
