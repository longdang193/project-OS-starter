---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: secretary-safety-and-validation-follow-up
targets:
  - docs/superpowers/plans/2026-10-06-00-40-secretary-safety-and-validation-follow-up-plan.md
  - docs/architecture.md
  - repo_config/starter-kit-manifest.json
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - .agents/skills/skill-project-secretary/SKILL.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/templates/secretary-docket.yaml
  - scripts/validation_findings.py
  - scripts/validate_planning_lifecycle.py
  - scripts/validate_template_required_sections.py
  - scripts/validate_repo_contracts.py
  - scripts/project_os_runtime/secretary_adapter.py
  - scripts/project_os_runtime/secretary_events.py
  - scripts/benchmark_secretary_architecture.py
  - generated_agents/codex/skills/skill-project-secretary/SKILL.md
  - generated_agents/claude/skills/skill-project-secretary/SKILL.md
  - generated_agents/antigravity/skills/skill-project-secretary/SKILL.md
  - generated_agents/codex/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/claude/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md
  - tests/test_validation_findings.py
  - tests/test_validate_planning_lifecycle.py
  - tests/test_validate_template_required_sections.py
  - tests/test_validate_repo_contracts.py
  - tests/test_secretary_docket.py
  - tests/test_skill_project_secretary.py
  - tests/test_skill_chief_of_staff.py
  - tests/test_secretary_adapter.py
  - tests/test_secretary_events.py
  - tests/test_secretary_benchmark.py
  - tests/test_starter_kit_generation.py
---

# Secretary Safety And Validation Follow-Up Plan

## Verdict Review

Verdict is accepted with one scope correction: this follow-up hardens the
manual Secretary contract and the evidence gates required before automated
activation. It does not add Paseo, a scheduler, a production transport, a new
workflow database, or Secretary fields to plan/spec templates.

The verdict's findings are justified and patched before execution:

- PR #51's Docket template is reused, not replaced. Its example must not create
  a fictitious obligation when copied, and actual Docket loading needs structural
  validation outside Markdown plan validation.
- Validation currently treats every finding as fatal. Severity must distinguish
  harmless historical metadata from failures that can make selected execution
  unsafe. Historical status alone must not suppress authority, dependency,
  workspace, proof, path, data-integrity, or security failures.
- `--fast` currently does not reduce `build_subprocess_steps()`. CoS needs a
  scoped preflight for the bound plan and relevant runtime contracts, while the
  repository audit may continue reporting broader maintenance findings.
- The in-memory adapter needs explicit ownership, request-fingerprint, release,
  and delivery semantics before any automated activation is considered safe.
  Its tests must not claim process-crash durability that only a transport-owned
  durable receipt journal can provide.
- Event suppression must use current evidence of resolution or supersession.
  A newer revision alone does not discharge an older unresolved obligation.
  Coalescing must preserve evidence references and define source-scoped identity.
- The benchmark is a deterministic contract scenario suite, not a performance
  study. Repeated identical runs add no evidence; changed inputs and failure
  probes have higher value.
- The Docket stays in execution-facing storage, and its loader remains deferred
  until a real Docket or automated consumer exists.
- Preflight scopes both planning and template validation to the bound plan and
  keeps repository runtime/security invariants blocking without migrating the
  entire validator stack.

## Goal

Make validation severity-aware and execution-scoped, then close the adapter and
event-policy safety gaps identified after PR #51. Preserve ordinary manual
Secretary use while keeping automated activation gated on stronger evidence.

## Implementation Outcomes

### Severity-aware, scoped validation

Validation exposes stable warning/error findings, and CoS preflight checks only
the bound plan plus applicable runtime contracts while repository audit remains
explicitly broader.

### Safe Secretary contracts

The existing Docket template, adapter, event policy, benchmark, and generated
skill projections enforce the reviewed safety invariants with focused tests and
fresh repository-level proof.

## Non-Goals

- No Paseo integration, authentication, scheduler, background event loop, or
  production controller transport.
- No new Docket template and no actual project Docket file until a real
  unresolved obligation requires persistence.
- No Secretary-specific fields in implementation-plan or specification
  templates.
- No bulk migration or rewriting of historical plans.
- No claim of latency, token, cold-start, or reliability improvement from fake
  transports.
- No replacement of plan, source, tests, Git/GitHub, or accepted workflow
  decisions as canonical truth.

## Target Contracts

### Severity and scope

Planning and template findings carry a stable code, explicit `warning` or
`error` severity, path, and message. Warning-only scans return success. Errors
return nonzero and block the affected operation. Historical metadata warnings
do not grant an exemption to unsafe selected work. Repository runtime/security
invariants keep their existing blocking `ValidationIssue` contract.

The existing `validate_repo_contracts.py` command exposes only `preflight` and
`audit` scopes. Default scope is `audit`; `--fast` aliases `preflight`, and
`--fast --scope audit` is rejected. Preflight validates the supplied bound plan,
its template contract, agent-profile/configuration/runtime ownership and
security boundaries needed for dispatch. Audit retains repository-wide
maintenance checks. CoS consumes blocking findings, not human-readable string
matching.

### Docket

`docs/operating_system/templates/secretary-docket.yaml` remains the only
template. Its parsed value is an empty list; the illustrative entry is comment
text. If a real project Docket becomes necessary, its execution-facing path is
`docs/superpowers/secretary-docket.yaml`, created only when the first obligation
cannot be reconstructed from canonical evidence. Project Secretary is the one
active writer. Owning workflows provide discharge evidence; they do not copy
workflow state into the Docket. Discharged entries are removed by Secretary
after canonical evidence, an explicit user decision, or owning workflow
evidence proves discharge. This PR adds structural template tests only; a
production loader waits for a real Docket or automated machine-readable
consumer.

### Adapter and event safety

The in-process adapter remains a contract fake. It must enforce one active
controller owner per `(repository_identity, workstream_identity)`, bind an
activation key to a normalized request fingerprint containing repository,
canonical work, expected branch, expected base, objective, and evidence refs,
preserve historical receipts without restoring released active ownership, and
make delivery idempotent by delivery identity plus controller and payload
fingerprint. Branch and base are caller-supplied activation inputs. Process-
crash durability remains a future transport obligation, not a claim of the
in-memory journal.

Event identity is source-scoped. Coalescing merges evidence references and
keeps the newest observation according to source ordering. `observed_anchor`
identifies canonical evidence; optional `source_sequence` orders observations.
Older events remain actionable unless current evidence explicitly marks their
identity resolved or superseded. Event decisions remain separate from
acceptance, retirement, retry, and task state.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-code-standards`, `skill-backend-verification`, `skill-test-driven-development`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: current workspace; create a `codex/` branch before execution
- Commit policy: no commits during implementation; finish through a separate
  approved PR disposition
- Preauthorized local actions: modify named canonical sources and tests,
  synchronize generated Secretary and CoS projections, update starter-kit
  manifest/generation proof and architecture/runtime docs, and run named
  validators and tests
- User-approval actions: dependency installation, authentication, Paseo work,
  commits, pushes, PR creation, merge, cleanup, and changes outside targets
- Parallel ownership: none; shared finding and runtime contracts require one
  controller
- Sequential fallback: complete Task 1 before Task 3; Tasks 2, 4, and 5 are
  independent; complete Tasks 3-5 before Task 6; complete Task 7 only after
  all focused proof passes

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/secretary-safety-and-validation-follow-up`
- Base commit: `0f18b263e62548b42356fba16a0fe699f44cdc10`
- Expected workspace: preserve pre-existing untracked `.playwright-mcp/`, `db/`,
  and `temp_evidence.json`; add only named plan and implementation files
- Next action: Task 1 — define shared severity and finding contract
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | validation finding tests | `tests/test_validation_findings.py`; 54 validator tests pass |
| Task 2 | `completed` | current | `codex` | none | Docket template and skill contract tests | `tests/test_secretary_docket.py`; 7 Docket/skill tests pass |
| Task 3 | `completed` | current | `codex` | Task 1 | scoped preflight/audit tests | 104 validator/CoS tests pass; bound preflight passes |
| Task 4 | `completed` | current | `codex` | none | adapter invariant tests | 11 adapter tests pass |
| Task 5 | `completed` | current | `codex` | none | event relevance tests | 11 event tests pass |
| Task 6 | `completed` | current | `codex` | Task 3, Task 4, Task 5 | deterministic contract scenarios | 9 benchmark tests pass; one-run JSON verified |
| Task 7 | `completed` | current | `codex` | Task 6 | final validators and full suite | 918 passed, 1 skipped; validators, generated checks, audit, and diff check pass |

## Task Breakdown

### Task 1: Introduce severity-aware validation findings

**Purpose:**
- Make warning-only historical metadata non-blocking without weakening current
  authoring, execution, proof, path, data-integrity, or security checks.

**Task Function:**
- Create one shared finding model and classification helper used by planning
  and template validators.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: narrow shared validation contract with direct tests.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: severity behavior is directly fixture-tested.

**Specification Coverage:**
- Stable finding code and explicit severity for planning/template findings only.
- Warning-only scans return success.
- Historical missing metadata warns; selected unsafe work blocks.
- One malformed archive does not terminate unrelated repository scanning.
- New and active artifacts retain current authoring requirements.

**Files And Symbols:**
- Create: `scripts/validation_findings.py`
- Modify: `scripts/validate_planning_lifecycle.py`
- Modify: `scripts/validate_template_required_sections.py`
- Create: `tests/test_validation_findings.py`
- Modify: `tests/test_validate_planning_lifecycle.py`
- Modify: `tests/test_validate_template_required_sections.py`

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: add the shared finding contract and focused
  fixtures; preserve current blocking semantics for unsafe active work
- Stop for: any proposal to silence authority, dependency, workspace, accepted
  proof, path, data-integrity, or security findings

**Steps:**
- [x] Step 1: Define `ValidationFinding` with stable `code`, `severity`, `path`,
  and `message`, plus one `has_blocking_findings()` helper.
- [x] Step 2: Replace duplicate validator finding models with the shared model;
  keep human-readable output stable enough for existing consumers.
- [x] Step 3: Classify by stable code plus context: unrelated historical
  metadata and malformed historical archives warn; selected-plan parse failure,
  ambiguity, invalid dependencies, missing authority, unsafe paths,
  contradictory proof, and malformed operational data error.
- [x] Step 4: Catch parse failures per discovered document, emit a finding for
  that document, and continue scanning unrelated documents.
- [x] Step 5: Add fixtures proving completed legacy metadata warns and exits zero,
  active metadata errors exit nonzero, and unsafe findings remain blocking even
  when the artifact is marked completed.

**Verification:**
- [x] `python -m pytest -q tests/test_validation_findings.py tests/test_validate_planning_lifecycle.py tests/test_validate_template_required_sections.py`
- Expected: warning/error classification, continuation, and current authoring
  rules pass.
- [x] `py scripts/validate_planning_lifecycle.py`
- Expected: current repository plan findings are clean or explicitly classified.

**Exit Criteria:**
- Planning and template validators share severity semantics and warning-only
  historical findings no longer block unrelated work.

### Task 2: Reuse and validate the optional Docket contract

**Purpose:**
- Clarify project-local Docket ownership without creating another workflow
  registry or changing plan templates.

**Task Function:**
- Update the existing template and Secretary skill, then add structural tests
  for the template contract. Defer a production loader until a real Docket or
  automated machine-readable consumer exists.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one canonical template and one skill contract.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: direct shape and ownership tests.

**Specification Coverage:**
- Template parses as an empty list with comments-only illustration.
- Actual project-local path, sole writer, and discharge rule are explicit.
- The documented entry shape is testable without creating a live Docket.
- No Docket is created until persistence is needed.

**Files And Symbols:**
- Modify: `docs/operating_system/templates/secretary-docket.yaml`
- Modify: `.agents/skills/skill-project-secretary/SKILL.md`
- Create: `tests/test_secretary_docket.py`
- Modify: `tests/test_skill_project_secretary.py`

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: update the existing template/skill and add
  structural template tests
- Stop for: mandatory Docket fields beyond `id` and `objective`, duplicated
  lifecycle state, automatic Docket creation, or a second persistence registry

**Steps:**
- [x] Step 1: Change the template's parsed value to `[]`; retain the example only
  in YAML comments and label it illustrative.
- [x] Step 2: Document `docs/superpowers/secretary-docket.yaml` as project-local
  location, Project Secretary as sole active writer, and canonical-evidence,
  user-decision, or owning-workflow discharge as removal authority.
- [x] Step 3: Replace literal template assertions with shape assertions: list
  root, comments-only illustration, and documented optional references.
- [x] Step 4: Keep the loader out of this PR; record its activation condition in
  the plan and skill contract.
- [x] Step 5: Test that no actual project Docket is created by template parsing.

**Verification:**
- [x] `python -m pytest -q tests/test_secretary_docket.py tests/test_skill_project_secretary.py`
- Expected: template, ownership, and discharge contracts pass without runtime
  loader machinery.
- [x] `python -c "import yaml; assert yaml.safe_load(open('docs/operating_system/templates/secretary-docket.yaml', encoding='utf-8')) == []"`
- Expected: existing template parses to an empty list.

**Exit Criteria:**
- Docket usage is explicit, minimal, structurally validated, and still optional.

### Task 3: Separate CoS preflight from repository audit

**Purpose:**
- Let CoS block only applicable safety/correctness failures while repository
  hygiene still reports unrelated historical maintenance warnings.

**Task Function:**
- Add bound-plan selection and explicit validation scopes through the existing
  `validate_repo_contracts.py` command.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: existing validator orchestration and CoS command contract.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: preflight scope controls dispatch safety.

**Specification Coverage:**
- `--scope preflight` validates the supplied bound plan and applicable runtime
  contracts only, including both planning and template checks for that plan.
- `--scope audit` scans repository-wide maintenance surfaces.
- `--fast` remains a compatibility alias for preflight and does not silently run
  the full audit.
- `--fast --scope audit` is rejected as conflicting input.
- Warning-only results return success; blocking errors return nonzero.
- CoS passes the bound plan and blocks only on blocking findings.

**Files And Symbols:**
- Modify: `scripts/validate_planning_lifecycle.py`
- Modify: `scripts/validate_template_required_sections.py`
- Modify: `scripts/validate_repo_contracts.py`
- Modify: `.agents/skills/skill-chief-of-staff/SKILL.md`
- Create: `tests/test_validate_repo_contracts.py` additions
- Modify: `tests/test_validate_planning_lifecycle.py` additions
- Modify: `tests/test_validate_template_required_sections.py` additions
- Modify: `tests/test_skill_chief_of_staff.py`

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: add explicit scope/plan/document arguments and
  update CoS command guidance; preserve full audit behavior as default
- Stop for: bypassing selected-plan authority/dependency/proof errors, removing
  repository audit coverage, or making `--fast` a string-matching exception

**Steps:**
- [x] Step 1: Add `--scope {preflight,audit}` and `--plan <path>` to the
  existing validation command; keep `--fast` as `preflight` compatibility mode
  and reject conflicting `--fast --scope audit`.
- [x] Step 2: Make `validate_planning_lifecycle.py` accept one bound plan path
  for preflight and classify only that plan's applicable findings.
- [x] Step 3: Make `validate_template_required_sections.py` accept one bound
  document for preflight so historical template targets are not enumerated.
- [x] Step 4: Make `build_subprocess_steps()` select only bound plan lifecycle,
  bound template, profile/configuration, runtime ownership/boundary, and
  security/environment checks for preflight; retain repository-wide audit
  checks for audit.
- [x] Step 5: Update CoS guidance to pass the bound plan path and consume the
  blocking result; warning-only preflight continues.
- [x] Step 6: Add tests for fast/preflight step selection, bound-plan and
  bound-template errors, warning-only historical archives, conflicting flags,
  and full audit retention.

**Verification:**
- [x] `python -m pytest -q tests/test_validate_repo_contracts.py tests/test_validate_planning_lifecycle.py tests/test_validate_template_required_sections.py tests/test_skill_chief_of_staff.py`
- Expected: preflight blocks applicable errors, continues warnings, and audit
  remains comprehensive.
- [x] `py scripts/validate_repo_contracts.py --fast --plan docs/superpowers/plans/2026-10-06-00-40-secretary-safety-and-validation-follow-up-plan.md`
- Expected: bound active/proposed plan preflight passes without scanning unrelated
  historical archives.

**Exit Criteria:**
- CoS preflight and repository audit have distinct, tested effects through one
  validator command.

### Task 4: Harden adapter ownership and delivery semantics

**Purpose:**
- Close duplicate-controller, conflicting-reuse, release/replay, delivery, and
  Git-binding evidence gaps before any automated activation.

**Task Function:**
- Strengthen only the in-memory contract fake and tests; keep production
  transport deferred.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded runtime contract with direct side-effect proof.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: duplicate and replay semantics affect automated activation
  safety.

**Specification Coverage:**
- One active controller owner per `(repository_identity, workstream_identity)`.
- Activation key plus request fingerprint rejects conflicting reuse.
- Activation input includes repository identity, canonical work/plan identity,
  expected branch, and expected base commit.
- Released historical receipt never restores active ownership.
- Delivery identity is idempotent only for the same controller and payload
  fingerprint; conflicting reuse requires reconciliation.
- In-memory journal proves contract behavior only; durable crash recovery remains
  a future transport-owned obligation.

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/secretary_adapter.py`
- Modify: `tests/test_secretary_adapter.py`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: modify the provider-neutral fake, typed receipts,
  and focused tests
- Stop for: production transport, Secretary database, silent duplicate effects,
  or claims of process-crash durability from in-memory state

**Steps:**
- [x] Step 1: Add a caller-supplied binding containing repository identity,
  canonical work/plan identity, expected branch, and expected base commit.
- [x] Step 2: Add deterministic request fingerprinting from the binding,
  normalized objective, and sorted canonical evidence references.
- [x] Step 3: Reject a second activation key for an already active bound
  workstream
  with `recovery_required=True` and no activation side effect.
- [x] Step 4: Return historical receipt facts after release without restoring the
  released controller to the active map; require a new activation decision.
- [x] Step 5: Add delivery identity plus controller/payload fingerprint; same key
  and same payload reuses confirmation, changed payload returns recovery.
- [x] Step 6: Test caller-requested non-default branch/base matching and stale
  mismatches.
- [x] Step 7: Document that only transport-owned durable journals can claim
  process-crash reconciliation and that callers decide continue/reconcile/block.

**Verification:**
- [x] `python -m pytest -q tests/test_secretary_adapter.py`
- Expected: conflicting binding/key/fingerprint, release/replay, delivery,
  branch/base, restart-journal, and side-effect tests pass.

**Exit Criteria:**
- Adapter contract blocks unsafe duplicate or replay effects without adding a
  production transport or workflow database.

### Task 5: Make event suppression evidence-based

**Purpose:**
- Prevent unresolved older obligations from disappearing merely because a newer
  revision exists.

**Task Function:**
- Refine source-scoped coalescing and explicit resolution/supersession evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic pure policy with focused failure tests.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: unsafe suppression can hide required human attention.

**Specification Coverage:**
- Event identity is source-scoped.
- Coalescing preserves the newest source-ordered observation and union of
  evidence references.
- Canonical identity uses `observed_anchor`; optional `source_sequence` handles
  source ordering without inventing a project-wide revision.
- Older unresolved events return reconciliation/attention, not `NO_ACTION`.
- Only explicit current evidence of resolution or supersession suppresses an old
  event.
- Event decisions never accept completion, retirement, retry, or task state.

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/secretary_events.py`
- Modify: `tests/test_secretary_events.py`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: modify pure event policy and tests
- Stop for: scheduler creation, automatic lifecycle action, or suppression based
  only on revision comparison

**Steps:**
- [x] Step 1: Include `source` in the event identity key and define identity as
  source-scoped.
- [x] Step 2: Replace `canonical_revision` with `observed_anchor` and optional
  `source_sequence`; use source ordering only for coalescing.
- [x] Step 3: Merge evidence references deterministically when coalescing matching
  hints; never discard references from the selected observation.
- [x] Step 4: Extend reconciliation evidence with explicit resolved/superseded
  event identities.
- [x] Step 5: Return `RECONCILE` for older unresolved events and `NO_ACTION` only
  when current evidence marks the identity resolved or superseded.
- [x] Step 6: Add tests for same identity from different sources, merged refs,
  unresolved old authority events, resolved old events, and routine activity.

**Verification:**
- [x] `python -m pytest -q tests/test_secretary_events.py`
- Expected: event policy preserves actionable unresolved obligations and remains
  separate from acceptance/lifecycle state.

**Exit Criteria:**
- Event activation is deterministic and evidence-reconciled without a scheduler.

### Task 6: Narrow benchmark and documentation claims

**Purpose:**
- Keep deterministic evidence honest while exercising changed safety inputs.

**Task Function:**
- Convert the benchmark to one run per deterministic scenario and add high-value
  conflict/replay/event cases.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: benchmark fixtures and documentation have one owner.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: no live performance claim is made.

**Specification Coverage:**
- Deterministic benchmark is labeled fake contract evidence.
- Scenarios cover conflicting activation keys, release/replay, lost delivery,
  and unresolved old events.
- No fake latency/token/reliability claim is emitted.
- Secretary, runtime, adapter, and validator docs each own one concern.

**Files And Symbols:**
- Modify: `scripts/benchmark_secretary_architecture.py`
- Modify: `tests/test_secretary_benchmark.py`
- Modify: `.agents/skills/skill-project-secretary/SKILL.md`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: `docs/architecture.md`

**Dependencies:**
- Task 3, Task 4, Task 5 complete.

**Authority:**
- Preauthorized local actions: adjust deterministic scenarios and ownership
  wording; run focused benchmark tests
- Stop for: live performance claims without a real adapter or duplicated
  authoritative documentation

**Steps:**
- [x] Step 1: Set deterministic contract execution to one run per scenario and
  retain `live=False`, unset latency/token fields, and evidence provenance.
- [x] Step 2: Add changed-input scenarios for conflicting activation keys,
  request-fingerprint conflict, release/replay, lost delivery identity, and
  unresolved old events.
- [x] Step 3: Remove repeated identical-run assertions and assert correctness,
  failure classification, duplicate effects, reconciliation calls, and payload /
  context shape instead.
- [x] Step 4: Clarify in runtime/architecture docs that receipts are operational
  evidence for duplicate-effect avoidance, never plan/Git recovery truth.
- [x] Step 5: Keep Docket routing in Secretary skill, execution/acceptance in
  existing planning rules, adapter semantics in adapter code, and severity in
  validators.

**Verification:**
- [x] `python -m pytest -q tests/test_secretary_benchmark.py`
- Expected: one deterministic result per architecture/scenario and no live
  performance claims.
- [x] `python scripts/benchmark_secretary_architecture.py 1`
- Expected: structured JSON contains only deterministic contract evidence.

**Exit Criteria:**
- Benchmark and documentation claims match observable evidence and changed-input
  coverage.

### Task 7: Synchronize and complete acceptance evidence

**Purpose:**
- Prove the follow-up PR without changing the completed PR #51 history.

**Task Function:**
- Synchronize generated skill projections and run final focused, repository, and
  full-suite checks.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic generation and lead-controlled acceptance.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: final proof spans validation, runtime safety, generated output,
  and preserved deferrals.

**Specification Coverage:**
- Canonical Secretary source precedes generated projections.
- Canonical CoS source precedes generated projections.
- Starter-kit manifest ships the shared validation helper with its consumers.
- Paseo remains deferred.
- No plan/spec template changes are introduced.
- All findings, deferrals, and residual risks are recorded in this plan.

**Files And Symbols:**
- Modify: generated Secretary and CoS skill projections selected by
  `scripts/sync_agent_adapters.py`
- Modify: `repo_config/starter-kit-manifest.json`
- Verify: `tests/test_starter_kit_generation.py`
- Verify: `docs/architecture.md`
- Verify: `docs/superpowers/plans/2026-10-06-00-40-secretary-safety-and-validation-follow-up-plan.md`
- Verify: `scripts/validate_planning_lifecycle.py`
- Verify: `scripts/validate_repo_contracts.py`

**Dependencies:**
- Task 6 complete.

**Authority:**
- Preauthorized local actions: synchronize generated projections and run named
  verification commands
- Stop for: generated drift, failed blocking validator, changed out-of-scope
  files, or any request to add Paseo/live runtime work

**Steps:**
- [x] Step 1: Run `py scripts/sync_agent_adapters.py --all-platforms` and inspect
  only projections caused by canonical Secretary and CoS changes.
- [x] Step 2: Verify starter-kit generation includes `scripts/validation_findings.py`
  whenever either document validator is shipped.
- [x] Step 3: Run all focused validation/runtime tests and repository validators.
- [x] Step 4: Run full `python -m pytest -q` and `git diff --check`.
- [x] Step 5: Perform one fresh plan-document review; record exact evidence,
  approved deferrals, and any residual risk before status transition.

**Verification:**
- [x] `python -m pytest -q tests/test_validation_findings.py tests/test_validate_planning_lifecycle.py tests/test_validate_template_required_sections.py tests/test_validate_repo_contracts.py tests/test_secretary_docket.py tests/test_secretary_adapter.py tests/test_secretary_events.py tests/test_secretary_benchmark.py tests/test_skill_project_secretary.py tests/test_skill_chief_of_staff.py tests/test_starter_kit_generation.py`
- Expected: 166 focused tests pass.
- [x] `py scripts/validate_planning_lifecycle.py`
- Expected: plan contract and task ledger pass.
- [x] `py scripts/validate_repo_contracts.py`
- Expected: repository audit passes.
- [x] `py scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: generated projections have no drift.
- [x] `py scripts/validate_generated_header_format.py`
- Expected: generated headers pass.
- [x] `python -m pytest -q`
- Expected: 918 tests pass, 1 skipped.
- [x] `git diff --check`
- Expected: no whitespace errors.

**Exit Criteria:**
- All current-scope safety gates and validators pass; fresh verification
  authorizes completed status.

## Verification

- Focused tests cover validation findings, Docket loading, scoped preflight,
  adapter ownership/delivery, event relevance, benchmark scenarios, and skill
  contracts.
- Repository validators, generated-surface checks, full test suite, and
  `git diff --check` pass, with unrelated failures classified explicitly.
- Fresh plan review confirms Paseo, scheduler, production transport, and
  template changes remain out of scope.

## Completion Criteria

1. Warning-only historical metadata returns success without suppressing unsafe
   selected-plan errors.
2. CoS `--fast` preflight validates one bound plan and its bound template plus
   dispatch-critical contracts; repository audit remains broader and explicit.
3. Docket template remains one optional empty-list template; execution-facing
   path, writer, and clearing semantics are documented and tested without a
   production loader.
4. Adapter binds ownership and fingerprints to repository/canonical work/Git
   identity, rejects conflicting reuse, does not replay released ownership, and
   deduplicates only identical delivery payloads.
5. Event policy uses source-scoped anchors, keeps unresolved older obligations
   actionable, and preserves evidence references across coalescing.
6. Benchmark evidence is deterministic contract evidence only and covers changed
   safety inputs without fake performance claims.
7. Generated surfaces, Starter-kit manifest, focused tests, repository
   validators, and full suite reconcile before plan completion.
8. Paseo remains explicitly deferred and no production transport, scheduler, or
   Docket loader is
   added.

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified`. Completion does not
authorize commit, push, merge, publication, dependency installation,
authentication, or cleanup.
