---
artifact_type: spec
status: active
layer: change
template_id: detailed-specification
---

# Required Skill Sets, Allowed Facets, And Operating Profiles

## Goal and Problem

### Problem

- current behavior: each route owns one static expanded `skills` list.
- affected systems: controller request resolution, immutable packets, route policy,
  generated routing guidance, managed agents, timeout escalation, and provider
  runtime binding.
- evidence: a route can require a skill in plan or request text while its resolved
  packet omits that skill; core copies only route `skills` into the packet.
- consequence of no change: maintainers either over-apply specialist skills to every
  route or repeatedly patch route policy and approval requests for similar work;
  timeout escalation can rebuild a packet without required provider binding.

### Goal

- desired outcome: policy defines reusable minimum skill sets and bounded optional
  facets plus tested operating profiles; controller selects only permitted facets
  and profiles before packet creation.
- observable success: equivalent requests resolve the same immutable skills from
  one policy source, while backend-specific work adds backend proof without making
  it mandatory for unrelated local changes, and timeout escalation moves through
  a policy-approved envelope without losing runtime binding.

## Required Outcomes

### Outcome: Policy-Owned Skill Composition

- affected actor or system: repository policy and core resolver.
- required result: a route declares ordered required skill-set IDs and allowed
  optional skill-set IDs instead of copying expanded skills into each route.
- success condition: changing a set changes every consuming route through one
  policy definition.

### Outcome: Bounded Controller Selection

- affected actor or system: controller request admission.
- required result: controller may select allowed skill-set IDs with a recorded
  reason before packet creation.
- success condition: unknown, duplicate, or route-disallowed selections fail
  admission before packet, workspace, or run state exists.

### Outcome: Immutable Agent Contract

- affected actor or system: packet, host, and agent lane.
- required result: core stores required IDs, selected IDs and reasons, resolved
  IDs, and ordered resolved skills in immutable packet state.
- success condition: agents receive only resolved skills and cannot add, remove,
  or replace facet selections.

### Outcome: Bounded Operating Autonomy

- affected actor or system: controller escalation and packet resolver.
- required result: route selects a default operating profile and permits only
  named profile transitions defined by policy.
- success condition: controller can select an approved profile without raw
  authority, tool, runtime, model, budget, or check overrides.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
|---|---|---|---|---|
| Who selects skills now? | Route packet copies `route["skills"]`. | `packages/harness-core/src/harness_core/managed.py` | high | Request prose cannot grant a missing skill. |
| Where does route policy live? | Routes define direct `skills`, `rules`, authority, toolset, and verification profile. | `repo_config/harness.yaml` | high | Composition must be policy-owned. |
| What validates route shape? | Route field allow-list rejects unknown configuration keys. | `packages/harness-core/src/harness_core/config_validation.py` | high | New policy fields require explicit schema validation. |
| What fixes host/core packet drift? | Core owns normalized packet content; host consumes resolved packet fields. | `docs/operating_system/procedures/managed-execution-adapter-contract.md` | high | Facet metadata must remain core-owned and host-optional. |

### Prototype and Validation Evidence

- prototype reference: Not applicable. Existing policy and resolver establish the
  behavior to replace.
- validated scenarios and states: static route selection cannot include skills
  named only in request text; host compatibility requires core-owned packet
  normalization.
- findings incorporated into approved behavior: controller selection remains
  bounded by route policy and resolves before immutable packet creation.
- rejected alternatives: arbitrary request skill names; duplicate specialist
  skills in every route; host-side skill selection.

### Scope

- included behavior: skill-set catalog, required and allowed route composition,
  controller selection, packet provenance, validation, generated routing output,
  operating-profile catalog, timeout transitions, and compatibility tests.
- affected boundaries: `repo_config/harness.yaml`, plan-linked managed requests,
  packet API 5 resolver, controller evidence, and agent prompt inputs.
- admissible cases: routes with only required sets; routes with selected allowed
  sets; legacy routes retaining direct skills during migration.
- compatibility expectation: an unmodified legacy route resolves exactly its
  current skills. Selected skill sets never widen route authority, paths, runtime,
  sandbox, model identity, or execution budget. Operating-profile selection stays
  within explicit route ceilings and transition edges.

### Non-Goals

- arbitrary agent or caller-provided skill names.
- runtime provider, model, authority, path, sandbox, budget, or approval-gate
  selection through skill facets.
- independent controller selection of tools, rules, checks, or verification
  profiles outside a named operating profile.
- cross-provider operating-profile selection in this release. Every allowed
  profile on one route resolves the route default runtime provider.
- automatic semantic inference that silently selects a specialist skill set.
- changing historical packets, terminal runs, or legacy route behavior.

### Requirements and Behavioral Contract

#### Requirement: Skill-Set Catalog

- trigger or actor: policy author defines reusable skill composition.
- preconditions: every referenced skill exists in repository skill catalog.
- required behavior: policy owns `skill_sets`, keyed by unique non-empty IDs.
  Each set has ordered unique `skills` and a non-empty controller-facing
  `selection_guidance` string.
- output or state change: no runtime state changes until route resolution uses a
  set.
- failure behavior: empty IDs, empty sets, duplicate skills, unknown skills, or
  invalid guidance fail policy validation.
- observable acceptance: catalog validation identifies set and invalid member.

#### Requirement: Required And Allowed Route Sets

- trigger or actor: policy author configures a route for composition.
- preconditions: route references existing catalog IDs.
- required behavior: a composed route declares ordered unique
  `required_skill_sets` and ordered unique `allowed_skill_sets`. The lists are
  disjoint. Required sets always resolve; allowed sets resolve only when selected.
- output or state change: route packet has ordered resolved skills derived from
  required sets followed by selected allowed sets, with stable first-occurrence
  de-duplication.
- failure behavior: an unresolved, duplicate, or overlapping set ID fails policy
  validation.
- observable acceptance: required-only route packet excludes optional specialist
  skills; selecting allowed backend set adds its skills once.

#### Requirement: Controller Selection

- trigger or actor: controller prepares a managed request.
- preconditions: task route supports allowed skill sets.
- required behavior: request may include `skill_set_selections`, an ordered list
  of `{id, reason}` objects. `id` must be in route `allowed_skill_sets`; `reason`
  must be non-empty and records why the facet applies. Omission means no optional
  set is selected.
- output or state change: core resolves selection before packet creation and
  persists normalized selection in packet and run request evidence.
- failure behavior: non-list input, malformed object, duplicate ID, unknown ID,
  disallowed ID, or blank reason returns deterministic admission error before
  workspace preparation or lane dispatch.
- observable acceptance: a controller can add permitted backend proof without
  editing policy, but cannot add any unregistered skill.

#### Requirement: Plan-Linked Requests

- trigger or actor: controller submits an approved plan-linked task.
- preconditions: plan coordination resolves task mode, base, and paths.
- required behavior: skill-set selection remains request-level controller choice
  within route allowance. Plan files may describe why a specialist facet applies
  but do not copy expanded skills or grant a facet outside policy.
- output or state change: packet contains both plan digest and resolved selection
  provenance as immutable packet content. No new general packet digest is added.
- failure behavior: a selection never changes plan-owned mode, base, paths, or
  task identity.
- observable acceptance: selecting an allowed facet for a plan-linked request
  creates no new plan identity when no packet exists and no plan-owned fact changes.

#### Requirement: Packet And Host Boundary

- trigger or actor: core resolves a valid request.
- preconditions: policy and request selection pass validation.
- required behavior: packet contains `skill_sets` metadata with `required`,
  `selected`, and `resolved` IDs, plus existing `skills` as resolved ordered skill
  names. Host projects the exact ordered `skills` list into lane task context and
  instructs the agent to follow those named repository skills. Host and agent
  treat `skill_sets` only as audit metadata.
- output or state change: immutable packet records exact selection provenance.
- failure behavior: host must not infer, add, or mutate skills from user request
  text, policy, or facet metadata; host passes only packet-resolved names.
- observable acceptance: packet replay yields identical resolved skills and host
  task context for same policy, request selection, and packet base.

#### Requirement: Operating-Profile Catalog And Route Range

- trigger or actor: policy author defines reusable execution envelopes.
- preconditions: every referenced authority, toolset, verification profile,
  runtime provider, agent template, and execution-budget profile exists.
- required behavior: policy owns `operating_profiles`, keyed by unique non-empty
  IDs. A profile resolves exactly one authority, toolset, verification profile,
  runtime provider, agent template, and execution-budget profile. Optional
  `extends` names one parent; child-declared fields override parent fields, and
  resolved fields must be complete without cycles. One pure policy resolver owns
  this inheritance for configuration validation and packet resolution. Each
  composed route declares one `default_operating_profile`, ordered unique
  `allowed_operating_profiles`, and optional ordered `escalation_transitions`
  records shaped `{from, on, to}`. `from` and `to` must be route-allowed profile
  IDs; v1 permits only `on: dispatch_timeout`; each `{from, on}` pair is unique;
  default profile is allowed. Every allowed profile resolves policy default runtime
  provider, so current host preflight remains single-provider.
- controller selection: request may include one
  `operating_profile_selection: {id, reason}` object. `id` must be route-allowed
  and `reason` must be non-empty. Omission selects route default. For timeout
  escalation core selects destination from active profile plus matching route
  edge; `decision.successor` cannot select a profile or provider.
- output or state change: core resolves one complete profile before packet
  creation and stores default ID, selected ID and reason, resolved ID, resolved
  values, and transition reason in immutable packet state. No new policy digest
  is added; immutable packet content and existing plan digest retain provenance.
- failure behavior: unknown profile, inheritance cycle, incomplete profile,
  route-disallowed profile, malformed selection, raw field override, mismatched
  `runtime_provider_id`, cross-provider route profile, or transition not allowed
  for the outcome fails admission before workspace preparation or run state change.
- observable acceptance: a selected extended profile changes only its declared
  fields while inherited fields remain equal to its base profile.

#### Requirement: Successor Runtime-Binding Inheritance

- trigger or actor: controller escalates a `dispatch_timeout` through an allowed
  same-provider operating-profile transition.
- preconditions: previous immutable packet has a valid provider runtime binding
  and successor resolves the same runtime provider.
- required behavior: core, not controller request input, copies prior packet
  binding into successor packet resolution. Host still re-reads trusted runtime
  configuration before each lane and compares it with immutable binding.
- output or state change: successor creates a new immutable packet with selected
  profile and inherited binding.
- failure behavior: missing prior binding, invalid inherited binding, or changed
  host configuration blocks before product work. Cross-provider route transitions
  fail policy validation in v1; no automatic runtime fallback exists.
- observable acceptance: default-to-extended same-provider timeout escalation
  reaches `planned`; provider configuration drift returns
  `provider_configuration_changed` before lane dispatch.

### Constraints and Alternatives

- constraint: current route policy has direct static skills and strict schema
  validation.
- alternative: add all specialist skills to `local_change`.
  - benefit: smallest configuration diff.
  - trade-off: specialist work applies to unrelated local changes.
  - reason rejected: fails minimal-selection goal.
- alternative: allow raw request skill names.
  - benefit: maximum controller flexibility.
  - trade-off: creates authority ambiguity, typo surface, and non-reproducible
    policy bypass.
  - reason rejected: violates immutable packet and SSOT boundaries.

## Design Decisions

### Decision: Skill-Only Facets First

- context: skills share additive ordered-list semantics; tools, capabilities, and
  verification profiles have different authority and execution effects.
- selected approach: first release introduces only required and allowed skill
  sets. `skills` is resolved uniformly for every composed route.
- rationale: fixes current mismatch without adding a generic merger for fields
  with incompatible safety semantics.
- alternatives considered: one universal facet object for skills, rules, tools,
  checks, and profiles now.
- accepted trade-offs: future rule/check/tool composition needs a separate
  approved extension, but avoids privilege expansion hidden behind a generic
  abstraction.
- affected owners and boundaries: core owns resolution and validation; policy
  owns catalogs and permissions; controller owns bounded selection; host projects
  only packet-resolved skill names into lane context.

### Decision: Profile-Bounded Operating Envelopes

- context: raw independent authority, tool, runtime, model, budget, and check
  selection creates unsafe combinations and controller micromanagement.
- selected approach: controller selects one route-allowed complete operating
  profile. Route policy owns profile ceilings and directed escalation edges. All
  allowed profiles on one v1 route use its default runtime provider.
- rationale: tested envelopes preserve compatible combinations while allowing
  bounded autonomy such as default-to-extended timeout escalation.
- alternatives considered: independently selectable ranges per field; caller
  supplied provider binding; controller-selected arbitrary tool profiles.
- accepted trade-offs: new profile is required for a new valid combination, but
  no caller can assemble an untested cross-product. Cross-provider profiles need
  later pre-packet host-routing design.
- affected owners and boundaries: policy owns profiles and ceilings; core owns
  resolution and successor binding inheritance; host owns trusted preflight and
  configuration-drift proof.

### Decision: Future Symmetry Through One Selection Protocol

- context: skills are additive guidance while operating controls require complete
  compatible envelopes.
- selected approach: skill facets use required/allowed/selected/resolved list
  composition; operating profiles use default/allowed/selected/resolved envelope
  composition. Skill selections are ordered `{id, reason}` records; operating
  selection is one `{id, reason}` record; timeout edges are `{from, on, to}`.
  Both record selection provenance before packet creation.
- rationale: preserves one bounded-controller protocol without treating tools and
  authority as additive lists.
- alternatives considered: one universal merger for every packet field.
- accepted trade-offs: rules/checks/tool changes occur only through a new profile
  in first release; independent facets for those domains require a later spec.
- affected owners and boundaries: a new independently composable domain requires
  its own validation, authority, and compatibility proof.

### Decision: One Profile Resolver, No Extra Digests

- context: inheritance must resolve identically during validation and packet
  creation, while immutable packets already preserve resolved values.
- selected approach: one pure policy resolver serves validation and managed packet
  resolution. Packet selection and profile provenance remain normal immutable
  packet fields; existing plan digest retains plan identity.
- rationale: removes validation/runtime drift and avoids unmanaged `packet_digest`
  or `policy_digest` fields with no verifier.
- affected owners and boundaries: core owns shared resolution; host receives only
  resolved packet fields and does not validate policy or digest policy itself.

### Compatibility, Migration, and Risk

- old behavior: all routes use direct static `skills`; no controller-selected
  specialist sets exist.
- new behavior: legacy routes retain direct `skills` and static route profiles;
  composed routes use catalog IDs and optional bounded selections. Migrated routes
  use named operating profiles.
- compatibility boundary: no request, packet, host, or provider API version bump.
  Existing routes and packets remain valid. New `skill_sets` and operating-profile
  metadata is additive; existing `skills` becomes explicit host task context.
- migration or backfill: migrate `local_change` to a required base set, allowed
  backend-proof set, standard operating profile, and extended timeout profile only
  after resolver and policy validation ship.
- rollout and rollback: enable composition per route; reverting a route to direct
  skills removes optional selection without changing historical packets.
- deprecation or consumer impact: direct route `skills` remain supported until a
  separately approved deprecation specification.
- risk:
  - controller over-selects facets.
    - mitigation: policy guidance, recorded reasons, and controller review of
      packet selection evidence.
  - policy authors duplicate skills across sets.
    - mitigation: set-local validation and stable packet de-duplication.
  - profile inheritance hides a widened authority or runtime.
    - mitigation: one shared resolver validates complete profile against route
      ceilings and records explicit field provenance.

## Invariants and Edge Cases

### Invariants

- policy is sole source for available skill-set IDs and their expanded skills.
- every required skill set resolves for every packet of its route.
- controller may select only route-allowed IDs before packet creation.
- resolved skills are deterministic, ordered, and de-duplicated.
- selected skill sets never alter route authority or other static execution bounds.
- every operating profile resolves one complete tested execution envelope.
- controller can select only route-allowed profiles and directed transitions.
- same-provider successor escalation inherits binding internally; controller never
  supplies provider binding.
- every allowed route profile has same provider; mismatched provider request or
  changed host configuration never uses inherited or fallback binding.
- packet and run evidence preserve selection provenance; agents cannot mutate it.
- legacy direct-skill routes preserve current packet output.

### Edge Cases

- empty selection: resolve required sets only.
- duplicate selected ID or duplicate route set ID: reject before packet creation.
- same skill in multiple valid sets: include once in first resolved occurrence.
- unknown or missing catalog set: fail policy validation.
- selected set not allowed by route: reject request before workspace or run state.
- plan-linked request: preserve plan-derived mode/base/paths; selection is bounded
  request metadata only.
- retry or successor: a changed selection requires new immutable packet; an
  existing packet never changes.
- timeout escalation: same-provider extended profile inherits prior binding; a
  missing binding blocks instead of rebuilding an unbound packet.
- profile inheritance: child fields override one parent chain; cycles, missing
  parent, or incomplete result fail shared-resolver validation.
- mixed-version state: readers preserve historical packets without assuming new
  metadata; dispatch uses current resolved packet only.
- generated-source consistency: routing documentation renders required and
  allowed set IDs plus resolved static baseline, never hand-maintained copies.

## Validation Plan

### Backend Verification Claims

- direct boundary: resolve managed packet from policy and request selection.
- important success and failure behavior: required-only, selected-allowed,
  legacy direct-skill, duplicate, malformed, unknown, disallowed, standard,
  extended, and invalid-profile cases.
- final state or side effects: invalid selection creates no packet, workspace, or
  run state; valid packet stores deterministic selection metadata and skills.
- rollback, retry, duplicate, or idempotency behavior: retries and successors
  create new packets; prior packet selection remains unchanged. Same-provider
  timeout escalation inherits prior binding; provider mismatch or configuration
  drift blocks before lanes.
- canonical contract and conformance proof: configuration validator, resolver
  tests, generated routing check, and host packet-consumption regression.
- real dependencies requiring proof: Not applicable. Policy resolution is local.
- representative-operation trace mechanism: managed request resolution and host
  prompt proof for legacy and composed packet shapes.
- performance claim and threshold: Not applicable. Selection is bounded policy
  list processing; no external I/O is introduced.

### Acceptance Criterion: Required-Only Resolution

- setup or precondition: composed route with required base and allowed backend set.
- action: resolve request without `skill_set_selections`.
- expected result: packet contains base set IDs and base skills only.
- failure condition: backend skill appears without selection.
- proof method: focused resolver test.
- expected evidence: immutable packet selection metadata and ordered skills.

### Acceptance Criterion: Allowed Facet Selection

- setup or precondition: same composed route.
- action: controller selects backend set with a reason.
- expected result: packet contains selected ID, reason, and backend skill once.
- failure condition: duplicate or reordered unrelated base skills.
- proof method: focused resolver test and immutable packet provenance assertion.
- expected evidence: normalized packet and run request evidence.

### Acceptance Criterion: Invalid Selection Rejection

- setup or precondition: composed route.
- action: submit malformed, duplicate, unknown, or disallowed selection.
- expected result: deterministic error before packet, workspace, or run state.
- failure condition: any run directory or partial packet exists.
- proof method: focused resolver and managed-run admission tests.
- expected evidence: error code and unchanged run root.

### Acceptance Criterion: Legacy Compatibility

- setup or precondition: existing route with direct static skills and historical
  packet without selection metadata.
- action: resolve and consume packet through host prompt path.
- expected result: legacy packet keeps current ordered skills and host task context
  projects those names without requiring facet metadata.
- failure condition: legacy route requires new configuration fields or host rejects
  packet solely for absent facet metadata.
- proof method: existing route regression plus host adapter regression.
- expected evidence: stable packet fields and passing host test.

### Acceptance Criterion: Profile-Governed Timeout Escalation

- setup or precondition: route permits `default` to `extended` transition for
  `dispatch_timeout`; original packet has valid same-provider binding.
- action: controller records allowed escalation.
- expected result: successor packet resolves extended budget and inherits binding;
  state becomes `planned`.
- failure condition: resolver requires caller-supplied binding or changes any
  non-profile field.
- proof method: focused successor-decision and host-preflight tests.
- expected evidence: packet profile provenance, inherited binding, and no product
  lane execution before admission completes.

### Acceptance Criterion: Runtime And Profile Rejection

- setup or precondition: route profile range and prior packet binding exist.
- action: select disallowed profile, submit malformed profile selection, attempt
  raw field override or mismatched `runtime_provider_id`, define cross-provider
  route profiles, or present changed host configuration.
- expected result: admission blocks before workspace or lane dispatch; changed
  configuration reports `provider_configuration_changed`.
- failure condition: controller creates a packet with unvalidated runtime or a
  mixed authority/tool/model combination.
- proof method: focused policy, resolver, successor-decision, and host tests.
- expected evidence: deterministic error and unchanged product workspace.

## Completion Criteria

Specification is complete when:

1. policy-owned required and allowed skill-set composition is unambiguous
2. controller selection is bounded, auditable, and immutable after packet creation
3. legacy routes and historical packets have defined compatibility behavior
4. operating profiles define every authority-bearing selection
5. invalid selection cannot create workspace, packet, or run side effects
6. generated routing output and all resolver/host proof targets are defined
7. operating-profile and same-provider binding rules are explicit
8. implementation sequencing remains deferred to an approved plan
9. host skill projection and shared profile-resolution ownership are explicit
