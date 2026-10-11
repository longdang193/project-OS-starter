---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: delivery-b-reporting-boundary
targets:
  - scripts/observe_9router_usage.py
  - scripts/secretary_evidence_adapter.py
  - scripts/secretary_live_runtime.py
  - scripts/benchmark_secretary_reporting.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - tests/test_observe_9router_usage.py
  - tests/test_secretary_evidence_adapter.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_reporting_benchmark.py
  - .github/workflows/runtime-contracts.yml
---

# Delivery B Reporting Boundary

## Goal

Implement the approved Delivery B direction as a read-only reporting boundary:
provider measurements remain useful at their strongest independently proven
attribution level, while reporting availability, ambiguity, partial coverage,
or Secretary receipt failure cannot change semantic acceptance, retry,
continuation, cleanup, settlement, or integration.

The plan starts from `origin/main` at `50ea7498596f7487f0650f3f6c0737c4d2a740dd`,
which contains the completed Delivery A acceptance boundary and the existing
`scripts/secretary_evidence_adapter.py` surface. The current checkout is behind
that base and contains unrelated tracked and untracked changes; execution must
use a clean isolated worktree and leave the current checkout untouched.

Target invariant:

> One owner per fact. Provider observation owns provider evidence. The live
> Secretary wrapper owns Secretary execution and Secretary-native facts. The
> evidence adapter owns classification and presentation. CoS owns semantic
> acceptance. Runtime owners own settlement and resource safety.

## Implementation Outcomes

### Delivery A remains frozen

`evaluate_acceptance()` continues to decide only semantic task acceptance from
its existing controller, task, Worker, artifact, Git, and verification inputs.
Reporting payloads and provider telemetry are absent from that decision path.
Settlement remains represented in acceptance proof where required by the
existing contract, but reporting must not become a new acceptance prerequisite.
`runtime-surfaces.md` describes this ownership truthfully.

### Provider observations become request-first and coverage-aware

`observe_9router_usage.py` reads the provider database through one bounded,
read-only, snapshot-consistent operation. It joins usage rows to request-detail
rows by the existing request-detail identifier, validates each pair
independently, preserves usable failed-request measurements, and returns
explicit availability, attribution, and coverage rather than one overloaded
status.

Missing cache or cost evidence remains unknown. A zero is emitted only when the
source explicitly proves zero. Ambiguous joins are excluded and reported,
while independently verified rows remain reportable.

### The reporting adapter is the only projection boundary

`scripts/secretary_evidence_adapter.py` consumes provider observations, launcher
facts, and a validated Secretary receipt independently. A request join gives
request attribution; a request-to-session mapping gives session attribution; and
a validated Secretary receipt explicitly binding provider session `S` to attempt
`A` or run `R`, together with coverage of the relevant request set, gives
Secretary-attributed attempt/run reporting. The adapter never infers attempt/run
from session identity alone, synthesizes missing identifiers, or becomes an
acceptance, retry, settlement, cleanup, or continuation authority.

The adapter preserves its existing sanitized bundle shape and adds the
independent dimensions:

- Availability: `available`, `partial`, `missing`, or `inconclusive`.
- Attribution: `request`, `session`, `attempt`, `run`, `window`, or `none`.
- Coverage: `complete`, `partial`, or `unknown`.

### Live runtime provenance stays truthful

`secretary_live_runtime.py` continues to collect provider observations as
separate reporting evidence, but no longer relabels router observations as
`source: response.usage` or fills `secretary_turns` from router
`request_count`. Secretary-native metrics remain sourced from the validated
Secretary receipt; provider economics remain provider evidence.

### Delivery B stops at measured proof

Focused failure, ambiguity, database-outage, and scaling probes prove the
reporting boundary. The work adds no persistent Project OS telemetry database,
cache, daemon, ingestion process, provider schema mutation, upstream 9router
change, WorkerResult migration, cleanup manager, or Delivery C compatibility
deletion.

## Scope Boundaries

- Do not modify Herdr, Codex, the 9router database schema, provider runtime, or
  external provider configuration.
- Do not add persistent telemetry state, a mirror database, cache, daemon,
  event bus, scheduler, economics ledger, or global reporting registry.
- Do not make Secretary receipt availability mandatory for provider reporting;
  it blocks only Secretary-attributed claims.
- Do not make reporting a dependency of `evaluate_acceptance()`, plan
  transitions, retry, continuation, settlement, retirement, or evidence
  release.
- Do not change `secretary_adapter.py`, `secretary_receipts.py`, or runtime
  ownership unless Task 1 identifies a concrete contract break in the declared
  Delivery B surfaces.
- Do not implement WorkerResult v2, `READY` naming migration, broad phase
  deletion, or other Delivery C compatibility work.
- GitHub `main` protection is an external administration track, not a local
  Delivery B implementation task. The plan records its handoff but does not
  mutate GitHub or claim remote policy completion.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `clean task-specific worktree from origin/main`; preserve the current dirty checkout untouched
- Plan bootstrap: after creating the isolated worktree, copy only this reviewed plan into the execution branch before any task ledger update or implementation edit; do not import unrelated current-checkout changes.
- Commit policy: local checkpoint commits are allowed only after the relevant proof passes and the coordination ledger records the evidence; prefer checkpoints after Task 1, Tasks 2–4, Task 6, and final verification. Push, merge, and any remote branch disposition require explicit user approval.
- Preauthorized local actions: inspect declared source and tests, edit declared files, create the bounded reporting benchmark and its fixtures, run focused tests/probes/validators, and record sanitized local evidence
- User-approval actions: create or delete worktrees outside the declared lane, push, merge, GitHub protection or ruleset mutation, provider/9router mutation, destructive cleanup, compatibility deletion outside the declared targets, or scope expansion
- Parallel ownership: `none`; observer, classification, runtime, and final verification share contracts and execute sequentially
- Sequential fallback: execute Tasks 1–7 in order; keep later tasks pending when an earlier proof gate fails

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/delivery-b-reporting-boundary`
- Base commit: `50ea7498596f7487f0650f3f6c0737c4d2a740dd`
- Expected workspace: clean isolated worktree at the base above; preserve the current checkout's 27 unrelated tracked/untracked changes and do not stage, delete, stash, or rewrite them
- Execution workspace: `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\delivery-b-reporting-boundary\project-OS-starter`
- Execution result: implementation and required local proof completed on the declared base; original checkout remained untouched
- Next action: preserve this plan and implementation for explicit branch disposition; do not start Delivery C or GitHub protection mutation
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated | `codex` | none | Delivery A baseline, structural reporting-independence proof, and source inventory | `100 passed, 1 skipped` baseline; caller inventory and acceptance-independence audit recorded in execution evidence |
| Task 2 | `completed` | isolated | `codex` | Task 1 | focused observer suite and read-only boundary proof | `22 passed`; canonical bounded reader, row validation, locked-read bound, and sensitive-column checks |
| Task 3 | `completed` | isolated | `codex` | Task 2 | classification and adapter contract tests | adapter suite passed; availability, attribution, coverage, and receipt/session bridge cases covered |
| Task 4 | `completed` | isolated | `codex` | Task 3 | live-runtime provenance regression suite | live-runtime suite passed; cleanup precedes post-cleanup provider observation; router telemetry does not populate Secretary-native metrics |
| Task 5 | `completed` | isolated | `codex` | Task 4 | adapter integration and missing-receipt proof | `50 passed` adapter/live-runtime integration proof; missing and partial evidence remain non-authoritative |
| Task 6 | `completed` | isolated | `codex` | Task 5 | failure/ambiguity/performance probe output | benchmark baseline/final JSON retained outside repo; locked-read regression passed; query plan/index findings recorded |
| Task 7 | `completed` | isolated | `codex` | Task 6 | final focused/full validation and scope audit | `196 passed, 1 skipped`; repository contracts, plan lifecycle, diff check, and authority audit passed |

Only the lead controller updates this ledger. A checked item records progress,
not proof.

## Task Breakdown

### Task 1: Freeze Delivery A and establish the reporting baseline

**Purpose:**
- Establish the exact post-Delivery-A acceptance contract, current reporting
  callers, test baseline, and clean execution base before changing telemetry.

**Task Function:**
- Contract boundary inventory and regression-baseline setup.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: source and test truth must be reconciled before selecting an executor profile.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns the initial source and baseline gate.

**Specification Coverage:**
- Freeze semantic acceptance as independent from provider reporting and
  Secretary availability.
- Correct the stale runtime ownership prose without changing acceptance code
  or settlement/release safety.
- Preserve the existing Delivery A acceptance tests and structurally prove that
  reporting payloads are not consumed; do not add artificial telemetry inputs to
  `evaluate_acceptance()` tests.
- Identify every caller and test of the observer, adapter, and live runtime
  before modifying shared contracts.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_observe_provider_telemetry` and `_build_codex_runtime_snapshot`
- Inspect: `scripts/secretary_evidence_adapter.py:build_evidence_bundle`, `_provider_usage`, and `_join_provider_usage`
- Inspect: `scripts/observe_9router_usage.py:observe_window_usage`, `observe_usage`, and `observe_run_usage`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md:acceptance ownership statement`
- Add: `scripts/benchmark_secretary_reporting.py:baseline-capable synthetic harness only; no production observer changes`
- Inspect only: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance` and `tests/test_project_os_runtime.py:Delivery A acceptance coverage`
- Verify: `tests/test_observe_9router_usage.py`, `tests/test_secretary_evidence_adapter.py`, and `tests/test_secretary_live_runtime.py`

**Dependencies:**
- Clean worktree from `origin/main` at `50ea7498596f7487f0650f3f6c0737c4d2a740dd`.

**Authority:**
- Preauthorized local actions: inspect the declared source/tests, correct the declared documentation sentence, preserve existing Delivery A tests, create and run the baseline-capable synthetic harness, and record structural acceptance-independence proof.
- Stop for: source/test evidence that changes Delivery A authority, a required caller outside declared targets, a stale or different base, or any request to alter runtime settlement ownership.

**Steps:**
- [x] Step 1: Confirm the isolated worktree resolves to the declared base and record the focused baseline command output.
- [x] Step 2: Inventory all imports and callers of the observer, adapter, and live-runtime reporting path; classify each as canonical, compatibility, test, or external evidence.
- [x] Step 3: Preserve the existing `PASS`, `FAIL`, or `BLOCKED` acceptance regressions and inspect `evaluate_acceptance()` inputs/callers to prove reporting payloads are not consumed; defer enabled/disabled/partial/unavailable equivalence to Task 5.
- [x] Step 4: Correct `runtime-surfaces.md` so `evaluate_acceptance()` is not described as deriving its semantic decision from unrelated settlement or telemetry facts.
- [x] Step 5: Before any observer/runtime edit, create the declared synthetic benchmark harness, run its baseline command `py -B scripts/benchmark_secretary_reporting.py --phase baseline --repetitions 5 --history-sizes 0,100,1000`, and record the fixed workload/query-plan snapshot, Python version, SQLite version, OS, dataset sizes, repetition policy, and output path for Task 6 comparison.

**Verification:**
- [x] `py -B -m pytest -q tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_evidence_release.py`
- Expected: existing Delivery A acceptance, dependent-transition, settlement, and evidence-release tests pass; no artificial reporting argument or new acceptance dependency is introduced.
- [x] `rg -n "observe_window_usage|observe_usage|observe_run_usage|build_evidence_bundle|_observe_provider_telemetry|_build_codex_runtime_snapshot" scripts tests`
- Expected: every production caller is listed in the task evidence before Task 2 changes a shared return contract.
- [x] `rg -n "evaluate_acceptance\(\).*settlement facts|settlement facts" docs/operating_system/runtime/runtime-surfaces.md`
- Expected: no stale ownership sentence remains.

**Exit Criteria:**
- The post-Delivery-A boundary, callers, baseline, and documentation owner are recorded; reporting can be changed without changing acceptance authority.

### Task 2: Refactor 9router observation around per-request evidence

**Purpose:**
- Replace broad, all-or-nothing telemetry scans with a bounded read-only
  request-first observation contract that preserves valid subsets and exposes
  explicit coverage.

**Task Function:**
- Read-only SQLite evidence extraction and partial-data classification.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: the observer is a shared provider-boundary reader with SQL, data-validation, and compatibility risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused automated tests and direct read-only probes are the required validator.

**Specification Coverage:**
- Use one read-only connection and one consistent read transaction/snapshot per observation.
- Bound candidate selection in SQL only after checking timestamp representation and available indexes.
- Join `usageHistory.meta.request_detail_id` to `requestDetails.id` before session qualification.
- Validate each request/usage pair independently; aggregate verified rows only.
- Preserve measured usage from failed requests where values are valid.
- Keep ambiguous joins excluded and visible in coverage; do not reject every valid row because of an unrelated ambiguous row.
- Represent missing cache/cost evidence as unknown, never synthetic zero.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/observe_9router_usage.py:_tables`, `_token_details`, `_aggregate_usage`, `observe_window_usage`, `observe_usage`, `observe_run_usage`, and `_result`
- Verify: `tests/test_observe_9router_usage.py:_database` and all observer tests
- Add or modify fixtures only inside `tests/test_observe_9router_usage.py`; do not modify a provider database or checked-in provider schema

**Dependencies:**
- Task 1 caller inventory and accepted Delivery A baseline.

**Authority:**
- Preauthorized local actions: edit the declared observer functions, add temporary SQLite fixtures in tests, inspect schema/index metadata read-only, and preserve the existing CLI entry point and source sanitization.
- Stop for: a required provider schema mutation, a new persistent Project OS store, unsafe timestamp ordering, inability to bound the join, or a compatibility break outside the declared observer callers.

**Steps:**
- [x] Step 1: Open one read-only SQLite connection, begin one consistent read snapshot, and select only the bounded candidate columns needed for the requested window and filters.
- [x] Step 2: Resolve request-detail identifiers from the existing `meta` payload and join each candidate to its `requestDetails` row without temporal overlap as the primary attribution rule.
- [x] Step 3: Return per-row validation outcomes for valid usage, failed-with-usage, invalid usage, missing detail, duplicate/ambiguous join, and unattributed request rows; aggregate only valid numeric fields.
- [x] Step 4: Replace absent token-detail defaults with unknown cache fields and independent cache coverage; retain provider-recorded cost separately from estimated or unavailable cost.
- [x] Step 5: Make one canonical internal reader own normalization and have `observe_window_usage`, `observe_usage`, and `observe_run_usage` act as thin compatibility projections, while adding explicit availability, attribution, coverage, selected count, measured count, and excluded-row reasons.
- [x] Step 6: Keep whole-session isolation as a qualification field rather than a prerequisite for reporting independently joined request measurements.
- [x] Step 7: Bound locked, unavailable, or stalled reads to a declared `1,000 ms` observation budget using SQLite busy handling plus a progress/deadline guard; return inconclusive diagnostics on expiry instead of holding a lifecycle owner open.

**Verification:**
- [x] `py -B -m pytest -q tests/test_observe_9router_usage.py`
- Expected: normal matched usage passes; overlapping sessions retain independently joined rows; duplicate joins report excluded ambiguity; failed rows with valid usage contribute to measured totals; invalid rows reduce coverage without erasing valid totals; missing cache/cost remains unknown; unavailable/locked/schema-invalid databases return bounded inconclusive diagnostics.
- [x] `py -B -m pytest -q tests/test_observe_9router_usage.py -k "sensitive or timestamp or boundary or join or overlap or cache or cost"`
- Expected: source provenance, timestamp boundaries, join identity, ambiguity, and unknown-field behavior remain covered.

**Exit Criteria:**
- Provider observations are request-first, read-only, snapshot-consistent, coverage-aware, and backward-compatible for all declared consumers without mutating 9router state.

### Task 3: Make the evidence adapter own the three-axis reporting classification

**Purpose:**
- Make `scripts/secretary_evidence_adapter.py` the single projection boundary
  that reports provider and Secretary evidence independently.

**Task Function:**
- Evidence classification, identity-safe projection, and compatibility shaping.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: the adapter crosses provider, launcher, and receipt contracts but remains a bounded pure projection surface.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic adapter tests cover the classification matrix.

**Specification Coverage:**
- Keep availability, attribution, and coverage independent rather than encoding them as a compound state.
- Preserve `source: 9router-local-read-only` and distinguish router-recorded cost, published-rate estimates, and provider billing.
- Apply the exact bridge rule: request join → request attribution; request session mapping → session attribution; validated Secretary receipt binding provider session `S` to attempt `A`/run `R` plus coverage of the relevant request set → Secretary-attributed attempt/run reporting.
- Never infer attempt/run from session identity alone and never synthesize missing identifiers.
- Keep Secretary receipt absence from discarding independently reportable provider evidence.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/secretary_evidence_adapter.py:_join_provider_usage`, `_provider_usage`, `build_evidence_bundle`, and the adapter schema constants
- Verify: `tests/test_secretary_evidence_adapter.py:build_evidence_bundle` scenarios and `load_reusable_target`
- Inspect without changing: `scripts/project_os_runtime/secretary_receipts.py:validate_live_receipt`

**Dependencies:**
- Task 2 observation fields and row-level coverage contract.

**Authority:**
- Preauthorized local actions: modify the local adapter projection and focused tests, preserve sanitized field allowlists, and retain the existing bundle CLI inputs/outputs.
- Stop for: a requested acceptance/settlement decision in the adapter, an identity join that depends only on time overlap, a new persistent schema, or any raw secret/transport payload entering the bundle.

**Steps:**
- [x] Step 1: Add a small classification helper with the exact availability, attribution, and coverage vocabularies and deterministic normalization of missing/unknown values.
- [x] Step 2: Map provider observation fields into the existing `provider_usage` object without relabelling router evidence as Secretary-native evidence.
- [x] Step 3: Make validated Secretary receipt presence, explicit session-to-attempt/run binding, and request-set coverage independent inputs to `secretary_attributed`; retain `partial-unattributed` only as a compatibility presentation field, not as the principal state.
- [x] Step 4: Preserve `readiness` semantics for live capability reporting while ensuring provider measurements remain visible when the Secretary receipt is missing, malformed, or blocked.
- [x] Step 5: Add tests for available/request/partial, available/session/complete, valid session-only evidence, valid receipt plus exact session bridge, missing receipt, mismatched identifiers, no join, and provider-only observation.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_evidence_adapter.py tests/test_secretary_receipts.py tests/test_secretary_evidence.py`
- Expected: sanitized bundle construction passes; missing or invalid Secretary receipts block only Secretary-attributed claims; provider evidence retains its actual source and attribution; no synthetic attempt/run/session identity appears.
- [x] `rg -n "partial-unattributed|response\.usage|secretary_attributed|availability|attribution|coverage" scripts/secretary_evidence_adapter.py tests/test_secretary_evidence_adapter.py`
- Expected: compound attribution is compatibility-only, router provenance is preserved, and the three axes are explicit in the adapter contract.

**Exit Criteria:**
- One adapter owns reporting projection and classification; it cannot grant acceptance, settlement, retry, continuation, cleanup, or integration authority.

### Task 4: Remove provenance inflation from the live Secretary wrapper

**Purpose:**
- Keep provider observations separate from Secretary-native runtime metrics while
  preserving live launch, cleanup, receipt validation, and capability behavior.

**Task Function:**
- Runtime evidence ownership correction with regression protection.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: the live wrapper owns subprocess and receipt behavior, so changes must be narrow and directly boundary-tested.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the existing live-runtime suite is the direct validator for the wrapper boundary.

**Specification Coverage:**
- Never convert router database observations into `source: response.usage`.
- Never derive `secretary_turns` from provider `request_count`.
- Keep Secretary-native metrics sourced only from validated Secretary runtime evidence.
- Keep provider observations available as separate sanitized reporting evidence.
- Do not delay launch completion, cleanup, retirement, or settlement on reporting success or a stalled observation. Capture the Secretary-native runtime result and close the Herdr workspace first; invoke the provider reporting read only after cleanup, with the declared `1,000 ms` budget, and attach it as a separate best-effort field. Reporting failure returns a useful inconclusive result and cannot alter the already-recorded lifecycle disposition.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/secretary_live_runtime.py:_safe_token_usage`, `_safe_runtime_snapshot`, `_build_codex_runtime_snapshot`, and `_observe_provider_telemetry` integration
- Verify: `tests/test_secretary_live_runtime.py:test_safe_runtime_snapshot_preserves_structured_economics`, `test_safe_runtime_snapshot_drops_unobserved_token_provenance`, `test_completed_codex_transport_promotes_only_matched_9router_usage`, and provider telemetry tests
- Inspect: `scripts/project_os_runtime/secretary_receipts.py:build_live_receipt` and `validate_live_receipt`

**Dependencies:**
- Tasks 2 and 3 define the provider observation and projection contracts.

**Authority:**
- Preauthorized local actions: remove only the provider-to-Secretary metric promotion path, update focused live-runtime tests, and perform the bounded reporting-only reorder that captures Secretary-native runtime state, closes the Herdr workspace, then performs the `1,000 ms` provider observation as a separate best-effort field; preserve launch/cleanup/receipt identity validation and cleanup ownership.
- Stop for: any change to subprocess ownership, cleanup ownership, runtime settlement, receipt authority, provider route, or required live capability behavior; do not change cleanup semantics beyond moving the non-authoritative provider read after the existing close operation.

**Steps:**
- [x] Step 1: Remove the `_build_codex_runtime_snapshot()` path that injects provider token fields with `response.usage` provenance.
- [x] Step 2: Remove the fallback that maps provider `request_count` to `metrics.secretary_turns`; leave the field unknown unless Secretary-native evidence supplies it.
- [x] Step 3: Preserve `provider_telemetry` as a separate sanitized field with the adapter’s raw source and independent classification.
- [x] Step 4: Update tests so matched router usage remains reportable but does not alter Secretary-native `token_usage` or `secretary_turns`.
- [x] Step 5: Add a locked/stalled-observer regression proving the cleanup/close event occurs before reporting begins, reporting returns within `1,000 ms`, and the already-recorded cleanup, retirement, settlement, and launch-completion results remain unchanged.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_receipts.py`
- Expected: launch identity, cleanup, receipt validation, secret exclusion, provider observation, and failure behavior pass; router observations never become Secretary-native metrics.
- [x] `rg -n "source.?[=:].?response\.usage|secretary_turns.*request_count|request_count.*secretary_turns" scripts/secretary_live_runtime.py`
- Expected: no provider-to-Secretary provenance or turn-count promotion remains.

**Exit Criteria:**
- The live wrapper owns only live Secretary facts and execution safety; provider economics remain separately observable without changing runtime lifecycle behavior.

### Task 5: Integrate the independent reporting paths without adding authority

**Purpose:**
- Prove the observer, adapter, and live wrapper compose into one read-only
  reporting path while retaining independent launcher, provider, Herdr, and
  Secretary receipt evidence.

**Task Function:**
- Cross-surface contract integration and source-boundary proof.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: integration touches multiple existing evidence producers but no workflow authority.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct integration tests and source-wide ownership checks are sufficient.

**Specification Coverage:**
- Provider evidence remains reportable without a Secretary receipt.
- Valid Secretary receipt plus the exact validated session-to-attempt/run bridge and relevant request-set coverage may strengthen attribution, but not beyond the proven level.
- A locked, unavailable, or deliberately stalled provider read starts only after lifecycle cleanup, returns within the declared `1,000 ms` observation bound, and cannot change cleanup, settlement, retry, continuation, or integration.
- Reporting failure cannot launch another Worker, Secretary, or model process.
- Reporting failure cannot delay runtime settlement, cleanup, retirement, retry, continuation, or integration.
- No new persistent Project OS telemetry state is introduced.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`
- `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/secretary_evidence_adapter.py:build_evidence_bundle` and `collect_provider_usage` only where required by Tasks 2–4 contracts
- Verify: `scripts/secretary_live_runtime.py:run_smoke`, `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`, and `scripts/project_os_runtime/attempt.py:settlement_decision`
- Verify: `tests/test_secretary_evidence_adapter.py`, `tests/test_secretary_live_runtime.py`, `tests/test_project_os_runtime.py`, and `tests/test_evidence_release.py`

**Dependencies:**
- Tasks 1–4 complete with focused proof accepted.

**Authority:**
- Preauthorized local actions: add cross-surface fixtures and integration assertions using temporary files/databases, then update only declared compatibility fields.
- Stop for: any new authority edge, process launch in a reporting-only test, cleanup/settlement dependency on telemetry, or persistent state outside existing evidence files.

**Steps:**
- [x] Step 1: Build bundles from provider-only, provider-plus-invalid-receipt, valid session-only, provider-plus-valid-receipt-without-join, and provider-plus-valid-receipt-with-exact-session-bridge inputs.
- [x] Step 2: Assert the strongest proven attribution is preserved in each bundle and no missing identifier is synthesized.
- [x] Step 3: Run acceptance, settlement, retry, and cleanup decisions with reporting enabled, disabled, partial, unavailable, and deliberately stalled/locked reporting; assert the cleanup/close event precedes reporting, reporting completes within `1,000 ms`, and semantic/lifecycle outputs and cleanup/settlement completion remain unchanged.
- [x] Step 4: Review changed hunks and imports for newly introduced subprocess, database-write, scheduler, cache, or workflow-authority paths; preserve existing adapter I/O that is unrelated to authority.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_evidence_adapter.py tests/test_secretary_live_runtime.py tests/test_project_os_runtime.py tests/test_evidence_release.py`
- Expected: reporting on/off equivalence holds; missing receipts preserve provider-only reporting; evidence release and runtime safety remain independently guarded.
- [x] Diff-aware authority audit of `scripts/secretary_evidence_adapter.py` and its tests.
- Expected: changed hunks add no workflow, scheduler, provider-write, cache, or new process authority; existing Herdr status probing and requested output writing remain classified as compatibility I/O, not forbidden new authority.

**Exit Criteria:**
- The reporting boundary composes correctly with existing execution and lifecycle owners without creating a second control path.

### Task 6: Add failure, ambiguity, and scalability probes

**Purpose:**
- Produce direct evidence for the Delivery B merge gates, especially bounded
  work as irrelevant provider history grows.

**Task Function:**
- Representative failure and performance measurement.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: performance and data-boundary evidence require a profile selected after the implementation contract is stable.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead accepts measured probe output against the declared gates.

**Specification Coverage:**
- Cover overlapping sessions, duplicate joins, partial usage, failed requests, missing cache/cost, unavailable/locked databases, and telemetry enabled/disabled equivalence.
- Inspect `EXPLAIN QUERY PLAN` and index definitions, and measure p50/p95 latency, SQL query count, selected/validated/excluded rows, VM steps or progress-handler counts, and peak memory for a fixed requested window while irrelevant historical rows grow.
- Distinguish bounded Project OS query work from the stronger claim that SQLite physical scan cost is independent of total database size.
- If upstream schema/indexing prevents history-independent physical scans, record the limitation and stop; do not add a Project OS cache, mirror database, background indexer, or upstream mutation to rescue the benchmark.
- Compare the final implementation with the same benchmark workload and environment on the declared baseline `origin/main@50ea7498596f7487f0650f3f6c0737c4d2a740dd`; record Python, SQLite, OS, dataset sizes, repetitions, and metric definitions. The lead controller owns the no-material-regression judgment from this paired evidence; hosted CI owns correctness only and must not enforce noisy latency thresholds.
- Verify the observer does not read sensitive columns or mutate the provider database.
- Keep all probe data synthetic, temporary, and sanitized.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`
- `skill-test-driven-development`

**Files And Symbols:**
- Add: `scripts/benchmark_secretary_reporting.py:bounded synthetic SQLite reporting probe`
- Add: `tests/test_secretary_reporting_benchmark.py:probe contract and output validation`
- Modify: `.github/workflows/runtime-contracts.yml:maintained lightweight benchmark-correctness test ownership`
- Modify: `tests/test_observe_9router_usage.py:synthetic database builders` only to expose reusable bounded scenarios
- Verify: `scripts/observe_9router_usage.py` and `scripts/secretary_evidence_adapter.py`

**Dependencies:**
- Tasks 2–5 complete; the observer and adapter schemas must be stable enough to measure.

**Authority:**
- Preauthorized local actions: add a deterministic synthetic benchmark that uses temporary SQLite files, `sqlite3` trace/progress hooks, `EXPLAIN QUERY PLAN`, `time.perf_counter`, and `tracemalloc`; add only its lightweight schema/output/boundedness correctness test to the existing runtime-contracts CI owner; keep p50/p95 timing comparison manual. Write only explicit output paths supplied by the caller.
- Stop for: live provider database access in tests, provider schema/index mutation, unbounded benchmark duration, unsupported performance claims, or a result that cannot distinguish unrelated history from requested rows.

**Steps:**
- [x] Step 1: Build synthetic databases with fixed requested rows plus controlled irrelevant historical rows, overlapping sessions, duplicate request-detail matches, failed rows, malformed token details, and missing cost/cache fields.
- [x] Step 2: Reuse the Task 1 harness and workload: compare the recorded baseline command `py -B scripts/benchmark_secretary_reporting.py --phase baseline --repetitions 5 --history-sizes 0,100,1000` with the final command `py -B scripts/benchmark_secretary_reporting.py --phase final --repetitions 5 --history-sizes 0,100,1000` in comparable clean environments; inspect query plans/indexes, then record p50/p95 latency, query count, selected/validated/excluded row counts, VM steps/progress counts, and peak memory for each.
- [x] Step 3: Assert the requested-result semantics for every failure case and compare scaling against the same environment and workload shape.
- [x] Step 4: Classify the result separately as bounded Project OS query behavior and, only when proven, history-independent SQLite physical scanning; emit sanitized JSON or console output containing only schema version, dataset sizes, plan/index findings, metrics, dispositions, and reasons.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_reporting_benchmark.py tests/test_observe_9router_usage.py`
- Expected: deterministic probe scenarios pass and output validation rejects missing metrics or fabricated zero/complete coverage.
- [x] Add the lightweight correctness test to `.github/workflows/runtime-contracts.yml`; keep unstable latency thresholds and p50/p95 comparisons out of hosted CI.
- [x] `py -B scripts/benchmark_secretary_reporting.py --help`
- Expected: the probe exposes bounded dataset-size, repetition, and output controls without requiring live provider access.
- [x] `py -B scripts/benchmark_secretary_reporting.py --phase final --repetitions 5 --history-sizes 0,100,1000`
- Expected: manual output records p50/p95, query count, selected/validated/excluded rows, VM steps/progress counts, peak memory, query-plan/index findings, and unchanged semantic dispositions; no provider mutation occurs. If physical scans grow with irrelevant history, record that limitation and stop without adding persistence or upstream changes.

**Exit Criteria:**
- All Delivery B acceptance gates have direct failure or performance evidence, and the scaling result is recorded without introducing persistent telemetry state.

### Task 7: Run final verification and close the Delivery B boundary

**Purpose:**
- Reconcile the implementation against the plan, prove no authority or scope
  drift, and explicitly stop before Delivery C or unapproved GitHub mutation.

**Task Function:**
- Cross-task verification, source audit, and acceptance handoff.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: final verification profile is selected after implementation evidence exists.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent review is required for the final reporting/authority boundary and is selected separately from the executor.

**Specification Coverage:**
- Verify every Delivery B merge gate: semantic isolation, launch isolation,
  cleanup isolation, missing receipt behavior, overlap/ambiguity behavior,
  failed-request coverage, unknown cache/cost, database outage, provenance,
  scalability, no persistent state, and no external provider mutation.
- Record GitHub `main` protection as an external handoff, not local completion.
- Record Delivery C as deferred pending a fresh caller inventory or measured
  compatibility cost.

**Required Skills:**
- `skill-plan-document-reviewer`
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: all declared targets and their focused tests
- Verify: `.github/workflows/runtime-contracts.yml`, `scripts/validate_repo_contracts.py`, and repository import/contract boundaries
- Modify: this plan's `Coordination State`, task ledger, `Verification`, and `Completion Criteria` only after proof is accepted

**Dependencies:**
- Tasks 1–6 complete with their declared proof.

**Authority:**
- Preauthorized local actions: run the final test/validator suite, inspect the complete diff, request one independent plan/code review, apply narrowly justified fixes within declared targets, and record evidence in this plan.
- Stop for: failed required proof, unresolved review finding, stale base, changed acceptance owner, changed external scope, GitHub mutation request, or any need to begin Delivery C.

**Steps:**
- [x] Step 1: Run focused observer, adapter, runtime, acceptance, evidence-release, and benchmark suites.
- [x] Step 2: Run repository contract validation and planning lifecycle validation against this plan.
- [x] Step 3: Audit source-wide provenance and ownership: no router observation becomes Secretary-native, no request count becomes Secretary turns, no reporting path writes provider/workflow state, and no new persistent telemetry owner exists.
- [x] Step 4: Confirm the final diff contains only declared Delivery B targets plus this plan and that the current checkout's unrelated changes remain untouched.
- [x] Step 5: Review changed hunks and targeted source searches for new authority or provenance patterns, record measured results and known limits, and record the separate GitHub protection handoff and Delivery C stop decision.

**Verification:**
- [x] `py -B -m pytest -q tests/test_observe_9router_usage.py tests/test_secretary_evidence_adapter.py tests/test_secretary_live_runtime.py tests/test_secretary_receipts.py tests/test_secretary_evidence.py tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_evidence_release.py tests/test_secretary_reporting_benchmark.py`
- Expected: focused Delivery B and preserved Delivery A suites pass.
- [x] `py -B scripts/validate_repo_contracts.py`
- Expected: repository contract/import/prose checks pass with no unapproved runtime dependency.
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-11-14-15-delivery-b-reporting-boundary-plan.md`
- Expected: frontmatter, coordination schema, task ledger, required sections, and checked completion evidence satisfy the plan contract.
- [x] `git diff --check`
- Expected: no whitespace errors.
- [x] Diff-aware provenance and authority audit of changed hunks in `scripts/secretary_live_runtime.py`, `scripts/secretary_evidence_adapter.py`, the observer, tests, benchmark, and workflow.
- Expected: targeted searches find no new router-to-Secretary provenance, request-count turn inference, provider/workflow mutation, scheduler/cache owner, or authority edge; existing permitted subprocess/output I/O is not treated as a new violation.

**Exit Criteria:**
- Delivery B is complete only when provider measurements remain reportable at their strongest independently proven attribution level; no request/session/attempt/run attribution crosses an unproven identity boundary; partial measurement remains useful without fabricated zeros or complete totals; reporting cannot change acceptance, retry, cleanup, continuation, settlement, or integration; one canonical read/normalization path owns reporting; no new persistent Project OS telemetry owner exists; and measured query work shows no material regression as irrelevant history grows. If upstream indexing prevents history-independent physical scans, the limitation is recorded and the work stops without a local cache, mirror, indexer, or upstream mutation. The plan remains proposed until fresh verification authorizes a terminal status.

## External Handoff And Deferred Work

### GitHub protection handoff

After local Delivery B proof, separately inspect and configure the intended
GitHub `main` protection or ruleset through the authorized GitHub administration
path. That action must require explicit user approval, use provider-visible
policy evidence, and remain outside this local reporting diff. Project OS should
read and verify GitHub policy rather than reimplement it locally.

### Delivery C stop condition

Do not start WorkerResult v2, `READY` naming migration, broad phase deletion,
telemetry persistence, cleanup-manager work, upstream 9router changes, or
compatibility deletion until a fresh source-wide caller inventory or measured
profile identifies a concrete compatibility cost worth removing.

## Verification

- Focused observer, adapter, live-runtime, acceptance, release, and benchmark suites pass on the clean `origin/main` worktree.
- Repository contract and planning lifecycle validators pass.
- `git diff --check` passes.
- Fresh probe output records every required failure, query-plan/index finding, and scaling metric without credentials or persistent provider state; p50/p95 timing remains manual evidence rather than an unstable hosted-CI threshold.
- Fresh live probe root cause and remediation: the original 1,000 ms 9router deadline was caused by wrapping indexed `usageHistory.timestamp` in `datetime()` and allowing SQLite to choose the broad `provider` index; the observer now uses the existing read-only timestamp index when present, keeps offset-aware request parsing, and exact-filters normalized timestamps. Direct live reads completed in approximately 3–11 ms against the 2026-10-11 database without mutation. The Secretary structured receipt remains externally unavailable: Herdr/Codex transport and cleanup are proven, but Codex CLI `0.162.0` emitted no observed Secretary metrics/receipt; historical probes show the same capability boundary, so no local workaround or acceptance promotion was added.
- Fresh synthetic scaling evidence: baseline p95 reached 14.227 ms at 1,000 irrelevant history rows, while final p95 remained 2.353 ms with `query_count=3`, `selected_rows=2`, and `validated_rows=2`; this proves bounded observer behavior for the tested indexed workload, not a guarantee for provider schemas without a timestamp index.
- Source audit finds no router-to-Secretary provenance inflation, no request-count turn inference, no reporting authority edge, and no provider/Herdr/Codex mutation.
- One independent review confirms the reporting boundary is read-only and Delivery A remains unchanged.

## Completion Criteria

The plan is ready for completion verification when:

1. Delivery A acceptance and runtime-safety invariants remain proven.
2. 9router observation uses bounded request-first joins and independent row validation.
3. Availability, attribution, and coverage are explicit and non-collapsing.
4. Missing or partial provider/Secretary evidence remains useful without invented identity or zero values.
5. Live Secretary metrics contain only Secretary-native facts; provider evidence keeps provider provenance.
6. Reporting cannot alter acceptance, retry, continuation, settlement, cleanup, retirement, or integration.
7. Failure, ambiguity, outage, and scaling probes pass with sanitized evidence, including query-plan/index inspection, query/row/VM-step/progress/memory measurements, and manual p50/p95 results where physical-scan limits permit a meaningful comparison.
8. No new persistent Project OS telemetry state or external provider mutation exists.
9. GitHub protection is recorded as a separate approved handoff, not falsely claimed as local completion.
10. Delivery C remains explicitly deferred.

Only `skill-verification-before-completion` may set the final plan status to
`completed` after fresh repository evidence is reconciled into this plan.
