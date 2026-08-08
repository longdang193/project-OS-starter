---
artifact_type: spec
template_id: detailed-specification
status: active
layer: change
name: harness-policy-ssot-composition
targets:
  - repo_config/harness.yaml
  - packages/harness-core
  - scripts/render_harness_routing.py
  - docs/operating_system/tooling/harness-routing.generated.md
  - repo_config/starter-kit-manifest.json
  - docs/operating_system/rules/multi-agent-orchestration-rule.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
---

# Harness Policy SSOT Composition

## Goal and Problem

### Problem

- current policy repeats resolved packet fields across routes while also defining
  unused or inert policy structures.
- affected systems: static policy, `harness-core` packet resolution,
  controller-owned verification, host tool-binding evidence, generated agent
  guidance, and maintainers changing routes.
- evidence:
  - routes repeat workspace, checks, retry, budget, provider selection, and
    delegation fields in `repo_config/harness.yaml`.
  - `capabilities.sets` is validated but no route resolves a set.
  - `tools.*.fallback` is declared but is not read into resolved packets or
    executed by core.
  - all configured `context_limits` are validation-only; packet and artifact
    content are not bounded by those settings at runtime.
  - core, not worker capability, executes mandatory checks after integration.
  - `review_required` is passed into packet topology data but does not create
    a review acceptance criterion or a review lane.
- consequence of no change: route policy drifts, inactive settings imply
  protections that do not exist, and maintainers must reconcile core, YAML,
  rules, and duplicated route fields to know one execution contract.

### Goal

- desired outcome: one small policy grammar expresses route intent; core
  deterministically resolves that intent into immutable packet policy.
- observable success:
  - each security-relevant authority has one visible route owner;
  - each repeated safe default has one policy owner;
  - every configured limit, verification requirement, and tool behavior has
    one runtime enforcer;
  - equivalent route classes use equivalent profile selection, not copied
    arrays;
  - generated guidance explains procedure without redefining machine policy.

## Required Outcomes

### Outcome: Clear authority ownership

- affected actor or system: route author, controller, worker, validator, and
  host adapter.
- required result: core owns lifecycle and enforcement; static policy owns
  declared intent; trusted host configuration owns physical provider transport;
  run records own mutable execution truth.
- success condition: no endpoint, launcher command, credential, or transport
  value enters repository policy, packet, run request, plan, or generated
  guidance.

### Outcome: One-hop route composition

- affected actor or system: route policy and packet resolver.
- required result: each route selects named authority, toolset, and
  verification profiles without inheritance, deep merge, or route-class trees.
- success condition: profile edits affect all selected routes consistently;
  route-specific deviations remain directly visible.

### Outcome: Symmetric read and write behavior

- affected actor or system: read-only, write-capable, delegated, single-lane,
  sequential, and parallel executions.
- required result: equivalent route dimensions use shared semantics:
  read-only routes prove no workspace change; write routes run configured
  controller checks; all routes use same acceptance and evidence model.
- success condition: `git diff --check` is never treated as proof that a
  read-only workspace remained unchanged.

### Outcome: Enforced bounded packet context

- affected actor or system: packet resolver, host adapter, controller, and
  retained diagnostic evidence.
- required result: each configured context limit is enforced before content
  enters packet, readonly-artifact descriptors, or retained evidence.
- success condition: oversized objective, fact, summary, or artifact content
  is rejected with a typed validation failure; count and byte limits bound
  total packet material.

### Outcome: Stable compatibility boundary

- affected actor or system: historical runs, current policy, core API, and
  provider transport.
- required result: new policy affects only newly resolved packets; existing
  immutable packets and runs remain readable under supported compatibility
  profiles.
- success condition: policy simplification neither changes historical run
  evidence nor collapses request API, packet API, host API, and provider
  contract versions into one misleading version number.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
|---|---|---|---|---|
| Does route policy repeat resolved values? | Nine routes repeat runtime selection, retry policy, budget profile, checks, and workspace fields. | `repo_config/harness.yaml` | high | Resolve safe defaults once. |
| Do capability sets currently provide SSOT? | Set definitions only receive schema validation; routes hold separate arrays. | `packages/harness-core/src/harness_core/config_validation.py` | high | Replace unused sets with resolved authority profiles. |
| Does fallback change execution authority? | Core creates tool bindings from route tools; no core fallback resolver exists. | `packages/harness-core/src/harness_core/managed.py` | high | Remove fallback declarations. Do not add silent fallback. |
| Who runs mandatory checks? | Executor invokes host `run_checks` after final-state integration. | `packages/harness-core/src/harness_core/managed.py` | high | Keep checks controller-owned; remove stale worker check capability. |
| Is acceptance bypassable by state graph alone? | Controller rejects `accept` unless every criterion is proven. | `packages/harness-core/src/harness_core/managed.py` | high | Preserve acceptance guard as core invariant. |
| Is writer delegation multiplicative per lane? | Active delegated children are counted from attempt-level child state. | `packages/harness-core/src/harness_core/managed.py` | high | Preserve run-wide child budget; document its scope. |
| Are context limits runtime enforced? | Settings are schema-validated but have no runtime consumer. | `repo_config/harness.yaml`; `packages/harness-core/src/harness_core/config_validation.py` | high | Add runtime enforcement before claiming bounded packets. |
| Does provider identity equal transport configuration? | Compatibility profiles map request, packet, host, and provider versions independently. | `packages/harness-core/src/harness_core/compatibility.py` | high | Keep independent versions and host-owned transport. |

### Relationship to Active Specifications

- this specification owns harness policy grammar, route/profile resolution,
  controller-verification ownership, and policy-derived output boundaries.
- `2026-08-05-uniform-harness-execution-orchestrator.md` remains authoritative
  for managed lifecycle, immutable attempt packets, run records, controller
  decisions, and review-versus-approval evidence semantics.
- `2026-08-07-harness-invocation-delegation-protocol.md` remains authoritative
  for invocation context projection, context digest, reference/base identity,
  child outcome projection, and run-wide delegation reservation semantics.
  This specification supersedes only that document's reusable capability-set
  requirement and worker `checks.run` grant: authorities replace capability
  sets, and controller-owned verification replaces worker check authority.
- `2026-08-08-codex-provider-transport-ssot.md` remains authoritative for
  provider session and trusted host-transport configuration. This specification
  preserves its provider identity and packet/host compatibility boundaries.

### Prototype and Validation Evidence

- prototype reference: Not applicable. Existing packet resolution and unit
  tests provide sufficient contract evidence; no interface prototype is needed.
- validated scenarios and states: policy parsing, packet construction,
  controller check execution, acceptance gating, terminal evidence retention,
  friction follow-up selection, and compatibility mapping.
- findings incorporated into approved behavior: fallback is removed rather than
  expanded; `max_parallel_writers` remains writer-specific; diagnosis keeps
  `skill-improve-harness` because that skill already separates diagnosis from
  remediation.
- rejected alternatives: generic profile inheritance, implicit write or
  delegation authority, per-route physical transport configuration, and a new
  diagnosis skill duplicating existing procedure.

### Scope

- included behavior:
  - policy grammar, deterministic profile resolution, runtime enforcement,
    policy validation, and canonical operational guidance;
  - authority, toolset, verification, topology, delegation, approval, and
    context-boundary semantics;
  - compatibility preservation for existing packet and run records.
- affected boundaries: `repo_config/harness.yaml`, `harness-core`, host packet
  binding contract, canonical rules, and generated agent surfaces.
- admissible cases: all existing route types, supported execution topologies,
  supported provider compatibility profiles, and read-only diagnostic follow-up.
- compatibility expectation: accepted new policy must resolve to behaviorally
  equivalent packets except for intentional fixes specified here.

### Non-Goals

- add another runtime provider, tool launcher, MCP server, queue, scheduler,
  dynamic route inheritance, or broad agent abstraction.
- change product task behavior, host transport selection, credentials, endpoint
  storage, managed-run lifecycle ownership, or supported historical packet APIs.
- make parallel read-only work artificially share a writer limit; a distinct
  global lane limit needs a separate measured host-capacity requirement.
- create a second diagnostics skill or move remediation authority into
  `harness_diagnosis`.

### Requirements and Behavioral Contract

#### Requirement: Policy grammar

- trigger or actor: maintainer declares or changes a route.
- preconditions: canonical policy validates and a requested route exists.
- required behavior: policy version `4` supports exactly one level of route
  composition. The policy accepts only these resolution inputs:

  ```yaml
  version: 4
  harness_core:
    request_api: 4

  defaults:
    source_workspace: current_repo
    runtime_provider: codex_app_server
    retry_policy: bounded
    execution_budget_profile: default
    approval_gates: []

  runtime_providers:
    codex_app_server:
      contract_version: 4

  authorities:
    read_only:
      capabilities: [repo.read, code.search, docs.query]
      workspace_write_access: read_only
    workspace_write:
      capabilities: [repo.read, repo.write, code.search]
      workspace_write_access: workspace_write

  toolsets:
    code: [...]
    research: [...]

  verification_profiles:
    read_only:
      postconditions: [workspace_unchanged]
      checks: []
    write:
      postconditions: []
      checks: [diff]

  routes:
    <name>:
      template: low | normal | high
      role: <role>
      rules: [...]
      skills: [...]
      authority: <authority-profile>
      toolset: <toolset-profile>
      verification_profile: <verification-profile>
      delegation_profile: disabled | read_only_research
      approval_gates: [...] # optional; defaults to []
      execution_modes: [...]
  ```

- route resolution has fixed precedence: route-local required fields and
  selected profile names first; selected authority, toolset, and verification
  profile second; safe defaults last. Defaults may fill only source workspace,
  provider selection, retry policy, budget profile, and empty approval gates.
- verification profile `checks` names top-level `checks` commands. Its
  `postconditions` names core-built-in proof only; version `4` supports
  `workspace_unchanged` and it compares final change set with packet base.
- a selected tool retains access declared by its tool binding. Effective access
  is read-only for validator or read-only packet lanes; otherwise it is the
  selected tool's writer access. Authority cannot widen a tool binding.
- output or state change: core resolves profile values and defaults into a
  complete immutable packet. Resolved packet records selected profile names and
  self-contained values.
- failure behavior: a policy version other than `4`, unknown profile, missing
  required route selection, invalid profile shape, forbidden authority/tool
  combination, or unresolvable policy produces a typed validation failure before
  packet creation.
- observable acceptance: no route directly repeats capability arrays, tool
  arrays, or controller-verification commands that its selected profile owns.

#### Requirement: Explicit security authority

- trigger or actor: packet resolution for every route.
- preconditions: route declares a valid authority and delegation setting.
- required behavior:
  - route authority is explicit and resolves all worker capabilities plus
    workspace access;
  - every route explicitly declares delegation as `disabled` or a named
    bounded profile;
  - nonempty approval gates are route-local and remain visible;
  - defaults may never grant `repo.write`, delegation, an approval bypass,
    external side effect, or verification bypass.
- output or state change: packet exposes resolved capabilities,
  `workspace_write_access`, delegation budget, and approval gates.
- failure behavior: escalation beyond selected authority rejects before host
  dispatch.
- observable acceptance: adding a new route requires a visible authority and
  delegation decision; no role name implicitly grants write access.

#### Requirement: Controller-owned verification

- trigger or actor: managed lane execution reaches final-state verification.
- preconditions: route selected a verification profile.
- required behavior:
  - core or enforced host runs verification checks, records observations, and
    evaluates acceptance criteria;
  - worker authority does not include `checks.run` solely because a route has
    mandatory checks;
  - write verification runs configured check commands;
  - read-only verification proves empty change set against the packet base and
    fails when any workspace change exists.
- output or state change: one check-node observation and one evidence-backed
  verification outcome enter attempt state.
- failure behavior: absent, malformed, failed, or conflicting check evidence
  blocks verification and cannot produce `accepted`.
- observable acceptance: all verified packets use same controller evidence
  shape; read-only mutation fails even when changed content has no whitespace
  error.

#### Requirement: Tool binding and fallback

- trigger or actor: route packet resolution and host tool-binding verification.
- preconditions: a route selected a toolset.
- required behavior:
  - policy names logical tools and stable non-secret `host_kind` binding
    identities;
  - packet carries only selected tools and their verified binding requirements;
  - host verifies binding identity, access class, probe, workspace, and runtime
    provider before lane dispatch;
  - `tools.*.fallback` is unsupported and removed from policy.
- output or state change: host records binding evidence for exactly route-granted
  tools.
- failure behavior: unavailable or mismatched binding blocks dispatch; no
  fallback silently grants an unselected tool.
- observable acceptance: failed Semble availability cannot cause a Serena
  invocation unless route toolset explicitly includes Serena.

#### Requirement: Topology and review symmetry

- trigger or actor: route selects single, sequential, or parallel topology.
- preconditions: requested topology is allowed by route and host advertises
  enforced support.
- required behavior:
  - topology owns scheduling only;
  - single and sequential topology derive writer concurrency of one;
  - parallel topology owns explicit `max_parallel_writers` because core applies
    that limit only to write-capable lanes;
  - validator role is one core lifecycle invariant unless a future supported
    semantic distinction requires a documented override;
  - review is an explicit acceptance criterion and evidence path, not a
    topology boolean.
- output or state change: packet lane DAG always contains independent validator
  behavior; review evidence only affects criteria that request review.
- failure behavior: missing review evidence yields `review_required`; it cannot
  be accepted. Retry remains a successor-attempt decision when policy allows it.
- observable acceptance: topology alone cannot add or omit review requirement;
  read-only lanes do not consume writer slots.

#### Requirement: Bounded packet and evidence context

- trigger or actor: request admission, packet resolution, retained-evidence
  normalization, and readonly-artifact materialization.
- preconditions: policy declares positive context limits.
- required behavior:
  - `objective_max_bytes` bounds managed `user_request` UTF-8 bytes;
  - invocation context retains its existing fact/reference schema:
    `fact_max_bytes` bounds total serialized fact bytes, `max_facts` bounds
    fact count, and context digest plus artifact/base identity remain mandatory;
  - `outcome_summary_max_bytes` bounds invocation-local child outcome summary;
  - `max_artifacts` bounds artifact count;
  - policy adds one explicit per-artifact byte limit; `max_artifacts` plus this
    limit bound aggregate artifact payload;
  - retained command traces retain existing per-command sanitization limits and
    must also satisfy the artifact byte limit;
  - readonly artifact descriptors retain content only when within policy bounds
    and preserve digest and byte-length evidence.
- output or state change: accepted packet and retained evidence stay within
  configured bounds and retain required context digest/reference identity.
- failure behavior: content that exceeds its count or byte boundary is rejected
  before dispatch or before persisted evidence is accepted.
- observable acceptance: a valid packet cannot contain a reference or embedded
  artifact payload exceeding configured bounds.

## Design Decisions

### Decision: Core resolves route intent once

- context: routes currently copy resolved fields while core directly reads
  per-route arrays and values.
- selected approach: introduce one deterministic resolver from route intent,
  safe defaults, and one-hop named profiles to complete packet policy.
- rationale: core already creates immutable complete packets; resolution belongs
  beside packet construction rather than in routes, rules, or hosts.
- alternatives considered:
  - retain copied route fields: rejected because drift already exists;
  - generic inheritance and deep merges: rejected because provenance and
    security review become harder;
  - remove all profiles: rejected because equivalent route classes would again
    duplicate their shared contract.
- accepted trade-offs: profile resolution needs validation and focused tests;
  route policy gains a small fixed vocabulary.
- affected owners and boundaries: core owns resolver; YAML owns inputs; packet
  owns resolved output.

### Decision: Authority profiles replace capability sets

- context: generic capability sets are inactive and do not express workspace
  access or verification relationship.
- selected approach: replace them with named `authorities` that resolve worker
  capabilities and workspace access. Routes select authority explicitly.
- rationale: authority is policy, not a loose array. Named profiles preserve
  symmetric read-only and write behavior while keeping a route's decision
  visible.
- alternatives considered:
  - keep unused sets: rejected;
  - put raw capabilities on every route: rejected for drift risk;
  - infer authority from role: rejected because role must not imply write
    permission.
- accepted trade-offs: capability detail moves one hop from route, mitigated by
  an explicit authority name and self-contained resolved packet.
- affected owners and boundaries: YAML authority profile and core resolver.

### Decision: Keep physical binding proof, move transport out of policy

- context: route-selected tools need host verification, while endpoint and
  launcher details must never enter repository policy.
- selected approach: retain `host_kind` as stable logical binding-contract name
  in tool policy and keep physical launch and connection configuration
  host-owned.
- rationale: packet/host binding equality is a security and reproducibility
  check; endpoint-like configuration is not.
- alternatives considered:
  - remove binding identity entirely: rejected because host evidence loses an
    exact expected binding;
  - rename `host_kind`: rejected because packet API 5 and host API 4 consume
    the current field name; a rename needs a synchronized protocol release.
- accepted trade-offs: host and core must share documented binding identifiers;
  field-name clarity is deferred until a justified protocol version change.
- affected owners and boundaries: policy declares binding contract; trusted host
  resolves physical implementation; provider transport specification remains
  authoritative for session behavior.

### Decision: Core owns invariant lifecycle policy

- context: state graph, check ownership, validator role, and accepted-result
  guard are universal lifecycle semantics, not route choices.
- selected approach: core owns these invariants; static policy exposes only
  route-selectable behavior. Remove static state transition configuration and
  duplicated universal topology fields.
- rationale: universal semantics become safer when one code path enforces them.
- alternatives considered:
  - configurable transition graph: rejected because it permits policy drift and
    offers no current route-specific behavior;
  - duplicate lifecycle text in rules: rejected because prose cannot enforce
    packet behavior.
- accepted trade-offs: future lifecycle changes require core release rather
  than a YAML-only edit.
- affected owners and boundaries: core, canonical lifecycle rule, packet, and
  run record.

### Decision: No silent fallback; bounded failures become evidence

- context: optional tool fallback is neither enforced nor visible in packet
  authority.
- selected approach: remove fallback declarations. Unavailable selected tools
  surface typed preflight or binding failure; controller selects a successor
  route or explicitly grants another toolset only through new packet policy.
- rationale: exact route tool authority is more valuable than invisible
  convenience behavior.
- alternatives considered:
  - intersected automatic fallback: rejected now because it adds resolution
    logic without a verified need;
  - host-selected fallback: rejected because it bypasses route authority.
- accepted trade-offs: controller may need explicit reclassification after
  optional-tool failure.
- affected owners and boundaries: core binding verification, controller, and
  policy route selection.

### Decision: Policy-derived surfaces remain generated

- context: `harness.yaml` is rendered into routing guidance and included in
  generated starter-kit output.
- selected approach: canonical policy, renderer, template, and starter-kit
  manifest remain source inputs; routing guidance and starter-kit output remain
  derived surfaces.
- rationale: one policy edit must not require manual copy updates in shipped or
  generated files.
- alternatives considered:
  - edit generated routing or starter-kit output directly: rejected because it
    creates competing policy ownership;
  - exclude starter-kit output from policy migration: rejected because shipped
    consumers would drift from canonical policy.
- accepted trade-offs: policy changes require rendering, starter-kit build, and
  drift proof during validation.
- affected owners and boundaries: policy renderer, starter-kit manifest,
  generated routing guidance, and disposable starter-kit output.

### Compatibility, Migration, and Risk

- old behavior: routes encode many resolved values, sets and fallback are
  inactive, context limits are unenforced, and topology exposes unused or
  universal fields.
- new behavior: routes encode intent; one resolver emits complete immutable
  packet policy; runtime enforces every declared verification and context
  boundary.
- compatibility boundary: policy version `4` changes atomically with core
  resolver and validator. Existing run records and supported packet API readers
  remain unchanged; packet and host field names remain unchanged.
- migration or backfill: no data backfill. New policy affects new attempts;
  existing packet snapshots preserve historical truth.
- rollout and rollback: release policy version `4`, parser, resolver, renderer,
  starter-kit manifest integration, and validation as one compatible change.
  Revert restores version `3` policy and parser together before creating new
  policy-format packets; never rewrite historical runs.
- deprecation or consumer impact: remove unsupported `fallback`, generic
  capability sets, route-level `checks.run`, static state graph, and unused
  topology review flag. Regenerate routing guidance and starter-kit output from
  canonical source; never hand-edit derived files.
- risk:
  - policy migration may accidentally widen authority.
    - mitigation: reject defaults that grant security-sensitive authority;
      snapshot and test resolved packet contents for every existing route.
  - profile indirection may obscure route behavior.
    - mitigation: one-hop references only, explicit route authority and
      delegation, complete packet output, and validation errors with profile
      provenance.
  - context bounds may reject formerly accepted oversized evidence.
    - mitigation: enforce declared limits with typed failures; do not silently
      truncate evidence that is required for correctness.

## Invariants and Edge Cases

### Invariants

- Core is sole owner of lifecycle transition enforcement; `accepted` requires
  all configured criteria proven.
- Packet is complete, immutable, and sufficient to verify route authority,
  tool binding, checks, budget, context limits, and approval gates.
- Static policy contains no provider endpoint, launch command, secret, or
  credential. Controller verification commands remain policy-owned checks.
- Route defaults never provide write, delegation, approval bypass, external
  side effect, or verification bypass.
- Every route has exactly one explicit authority, toolset, verification profile,
  and delegation profile.
- Fallback never expands route tool authority because fallback is unsupported.
- Read-only execution must prove zero changes; write execution must prove its
  configured controller-owned verification checks.
- Parallel writable lanes have disjoint paths and isolated workspaces.
- Delegated children remain read-only, within parent authority and paths, and
  within run-wide depth, count, concurrency, and timeout budgets.
- Rules and skills describe procedure only; they do not become a second owner
  of machine limits or state transitions.

### Edge Cases

- empty or minimal input: a route with no requested change still resolves a
  complete packet and runs its selected read-only or write verification policy.
- normal and large input: declared byte and count limits reject oversize packet
  context or artifacts before host dispatch.
- duplicate, missing, malformed, or unsupported data: duplicate profile names,
  unknown selections, duplicated artifacts, malformed bindings, and unsupported
  policy keys fail validation before packet creation.
- retry, cancellation, timeout, partial failure, or concurrency: retries create
  successor attempts; terminal evidence remains immutable; writer completion
  failure remains blocked and can enter friction follow-up only after configured
  distinct-run threshold; reader work does not consume writer slots.
- migration or mixed-version state: current core reads supported historical
  packets; legacy policies are not mixed with new format within one resolved
  attempt.
- generated-source consistency: generated `AGENTS.md` surfaces derive from
  canonical templates and are never hand-edited; routing guidance and starter
  kit derive from canonical policy and are never hand-edited.
- security boundary: host may satisfy only packet-declared logical bindings;
  host transport configuration remains trusted-user configuration outside repo.

## Validation Plan

### Backend Verification Claims

- direct boundary: parse each valid and invalid policy shape, resolve packets,
  and verify packet fields, profile provenance, authority, and defaults.
- important success and failure behavior: prove every current route resolves
  intended capability, tool, delegation, topology, check, approval, and
  provider behavior; prove unknown or forbidden profiles fail before packet
  creation.
- final state or side effects: prove run records contain resolved immutable
  packet and controller-owned check or no-change evidence; rejected input
  creates no packet or run mutation.
- rollback, retry, duplicate, or idempotency behavior: prove successor attempts
  preserve supported historical packet readability, approval semantics, timeout
  escalation, and run-wide delegation budget.
- canonical contract and conformance proof: validate canonical policy,
  templates, generated agent sync, routing render, starter-kit build,
  provider compatibility matrix, and all policy-to-packet contract tests.
- real dependencies requiring proof: host adapter test double or supported host
  integration must prove binding identity, readonly workspace access, and
  controller check evidence. No external service dependency is added.
- representative-operation trace mechanism: run record assertion traces one
  read-only route, one write route, one parallel write route, and one friction
  diagnosis candidate from request through final evidence.
- performance claim and threshold: Not applicable. No performance target is
  claimed; packet-resolution overhead must remain bounded by existing request
  limits.

### Acceptance Criterion: Route intent resolves once

- setup or precondition: canonical policy declares defaults, profiles, and each
  current route.
- action: resolve every supported route and topology into packets.
- expected result: each packet is complete and route behavior matches approved
  intent without copied safe defaults or raw capability/tool arrays.
- failure condition: any unresolved value, invalid one-hop reference, or profile
  merge changes route authority.
- proof method: policy-to-packet table-driven tests plus canonical validator.
- expected evidence: per-route resolved-packet snapshots and validation output.

### Acceptance Criterion: Authority and verification remain symmetric

- setup or precondition: one read-only and one write-capable route use their
  designated profiles.
- action: dispatch controlled mutations and non-mutations through enforced host
  adapter behavior.
- expected result: read-only mutation fails on workspace-change proof; write
  route executes controller checks; neither path relies on worker `checks.run`.
- failure condition: whitespace-clean read-only mutation passes, worker
  capability controls mandatory check execution, or defaults grant write.
- proof method: direct managed execution tests with change collector and host
  binding evidence.
- expected evidence: check-node observations, empty-change assertion, and
  rejected-run outcomes.

### Acceptance Criterion: No hidden tool fallback

- setup or precondition: a route selects a toolset without Serena.
- action: selected optional tool becomes unavailable during binding verification.
- expected result: dispatch fails with typed binding or availability evidence;
  no unselected tool runs.
- failure condition: adapter invokes a tool absent from packet tool bindings.
- proof method: adapter call recording and packet binding assertions.
- expected evidence: failed outcome, binding evidence, and no unexpected tool
  invocation.

### Acceptance Criterion: Context limits are real limits

- setup or precondition: valid policy declares all positive context limits.
- action: submit boundary-sized and oversized objectives, facts, summaries, and
  artifacts.
- expected result: boundary-sized values resolve; oversized values reject before
  dispatch or evidence persistence.
- failure condition: oversized embedded content appears in packet or readonly
  artifact descriptor.
- proof method: direct resolver and retained-evidence tests with byte-accurate
  assertions.
- expected evidence: typed validation errors and bounded packet/evidence data.

### Acceptance Criterion: Historical evidence remains readable

- setup or precondition: supported historical packet and run fixtures exist.
- action: load them after policy grammar migration and resolve a new attempt.
- expected result: historical records remain readable; new packet uses new
  grammar and immutable resolved values.
- failure condition: parser migration rewrites history or breaks supported
  compatibility profiles.
- proof method: compatibility matrix tests and run-record read tests.
- expected evidence: matrix results, packet-version assertions, and unchanged
  historical fixture data.

### Acceptance Criterion: Derived policy surfaces remain synchronized

- setup or precondition: canonical version `4` policy, routing renderer, and
  starter-kit manifest exist.
- action: render routing guidance and build starter-kit output from canonical
  sources.
- expected result: generated routing and starter-kit `harness.yaml` represent
  canonical policy without manual edits or stale removed fields.
- failure condition: generated output differs from canonical source mapping or
  retains deleted policy fields.
- proof method: renderer, starter-kit generation, and generated-output drift
  validation.
- expected evidence: generated artifacts, clean drift result, and starter-kit
  policy validation.

## Completion Criteria

Specification is complete when:

1. problem, evidence, goal, scope, and non-goals are explicit;
2. route composition, ownership boundaries, authority rules, and verification
   semantics are unambiguous;
3. lifecycle, fallback, context-bound, delegation, compatibility, and
   generated-source decisions have one named owner;
4. invariants and applicable edge cases are explicit;
5. every required outcome maps to direct backend acceptance and proof intent;
6. no unresolved behavior remains hidden as implementation detail;
7. implementation sequencing remains reserved for a separate plan.
