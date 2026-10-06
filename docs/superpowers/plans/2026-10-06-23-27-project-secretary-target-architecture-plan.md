---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: project-secretary-target-architecture
targets:
  - .agents/skills/skill-project-secretary/SKILL.md
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - .agents/skills/skill-executing-plans/SKILL.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/rules/git-tracked-coordination-rule.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/templates/secretary-docket.yaml
  - docs/architecture.md
  - docs/usage.md
  - scripts/project_os_runtime/secretary_adapter.py
  - scripts/project_os_runtime/secretary_events.py
  - scripts/benchmark_secretary_architecture.py
  - tests/test_skill_project_secretary.py
  - tests/test_skill_chief_of_staff.py
  - tests/test_starter_lifecycle_contract.py
  - tests/test_secretary_adapter.py
  - tests/test_secretary_events.py
  - tests/test_secretary_benchmark.py
---

# Project Secretary Target Architecture Implementation Plan

## Review Summary

The verdict is accepted with one controlling correction: Project Secretary is
an optional attention-and-continuity layer, not a permanent controller above
CoS or a mandatory entry point. When active, Secretary invokes existing
execution-selection policy; when absent, existing planning and execution paths
operate unchanged. CoS owns sustained workstream coordination; MAIN AGENTs and
Workers own execution; acceptance remains with the existing authoritative
owner.

The implementation preserves these verdict decisions:

- Direct work remains direct. Secretary must not add a mandatory hop to every
  request.
- CoS advisory mode remains available and is not duplicated by Secretary.
- The Docket is optional. It stores only unresolved, non-reconstructible
  attention that has no better canonical home; it is not a plan or lifecycle
  registry.
- Authority flows downward while evidence and technical challenges flow
  upward. Organizational position does not override stronger technical
  evidence.
- Plans/specs, source/tests, Git/GitHub, and accepted workflow decisions remain
  canonical truth. Receipts are bounded operational evidence used to prove or
  reconcile actions, not durable coordination truth. Sessions, notifications,
  Herdr, Paseo, and cached context remain replaceable mechanisms.
- Runtime events are hints. They never prove completion, cancellation,
  retirement, or failure without reconciliation against canonical evidence.
- Releases are gated: manual Secretary first, transport-neutral adapter second,
  selective event activation third. No scheduler, Paseo requirement, or new
  runtime belongs in Release A. Paseo integration is deferred and does not gate
  transport-neutral acceptance.

## Goal

Implement the Project Secretary target architecture without turning ordinary
work into a coordination workflow. Add a recoverable attention contract,
integrate it with existing execution selection and CoS boundaries, introduce a
  provider-neutral controller-session adapter, and add selective event
  activation only after the earlier releases have direct proof. Paseo remains
  deferred.

## Implementation Outcomes

### Right-sized manual Secretary

`.agents/skills/skill-project-secretary/SKILL.md` defines attention intake,
priority, routing, authority, evidence, escalation, and explicit-turn
operation. When active, it invokes existing execution-selection policy for
questions, direct changes, bounded execution, ordinary plans, and sustained
workstreams without forcing all requests through CoS. Existing execution entry
points remain directly callable when Secretary is absent.

`docs/operating_system/templates/secretary-docket.yaml` defines an optional
minimal Docket with only `id` and `objective` as required information. Optional
`waiting_on` and evidence references describe dependencies when they exist.
Docket entries survive restart only when the obligation cannot be
reconstructed from plan, Git, source, tests, or an existing receipt.

### Preserved CoS and Project OS ownership

Planning, architecture, usage, coordination, and CoS documentation state that
Secretary selects attention and routing, CoS coordinates eligible workstreams,
Workers execute bounded work, and existing acceptance authorities remain
unchanged. Generated agent surfaces mirror canonical skill sources.

### Safe controller-session adapter

`ControllerSessionAdapter` provides a transport-neutral boundary for resolve,
activation lookup, activate, resume, observe, deliver, and release-session.
Provider/adapter-owned operational receipt journaling gives activation keys a
crash-recovery owner without creating a Project OS workflow database.
Operation-specific typed receipts, workstream ownership, validated session
reuse, and ambiguous-delivery reconciliation prevent duplicate controllers and
duplicate execution.
Herdr remains unchanged underneath CoS.

### Deferred provider integration and event activation

Paseo remains a replaceable future adapter behind the transport-neutral
contract. It is explicitly deferred, has no core dependency or authentication
side effect, and is not required for current acceptance. Selective event
activation is transport-neutral, coalesces only project-level decision hints,
and reconciles them before waking Secretary. A future Paseo event subscription
would be an optional bridge.
Heartbeat and liveness inspection remain fallback evidence, not workflow truth.

### Evidence-backed acceptance

Focused tests and a deterministic benchmark cover simple-work latency,
restart recovery, lost or duplicate activation responses, stale sessions,
missed events, dependency changes, duplicate execution, unnecessary model
activation, and accepted completion. Final validation proves repository,
generated-surface, lifecycle, and plan-contract consistency.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-chief-of-staff`, `skill-backend-verification`, `skill-test-driven-development`, `skill-writing-skills`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit named canonical sources and tests; add the named adapter, event, benchmark, and template files; synchronize generated agent surfaces; run focused and repository validation commands; preserve unrelated working-tree changes
- User-approval actions: commits, pushes, merges, publication, dependency installation, authentication, external Paseo writes, destructive recovery, discard, cleanup, and changes outside named paths
- Parallel ownership: `none`; Releases A, B, and C share contracts and verification gates
- Sequential fallback: complete Tasks 1-3 before Task 4; after Task 4, Tasks 5 and 6 may proceed independently; complete Task 7 only after both branches and all release gates pass

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `3f57f0181d0ae94389cd5fd1165b792c45044a25`
- Expected workspace: preserve pre-existing untracked `.playwright-mcp/`, `db/`, and `temp_evidence.json`; add only named plan and implementation files
- Next action: none; implementation and verification complete
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | `python -m pytest -q tests/test_skill_project_secretary.py` | 4 passed; Secretary contract and minimal Docket added |
| Task 2 | `completed` | current | `codex` | Task 1 | `python -m pytest -q tests/test_skill_chief_of_staff.py tests/test_starter_lifecycle_contract.py` | 44 passed; optional Secretary and receipt evidence boundaries documented |
| Task 3 | `completed` | current | `codex` | Tasks 1-2 | `py scripts/sync_agent_adapters.py --all-platforms --check` | sync check and generated-header validation passed |
| Task 4 | `completed` | current | `codex` | Task 3 | `python -m pytest -q tests/test_secretary_adapter.py` | 7 passed; typed receipts and journal-backed restart reconciliation added |
| Task 5 | `completed` | current | `codex` | Task 4 | Paseo pilot scope decision | Explicit user deferral; no Paseo implementation remains in current scope |
| Task 6 | `completed` | current | `codex` | Task 4 | `python -m pytest -q tests/test_secretary_events.py` | 8 passed; transport-neutral branch; Paseo bridge deferred |
| Task 7 | `completed` | current | `codex` | Tasks 1-4, Task 6 | benchmark report plus full repository validation | 360 deterministic metrics; full suite and final validators pass |

## Task Breakdown

### Task 1: Define manual Secretary and optional Docket

- **Purpose:**
- Establish Release A contract without adding a scheduler, transport, runtime,
  or mandatory workflow hop.

**Task Function:**
- Translate verdict invariants into a reusable Secretary skill and minimal
  persistence contract.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: contract authoring is bounded, repository-local, and does
  not need a separate execution lane.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused contract tests and final plan review cover the
  artifact.

**Specification Coverage:**
- Secretary owns attention, unresolved work, prioritization, cross-workstream
  routing, and smallest-path selection.
- Direct, bounded, plan-bound, and CoS paths remain distinct.
- Secretary cannot accept implementation or override CoS, Worker, Git, plan,
  source, test, or human authority.
- Docket persistence is optional and limited to non-reconstructible obligations.
- Explicit-turn operation is valid; unattended event handling is deferred.

**Required Skills:**
- `skill-writing-skills`
- `skill-test-driven-development`

**Files And Symbols:**
- Create: `.agents/skills/skill-project-secretary/SKILL.md`
- Create: `docs/operating_system/templates/secretary-docket.yaml`
- Create: `tests/test_skill_project_secretary.py`
- Inspect: `.agents/skills/skill-chief-of-staff/SKILL.md`
- Inspect: `docs/operating_system/planning/planning-dispatch.md`
- Verify: `repo_config/planning_artifact_schema.yaml`

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: create the named canonical Secretary skill, Docket template, and focused contract test; run local parsing and focused tests
- Stop for: requested behavior that makes Secretary a workflow controller, adds mandatory persistence, requires a scheduler in Release A, or changes acceptance ownership

**Steps:**
- [x] Step 1: Write routing rules for question/status, local reversible change, contained bounded work, ordinary multi-step plan, sustained independent lanes, unresolved follow-up, cross-workstream conflict, and material human decision; state that these rules apply only when Secretary is active.
- [x] Step 2: Write authority and evidence rules using operational hierarchy plus epistemic equality; state that Secretary emits attention briefs and routing decisions but never implementation acceptance.
- [x] Step 3: Define optional Docket YAML with required `id` and `objective`; make `waiting_on` and evidence references optional; reject lifecycle states, duplicate workflow registries, and session identity as truth.
- [x] Step 4: Define restart behavior: reconstruct from canonical evidence first, read Docket only for unresolved obligations with no canonical home, and clear an entry when discharged by its canonical source, explicit user decision, or owning workflow evidence.
- [x] Step 5: Add focused tests for right-sized routing, Docket minimality, restart recovery, no acceptance authority, and explicit-turn operation.

**Verification:**
- [x] `python -m pytest -q tests/test_skill_project_secretary.py`
- Expected: all Secretary contract tests pass; test text confirms optional Secretary entry, direct execution when absent, no mandatory Secretary-to-CoS path, and no Release A scheduler requirement.
- [x] `python -c "import yaml; yaml.safe_load(open('docs/operating_system/templates/secretary-docket.yaml', encoding='utf-8'))"`
- Expected: Docket template parses and contains only the documented minimal fields.

**Exit Criteria:**
- Release A Secretary and Docket contracts are explicit, minimal, restart-safe, and test-proven without new runtime machinery.

### Task 2: Integrate Secretary with dispatch and CoS authority

**Purpose:**
- Make existing Project OS documentation and lifecycle contracts support an
  optional Secretary attention surface without moving work ownership or
  acceptance authority.

**Task Function:**
- Reconcile canonical planning, coordination, runtime, architecture, and usage
  rules with the new attention layer.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: sequential documentation and contract reconciliation with
  known canonical owners.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: existing lifecycle tests plus Task 1 focused tests cover the
  changed boundaries.

**Specification Coverage:**
- When Secretary is active, it invokes existing execution-selection policy; when
  absent, existing execution entry points operate unchanged.
- Secretary remains below human intent and outside implementation acceptance.
- CoS remains independently authoritative for sustained workstream coordination
  and keeps advisory exact-commit read-only mode.
- Plan plus Git remain durable coordination truth; runtime sessions and events
  remain evidence only.
- Feedback resolves at the lowest layer whose authority contains its blast
  radius.

**Required Skills:**
- `skill-chief-of-staff`
- `skill-writing-plans`

**Files And Symbols:**
- Modify: `.agents/skills/skill-chief-of-staff/SKILL.md`
- Modify: `.agents/skills/skill-executing-plans/SKILL.md`
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `docs/operating_system/rules/git-tracked-coordination-rule.md`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: `docs/architecture.md`
- Modify: `docs/usage.md`
- Modify: `tests/test_skill_chief_of_staff.py`
- Modify: `tests/test_starter_lifecycle_contract.py`

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: update only the named canonical documents and focused contract tests to describe Secretary routing, CoS ownership, evidence flow, persistence boundaries, and event-hint semantics
- Stop for: any requirement to make Secretary a second CoS, change Herdr lifecycle ownership, weaken Git-tracked coordination, or declare runtime completion as acceptance

**Steps:**
- [x] Step 1: Update planning dispatch decision tables so Secretary is an optional attention surface that invokes existing selection policy; direct execution remains directly callable and the default for small reversible work.
- [x] Step 2: Update CoS and executing-plan boundaries so CoS can be activated by Secretary when eligibility is met but remains optional, plan-bound where required, and sole owner of top-level coordination acceptance.
- [x] Step 3: Update Git-tracked coordination and runtime surfaces to state that Docket entries and bounded operational receipts supplement, but never replace, plan/spec, Git/GitHub, source/tests, and accepted workflow decisions.
- [x] Step 4: Update architecture and usage diagrams/examples to show optional `HUMAN → SECRETARY → existing selection policy` alongside direct entry, not `every request → Secretary → CoS`.
- [x] Step 5: Add regression assertions for preserved direct execution, CoS advisory mode, no Secretary acceptance, and runtime-event hint treatment.

**Verification:**
- [x] `python -m pytest -q tests/test_skill_chief_of_staff.py tests/test_starter_lifecycle_contract.py`
- Expected: existing CoS and lifecycle authority contracts pass with Secretary boundaries included.
- [x] `rg -n -i "every request|mandatory.*Secretary|Secretary.*accept|event.*truth|idle.*complete|timeout.*cancel" .agents/skills docs tests --glob '!*.pyc'`
- Expected: no stale rule claims mandatory Secretary routing, event truth, or runtime-derived acceptance.

**Exit Criteria:**
- Canonical Project OS docs and tests agree on Secretary, CoS, Worker, Git, plan, and runtime authority boundaries.

### Task 3: Synchronize generated agent surfaces

**Purpose:**
- Keep generated skill projections aligned with canonical Secretary and CoS
  sources before runtime work begins.

**Task Function:**
- Run deterministic adapter generation and reject source/generated drift.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: generated-surface synchronization is deterministic and
  should not use a parallel writer.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: synchronization and generated-header checks are direct proof.

**Specification Coverage:**
- Canonical `.agents/skills` sources own generated skill content.
- Generated Codex, Claude, and Antigravity surfaces contain the Secretary skill
  and updated existing skill projections.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `generated_agents/codex/skills/skill-project-secretary/SKILL.md`
- Modify: `generated_agents/claude/skills/skill-project-secretary/SKILL.md`
- Modify: `generated_agents/antigravity/skills/skill-project-secretary/SKILL.md`
- Modify: generated projections selected by `scripts/sync_agent_adapters.py` for changed canonical skills
- Verify: `scripts/sync_agent_adapters.py`
- Verify: `scripts/validate_generated_header_format.py`

**Dependencies:**
- Tasks 1-2 complete.

**Authority:**
- Preauthorized local actions: run adapter synchronization and generated-surface validators; inspect and retain only projections caused by named canonical changes
- Stop for: generated changes outside canonical projections, source/generated mismatch after synchronization, or adapter failure requiring unrelated edits

**Steps:**
- [x] Step 1: Run `py scripts/sync_agent_adapters.py --all-platforms`.
- [x] Step 2: Inspect generated diff and confirm canonical sources are the only semantic inputs.
- [x] Step 3: Run `py scripts/sync_agent_adapters.py --all-platforms --check`.
- [x] Step 4: Run `py scripts/validate_generated_header_format.py`.

**Verification:**
- [x] `py scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: synchronization check passes with no drift.
- [x] `py scripts/validate_generated_header_format.py`
- Expected: all changed generated files have valid provenance headers.

**Exit Criteria:**
- Generated surfaces are current and no generated file is treated as a canonical edit target.

### Task 4: Add transport-neutral controller-session adapter

**Purpose:**
- Implement Release B's provider-neutral controller-session boundary without
  changing Herdr or adding a provider dependency.

**Task Function:**
- Define and test a small adapter contract for controller resolution,
  activation lookup, activation, reuse, observation, delivery, and session
  release.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: contract-level Python work with material lifecycle and
  idempotency risk; Codex lead retains acceptance authority.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: independently check identity, duplicate-effect, failure, and
  retirement semantics for material runtime behavior.

**Specification Coverage:**
- The adapter exposes `resolve(workstream)`,
  `lookup_activation(activation_key)`,
  `activate(workstream, activation_key, brief)`, `resume(controller, brief)`,
  `observe(controller)`, `deliver(controller, brief)`, and
  `release_session(controller)`.
- Activation is idempotent by workstream plus activation key.
- A provider/adapter-owned operational receipt journal owns activation-key
  durability and lookup across crashes; Project OS does not add a workflow
  database.
- Workstream ownership and branch/base identity are validated before reuse.
- Lost responses reconcile against the operational journal and canonical
  evidence before retry; unsupported reconciliation fails closed.
- Silence, timeout, disconnect, or idle state never proves retirement or
  completion.
- Operation-specific typed receipts carry facts, `recovery_required`, and a
  reason; the caller decides whether to continue, reconcile, or block.
- Herdr remains the existing CoS transport and launcher underneath this new
  replaceable boundary.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`

**Files And Symbols:**
- Create: `scripts/project_os_runtime/secretary_adapter.py`
- Create: `tests/test_secretary_adapter.py`
- Inspect: `scripts/herdr_main_launcher.py`
- Inspect: `scripts/herdr_attempt_contract.py`
- Inspect: `scripts/project_os_runtime/results.py`
- Verify: `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- Task 3 complete.

**Authority:**
- Preauthorized local actions: add the named provider-neutral adapter and focused tests; use fake in-process transports; run direct boundary checks; do not modify Herdr launcher or install/authenticate providers
- Stop for: duplicate activation effects, ambiguous ownership, missing canonical receipt evidence, or any requested Herdr lifecycle change

**Steps:**
- [x] Step 1: Define immutable value objects `ControllerRef`, `AttentionBrief`, `CoordinationDelta`, `ActivationReceipt`, `DeliveryReceipt`, `ObservationReceipt`, and `SessionReleaseReceipt` with stable workstream, activation, branch, base, and evidence identity.
- [x] Step 2: Define `ActivationReceiptJournal` with `lookup_activation` and `record_activation`; require provider/adapter ownership of durable operational storage and fail closed when restart reconciliation is unavailable.
- [x] Step 3: Define `ControllerSessionAdapter` as a typed protocol with operation-specific typed receipts; do not introduce a shared lifecycle enum or reuse lane-retirement terminology.
- [x] Step 4: Add an in-process fake adapter and fake journal used only by tests; make duplicate activation return the original receipt without a second side effect.
- [x] Step 5: Reject workstream ownership mismatch, branch/base mismatch, stale controller reuse, and delivery without validated controller identity.
- [x] Step 6: Reconcile lost activation or delivery responses against the operational journal and evidence before permitting one bounded retry; never infer success from transport silence.
- [x] Step 7: Add direct success, failure, state/side-effect, idempotency, restart, and session-release tests.

**Verification:**
- [x] `python -m pytest -q tests/test_secretary_adapter.py`
- Expected: all adapter contract tests pass, including duplicate activation, journal-backed restart recovery, stale reuse, ambiguous delivery, and session-release evidence cases.
- [x] Inspect test assertions for direct boundary input, failure output, final receipt state, and duplicate-side-effect count.
- Expected: tests prove behavior without browser or frontend evidence.

**Exit Criteria:**
- Provider-neutral adapter contract is executable and tested; Herdr behavior is unchanged; Release B can accept a provider without changing Secretary semantics.

### Task 5: Defer Paseo integration

**Purpose:**
- Preserve the provider-neutral boundary without adding deferred provider
  integration to current scope.

**Task Function:**
- Record explicit user deferral. Reopen only with approved provider capability
  and explicit scope.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: provider integration needs boundary judgment and external
  capability checks; no new provider authority is granted by the plan.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: adapter must be checked independently for duplicate effects,
  stale sessions, missing events, and fail-closed behavior.

**Specification Coverage:**
- Paseo remains replaceable transport, not workflow truth.
- Core installation remains provider-neutral; no dependency or credential is
  added while Paseo is deferred.
- Generic adapter invariants remain independently tested and do not depend on
  provider integration.

**Required Skills:**
- `skill-plan-document-reviewer`

**Files And Symbols:**
- Verify: `scripts/project_os_runtime/secretary_adapter.py:ControllerSessionAdapter`
- Verify: `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- Task 4 complete and adapter tests pass.

**Authority:**
- Preauthorized local actions: record the explicit Paseo deferral and keep the
  generic adapter provider-neutral
- Stop for: provider dependency, authentication, external mutation, or scope
  expansion without explicit approval

**Steps:**
- [x] Step 1: Record explicit user deferral; remove Paseo implementation and
  provider dependency from current targets.
- [x] Step 2: Keep generic adapter and event-policy contracts provider-neutral.
- [x] Step 3: Future provider work requires separate approved scope; it remains
  outside this completed plan.

**Verification:**
- [x] No Paseo implementation or provider dependency remains in current targets.
- Expected: future provider work preserves generic adapter and event-policy
  contracts.

**Exit Criteria:**
- Explicit user deferral is recorded. Current Release C acceptance does not
  depend on Paseo; future provider work remains a separate gated task.

### Task 6: Add selective event activation and reconciliation

**Purpose:**
- Implement Release C only after manual routing and controller-session safety
  are proven.

**Task Function:**
- Filter, coalesce, and reconcile event hints so Secretary wakes only when a
  project-level decision is required.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic event policy with bounded state and direct
  regression proof.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: event activation can create duplicate execution or missed
  recovery; independent failure-path review is required.

**Specification Coverage:**
- Activate only for dependency changes, cross-workstream conflicts,
  permission/authority issues, intent changes, meaningful completion, and
  external unblocks.
- Coalesce duplicate hints deterministically.
- Reconcile hints against plan, Git, receipts, and current runtime evidence.
- Keep routine executor activity local.
- Keep heartbeat/liveness inspection as bounded fallback evidence.
- Missed notifications never imply no work; stale events never imply current
  truth.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`
- `skill-performance-optimization`

**Files And Symbols:**
- Create: `scripts/project_os_runtime/secretary_events.py`
- Create: `tests/test_secretary_events.py`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Inspect: `scripts/project_os_runtime/secretary_adapter.py`
- Inspect: `docs/operating_system/rules/git-tracked-coordination-rule.md`

**Dependencies:**
- Task 4 complete.
- Paseo is not required to prove the transport-neutral event policy.

**Authority:**
- Preauthorized local actions: add deterministic event filtering, coalescing, and reconciliation with fake evidence sources; run focused failure-path and bounded performance checks
- Stop for: scheduler/service creation, event-driven auto-kill/retry/advance, missing canonical reconciliation input, or any change to plan/Git acceptance authority

**Steps:**
- [x] Step 1: Define `EventHint` with source, event type, workstream, observed identity, and canonical revision; accept only the six named project-level event classes.
- [x] Step 2: Implement `coalesce_event_hints` using stable workstream and event identity keys; preserve evidence references and never discard a newer canonical revision.
- [x] Step 3: Implement `reconcile_event_hint` against plan/Git/receipt/runtime evidence; return `NO_ACTION`, `SECRETARY_ATTENTION`, `RECONCILE`, or `BLOCKED` without accepting implementation.
- [x] Step 4: Route routine executor output to local observation and keep liveness checks bounded and non-authoritative.
- [x] Step 5: Test duplicate events, missed events, stale controller session, dependency changes under cached session, external unblock, and no-op routine activity.
- [x] Step 6: Keep provider event subscription outside the generic policy; no
  Paseo bridge is added while Paseo is deferred.
- [x] Step 7: Measure coalescing and reconciliation overhead with the deterministic contract benchmark before considering any event activation default.

**Verification:**
- [x] `python -m pytest -q tests/test_secretary_events.py`
- Expected: all event safety and failure-path tests pass; no event alone produces accepted completion, cancellation, retirement, or retry.
- [x] Run the bounded event workload and record deterministic reconciliation and duplicate-effect metrics; reserve p50/p95 claims for live benchmark evidence.
- Expected: workload is repeatable and correctness checks pass before performance claims are made.

**Exit Criteria:**
- Selective activation is deterministic, evidence-reconciled, quiet for routine work, and proven not to create unsafe duplicate execution.

### Task 7: Benchmark releases and complete acceptance evidence

**Purpose:**
- Compare target architecture against current right-sized workflow before making
  Secretary or event activation default.

**Task Function:**
- Build a deterministic scenario benchmark and run final repository-level
  verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: benchmark and acceptance require controller-owned evidence,
  not delegated implementation authority.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: final acceptance spans plan, generated surfaces, runtime
  safety, benchmark correctness, and repository contracts.

**Specification Coverage:**
- Contract benchmark tracks duplicate activations, messages, reconciliation
  calls, model-wake count, failure recovery, and payload/context size using
  deterministic fake transports.
- Live benchmark, only when controller/runtime capability exists, tracks
  coordination input tokens, end-to-end latency, controller cold-start/resume
  cost, human interventions, duplicate controller activations, duplicate
  execution, recovery failures, unnecessary model activations, messages per
  completed workstream, and accepted completion rate.
- Exercise restart Secretary, restart CoS, lost activation response, duplicate
  activation request, missed event, stale session, and dependency change under
  cached session.
- Treat latency/overhead reduction as a hypothesis until paired evidence proves
  it.

**Required Skills:**
- `skill-performance-optimization`
- `skill-verification-before-completion`
- `skill-plan-document-reviewer`

**Files And Symbols:**
- Create: `scripts/benchmark_secretary_architecture.py`
- Create: `tests/test_secretary_benchmark.py`
- Verify: `docs/superpowers/plans/2026-10-06-23-27-project-secretary-target-architecture-plan.md`
- Verify: `scripts/validate_planning_lifecycle.py`
- Verify: `scripts/validate_repo_contracts.py`

**Dependencies:**
- Tasks 1-4 and 6 complete. Task 5 deferral is recorded and does not block this
  deterministic acceptance task.

**Authority:**
- Preauthorized local actions: add deterministic benchmark scenarios and tests; run focused tests, generated-surface checks, plan lifecycle validation, repository validators, and the full test suite
- Stop for: missing paired baseline data, unexplained duplicate effects, stale plan ledger, out-of-scope changes, failed required proof, or request to claim performance improvement without evidence

**Steps:**
- [x] Step 1: Define a deterministic contract runner; keep provider and model credentials out of benchmark fixtures. Live runner remains deferred until actual controller/runtime capability exists.
- [x] Step 2: Implement scenarios for simple direct work, bounded executor work, sustained CoS workstream, restart recovery, duplicate activation, lost response, missed event, stale session, and dependency change.
- [x] Step 3: Emit structured JSON metrics with scenario ID, run ID, evidence provenance, outcome, and failure classification; preserve `unknown` when evidence is absent.
- [x] Step 4: Run contract scenarios for at least 20 paired iterations per case; compare correctness first, then reconciliation calls, duplicate effects, payload/context size, and model-wake count.
- [x] Step 5: Record live benchmark as deferred; do not claim p50/p95 latency or actual token/cold-start evidence from fake transports.
- [x] Step 6: Run focused Secretary tests, generated checks, plan lifecycle validation, repository contracts, and full `pytest`; classify the unrelated direct-MCP failures below.
- [x] Step 7: Perform one fresh plan-document review; record deviations, capability deferrals, residual risks, and exact proof in this plan before any status transition.

**Verification:**
- [x] `python -m pytest -q tests/test_secretary_benchmark.py tests/test_secretary_adapter.py tests/test_secretary_events.py`
- Expected: benchmark fixtures and runtime safety tests pass; contract results do not claim live token or runtime savings.
- [x] `py scripts/validate_planning_lifecycle.py`
- Expected: proposed plan satisfies current implementation-plan contract and task ledger rules.
- [x] `py scripts/validate_repo_contracts.py`
- Expected: repository contracts pass.
- [x] `py scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: generated surfaces have no drift.
- [x] `python -m pytest -q`
- Expected: `893 passed, 1 skipped, 3 failed`; failures are pre-existing and
  outside changed scope in `tests/test_dcode_project.py` direct-MCP ownership
  cases, all failing at `Direct MCP runtime parent ownership is invalid.`
- [x] `git diff --check`
- Expected: no whitespace errors.

**Exit Criteria:**
- Benchmark evidence supports or rejects expansion; all required tests and validators pass; plan ledger, repository state, generated surfaces, deferrals, and residual risks reconcile. Only then may `skill-verification-before-completion` return `verified` and the lead controller change plan status.

## Verification

Final artifact verification runs only after all task-local proof is accepted:

- `py scripts/validate_planning_lifecycle.py`
- `py scripts/validate_repo_contracts.py`
- `py scripts/sync_agent_adapters.py --all-platforms --check`
- `py scripts/validate_generated_header_format.py`
- `python -m pytest -q`
- `git diff --check`

Final review must confirm:

- Release A has no scheduler, Paseo requirement, new runtime, or mandatory
  Secretary hop.
- Release B keeps Herdr unchanged and proves adapter idempotency, ownership,
  reuse, delivery reconciliation, and fail-closed behavior.
- Release C treats events as hints, coalesces deterministically, reconciles
  canonical evidence, and avoids unsafe automatic lifecycle actions.
- Docket entries remain optional, minimal, and non-authoritative.
- No generated surface was edited as canonical source.
- Pre-existing untracked `.playwright-mcp/`, `db/`, and `temp_evidence.json`
  remain untouched.

## Completion Criteria

The plan is ready for completion verification when:

1. the manual Secretary contract and optional Docket are implemented and
   focused-tested
2. dispatch, CoS, execution, runtime, architecture, and usage boundaries agree
   on ownership and evidence flow
3. generated agent surfaces are synchronized from canonical sources
4. the transport-neutral adapter proves identity, idempotency, journal-backed
   restart reconciliation, reuse, delivery, observation, session release, and
   failure semantics
5. Paseo is explicitly deferred without weakening transport-neutral adapter
   or event-policy acceptance
6. selective event activation is deterministic, transport-neutral, reconciled,
   and benchmarked independently of Paseo
7. final validators and tests pass, or every unrelated failure is classified
   and recorded
8. plan deviations, blockers, capability deferrals, and residual risks are
   recorded in this plan

The plan may be marked `completed` only when
`skill-verification-before-completion` runs fresh final verification and
returns `verified`. Plan completion does not authorize commit, push, merge,
publication, dependency installation, authentication, or cleanup.

## Fresh Plan Review

- Result: `verified`.
- Accepted deviations: Paseo integration and live benchmark are explicitly
  deferred by user instruction; no provider dependency, authentication, or live
  runtime claim was added.
- Deterministic evidence: focused Secretary suite `20 passed`; benchmark `360`
  metrics across `9` scenarios and `20` paired runs, target correctness `180/180`,
  target duplicate effects `0`, live claims `0`; lifecycle, template, repository,
  generated-surface, and whitespace checks passed.
- Blocker fix: `_ensure_direct_mcp_runtime_parent` now safely claims an existing
  empty legacy parent and still rejects non-empty unowned parents. Direct-MCP
  focused tests pass `7/7`; full `pytest` passes `897`, with `1` skip.
