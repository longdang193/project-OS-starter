---
artifact_type: spec
template_id: detailed-specification
status: active
layer: change
name: harness-claim-repair-ssot
targets:
  - agents/roles.yaml
  - repo_config/harness.yaml
  - packages/harness-core
  - ../codex-harness-host
  - docs/operating_system
---

# Harness Claim Repair SSOT

## Goal and Problem

### Problem

- current behavior or opportunity: a managed lane can finish useful, stable
  work yet return no final claim, non-JSON text, a non-object, wrong claim
  kind, or a claim that fails its required-field contract. Host JSON parsing
  currently fails separately from core schema validation. Core can then expose
  `claim_invalid` to controller retry policy without first asking same lane for
  required result.
- affected users, systems, or maintainers: controller, `harness-core`, provider
  hosts, managed agents, policy authors, and operators recovering completed lane.
- evidence: `agents/roles.yaml` owns one role result kind plus required fields
  and constraints. Core projects that contract into every lane packet and
  raises `ClaimError` for invalid object claims. Codex provider host separately
  raises `ClaimParseError` while parsing final JSON. `repo_config/harness.yaml`
  permits bounded successor attempts for `claim_invalid` and provides a
  60-second finalization reserve.
- consequence of no change: malformed and schema-invalid claims receive
  different lifecycle treatment. Controller spends a successor attempt before
  it can request small missing artifact. Role-specific repair prompts would
  duplicate role contract and drift from packet truth.

### Goal

- desired outcome: one core-owned claim-repair phase classifies every unusable
  completion claim uniformly, prompts eligible lanes exactly once for a
  read-only corrected claim, and reaches controller retry only after repair
  fails or is inadmissible.
- observable success: a valid repaired claim resumes normal verification in its
  original attempt. One failed repair records `claim_invalid` with immutable
  evidence. Timeouts, workspace failures, artifact failures, policy failures,
  provider failures, API failures, and finalization write attempts never enter
  claim repair.

## Required Outcomes

### Outcome: One packet-derived typed claim contract

- affected actor or system: policy authors, core, host, and every managed role.
- required result: `agents/roles.yaml` owns one top-level `claim_fields`
  catalog. It defines every field type used by managed claims, including shared
  optional `frictions`; role entries own result kind, required field names, and
  allowed-value constraints. V1 field types are `nonempty_string`,
  `string_list`, and `friction_list`. Core resolves full field definitions,
  required fields, and constraints into each immutable lane `claim_schema`.
  Repair prompt shape derives only from this projection.
- success condition: no core or host field-name branch defines type semantics.
  Changing catalog field type, role required fields, or constraints changes
  normal validation and repair validation together.

### Outcome: Symmetric unusable-claim classification

- affected actor or system: core, host, and controller.
- required result: core classifies these terminal/stable completion responses as
  one `unusable_claim` family with a safe subcode:
  `missing_final_claim`, `claim_not_json`, `claim_not_object`,
  `claim_kind_mismatch`, `claim_field_missing`, `claim_field_type_invalid`, or
  `claim_field_constraint_invalid`.
- success condition: malformed text and invalid JSON objects reach identical
  admission, repair, evidence, and controller-decision logic. Host parse
  errors carry observations to core; host does not make lifecycle decisions.

### Outcome: One bounded repair before successor retry

- affected actor or system: controller and every managed claim-producing agent
  lane.
- required result: for an admissible `unusable_claim`, core authorizes exactly
  one repair interaction in original lane and original attempt. It consumes
  only packet-owned finalization reserve and does not increment attempt count,
  replay task work, or run normal tool time.
- success condition: valid repaired claim continues normal same-attempt
  verification. Invalid, absent, or timed-out repaired claim records terminal
  `claim_invalid`; only then may controller record a policy-permitted bounded
  successor or block.

### Outcome: Read-only repair boundary

- affected actor or system: provider host and agent runtime.
- required result: host enforces read-only repair authority: no workspace
  writes, commands, diagnostics, tools, delegation, task execution, or work
  replay. It resumes exact original provider thread only when packet-required
  capability is enforced; otherwise core records no-repair outcome.
- success condition: repair cannot use malformed agent text as injected fresh
  prompt content, bypass packet budget or policy, alter workspace state, or
  make a second repair request.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
|---|---|---|---|---|
| Who owns result contracts? | Each role has one `result_kind`, required fields, and optional constraints, but field types are hardcoded in core and host. | `agents/roles.yaml`; core and host claim validators | high | Add one role-file `claim_fields` catalog and eliminate field-name type branches. |
| Does packet carry claim truth? | Core resolves `required_claim_kind`, required fields, and constraints into lanes; it does not project field types. | `packages/harness-core/src/harness_core/managed.py` | high | Packet V7 must carry full typed claim schema. |
| Where does schema validation run? | Core validates managed claims and raises `ClaimError` for role-contract failure. | `packages/harness-core/src/harness_core/managed.py` | high | Core classifies every unusable claim after host observation. |
| Where is asymmetry? | Host final JSON parser raises `ClaimParseError` before core gets object claim. | `../codex-harness-host/src/codex_harness_host/claims.py` | high | Parse failure becomes core-visible unusable-claim observation. |
| What retry budget exists? | Bounded policy has two attempts, includes `claim_invalid`, and finalization reserve is 60 seconds. | `repo_config/harness.yaml` | high | Repair stays inside current attempt and current reserve. |

### Prototype and Validation Evidence

- prototype reference or `Not applicable: <reason>`: Not applicable: approved
  direction changes managed backend lifecycle, not user-facing interaction.
- validated scenarios and states: source inspection confirms packet claim
  projection, core object validation, host parse boundary, bounded retry policy,
  and finalization reserve.
- findings incorporated into approved behavior: normalize parse and schema
  failure under core ownership; reuse packet claim schema; repair once before
  controller successor decision.
- rejected alternatives: immediate successor retry; host-owned retry decision;
  one custom prompt per role; feeding raw malformed output into fresh context;
  unrestricted recovery continuation.

### Scope

- included behavior: packet-resolved repair budget, normalized unusable-claim
  observation, admission predicate, read-only repair continuation, repeated
  validation, durable evidence, outcome handling, and compatibility rules for
  newly resolved packets.
- affected boundaries: role catalog, harness policy, core request and run
  lifecycle, host lane adapter, provider capability contract, canonical
  guidance, and direct backend verification.
- admissible cases: every managed `node_kind: agent` lane with packet claim
  contract, provider-completed terminal observation, exact original thread,
  unused repair budget, final workspace/evidence, enforced same-thread repair
  capability, and no non-claim terminal failure.
- compatibility expectation: historical packets remain readable under existing
  rules and retain original terminal behavior. Only newly resolved compatible
  packets may request claim repair.

### Non-Goals

- workspace or thread resume after incomplete work.
- retry-budget expansion, caller-selected execution budgets, or automatic
  controller acceptance.
- repair of failed verification, failed checks, approval gates, artifacts,
  policy, workspace, provider, API, or tool-security boundaries.
- role-specific repair prompts, custom agent templates, model selection, or
  toolset redesign.
- replaying task work, diagnostics, delegation, artifact handoff, or changing
  source-artifact selection.

### Requirements and Behavioral Contract

#### Requirement: Claim-repair policy and packet projection

- trigger or actor: policy load and immutable packet resolution.
- preconditions: route resolves managed lane with valid role contract.
- required behavior: policy schema V6 in `repo_config/harness.yaml` owns one
  generic `claim_repair` policy with `max_repairs_per_lane: 1`, route-independent
  admissible failure family, and required host capability
  `claim_repair_same_thread: enforced`. Existing `retry_policies` remains sole
  owner of successor eligibility and exhaustion. `execution_budgets` remains
  sole owner of time; repair has no separate timeout or caller override.
- output or state change: packet V7 stores resolved repair count, admissible
  subcodes, required same-thread capability, finalization reserve,
  `required_claim_kind`, and typed `claim_schema`.
- failure behavior: invalid repair policy, unknown subcode, absent role
  contract, or incompatible host blocks before workspace or lane dispatch.
- observable acceptance: core resolves same repair contract for every
  qualifying role and route without role-name conditionals.

#### Requirement: Core-owned unusable-claim classification

- trigger or actor: host reports terminal completion text, missing final claim,
  or parsed candidate claim for lane with stable terminal observation.
- preconditions: core can bind report to exact run, attempt, immutable packet,
  lane, and lane claim contract.
- required behavior: host reports a typed `claim_observation/v1` with exact
  lane and original thread identity. Its `state` is one of `missing`,
  `non_json`, `json_non_object`, or `object`; only `object` includes parsed
  `candidate_claim`. It may retain byte length and digest, never raw response
  text. Core maps observation state to `missing_final_claim`, `claim_not_json`,
  or `claim_not_object`, then performs result-kind, typed required-field, and
  constraint validation for object claims. It returns normal valid claim
  recording or `unusable_claim` with one safe subcode.
- output or state change: evidence records classification source, safe subcode,
  validator version, lane ID, and original completion state. It never records
  raw malformed response in packet, run state, failure detail, or fresh prompt.
- failure behavior: report identity mismatch, missing packet contract, invalid
  terminal observation, or host protocol violation is its own existing failure;
  it is not converted into unusable claim.
- observable acceptance: host parse failure and core object-schema failure
  produce same repair admission input and eventual outcome contract.

#### Requirement: Claim-repair admission

- trigger or actor: core receives an `unusable_claim` classification.
- preconditions: all conditions hold:
  1. lane is a managed `node_kind: agent` lane and provider reports completed
     terminal state; no timeout, interruption, cancellation, or in-flight work
     remains;
  2. host supplied final workspace baseline and required terminal evidence for
     exact lane and attempt;
  3. immutable packet repair budget for lane is unused;
  4. finalization reserve remains available under packet execution budget;
  5. original `thread_id` exists and host advertises
     `claim_repair_same_thread: enforced` for packet V7;
  6. no artifact descriptor/hash/proof failure, workspace baseline failure,
     provider configuration or transport failure, policy/API failure, approval
     gate failure, tool-security failure, or finalization write attempt exists.
- required behavior: core admits repair only when every predicate holds. It
  records admission decision before asking host to continue lane.
- output or state change: admitted lane enters one `claim_repair` finalization
  phase. Inadmissible unusable claim terminates as `claim_invalid` with explicit
  no-repair reason. Timeout, interruption, cancellation, and in-flight work
  preserve original terminal outcome.
- failure behavior: repair attempt during excluded failure path is rejected as
  protocol/policy failure and cannot repair or erase prior evidence.
- observable acceptance: no repair request exists for missing same-thread
  capability or thread identity, incomplete timeout, artifact failure,
  workspace failure, provider failure, policy/API failure, tool-security
  failure, or finalization write attempt.

#### Requirement: Read-only repair interaction

- trigger or actor: core admission requests one repair through packet-compatible
  host adapter.
- preconditions: exact lane packet, core classification, and finalization
  reserve are present.
- required behavior: host starts one read-only repair continuation on exact
  original provider thread for same lane. It starts no fresh thread or context.
  Host passes immutable packet claim schema, lane identity, safe subcode, and
  safe detail; it never interpolates original response text or an agent-generated
  paraphrase into repair prompt.
- output or state change: host returns one terminal candidate claim plus
  read-only finalization evidence. Core validates candidate with exactly same
  validator used for original claim.
- failure behavior: absent candidate, malformed candidate, schema-invalid
  candidate, finalization timeout, or denied completion becomes failed repair.
  Command, tool, diagnostic, delegation, workspace-write, or task-replay
  attempt is finalization authority violation and preserves that security or
  policy failure without another repair prompt.
- observable acceptance: repair cannot mutate workspace, invoke tool, consume
  normal lane budget, open fresh thread, or send more than one continuation.

#### Requirement: Generic repair prompt

- trigger or actor: host invokes accepted repair continuation.
- preconditions: core supplied safe classification and immutable packet claim
  contract.
- required behavior: host renders one generic prompt from packet data. It has
  these semantics and no role-specific additions:

  ```text
  Claim repair only.

  Previous completion response is unusable: `{{failure_code}}`.
  {{safe_failure_detail}}

  Do not continue task work.
  Do not modify files.
  Do not run commands, diagnostics, tools, or delegation.
  Do not explain failure.

  Return exactly one JSON object. No Markdown or prose.

  Lane: `{{lane_id}}`
  Required claim contract:
  {{claim_shape_json}}

  Use only facts already established in this lane. Do not invent files,
  findings, approvals, or verdicts. Replace every placeholder with truthful data.
  ```

  `safe_failure_detail` can identify missing packet-schema field names, expected
  kinds, expected JSON object shape, and allowed constraint values. It cannot
  contain source response content, filesystem text, secrets, tool output, or
  untrusted agent-generated text.
- output or state change: host records prompt-contract version and digest of
  rendered safe prompt in finalization evidence.
- failure behavior: missing packet schema or unsafe interpolation blocks repair
  before provider invocation.
- observable acceptance: every managed claim-producing lane gets
  claim-shape-equivalent prompt from its lane packet; no prompt file branches by
  role or route and no fresh repair context is created.

#### Requirement: Outcome and controller lifecycle

- trigger or actor: repeated core validation after repair, or repair denial or
  failure.
- preconditions: core has complete admission and finalization evidence.
- required behavior: valid repair appends normal lane claim and returns to
  existing same-attempt lane lifecycle. Failed or inadmissible repair records
  terminal `claim_invalid` with safe subcode and repair evidence. Failed
  executed repair also records one `claim_repair_failed` friction event; policy
  maps that code to existing `harness_diagnosis` route. `writer_completion_missing`
  remains its current non-repair timeout-evidence code and follow-up key.
  Controller alone selects permitted outcome decision from immutable retry
  policy after terminal record. A successor is new request and packet; it does
  not resume or mutate failed packet.
- output or state change: run state distinguishes original claim observation,
  repair admission, repair finalization, repeated validation, and final
  outcome. `claim_invalid` cannot be accepted without valid core-recorded claim
  and existing required verification evidence.
- failure behavior: repair does not turn timeout into retryable claim failure,
  expand `max_attempts`, alter escalation profiles, or allow caller choice of
  budget. Existing timeout rules continue unchanged.
- observable acceptance: controller sees `claim_invalid` only after one
  eligible repair opportunity or explicit no-repair reason, then applies
  current bounded decision policy.

### Constraints and Alternatives

- constraint: all lifecycle decisions remain core/controller-owned; host is
  provider adapter and authority enforcer.
- constraint: repair uses exact immutable packet and current trusted provider
  binding; no ambient workspace or `.harness` state may be mounted.
- constraint: raw invalid output is untrusted prompt data and must never be
  interpolated into repair prompt.
- alternative: retry successor immediately.
  - benefit: no host continuation protocol.
  - trade-off: wastes attempt budget and repeats finished work.
  - reason rejected: does not ask lane before retry and treats claim formatting
    as task failure.
- alternative: host parses, repairs, and accepts claim independently.
  - benefit: local implementation appears shorter.
  - trade-off: duplicates core contract/lifecycle logic and creates host drift.
  - reason rejected: violates one authoritative claim validator and controller
    decision ownership.
- alternative: custom repair prompt per role.
  - benefit: role-specific wording.
  - trade-off: duplicates claim schema and creates asymmetry.
  - reason rejected: packet claim schema already supplies needed contract.

## Design Decisions

### Decision: One generic repair state machine

- context: missing, malformed, wrong-kind, and schema-invalid claims differ in
  source syntax but all lack usable packet-defined final artifact.
- selected approach: normalize them into core-owned `unusable_claim`, evaluate
  one admission predicate, perform one read-only repair, then use one repeated
  core validator and terminal outcome.
- rationale: one lifecycle handles every admissible claim defect. Difference is
  data (`failure_code`, safe details, packet schema), not code path.
- alternatives considered: separate parse repair, schema repair, and
  missing-final finalizer paths.
- accepted trade-offs: host/core protocol gains typed completion observations
  and repair evidence; malformed output is intentionally less available for
  debugging outside same-thread provider context.
- affected owners and boundaries: role catalog owns claim fields; policy owns
  repair count and time source; packet freezes data; core owns classification,
  state, evidence, and outcome; host owns read-only enforcement; controller
  owns successor decision.

### Decision: Repair before bounded successor

- context: stable task work can be complete when only final claim is unusable.
- selected approach: repair occurs within original lane and original attempt
  before `claim_invalid` enters controller retry lifecycle.
- rationale: claim correction is smaller and more truthful than re-executing
  task work. It preserves bounded attempts and controller authority.
- alternatives considered: immediate failure or automatic multi-repair loop.
- accepted trade-offs: one finalization interaction may add bounded latency;
  repair is limited to one because repeated format prompts cannot establish new
  product facts.
- affected owners and boundaries: `claim_repair.max_repairs_per_lane` owns
  interaction count; `execution_budgets.finalization_reserve_seconds` owns
  time; retry policy owns successor decision.

### Decision: Host enforces repair authority; core validates result

- context: prompt instructions alone cannot prevent provider tool use or
  workspace change.
- selected approach: host exposes repair as dedicated continuation with
  read-only workspace and no commands, tools, diagnostics, or delegation. Core
  consumes candidate claim through normal validator.
- rationale: enforcement stays at provider boundary and one validator remains
  authoritative.
- alternatives considered: normal lane re-entry with instruction-only prompt or
  host-local schema acceptance.
- accepted trade-offs: compatible host must expose constrained continuation;
  older hosts cannot receive new repair packets.
- affected owners and boundaries: packet compatibility gates host dispatch;
  host observes authority violation; core records result and outcome.

### Decision: Exact-thread repair only

- context: malformed completion text is untrusted, while a fresh agent has no
  truthful record of files, findings, or verdict formed in prior lane.
- selected approach: repair requires host-enforced continuation of exact original
  provider thread. Missing continuation capability or original thread identity
  makes claim repair inadmissible; core records `claim_invalid` without prompt.
- rationale: original thread has lane-established facts without injecting raw
  output into new prompt. This preserves truthfulness, read-only authority, and
  one uniform repair path.
- alternatives considered: fresh context with raw output, fresh context with
  no facts, or new safe factual-handoff artifact.
- accepted trade-offs: providers without same-thread continuation skip repair
  and use existing bounded controller lifecycle. A factual-handoff artifact is
  deferred because it adds another contract and evidence surface.
- affected owners and boundaries: packet compatibility requires capability;
  host resumes exact thread; core records no-repair reason and outcome.

### Compatibility, Migration, and Risk

- old behavior: host parser failure and core schema failure follow separate
  paths; timeout with completed writer command and missing final claim reaches
  `writer_completion_missing`; `claim_invalid` can reach controller policy
  without repair.
- new behavior: policy schema V6 adds generic repair policy and typed claim
  catalog. Request API 5 resolves `claim_repair` compatibility profile: packet
  API 7, host API 6, and provider contract 6. Packet API 6 becomes
  `artifact_handoff_legacy` with no request aliases and retains host API 5 /
  provider contract 5 dispatch and read support. Packet APIs 3 through 7 remain
  readable under their existing compatible host profiles. Run API remains 2;
  packet-7 repair evidence is additive under existing attempt evidence map.
- compatibility boundary: packet V7 must not dispatch to host without exact
  API 6 / provider contract 6 identity plus
  `claim_repair_same_thread: enforced`. Packet V6 and older packets cannot gain
  repair retrospectively.
- migration or backfill: no run-state migration or artifact backfill. Core
  resolves new packets from existing request API 5 input shape; old run evidence
  and packet payloads remain immutable.
- rollout and rollback: enable only with packet/host compatibility pair. Roll
  back by resolving future packets without claim repair; never alter created
  packet or retry historical attempt.
- deprecation or consumer impact: `writer_completion_missing` retains current
  timeout-evidence semantics and `harness_diagnosis` mapping. New failed
  executed repair emits `claim_repair_failed`, which also maps to
  `harness_diagnosis`; all other `claim_invalid` outcomes do not create that
  follow-up. Consumers use core outcome reason plus repair evidence, not host
  parser exception type.
- risk:
  - risk: repair continuation performs new work.
    - mitigation: read-only host authority, no tool surface, one reserve-bound
      turn, and authority-violation terminal evidence.
  - risk: repair becomes unbounded retries.
    - mitigation: immutable one-repair count and existing bounded controller
      successor policy.
  - risk: malformed output injects instructions into repair prompt.
  - mitigation: never inject it into repair prompt; whitelist safe detail.
  - risk: host/core classify differently.
    - mitigation: core owns classification and repeated validation; host sends
      typed observations only.

## Invariants and Edge Cases

### Invariants

- `agents/roles.yaml` `claim_fields` catalog is sole source for normal and
  repair field types; role entries are sole source for result kind, required
  fields, and constraints.
- One lane gets at most one repair interaction per immutable packet.
- Repair runs only after stable terminal work and preserves exact lane, attempt,
  packet, workspace baseline, provider binding, and execution budget.
- Repair requires exact original thread continuation; missing capability or
  identity never creates fresh repair context.
- Repair is read-only and cannot run commands, tools, diagnostics, delegation,
  task work, or workspace writes.
- Core accepts claims only through same validator used for initial final claim.
- Controller alone records retry, escalation, waiver, approval, or block
  decision after core terminal outcome.
- Raw malformed output never enters repair prompt, mutable run state, or
  packet evidence.
- Ineligible failures preserve original safety/lifecycle semantics.

### Edge Cases

- empty or minimal input: empty, whitespace-only, or absent final response is
  `missing_final_claim` only when provider-completed terminal evidence and exact
  original thread exist; it gets one repair if admitted.
- normal and large input: all JSON object claims use same packet schema;
  oversized or truncated provider response that cannot supply valid object is
  unusable claim only if stable evidence remains valid, otherwise provider or
  transport failure.
- duplicate, missing, malformed, or unsupported data: repeated final text does
  not create another repair; duplicate claim recording remains existing core
  validation concern; unknown keys follow existing claim-schema policy.
- retry, cancellation, timeout, partial failure, or concurrency: incomplete
  timeout, interruption, cancellation, in-flight work, missing same-thread
  capability, and absent stable workspace receive no repair. Parallel lanes
  keep isolated packets and repair counters; one lane repair cannot consume
  another lane budget or alter dependency state.
- migration or mixed-version state: packet V6 retains host API 5/provider
  contract 5 dispatch. Packet V7 requires host API 6/provider contract 6 plus
  same-thread capability and cannot silently fall back to old finalizer semantics.
- generated-source consistency: canonical governance and generated agent
  surfaces describe same stable-claim repair boundary after implementation.
- security or accessibility boundary: repair uses server-enforced no-tool,
  read-only authority. No frontend or accessibility behavior is in scope.

## Validation Plan

### Backend Verification Claims

- direct boundary: core validates every claim type from packet-projected role
  field catalog, classifies each unusable-claim subcode from
  `claim_observation/v1` and object validation, and never branches on host
  parser exception type or field name.
- important success and failure behavior: eligible missing, malformed,
  wrong-kind, missing-field, invalid-type, and invalid-constraint claims on
  every managed claim-producing lane each receive one exact-thread repair;
  valid repair resumes same attempt; invalid repair becomes `claim_invalid` plus
  `claim_repair_failed`; excluded failure families receive no repair.
- final state or side effects: run evidence records source classification,
  admission result, repair count, finalization mode, repeated validator result,
  and outcome. Workspace diff and tool trace remain unchanged during repair.
- rollback, retry, duplicate, or idempotency behavior: repair does not mutate
  packet, increment attempt count, or create successor. Controller may create
  one existing-policy successor only after `claim_invalid`; repeated repair
  request is rejected idempotently.
- canonical contract and conformance proof: role catalog, policy schema, packet
  projection, core validator, and host capability/adapter agree on generic
  repair contract.
- real dependencies requiring proof: provider adapter proves exact-thread
  continuation with read-only no-tool authority; a provider lacking capability
  proves no repair invocation and core `claim_invalid` outcome.
- representative-operation trace mechanism: test or fixture captures lane ID,
  attempt ID, classification, repair admission, host authority mode, repeated
  validation, and outcome in run evidence.
- performance claim and threshold: Not applicable: no performance improvement
  claimed. Repair adds at most one packet-reserve-bound interaction.

### Acceptance Criterion: Valid initial claim remains unchanged

- setup or precondition: compatible repair-capable packet and terminal/stable
  lane return role-valid JSON object.
- action: core records completion claim.
- expected result: claim records once; host starts no repair continuation.
- failure condition: any repair evidence or budget use appears.
- proof method: focused core/host contract test and run evidence assertion.
- expected evidence: one normal claim record and zero repair events.

### Acceptance Criterion: Every admissible unusable claim repairs once

- setup or precondition: isolated fixtures for each declared unusable-claim
  subcode with terminal/stable workspace and evidence.
- action: host returns unusable completion; repair continuation returns valid
  packet-schema claim.
- expected result: core accepts repaired claim in original attempt and resumes
  normal verification.
- failure condition: successor attempt, task replay, duplicated repair, or
  role-specific prompt branch occurs.
- proof method: parameterized direct boundary tests plus host fake/provider
  evidence.
- expected evidence: one repair admission, one read-only continuation, same
  claim validator, and one valid claim record.

### Acceptance Criterion: Failed repair reaches controller once

- setup or precondition: admitted unusable claim whose repair candidate is
  absent, malformed, invalid, or reserve-timed-out.
- action: core completes repeated validation.
- expected result: terminal `claim_invalid` includes original and repair-safe
  evidence; controller receives existing immutable-policy decisions.
- failure condition: host retries repair, core accepts invalid candidate, or
  attempt count changes before controller decision.
- proof method: focused lifecycle test with repair count and decision assertions.
- expected evidence: one repair event, `claim_invalid`, preserved packet digest,
  and no successor before controller decision.

### Acceptance Criterion: Excluded failures never repair

- setup or precondition: fixtures for incomplete timeout, artifact proof/hash
  failure, workspace failure, provider/configuration failure, policy/API
  failure, tool-security failure, and finalization write attempt.
- action: core and host process terminal failure.
- expected result: original failure semantics remain; no repair prompt or
  repair-budget use occurs.
- failure condition: any excluded fixture invokes read-only repair.
- proof method: focused negative contract tests and host call spy.
- expected evidence: zero repair invocation and original terminal reason.

### Acceptance Criterion: Unsupported continuation never falls back

- setup or precondition: packet V7 reaches unusable claim on provider without
  `claim_repair_same_thread: enforced`, or without original thread identity.
- action: core evaluates repair admission.
- expected result: no repair continuation or fresh thread starts; terminal
  `claim_invalid` records explicit no-repair reason.
- failure condition: host starts new thread, interpolates raw response, or uses
  tools, commands, or write capability for repair.
- proof method: core/host capability contract test with call spy and evidence
  assertion.
- expected evidence: zero repair invocation, zero fresh thread, safe outcome,
  and unchanged workspace/tool trace.

## Completion Criteria

Specification is complete when:

1. one core-owned unusable-claim family and exact eligible subcodes are defined
2. policy, packet, core, host, and controller ownership is unambiguous
3. one repair admission predicate and one reserve-bound read-only repair are
   defined for every admissible role and route
4. no-repair safety boundaries preserve timeout, artifact, workspace, provider,
   policy, API, and tool-security behavior
5. prompt derivation, raw-text safety, evidence, compatibility, and controller
   successor lifecycle are explicit
6. backend verification claims and acceptance criteria cover successful repair,
   failed repair, and excluded paths
7. implementation sequencing, files, commands, and rollout execution remain
   deferred to implementation plan
