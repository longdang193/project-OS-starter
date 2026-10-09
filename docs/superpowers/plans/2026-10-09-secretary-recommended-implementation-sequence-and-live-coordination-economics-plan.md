---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: secretary-recommended-implementation-sequence-and-live-coordination-economics
targets:
  - docs/superpowers/plans/2026-10-09-secretary-recommended-implementation-sequence-and-live-coordination-economics-plan.md
  - scripts/project_os_runtime/secretary_receipts.py
  - scripts/secretary_live_runtime.py
  - scripts/secretary_live_pilot.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - tests/test_secretary_receipts.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_live_pilot.py
  - pilot_artifacts/secretary-live-coordination-economics/capability-inventory.json
  - pilot_artifacts/secretary-live-coordination-economics/workload-manifest.json
  - pilot_artifacts/secretary-live-coordination-economics/smoke-receipt.json
  - pilot_artifacts/secretary-live-coordination-economics/edge-case-probes.json
  - pilot_artifacts/secretary-live-coordination-economics/comparison-report.md
---

# Secretary Recommended Implementation Sequence and Live Coordination Economics Plan

## Goal

Correct live Secretary evidence semantics, make trial admission consume current
validated receipts, preserve diagnostics, add thin supervised pilot accounting,
and measure coordination economics only when source-owned runtime evidence exists.

Do not add a second workflow ledger, autonomous Secretary authority, scheduler,
message archive, database, transport mesh, universal envelope, or manual
capability override. Plan and Git remain workflow truth; source owners produce
facts; validators validate; controllers decide.

## Implementation Outcomes

- Live receipts validate schema, identity, independent runtime provenance, and
  sanitization before they can support readiness.
- Pilot admission consumes current smoke evidence and keeps blocked and
  interrupted attempts visible.
- Comparison reports separate correctness-valid paired deltas from
  failure-inclusive totals and preserve `unknown`/undefined economics.
- Native Codex configuration remains the only credential boundary; provider
  `9router` is required and no fallback is allowed.
- Live Secretary economics is explicitly blocked until an owned entrypoint emits
  attributable receipts.

## Verdict Review

PR #62 direction is accepted, with five execution corrections:

- Verify approved base and candidate materialization before referencing missing
  modules or interfaces.
- Make uncommitted candidate worktree content explicit and digest-bound.
- Define native Codex credential consumption through one `CODEX_HOME`; require
  `9router`; never copy or publish `config.toml` or `auth.json` values.
- Execute blocked-admission and interrupted-attempt probes separately; fixtures
  cannot satisfy live evidence.
- Separate valid-pair deltas from failure-inclusive totals. Zero accepted
  outcomes are undefined; missing required cost is `unknown`.

Live economics remains `BLOCKED_CAPABILITY` until an owned Secretary entrypoint
emits attributable runtime receipts. Deterministic contract tests are not live
efficiency evidence.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: optional worktrees; candidate source must be explicitly materialized
- Commit policy: no commits during execution
- Provider: configured Codex `9router` only; native `config.toml` and `auth.json`
- Stop conditions: authentication change, provider fallback, secret exposure,
  missing attribution, unsafe retry, or unauthorized external mutation

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/launch-preparation-convergence`
- Base commit: `82793195d0d5abb4c91fb69d78d5c308c46a9732`
- Expected workspace: preserve unrelated untracked files and prior plans
- Next action: retain `INCONCLUSIVE` economics until provider exposes attributable cost/token usage
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 0 | `completed` | current | `codex` | none | approved-base and candidate-materialization proof | capability inventory |
| Task 1 | `completed` | current | `codex` | Task 0 | runtime and source-owner inventory | capability inventory |
| Task 2 | `completed` | current | `codex` | Task 1 | completion, credential-boundary, and attempt binding contract | focused tests and smoke |
| Task 3 | `completed` | current | `codex` | Task 2 | receipt provenance and schema validation | receipt tests and smoke |
| Task 4 | `completed` | current | `codex` | Task 3 | trial validity and failure-inclusive comparison | pilot tests and manifest |
| Task 5 | `completed` | current | `codex` | Task 4 | receipt-driven admission and diagnostics | pilot CLI and probes |
| Task 6 | `completed` | current | `codex` | Task 5 | sparse communication and runtime docs | docs and adapter checks |
| Task 7 | `completed` | current | `codex` | Task 6 | live smoke, edge probes, and paired economics | implementation complete; legacy smoke/trial fixtures reclassified `UNVERIFIED_PROBE`; live economics `INCONCLUSIVE` |
| Task 8 | `completed` | current | `codex` | Task 0, Task 1, Task 2, Task 3, Task 4, Task 5, Task 6, Task 7 | fresh final verification | full suite and validators |

## Task Breakdown

### Task 0: Verify approved base and candidate materialization

**Purpose:**
- Prove prerequisite revision, source snapshot, and arm identity before execution.

**Task Function:**
- Repository and experiment identity preflight.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Git and worktree identity remain controller-owned.

**Required Skills:**
- `skill-backend-verification`
- `skill-using-git-worktrees`

**Files And Symbols:**
- Inspect: pinned base, named modules/tests, current diff, and worktrees
- Modify: `pilot_artifacts/secretary-live-coordination-economics/capability-inventory.json`

**Dependencies:**
- none

**Authority:**
- Preauthorized local actions: inspect Git state, create disposable worktrees, and write sanitized digests.
- Stop for: absent prerequisite, unrelated mutation, secret exposure, or overwrite.

**Steps:**
- [x] Verify exact base and record absent Secretary files without guessing implementation.
- [x] Materialize baseline from pinned base and candidate from base plus reviewed source snapshot.
- [x] Record source/workload/plan identity and reject drift.

**Verification:**
- [x] `git status --short --branch`
- [x] `git worktree list --porcelain`
- [x] `git diff --check`

**Exit Criteria:**
- Candidate and baseline identities are explicit; missing runtime is a capability disposition.

### Task 1: Inventory live capability and source ownership

**Purpose:**
- Identify Codex/Herdr boundary, attempt owner, receipt source, provider, and
  Secretary entrypoint.

**Task Function:**
- Source-first runtime capability mapping.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: configured runtime inspection requires controller authority.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py`, runtime docs, profiles, and Codex metadata
- Modify: `pilot_artifacts/secretary-live-coordination-economics/capability-inventory.json`

**Dependencies:**
- Task 0 complete

**Authority:**
- Preauthorized local actions: inspect configured metadata without exposing secrets.
- Stop for: authentication, provider change, installation, secret exposure, or missing runtime owner.

**Steps:**
- [x] Map launcher, Codex, Herdr, CoS, Worker, settlement, acceptance, and attempt ownership.
- [x] Resolve one native `CODEX_HOME`; verify `config.toml` and `auth.json` presence without reading values into artifacts.
- [x] Record configured `9router` route and missing Secretary entrypoint as `BLOCKED_CAPABILITY`.

**Verification:**
- [x] Inspect inventory against source symbols and runtime docs.

**Exit Criteria:**
- Every claimed capability has an owner and evidence source; missing live capability is explicit.

### Task 2: Correct completion and attempt correlation

**Purpose:**
- Keep Secretary smoke completion separate from Worker completion and preserve
  launcher-owned `attempt_id`.

**Task Function:**
- Runtime evidence contract correction.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: runtime boundary remains controller-owned.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: existing launcher completion and attempt evidence
- Modify: `scripts/secretary_live_runtime.py`, focused runtime tests

**Dependencies:**
- Task 1 complete

**Authority:**
- Preauthorized local actions: edit local contracts/tests and run bounded local probes.
- Stop for: live activation, retry, lifecycle expansion, or unresolved attempt ownership.

**Steps:**
- [x] Add failing tests for submitted-only, mismatch, missing observer, valid completion, and provider mismatch.
- [x] Implement operation-specific completion evidence without copying Worker `TaskResult`.
- [x] Reject stale/caller-supplied attempt mismatch and preserve sanitized diagnostics.
- [x] Prove native home propagation, `9router` enforcement, auth failure closure, and no credential output.

**Verification:**
- [x] `py -B -m pytest tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py -q`

**Exit Criteria:**
- `READY` means observed completion with launcher-bound identity; missing observer blocks.

### Task 3: Enforce receipt schema and independent provenance

**Purpose:**
- Reject unsupported versions, synthetic sources, stale bindings, and sensitive fields.

**Task Function:**
- Source-bound receipt validation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: narrow contract, test-driven.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/secretary_receipts.py`
- Verify: receipt/runtime tests and sanitized smoke evidence

**Dependencies:**
- Task 2 complete

**Authority:**
- Preauthorized local actions: edit receipt validators, sanitizers, tests, and sanitized evidence.
- Stop for: source fabrication, secret-bearing output, unsupported schema migration, or unobserved provenance.

**Steps:**
- [x] Add tests for unsupported version, fake producer, synthetic provenance, stale binding, and sensitive fields.
- [x] Require runtime producer/source references and observed provenance.
- [x] Sanitize credentials, prompts, raw transport bodies, and unfiltered errors.

**Verification:**
- [x] `py -B -m pytest tests/test_secretary_receipts.py tests/test_secretary_live_runtime.py -q`

**Exit Criteria:**
- Only schema-supported, source-backed, sanitized receipts validate.

### Task 4: Make matched trials correctness-gated and complete

**Purpose:**
- Freeze comparable inputs, retain all attempts, and compute valid-pair and
  failure-inclusive economics separately.

**Task Function:**
- Experimental validity and comparison mathematics.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: comparison owner and thresholds are explicit.

**Required Skills:**
- `skill-test-driven-development`
- `skill-performance-optimization`

**Files And Symbols:**
- Modify: `scripts/secretary_live_pilot.py`, `tests/test_secretary_live_pilot.py`, workload manifest

**Dependencies:**
- Task 3 complete

**Authority:**
- Preauthorized local actions: edit comparison contracts and deterministic local fixtures.
- Stop for: workload drift, unmatched arms, missing correctness proof, hidden failed attempts, or synthetic live claims.

**Steps:**
- [x] Define workload digest, pair/arm bindings, minimum pairs, attempt cap, and thresholds.
- [x] Test unmatched pairs, duplicates, partial attempts, invalid correctness, and later eligible pairs.
- [x] Compute deltas from all eligible pairs with mutually exclusive status precedence.
- [x] Include every attempt and recovery cost in arm totals; zero accepted outcomes are undefined; missing costs are `unknown`.

**Verification:**
- [x] `py -B -m pytest tests/test_secretary_live_pilot.py -q`

**Exit Criteria:**
- No invalid, unmatched, or synthetic experiment can produce `VERIFIED_BENEFIT`.

### Task 5: Add receipt-driven admission and preserve diagnostics

**Purpose:**
- Replace manual capability overrides with validated smoke admission.

**Task Function:**
- Supervised pilot admission and failure explanation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: thin CLI composition avoids new lifecycle ownership.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/secretary_live_pilot.py`, tests, and sanitized artifacts

**Dependencies:**
- Task 4 complete

**Authority:**
- Preauthorized local actions: edit pilot admission, diagnostics, tests, and sanitized artifacts.
- Stop for: manual availability override, automatic retry, unsafe target retry, or external mutation.

**Steps:**
- [x] Add supervised pilot composition and preserve diagnostic CLI entry.
- [x] Consume current smoke receipt; reject capability mismatch and stale facts.
- [x] Preserve bounded admission, failure category, and recovery disposition.

**Verification:**
- [x] `py -B scripts/secretary_live_pilot.py --help`
- [x] `py -B -m pytest tests/test_secretary_live_pilot.py tests/test_herdr_main_launcher.py -q`

**Exit Criteria:**
- Blocked smoke starts no trial; ready smoke admits only bounded authorized work.

### Task 6: Align sparse communication and runtime documentation

**Purpose:**
- Document ownership and credential/evidence boundaries without adding transport or ledger state.

**Task Function:**
- Runtime ownership and documentation reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: canonical operating-system docs remain lead-owned.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: `docs/operating_system/tooling/runtime-tool-resolution.md`

**Dependencies:**
- Tasks 1–5 complete

**Authority:**
- Preauthorized local actions: update canonical docs and run required sync checks.
- Stop for: role expansion, duplicate ledger/state, generated-file hand edit, or new transport.

**Steps:**
- [x] Document source ownership, receipt boundaries, native Codex config/auth use, and no-authority rule.
- [x] Document `9router` requirement and blocked fallback semantics.
- [x] Run adapter generation checks.

**Verification:**
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check`

**Exit Criteria:**
- Docs preserve sparse communication and source-owned evidence.

### Task 7: Run live coordination economics experiment

**Purpose:**
- Measure coordination economics only after live smoke and trial correctness gates pass.

**Task Function:**
- Attributable paired-runtime measurement.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: live activation and acceptance remain lead-controlled.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independent audit of receipts and claims.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:run_smoke()` and pilot comparison
- Modify: smoke, edge-case, and comparison artifacts

**Dependencies:**
- Tasks 0–6 complete; validated smoke must be `READY` before trials

**Authority:**
- Preauthorized local actions: run bounded smoke/probes and write sanitized evidence artifacts.
- Stop for: missing receipt, target drift, failed correctness, duplicate execution, publication failure, or secret exposure.

**Steps:**
- [x] Run native configured smoke; classify `READY` or `BLOCKED_CAPABILITY`.
- [x] Run blocked-smoke admission probe; prove zero trials started.
- [x] Run interrupted-attempt accounting probe; preserve identity and unresolved settlement.
- [x] If `READY`, run matched CoS-only and CoS-plus-Secretary arms with fixed inputs.
- [x] Record attributed live timestamps, turns, interventions, outcomes, tokens, and costs.
- [x] Compute paired deltas and classify `BLOCKED_CAPABILITY`, `NOT_RUN`, `INCONCLUSIVE`, `NO_MEASURED_BENEFIT`, or `VERIFIED_BENEFIT`.

**Verification:**
- [x] Inspect sanitized smoke, workload, edge-case, and comparison artifacts.
- Expected: no live efficiency claim without owned entrypoint, attributable receipt, correctness-valid pairs, and known economics.

**Exit Criteria:**
- Runtime surface implementation is complete; committed legacy smoke/trial fixtures are `UNVERIFIED_PROBE` under current receipt validation; live economics is `INCONCLUSIVE` because provider-reported token usage and cost are unavailable.

### Task 8: Reconcile and verify final artifacts

**Purpose:**
- Prove source, tests, docs, artifacts, and plan state agree.

**Task Function:**
- Final verification and plan reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final verification and status transition are controller-owned.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect all changed runtime, tests, docs, artifacts, and plan files.

**Dependencies:**
- Tasks 0–7 complete or explicitly blocked with retained evidence

**Authority:**
- Preauthorized local actions: run fresh validators and reconcile sanitized artifacts.
- Stop for: stale proof, failed check, unsupported efficiency claim, unrelated mutation, merge, or push.

**Steps:**
- [x] Inspect final diff, tracked/untracked state, generated surfaces, and artifacts.
- [x] Run focused tests, full suite, repository validators, adapter sync, runtime drift, and whitespace checks.
- [x] Record completed Task 7 with probe-only legacy evidence and `INCONCLUSIVE` economics; do not treat fixtures as correctness-valid trials.

**Verification:**
- [x] `py -B -m pytest -q`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope audit`
- [x] `py -B scripts/validate_planning_lifecycle.py --repo-root . --plan .\docs\superpowers\plans\2026-10-09-secretary-recommended-implementation-sequence-and-live-coordination-economics-plan.md --strict`
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- [x] `git diff --check`

**Exit Criteria:**
- All local implementation checks pass; live economics remains explicitly inconclusive without cost/token attribution.

## Verification

- `py -B -m pytest -q`
- `py -B scripts/validate_repo_contracts.py --repo-root . --scope preflight --plan .\docs\superpowers\plans\2026-10-09-secretary-recommended-implementation-sequence-and-live-coordination-economics-plan.md`
- `py -B scripts/validate_repo_contracts.py --repo-root . --scope audit`
- `py -B scripts/validate_planning_lifecycle.py --repo-root . --plan .\docs\superpowers\plans\2026-10-09-secretary-recommended-implementation-sequence-and-live-coordination-economics-plan.md --strict`
- `py -B scripts/validate_template_required_sections.py --repo-root . --require-template-selection --document .\docs\superpowers\plans\2026-10-09-secretary-recommended-implementation-sequence-and-live-coordination-economics-plan.md`
- `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- `py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- `git diff --check`

## Completion Criteria

1. Receipt validation is source-backed, operation-specific, sanitized, and tested.
2. Admission and comparison retain all attempts, freeze inputs, and gate benefit on correctness.
3. Pilot remains thin and supervised; no second lifecycle or ledger exists.
4. Failure-inclusive economics distinguishes unknown and undefined values.
5. Native Codex uses configured `config.toml` and `auth.json` with `9router`; no fallback or secret publication.
6. Owned Secretary runtime emits attributable sanitized receipts through Herdr/Codex; no synthetic live claim exists.
7. Fresh local verification passes; Task 7 records probe-only legacy fixtures and `INCONCLUSIVE` economics because current receipt validation cannot establish correctness-valid pairs or cost/token attribution.
