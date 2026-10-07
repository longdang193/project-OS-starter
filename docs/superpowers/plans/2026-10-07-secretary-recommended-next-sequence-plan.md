---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: secretary-recommended-next-sequence
targets:
  - docs/superpowers/plans/2026-10-07-secretary-recommended-next-sequence-plan.md
  - docs/architecture.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - .agents/skills/skill-project-secretary/SKILL.md
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - scripts/project_os_runtime/secretary_adapter.py
  - scripts/project_os_runtime/secretary_events.py
  - scripts/validation_findings.py
  - scripts/validate_planning_lifecycle.py
  - scripts/validate_template_required_sections.py
  - generated_agents/codex/skills/skill-project-secretary/SKILL.md
  - generated_agents/claude/skills/skill-project-secretary/SKILL.md
  - generated_agents/antigravity/skills/skill-project-secretary/SKILL.md
  - generated_agents/codex/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/claude/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md
  - tests/test_secretary_adapter.py
  - tests/test_secretary_events.py
  - tests/test_skill_project_secretary.py
  - tests/test_skill_chief_of_staff.py
  - tests/test_validation_findings.py
  - tests/test_validate_planning_lifecycle.py
  - tests/test_validate_template_required_sections.py
---

# Secretary Recommended Next Sequence Plan

## Goal

Deliver the next small Secretary convergence change without expanding the
architecture: correct controller ownership scope, make event identity stable
through coalescing and resolution, restore impact-based historical validation,
align canonical guidance, and complete a bounded assessment of whether a
separate live-transport pilot is ready.

Paseo remains deferred. Do not add roles, databases, message archives,
schedulers, approval loops, persistent validation caches, or a second task
tracker.

## Verdict Review

The supplied verdict is correct. Stage A is implementation-ready. Stage B must
leave this plan and become a separate pilot plan after capability discovery;
the repository currently exposes an in-memory contract fake, not a named live
Secretary-to-CoS transport.

### [P1] Live transport implementation belongs in a separate plan

**Problem:** The verdict requires a live transport pilot but does not name an
existing transport, endpoint, ownership store, or runtime capability that can
carry the controller-session contract.

**Why it matters:** Implementing a guessed transport would widen authority,
create new persistence, or duplicate existing runtime ownership. That would
violate the target architecture and make transport evidence non-authoritative.

**Evidence:** `scripts/project_os_runtime/secretary_adapter.py` contains
`InMemoryControllerSessionAdapter`; `docs/operating_system/runtime/runtime-surfaces.md`
describes it as a contract fake and reserves crash recovery for a transport-owned
journal.

**Preserve:** Transport owns delivery, observation, deadlines, cleanup, and
receipts. Plan + Git remains workflow truth. No autonomous background operation
is introduced.

**Smallest safe correction:** Replace live implementation with an inspect-only
transport readiness assessment. A qualifying result records the named
transport, exact owner/interfaces/files, receipt mechanism, dependencies, and
test interface for a new pilot plan. An unavailable result records the
capability gap and completes this plan without transport code.

### [P2] Controller ownership lookup is scoped too narrowly

**Problem:** The journal resolves conflicts by bare `workstream`, so identical
workstream names in different repositories conflict.

**Why it matters:** Independent repositories cannot activate equivalent
workstreams concurrently, while same-repository binding drift can be missed or
misclassified.

**Evidence:** `scripts/project_os_runtime/secretary_adapter.py` exposes
`lookup_workstream(workstream)` and calls it from `resolve()` and `activate()`.

**Preserve:** Full `ControllerBinding` comparison continues to detect binding
drift within one repository and workstream.

**Smallest safe correction:** Replace bare lookup with owner lookup keyed by
`(repository_identity, workstream)`. Same repository plus different binding
reconciles; different repositories plus same workstream remain independent.
Reserve atomic compare-and-set ownership for Stage B transport.

### [P2] Event identity differs between coalescing and resolution

**Problem:** Coalescing includes source, workstream, event type, and observed
identity, while `event_identity()` uses only source and observed identity.

**Why it matters:** Reused provider event IDs can suppress unrelated events in
another workstream or event type.

**Evidence:** `scripts/project_os_runtime/secretary_events.py` groups on a
four-part key but `event_identity()` returns `source:observed_identity`.

**Preserve:** Same-anchor evidence merges; trusted strictly ordered source
sequences may supersede; equal, missing, or incomparable ordering preserves
ambiguity and reconciles conservatively.

**Smallest safe correction:** Define one canonical four-component event identity
and use it for coalescing, resolution, and supersession. Opaque anchors, Git
SHAs, receipt IDs, and evidence IDs remain non-chronological.

### [P2] Historical severity coverage is incomplete

**Problem:** `planning_required_metadata_missing` is not fully covered by the
historical compatibility policy, and `template_selection_missing` is currently
warning even when a selected active plan consumes the missing metadata.

**Why it matters:** Broad audits can regress on harmless old authoring metadata,
while active authority, dependency, workspace, proof, integrity, and security
defects can be weakened by over-broad warning rules.

**Evidence:** `scripts/validation_findings.py`,
`scripts/validate_planning_lifecycle.py`, and
`scripts/validate_template_required_sections.py` emit overlapping categories;
current tests preserve selected completed template metadata as warning.

**Preserve:** Severity is code-driven, never parsed from human-readable text.
Historical cosmetic drift warns when semantics remain clear; consumed safety
facts and runtime/integrity/security failures block affected operations.

**Smallest safe correction:** Split severity into always-blocking,
blocking-when-consumed, and compatibility-warning categories; remove or align
dead/misnamed codes; add end-to-end fixtures that exercise emitted findings
through final blocking decisions.

## Implementation Outcomes

### Correctness-converged Secretary contracts

Adapter ownership, event identity, set-like delta fingerprints, and canonical
Secretary/CoS wording agree across source, tests, runtime guidance, and
generated adapters. Different repositories can own same-named workstreams;
same-repository drift reconciles; reordered set values do not create false
reconciliation.

### Impact-based validation remains safe and historical-compatible

Active or consumed authority, executor, ownership, workspace, dependency,
acceptance-proof, runtime, integrity, and security findings block as applicable.
Legacy cosmetic or authoring drift warns only when semantics remain clear.
End-to-end fixtures prove emitted validator codes reach the intended final
severity.

### Bounded live-transport decision and proof

One existing supported transport is either qualified with exact handoff facts
for a separate pilot plan, or its missing capability is recorded. This plan
adds no scheduler, background loop, new state store, or transport-specific
Secretary database.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-project-secretary`, `skill-code-standards`, `skill-backend-verification`, `skill-verification-before-completion`, `skill-plan-document-reviewer`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: create the named `codex/` branch, edit named canonical files and tests, regenerate named adapter mirrors, run declared local validators and tests, and inspect configured transport capabilities without installing, authenticating, or creating external state
- User-approval actions: push, merge, publication, external writes, destructive recovery, discard, cleanup, or any transport installation/authentication
- Parallel ownership: none; shared contract names require serialization
- Sequential fallback: run Tasks 1–6 in order; Task 6 is inspect-only and creates no transport implementation

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/secretary-correctness-convergence`
- Base commit: `ddbdb469b636ae5cecc24065d2a1f4d72ce3985c`
- Expected workspace: `tracked clean; preserve untracked .playwright-mcp/, db/, and temp_evidence.json`
- Next action: `branch finishing after user-directed Git disposition`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | canonical guidance tests | 32 passed |
| Task 2 | `completed` | current | `codex` | none | ownership and fingerprint tests | 14 passed |
| Task 3 | `completed` | current | `codex` | none | event identity and ambiguity tests | 15 passed |
| Task 4 | `completed` | current | `codex` | none | end-to-end validator fixtures | 63 passed |
| Task 5 | `completed` | current | `codex` | Tasks 1–4 | generated sync and full validation | 935 passed / 1 skipped; audit and sync passed |
| Task 6 | `completed` | current | `codex` | Task 5 | transport readiness assessment | `NOT_AVAILABLE`; pilot deferred |

## Task Breakdown

### Task 1: Align canonical ownership and sparse communication guidance

**Purpose:** Remove remaining wording that lets Secretary issue Worker task
briefs or makes accepted local work appear silent toward CoS.

**Task Function:** Canonical architecture and skill contract editing.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded documentation change with existing focused tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused skill tests and repository validators suffice.

**Specification Coverage:** Three-layer ownership sentence, four logical
exchanges, lowest-boundary escalation, no changed decision/no message, and
Secretary-only active Docket writing.

**Required Skills:** `skill-project-secretary`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `docs/architecture.md`, `.agents/skills/skill-project-secretary/SKILL.md`, `.agents/skills/skill-chief-of-staff/SKILL.md`
- Modify: Secretary routing table, accepted-work wording, sparse-boundary wording, and CoS escalation wording
- Verify: `tests/test_skill_project_secretary.py`, `tests/test_skill_chief_of_staff.py`

**Dependencies:** None.

**Authority:**
- Preauthorized local actions: modify named canonical docs and focused tests only
- Stop for: new role, lifecycle state, Docket field, approval loop, or changed Worker authority

**Steps:**
- [x] Replace any Secretary “task brief” output wording with bounded attention routing to the selected execution owner.
- [x] Clarify “silent” as silent toward Secretary while Worker evidence still returns to CoS and CoS still accepts it.
- [x] Keep exactly four logical exchanges and the “No changed cross-boundary decision → no cross-boundary message” rule.
- [x] Keep `docs/architecture.md` system-level and skills as primary owners for routing and CoS behavior.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_skill_project_secretary.py tests/test_skill_chief_of_staff.py`
- Expected: ownership, forbidden-authority, and sparse-communication assertions pass.

**Exit Criteria:** Canonical guidance has one ownership model and no Secretary-to-Worker task assignment authority.

### Task 2: Scope controller ownership and canonicalize delta fingerprints

**Purpose:** Prevent cross-repository false conflicts and false delivery
reconciliation.

**Task Function:** Runtime contract correction and replay/idempotency proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small contract change with direct adapter tests and no new dependency.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: backend boundary tests provide direct proof.

**Specification Coverage:** Owner key `(repository_identity, workstream)`, full binding drift detection, and set-like communication fields.

**Required Skills:** `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/secretary_adapter.py:ControllerSessionJournal`, `InMemoryControllerSessionJournal`, `InMemoryControllerSessionAdapter.resolve`, `InMemoryControllerSessionAdapter.activate`
- Modify: owner lookup protocol/storage/callers and `AttentionDelta`/`CoordinationDelta` normalization
- Verify: `tests/test_secretary_adapter.py`

**Dependencies:** None.

**Authority:**
- Preauthorized local actions: modify named adapter module and focused adapter tests only
- Stop for: persistent storage, external transport, changed receipt meaning, or non-deterministic ownership behavior

**Steps:**
- [x] Replace `lookup_workstream(workstream)` with owner lookup keyed by repository identity and workstream.
- [x] Prove same-repository binding drift returns reconciliation and different repositories with same workstream activate independently.
- [x] Normalize `constraint_refs`, `evidence_refs`, and `affected_workstreams` as sorted unique tuples before fingerprinting.
- [x] Prove reordered or duplicated set-like values reuse delivery; changed semantic values still fail closed.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_secretary_adapter.py`
- Expected: existing replay/release/delivery tests plus new cross-repository and normalization tests pass with no extra side effects.

**Exit Criteria:** In-memory contract matches repository-scoped ownership and stable set semantics; atomic claim remains explicitly transport-owned.

### Task 3: Use one event identity through coalescing and resolution

**Purpose:** Prevent reused provider event IDs from suppressing unrelated workstream or event-type events.

**Task Function:** Event reconciliation contract correction.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic pure-function change with focused tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: event unit and contract tests are sufficient.

**Specification Coverage:** Canonical identity `(source, workstream, event_type, observed_identity)`, chronology rules, ambiguity preservation, and conservative reconciliation.

**Required Skills:** `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/secretary_events.py:event_identity`, `coalesce_event_hints`, `reconcile_event_hint`, `ReconciliationEvidence`
- Modify: canonical identity representation and resolved/superseded event matching
- Verify: `tests/test_secretary_events.py`

**Dependencies:** None.

**Authority:**
- Preauthorized local actions: modify named event module and focused event tests only
- Stop for: lexical anchor ordering, opaque-identifier chronology, or broader event scheduling

**Steps:**
- [x] Define one collision-safe four-component identity used by coalescing, resolution, and supersession.
- [x] Add tests proving same source/ID in different workstreams or event types remains distinct.
- [x] Preserve same-anchor merge, strictly ordered source-sequence supersession, and ambiguous missing/equal/incomparable sequence behavior.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_secretary_events.py`
- Expected: identity isolation and chronology/ambiguity tests pass.

**Exit Criteria:** Event coalescing and reconciliation use identical identity semantics without adding a scheduler or event store.

### Task 4: Restore impact-based historical validation and fixture coverage

**Purpose:** Make severity depend on safety impact and consumption while keeping historical cosmetic drift non-blocking.

**Task Function:** Validator taxonomy and end-to-end compatibility testing.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: existing validator architecture and temporary-root fixtures provide bounded proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: validator tests directly exercise emitted findings and final blocking decisions.

**Specification Coverage:** `ALWAYS_BLOCKING_CODES`, `CONSUMED_BLOCKING_CODES`, and `COMPATIBILITY_WARNING_CODES`; semantic metadata codes; active template metadata blocking; completed historical warning; no message-text parsing.

**Required Skills:** `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/validation_findings.py:severity_for`, `scripts/validate_planning_lifecycle.py:validate_artifact`, `scripts/validate_template_required_sections.py:validate_documents`
- Modify: code taxonomy, emitted-code alignment, and historical compatibility handling
- Verify: `tests/test_validation_findings.py`, `tests/test_validate_planning_lifecycle.py`, `tests/test_validate_template_required_sections.py`

**Dependencies:** None; keep validator changes independent from adapter and event implementation.

**Authority:**
- Preauthorized local actions: modify named validator modules and focused fixture tests only
- Stop for: broad warning suppression, message-text severity parsing, or invented reference grammar in prose fields

**Steps:**
- [x] Define `ALWAYS_BLOCKING_CODES`, `CONSUMED_BLOCKING_CODES`, and `COMPATIBILITY_WARNING_CODES` from semantic codes actually emitted by validators.
- [x] Split broad required-metadata findings into semantic template metadata versus execution metadata, or make validators emit the correct semantic code at source.
- [x] Make missing modern `template_id` blocking for selected proposed/active plans and warning for old completed artifacts when semantics remain clear.
- [x] Align or remove dead/misnamed classification codes so emitted categories and classifier categories match.
- [x] Add end-to-end fixtures that run validators through final issue aggregation and prove warning-only results do not block while consumed safety findings do.
- [x] Keep scoped preflight limited to structured references already defined by the repository.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_validation_findings.py tests/test_validate_planning_lifecycle.py tests/test_validate_template_required_sections.py`
- Expected: emitted-code, historical-compatibility, active-consumption, and final blocking behavior pass.

**Exit Criteria:** Validator output has stable code-driven severity with direct end-to-end proof and no new mini-language.

### Task 5: Reconcile generated surfaces and complete Stage A proof

**Purpose:** Make canonical source, generated adapters, runtime guidance, and tests agree before any transport work.

**Task Function:** Generated-surface synchronization and release-gate verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic synchronization and repository validators.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository-provided validators and focused/full tests.

**Specification Coverage:** SSOT, generated-header integrity, impact-based validation, and Stage A acceptance.

**Required Skills:** `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/sync_agent_adapters.py`, `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: runtime guidance and generated skill mirrors derived from canonical skills; no direct generated edits
- Verify: generated mirrors, plan validators, repository contract validators, and full test suite

**Dependencies:** Tasks 1–4 complete.

**Authority:**
- Preauthorized local actions: run canonical adapter sync and declared local verification commands; accept deterministic generated output only
- Stop for: generated drift outside canonical changes, unrelated failures requiring source edits, or modifications to preserved disposable artifacts

**Steps:**
- [x] Update runtime guidance for repository-scoped ownership, canonical event identity, and transport-owned atomic claims.
- [x] Run `py -3 scripts/sync_agent_adapters.py --all-platforms`.
- [x] Run generated-surface and plan validators; inspect `git diff --check`.
- [x] Run focused tests, then full `py -3 -m pytest -q`.
- [x] Record Stage A evidence without changing plan status to completed until fresh verification authorizes it.

**Verification:**
- [x] `py -3 scripts/sync_agent_adapters.py --check`
- [x] `py -3 scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-07-secretary-recommended-next-sequence-plan.md`
- [x] `py -3 scripts/validate_template_required_sections.py --repo-root . --require-template-selection --document docs/superpowers/plans/2026-10-07-secretary-recommended-next-sequence-plan.md`
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root . --scope preflight --plan docs/superpowers/plans/2026-10-07-secretary-recommended-next-sequence-plan.md`
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root . --scope audit`
- [x] `git diff --check`
- Expected: generated surfaces match canonical inputs, validators pass, focused tests pass, and full suite has no new failures.

**Exit Criteria:** Stage A is proven, generated surfaces are synchronized, and preserved untracked artifacts remain untouched.

### Task 6: Assess live transport readiness

**Purpose:** Determine whether one existing configured transport satisfies the Secretary-to-CoS controller-session boundary. This task is inspect-only.

**Task Function:** Runtime capability assessment and bounded pilot handoff.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded inspection and decision record; no implementation profile needed.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: inspect-only task; no transport validator needed.

**Specification Coverage:** Independent controller/session creation, repository/workstream ownership, activation idempotency and reconciliation, message identity/deduplication, reconnect/re-resolution, release, fail-closed unknown outcome, and no new Project OS persistence.

**Required Skills:** `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `docs/operating_system/tooling/runtime-tool-resolution.md`, `docs/operating_system/runtime/runtime-surfaces.md`, existing configured runtime transport entrypoints
- Modify: this plan's assessment evidence only; no transport implementation files
- Verify: configured capability facts and exact pilot handoff requirements

**Dependencies:** Task 5 complete.

**Authority:**
- Preauthorized local actions: inspect configured transport capability and update this plan with qualified or unavailable assessment evidence
- Stop for: required installation/authentication, external writes, guessed endpoint, or any request to implement transport behavior in this plan

**Steps:**
- [x] Inspect configured capabilities; identify whether one existing transport can provide every required boundary guarantee.
- [x] Record `NOT_AVAILABLE`: current configured runtime paths expose worker lifecycle transport/receipts and the in-process Secretary adapter fake, but no named live Secretary-to-CoS controller-session transport with atomic ownership claim, activation reconciliation, delivery deduplication, reconnect/re-resolution, release, and fail-closed unknown-outcome handling.
- [x] Defer pilot work; create separate pilot plan only after capability discovery names transport, owner, interfaces, receipt mechanism, dependencies, and test interface.
- [x] Do not add transport code, telemetry, scheduler behavior, persistence, installation, or authentication.

**Verification:**
- [x] Assessment evidence names every required capability and its current source or absence.
- Expected: Task 6 completes as `QUALIFIED` or `NOT_AVAILABLE`; neither outcome leaves a blocked task or speculative implementation.

**Exit Criteria:** Transport readiness is recorded as `QUALIFIED` with separate-plan handoff facts or `NOT_AVAILABLE` with deferred capability gap.

## Verification

- `py -3 scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-07-secretary-recommended-next-sequence-plan.md`
- `py -3 scripts/validate_template_required_sections.py --repo-root . --require-template-selection --document docs/superpowers/plans/2026-10-07-secretary-recommended-next-sequence-plan.md`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --scope preflight --plan docs/superpowers/plans/2026-10-07-secretary-recommended-next-sequence-plan.md`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --scope audit`
- `py -3 scripts/sync_agent_adapters.py --check`
- `py -3 -m pytest -q`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. Stage A fixes repository-scoped ownership, canonical event identity, set-like delta normalization, validator severity, and canonical wording.
2. End-to-end tests prove historical compatibility does not weaken consumed safety findings.
3. Canonical sources and generated adapter surfaces are synchronized.
4. Task 6 completes as a transport readiness assessment; a qualified result has exact handoff facts for a separate pilot plan, and an unavailable result records the deferred capability gap.
5. Paseo remains deferred and no preserved untracked artifact is changed or deleted.
6. Fresh final verification passes, plan deviations are recorded, and `skill-verification-before-completion` returns `verified` before status changes from `proposed`.
