---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: secretary-communication-convergence
targets:
  - docs/superpowers/plans/2026-10-07-15-48-secretary-communication-convergence-plan.md
  - docs/architecture.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - .agents/skills/skill-project-secretary/SKILL.md
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - scripts/project_os_runtime/secretary_adapter.py
  - scripts/project_os_runtime/secretary_events.py
  - scripts/validation_findings.py
  - scripts/validate_planning_lifecycle.py
  - scripts/validate_template_required_sections.py
  - scripts/benchmark_secretary_architecture.py
  - generated_agents/codex/skills/skill-project-secretary/SKILL.md
  - generated_agents/claude/skills/skill-project-secretary/SKILL.md
  - generated_agents/antigravity/skills/skill-project-secretary/SKILL.md
  - generated_agents/codex/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/claude/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md
  - tests/test_secretary_adapter.py
  - tests/test_secretary_events.py
  - tests/test_secretary_benchmark.py
  - tests/test_validation_findings.py
  - tests/test_validate_planning_lifecycle.py
  - tests/test_validate_template_required_sections.py
  - tests/test_validate_repo_contracts.py
  - tests/test_skill_project_secretary.py
  - tests/test_skill_chief_of_staff.py
---

# Secretary Communication Convergence Plan

## Verdict Review

The supplied verdict is accepted as direction, with one scope correction:
the next change must harden the existing Secretary, CoS, validator, and event
contracts without creating a transport, scheduler, database, cache service, or
new orchestration role.

### [P2] Split protocol hardening from future transport work

**Problem:** The verdict combines immediate binding and ordering defects with
future transport durability, validation caching, healthy-session reuse, and
production-surface reduction.

**Why it matters:** No production Secretary-to-CoS transport exists yet. Adding
unused transport or cache machinery would create a second source of workflow
truth before the reference contracts are stable.

**Evidence:** `scripts/project_os_runtime/secretary_adapter.py` contains only
`InMemoryControllerSessionAdapter`; `docs/operating_system/runtime/runtime-surfaces.md`
labels it a contract fake and reserves durable state for a future transport.

**Preserve:** Plan/Git remains workflow truth, the Docket remains unresolved
attention only, and runtime transport owns delivery receipts when a real
transport exists.

**Smallest safe correction:** Implement contract-level binding, envelope,
ordering, validation, and documentation changes only. Defer transport pilot,
ephemeral validation cache, healthy-session reuse, and fixture extraction.

### [P2] Make event ambiguity explicit

**Problem:** Removing lexical anchor ordering without defining the no-sequence
case leaves coalescing behavior under-specified.

**Why it matters:** Opaque anchors identify evidence but do not prove chronology;
silently selecting one can drop an unresolved obligation.

**Smallest safe correction:** Same-anchor hints merge. Hints with trustworthy
source-local sequences use sequence order. Different anchors without comparable
sequence remain separately actionable and reconcile conservatively.

### [P2] Classify findings by safety impact

**Problem:** Selected or consumed status alone cannot decide warning versus error.

**Why it matters:** Cosmetic legacy metadata should not block execution, while
authority, dependency, proof, workspace, integrity, and security findings must
remain blocking.

**Smallest safe correction:** Extend the existing shared finding classifier with
an explicit code matrix and warning-specific output. Do not suppress unsafe
findings because an artifact is historical.

## Goal

Make Secretary-to-CoS communication sparse, self-binding, and fail-closed
before any automated activation is attempted. Clarify ownership, make binding
validation reusable across lifecycle operations, preserve unresolved event
obligations when chronology is unknown, and make validator output match its
blocking semantics.

## Implementation Outcomes

- Architecture and canonical skills state that Secretary selects the workstream,
  CoS selects the next authorized action, and Workers select implementation
  details inside granted scope.
- Secretary-to-CoS messages separate stable controller binding from changing
  attention or coordination deltas and carry one common identity envelope.
- Activation reuse, resolve, resume, observe reconciliation, and delivery use
  one binding predicate covering repository, canonical work, workstream,
  branch, and base.
- Shared-journal adapter tests prove controller ownership and delivery replay
  across adapter recreation without claiming process-crash durability for the
  in-memory fake.
- Event coalescing never derives chronology from opaque anchors and preserves
  ambiguous conflicting events for reconciliation.
- Planning and template validators classify findings by semantic impact and
  print warning-only success distinctly from blocking failure.
- The deterministic contract harness defaults to one run from both its Python
  API and CLI.
- Canonical skill changes regenerate all selected adapter projections, and all
  focused plus repository-level verification passes.

## Non-Goals

- No Paseo integration, scheduler, background event loop, authentication, or
  production controller-session transport.
- No new Secretary database, persistent validation cache, runtime registry, or
  CoS-to-CoS conversational mesh.
- No Docket loader and no new Docket template.
- No Secretary-specific fields in plan or specification templates.
- No worker context expansion with portfolio priorities, sibling conversations,
  or full CoS history.
- No extraction of in-memory fixtures or benchmark removal until a real
  transport supplies measurable latency and wake-up evidence.

## Preserved Invariants

- Plan plus Git remains durable workflow truth.
- Secretary owns project-level unresolved attention and is the sole active
  Docket writer.
- CoS owns workstream binding, assignment, continuation, evidence
  reconciliation, and acceptance.
- Workers own implementation details, local retries, debugging, and task proof
  inside granted authority.
- Runtime and future transport own delivery, observation, deadlines, cleanup,
  and receipts; they do not decide engineering acceptance.
- Cross-workstream control routes through Secretary. Accepted evidence travels
  sideways; CoS instances do not form a conversational mesh.
- Current and unsafe evidence findings remain blocking.
- Generated adapter files remain derived outputs; canonical sources change
  first.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Expected branch: `main` (execution deviation: branch creation is not authorized)
- Expected base: `origin/main` at execution start
- Workspace: current repository checkout; preserve pre-existing untracked
  `.playwright-mcp/`, `db/`, and `temp_evidence.json`
- Coordination owner: one lead controller
- Executor: `codex`
- Required skills: `skill-code-standards`, `skill-backend-verification`,
  `skill-verification-before-completion`, `skill-requesting-code-review`
- Commit policy: no checkpoint commits; commit only after final verification
- Parallel ownership: none; adapter, events, validators, and canonical skills
  share contract names and must be serialized
- Sequential fallback: run Tasks 1-5 in listed order, then Task 6
- Stop for: production transport requirements, new persistent state, changed
  worker authority, a new Docket schema, or any finding that requires
  weakening current safety failures

## Coordination State

- Coordination schema: `2`
- Branch: `main`
- Base commit: `b8d7b38` (`origin/main` at plan review)
- Expected workspace: current checkout; preserve pre-existing untracked `.playwright-mcp/`, `db/`, and `temp_evidence.json`
- Next action: none — implementation and verification complete
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | canonical skill tests | 32 passed; ownership docs aligned |
| Task 2 | `completed` | current | `codex` | Task 1 | adapter binding, envelope, replay, and mismatch tests | 12 passed; shared journal replay proven |
| Task 3 | `completed` | current | `codex` | Task 1 | event ordering and ambiguity tests | 14 passed; ambiguous anchors preserved |
| Task 4 | `completed` | current | `codex` | none | validator severity, consumed-reference, and warning UX tests | 88 passed; warning/error headers verified |
| Task 5 | `completed` | current | `codex` | Tasks 2-4 | benchmark one-run contract tests and CLI output | 9 passed; CLI one-run proof passed |
| Task 6 | `completed` | current | `codex` | Task 1, Task 2, Task 3, Task 4, Task 5 | generated sync, full suite, audit, and diff checks | generated sync, validators, 928 passed / 1 skipped, diff check |

## Task Breakdown

### Task 1: Clarify ownership and sparse communication

**Purpose:** Remove Secretary/CoS overlap before changing runtime contracts.

**Task Function:**
- Canonical ownership and communication contract editing.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: low ambiguity, documentation-focused scope, and direct test coverage.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: repository validators provide sufficient proof.

**Specification Coverage:**
- Secretary, CoS, Worker, Plan/Git, and Docket ownership boundaries; sparse
  routing; no-mesh control; sole Docket writer.

**Required Skills:**
- `skill-code-standards`

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: modify named canonical architecture and skill files plus their focused tests.
- Stop for: new role, new workflow state, new Docket field, or changed Worker authority.

**Files And Symbols:**

- Modify `docs/architecture.md` ownership and Secretary sections.
- Modify `.agents/skills/skill-project-secretary/SKILL.md` authority,
  communication, and Docket sections.
- Modify `.agents/skills/skill-chief-of-staff/SKILL.md` workstream attention and
  escalation sections.
- Modify `tests/test_skill_project_secretary.py` and
  `tests/test_skill_chief_of_staff.py` assertions for ownership boundaries.

**Required contract:**

- Secretary selects which workstream needs attention.
- CoS selects the next authorized action inside that workstream.
- Workers select implementation details inside their assigned scope.
- Secretary routes bounded attention; the selected execution owner establishes
  the execution contract.
- Secretary-to-CoS, CoS-to-Worker, Worker-to-CoS, and CoS-to-Secretary remain
  the only logical exchanges.
- Local debugging, granted retries, authorized continuation, routine runtime
  activity, and accepted local work with no external consequence stay silent.
- Secretary is the sole active Docket writer; workflows produce evidence but do
  not write Docket state directly.

**Steps:**

- [x] Replace overlapping CoS “attention selection” wording with the exact
  three-layer ownership sentence.
- [x] Remove Secretary authority to issue a Worker task brief; describe
  Secretary output as bounded attention routing.
- [x] Add the sparse-exchange table and lowest-boundary escalation rule to the
  Secretary skill only.
- [x] Add the no-CoS-to-CoS-mesh rule and accepted-evidence routing rule.
- [x] Keep `docs/architecture.md` concise at system level and keep the CoS skill
  focused on workstream-local attention and escalation.
- [x] Add canonical skill tests for positive ownership and forbidden authority.

**Verification:**
- [x] `python -m pytest -q tests/test_skill_project_secretary.py tests/test_skill_chief_of_staff.py`
- Expected: ownership and forbidden-authority assertions pass.

**Exit Criteria:** Canonical docs and skills agree on ownership, Docket writing, and
communication boundaries; focused skill tests pass.

### Task 2: Add binding envelope and fail-closed controller lifecycle

**Purpose:** Make asynchronous messages self-binding and prevent wrong-repo,
wrong-work, wrong-branch, or wrong-base reuse and delivery.

**Task Function:**
- Backend contract hardening and direct lifecycle proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: high correctness risk, bounded file ownership, and direct
  success/failure tests.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: direct pytest assertions cover the contract.

**Specification Coverage:**
- Stable binding identity, communication-only envelope, distinct activation and
  message identity, shared binding predicate, replay safety, release semantics,
  and fail-closed mismatch behavior.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Dependencies:**
- Task 1 ownership vocabulary complete.

**Authority:**
- Preauthorized local actions: modify the named adapter module and adapter tests; extend only the existing in-memory journal protocol.
- Stop for: database, transport, scheduler, credential, or external-service changes.

**Files And Symbols:**

- Modify `scripts/project_os_runtime/secretary_adapter.py`:
  `ControllerBinding`, `AttentionDelta`, `CoordinationDelta`,
  `CommunicationEnvelope`, `ControllerRef`, `ControllerSessionAdapter`,
  `ControllerSessionJournal`,
  `InMemoryControllerSessionAdapter`, and fingerprint helpers.
- Modify `tests/test_secretary_adapter.py` for contract and restart cases.
- Modify `docs/operating_system/runtime/runtime-surfaces.md` adapter contract.

**Required contract:**

- Replace the mixed `AttentionBrief` identity/content shape with:
  - `ControllerBinding(repository_identity, canonical_work, workstream,
    expected_branch, expected_base)`;
  - `AttentionDelta(reason, constraint_refs, evidence_refs,
    decision_needed)`;
  - `CommunicationEnvelope(binding, message_id, canonical_anchor, payload)` where
    payload is an `AttentionDelta` or `CoordinationDelta`.
- Keep `CoordinationDelta` delta-shaped: kind, affected workstreams,
  evidence references, and decision-needed state; do not carry full execution
  narratives.
- Define `canonical_anchor` as the canonical evidence position against which a
  delta was produced. It is not message ordering, acceptance proof, controller
  ownership, or runtime lifecycle.
- Make `resolve(binding)` repository-aware and require all five binding fields.
- Use `activation_id` only for controller-creation idempotency and
  `message_id` only for communication delivery idempotency.
- Add one `matches_binding(controller, binding)` predicate and call it from
  activation reuse, resume, and delivery. `observe(controller)` validates
  controller identity and does not consume an attention payload.
- Binding mismatch returns `recovery_required=True` with no side effect.
- Same activation ID plus same binding reuses its activation receipt;
  changing attention does not change activation identity.
- Same message ID plus same controller/binding and payload fingerprint reuses
  its delivery receipt. Changed binding or payload returns
  `recovery_required=True`.
- Rename the expanded journal contract to `ControllerSessionJournal`; it owns
  only activation receipts, active controller ownership, delivery receipts,
  release state, and controller identity allocation. Keep it in-memory for the
  reference fake; do not claim process-crash durability or workflow truth.
- Derive the fake controller ID from the activation ID or retain it in the
  activation receipt; do not add a mutable counter solely for restart tests.
- Released controller receipts never restore active ownership. Unknown outcome
  fails closed and requires reconciliation.

**Steps:**

- [x] Define immutable binding, delta, and envelope value objects with
  normalized tuple fields.
- [x] Refactor controller references and receipt fingerprints to use the
  binding object rather than duplicated identity fields.
- [x] Change protocol and adapter operations to
  `resolve(binding)`, `activate(binding, activation_id)`,
  `resume(controller, binding)`, `observe(controller)`,
  `deliver(controller, envelope)`, and `release_session(controller)`.
- [x] Keep changing attention out of activation and resume inputs; pass
  communication envelopes only through delivery.
- [x] Rename and narrow the journal protocol, and retain controller ownership
  and delivery receipts across adapters sharing one journal.
- [x] Add mismatch tests for repository, canonical work, workstream, branch,
  and base across activation reuse, resolve, resume, and delivery.
- [x] Add adapter-recreation tests for controller reuse, delivery reuse,
  changed-payload recovery, release, deterministic identity, and reactivation.

**Verification:**
- [x] `python -m pytest -q tests/test_secretary_adapter.py`
- Expected: binding mismatch, replay, release, and adapter-recreation tests pass with zero duplicate side effects.

**Exit Criteria:** Every lifecycle operation uses the same binding predicate;
shared-journal restart tests prove no duplicate controller or delivery side
effects; no test claims durable storage for the in-memory implementation.

### Task 3: Remove opaque-anchor chronology from event coalescing

**Purpose:** Preserve unresolved obligations when event order cannot be proved.

**Task Function:**
- Event policy correction and deterministic reconciliation testing.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: isolated event module with a small, directly testable state
  policy.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused event tests cover all ordering branches.

**Specification Coverage:**
- Source-local sequence ordering, same-anchor merge, conflicting-anchor
  preservation, and conservative reconciliation.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: modify the named event module, benchmark scenarios, and event tests.
- Stop for: chronology derived from opaque anchors, evidence IDs, Git hashes, or receipt IDs.

**Files And Symbols:**

- Modify `scripts/project_os_runtime/secretary_events.py`: `_ordering`,
  `coalesce_event_hints`, and reconciliation helpers.
- Modify `tests/test_secretary_events.py` for sequence, duplicate, and
  ambiguity cases.
- Modify `scripts/benchmark_secretary_architecture.py` scenarios only when
  required to reflect the event contract.

**Required contract:**

- `observed_anchor` identifies canonical evidence; it never establishes
  chronology.
- `source_sequence` orders observations only within one source identity.
- Same source, event identity, and same anchor merge evidence references.
- Different anchors with comparable source sequences select the greatest
  source sequence and retain merged evidence references.
- Different anchors with equal, missing, or incomparable source sequences are
  ambiguous: preserve both observations and reconcile; no lexical winner is
  selected.
- Reconciliation returns `RECONCILE` when current evidence or controller state
  cannot prove discharge.
- Resolved or superseded source-scoped event identities return `NO_ACTION`.

**Steps:**

- [x] Replace tuple ordering that uses `observed_anchor` as a tie-breaker for
  chronology.
- [x] Add explicit same-anchor merge and conflicting-anchor preservation.
- [x] Add explicit equal-sequence and one-missing-sequence ambiguity handling.
- [x] Keep deterministic serialization ordering separate from semantic event
  precedence.
- [x] Add tests for `zz-old` versus `aa-new` without sequence, sequence-based
  ordering, equal-sequence conflicts, duplicate references, and unresolved old
  events.

**Verification:**
- [x] `python -m pytest -q tests/test_secretary_events.py`
- Expected: sequence ordering, ambiguity preservation, duplicate merge, and unresolved-event tests pass.

**Exit Criteria:** No event path derives chronology from Git hashes, receipt IDs, or
opaque evidence IDs; focused event tests pass.

### Task 4: Classify validation by impact and validate consumed references

**Purpose:** Reduce false blocking from cosmetic historical metadata while
preserving all safety-critical failures.

**Task Function:**
- Shared validator semantics and bound-preflight contract correction.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-validator ownership with existing fixture-driven
  regression coverage.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: validator tests exercise classification and exit status.

**Specification Coverage:**
- Impact-based severity, consumed-reference scope, warning UX, and continued
  blocking of unsafe current evidence.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Dependencies:**
- Existing `ValidationFinding` contract from PR #52.

**Authority:**
- Preauthorized local actions: modify the shared finding helper, planning/template validators, and named validator tests.
- Stop for: warning downgrade of authority, dependency, workspace, proof, path, integrity, or security findings.

**Files And Symbols:**

- Modify `scripts/validation_findings.py` severity classification and finding
  code matrix.
- Modify `scripts/validate_planning_lifecycle.py` bound-plan and consumed
  reference selection, reporting, and per-artifact error handling.
- Modify `scripts/validate_template_required_sections.py` finding selection and
  warning/error reporting.
- Modify `tests/test_validation_findings.py`,
  `tests/test_validate_planning_lifecycle.py`,
  `tests/test_validate_template_required_sections.py`, and
  `tests/test_validate_repo_contracts.py`.

**Required contract:**

- Keep one shared `ValidationFinding` model and stable finding codes.
- Classify obsolete headings, missing modern descriptive metadata with
  unambiguous meaning, and cosmetic selected historical issues as warnings.
- Classify ambiguous ownership, authority, executor, workspace, dependency,
  missing or contradictory acceptance evidence, unsafe paths, runtime,
  integrity, and security findings as errors.
- Selected or consumed status makes a finding relevant; it does not make every
  finding fatal.
- Bound preflight validates only existing structured references represented by
  the current schema: the selected plan, its declared `parent_spec` when
  present, task dependency IDs in the coordination ledger, and other typed
  references already modeled by validators. It does not parse arbitrary target
  paths or prose in `Required Proof`.
- A missing or malformed consumed reference remains an error. Unrelated
  historical artifacts do not block bound execution.
- Warning-only runs print `Planning validation passed with warnings:` or
  `Template required-sections validation passed with warnings:` and return `0`.
- Blocking runs print `failed` and return nonzero.
- One malformed historical artifact produces a finding and does not terminate
  scanning of unrelated artifacts.

**Steps:**

- [x] Split only mixed safety categories into granular codes such as
  `planning_frontmatter_malformed`, `planning_required_metadata_missing`,
  `planning_authority_invalid`, `planning_dependency_invalid`,
  `template_selection_legacy_missing`, and
  `template_required_section_missing`.
- [x] Replace status-only severity promotion with a code-and-context matrix in
  `validation_findings.py`; classification must not inspect message strings.
- [x] Limit bound-plan reference validation to the existing structured fields;
  preserve full discovery for audit mode.
- [x] Split warning and blocking report headers and retain stable machine
  readable finding codes.
- [x] Add fixture matrix covering historical cosmetic warnings, selected
  authority errors, missing consumed evidence, malformed archives, and warning
  exit status.

**Verification:**
- [x] `python -m pytest -q tests/test_validation_findings.py tests/test_validate_planning_lifecycle.py tests/test_validate_repo_contracts.py`
- Expected: severity matrix, consumed-reference scope, warning output, and
  repository audit tests pass.

**Exit Criteria:** Bound preflight blocks unsafe consumed evidence, ignores
unrelated historical cosmetics, reports warning-only success clearly, and
repository audit remains broader than preflight.

### Task 5: Narrow benchmark defaults and preserve contract evidence

**Purpose:** Keep the deterministic scenario harness honest and cheap.

**Task Function:**
- Contract-harness default correction and deterministic output proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one-file maintenance change with direct test coverage.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: benchmark tests validate deterministic output.

**Specification Coverage:**
- One-run default, explicit iteration support, and non-performance contract
  semantics.

**Required Skills:**
- `skill-code-standards`

**Dependencies:**
- Tasks 2-4 preserve scenario names and contract outcomes.

**Authority:**
- Preauthorized local actions: modify the benchmark default and named benchmark tests.
- Stop for: new performance claims, external telemetry, model calls, or transport dependencies.

**Files And Symbols:**

- Modify `scripts/benchmark_secretary_architecture.py`: CLI default and scenario
  descriptions.
- Modify `tests/test_secretary_benchmark.py` default and explicit-iteration
  assertions.

**Required contract:**

- `run_contract_benchmark()` and the CLI default to one iteration.
- Explicit positive iteration counts remain supported.
- Output remains deterministic JSON of contract metrics; it is not presented as
  latency or model-performance evidence.
- Existing scenarios cover binding conflicts, release replay, delivery payload
  conflicts, unresolved old events, stale sessions, and dependency changes.

**Steps:**

- [x] Change the CLI fallback from `20` to `1`.
- [x] Keep one-run correctness comparisons and failure classifications.
- [x] Add a test proving default output has one run per scenario and explicit
  iteration count still repeats deterministically.

**Verification:**
- [x] `python -m pytest -q tests/test_secretary_benchmark.py`
- Expected: default and explicit-iteration benchmark tests pass.
- [x] `python scripts/benchmark_secretary_architecture.py 1`
- Expected: one deterministic metric pair per scenario is emitted.

**Exit Criteria:** Benchmark tests pass and one CLI invocation emits one complete
deterministic contract run.

### Task 6: Regenerate projections and run final proof

**Purpose:** Reconcile canonical sources, generated adapters, validators, and
repository-level proof after all behavior changes.

**Task Function:**
- Generated-surface synchronization and final acceptance verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic repository commands and generated-output proof.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: repository validators and pytest provide independent proof.

**Specification Coverage:**
- Canonical-to-generated ownership, adapter drift, full regression coverage, and
  preserved unrelated workspace state.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-requesting-code-review`

**Dependencies:**
- Task 1, Task 2, Task 3, Task 4, Task 5 complete.

**Authority:**
- Preauthorized local actions: regenerate named adapter projections and run named local validators, tests, and diff inspections.
- Stop for: push, merge, cleanup, publication, generated drift outside named projections, or failed required proof.

**Files And Symbols:**

- Generated outputs selected by `scripts/sync_agent_adapters.py` for the two
  canonical skills.
- No direct edits to generated files.

**Steps:**

- [x] Run `python scripts/sync_agent_adapters.py --all-platforms`.
- [x] Run `python scripts/sync_agent_adapters.py --all-platforms --check`.
- [x] Run `python scripts/validate_generated_header_format.py --repo-root .`.
- [x] Run `python scripts/validate_repo_contracts.py --repo-root . --scope preflight --plan docs/superpowers/plans/2026-10-07-15-48-secretary-communication-convergence-plan.md`.
- [x] Run `python scripts/validate_repo_contracts.py --repo-root . --scope audit`.
- [x] Run `python scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-07-15-48-secretary-communication-convergence-plan.md`.
- [x] Run `python scripts/validate_template_required_sections.py --require-template-selection --document docs/superpowers/plans/2026-10-07-15-48-secretary-communication-convergence-plan.md`.
- [x] Run `python -m pytest -q tests/test_secretary_adapter.py tests/test_secretary_events.py tests/test_secretary_benchmark.py tests/test_validation_findings.py tests/test_validate_planning_lifecycle.py tests/test_validate_template_required_sections.py tests/test_validate_repo_contracts.py tests/test_skill_project_secretary.py tests/test_skill_chief_of_staff.py`.
- [x] Run `python -m pytest -q`.
- [x] Run `git diff --check` and inspect `git status --short` for named changes
  only; preserve `.playwright-mcp/`, `db/`, and `temp_evidence.json`.

**Verification:**
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: all selected adapter projections are up to date.
- [x] `python -m pytest -q`
- Expected: full suite passes with no new failures.

**Exit Criteria:** Canonical/generated projections agree, all validators and tests
pass, no generated header drift exists, and no unapproved files changed.

## Deferred Follow-Up

After this plan passes and a real Secretary-to-CoS transport exists, draft a
separate plan for:

- transport-owned durable activation and delivery receipts;
- content-keyed ephemeral validation reuse with current dirty-input and
  ownership facts refreshed before material operations;
- batching and coalescing nonurgent attention before model wake;
- validated healthy CoS session reuse as a disposable performance cache;
- moving in-memory adapter fixtures and the deterministic harness out of
  production surfaces once real transport metrics exist;
- one transport pilot measured against manual operation for input tokens,
  decision latency, model wakes, messages per workstream, duplicate effects,
  reconciliation rate, human interventions, and cold-start versus resume cost.

## Verification

- Task-local proof covers ownership wording, binding mismatch behavior, shared
  journal replay, event ambiguity, validator severity, warning output, and
  benchmark defaults.
- Backend contract proof covers success, mismatch, release, replay, changed
  payload, stale controller, and unknown-outcome paths through direct adapter
  calls and fresh pytest output.
- Repository proof covers planning, template, generated-header, runtime drift,
  configuration, and Starter Kit classification contracts.
- Generated projections are refreshed only after canonical skill edits.
- No deployment, migration, credential, transport, or external-service proof is
  required because those surfaces are explicit non-goals.

## Completion Criteria

The plan is ready for completion verification when:

1. Ownership, Docket, and sparse communication rules are aligned across
   canonical docs and generated skills.
2. Binding, envelope, replay, release, and event-ordering contracts pass their
   focused tests.
3. Bound preflight distinguishes warning-only historical metadata from blocking
   consumed safety findings.
4. Benchmark defaults and output semantics are deterministic.
5. Generated projections are synchronized and all final validators and tests
   pass.
6. Deferred transport, cache, session-reuse, and production-surface work is
   recorded separately and not mixed into this change.

## Rollback And Handoff

- Revert the implementation commit if binding or event contracts regress; do
  not restore lexical event ordering or weaken validation errors.
- Keep this plan `proposed` until `skill-executing-plans` records implementation
  progress and `skill-verification-before-completion` returns fresh `verified`
  evidence.
- A future executor recovers branch, base, task order, file ownership, proof
  commands, preserved untracked artifacts, and deferred scope from this plan
  plus Git.
