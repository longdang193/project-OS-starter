---
layer: change
artifact_type: plan
contract_version: "1"
status: active
template_id: implementation-plan
name: secretary-live-runtime-and-evidence-surface
targets:
  - docs/superpowers/plans/2026-10-08-secretary-live-runtime-and-evidence-surface-plan.md
  - scripts/herdr_main_launcher.py
  - scripts/project_os_runtime/secretary_adapter.py
  - scripts/project_os_runtime/secretary_evidence.py
  - scripts/project_os_runtime/secretary_receipts.py
  - scripts/secretary_live_runtime.py
  - scripts/secretary_live_pilot.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - tests/test_herdr_main_launcher.py
  - tests/test_secretary_adapter.py
  - tests/test_secretary_evidence.py
  - tests/test_secretary_receipts.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_live_pilot.py
  - pilot_artifacts/secretary-live-runtime/capability-inventory.json
  - pilot_artifacts/secretary-live-runtime/receipt-schema.json
  - pilot_artifacts/secretary-live-runtime/smoke-receipt.json
  - pilot_artifacts/secretary-live-runtime/workload-manifest.json
  - pilot_artifacts/secretary-live-runtime/comparison-report.md
---

# Secretary Live Runtime and Evidence Surface Plan

## Goal

Create one bounded, owned Secretary launch path through Codex and Herdr, then
prove whether that path emits trustworthy live evidence for matched CoS-only and
Secretary-assisted trials. Preserve Plan, Git, Worker, settlement, and CoS
acceptance ownership. Do not create a second workflow ledger, autonomous
Secretary authority, scheduler, message archive, or permanent transport mesh.

This plan follows the completed Secretary live-evidence pilot. The prior pilot
proved receipt validation and matched-trial mechanics but could not prove live
Secretary economics because no owned Secretary runtime emitted attributable
receipts. This plan closes that prerequisite instead of treating deterministic
contract output as live evidence.

## Implementation Outcomes

### Owned supervised Secretary launch path

Herdr launches one bounded Secretary attempt through the existing Codex runtime
using the configured `CODEX_HOME`, `config.toml`, and `auth.json` resolution
path. The launch is pinned to provider `9router`, carries explicit runtime
identity, and refuses provider fallback. The launch surface records only
sanitized metadata; credentials, authorization headers, prompts, and raw
transport bodies never enter tracked files or receipts.

### Producer-bound live receipt surface

Each attempt emits one sanitized receipt binding `task_id`, `plan_revision`,
`attempt_id`, and `run_id`, plus repository, workstream, plan, Git, worktree,
provider, model, controller, and session identity. The receipt records entry and
exit timestamps for CoS, Secretary, Worker, publication, settlement, and
acceptance; CoS and Secretary turns; human interventions; publication,
settlement, and acceptance outcomes; and token usage and cost as numeric values
or explicit `unknown`. Missing, mismatched, stale, duplicated, or untrusted
fields invalidate the receipt.

### Correctness-gated matched trial

The existing pilot harness reruns a frozen workload with paired CoS-only
baseline and CoS-plus-Secretary candidate arms. At least three valid pairs are
required, with a cap of five attempted pairs. Correctness is evaluated before
coordination deltas. Efficiency remains `INCONCLUSIVE` or
`BLOCKED_CAPABILITY` when live receipts, counters, or attribution are absent;
no benefit is inferred from deterministic or partial data.

## Scope Boundaries

- Secretary remains read-only and supervised; CoS keeps assignment,
  continuation, escalation, and acceptance authority.
- Plan and Git remain workflow truth; receipts and pilot artifacts are evidence,
  not a task ledger.
- Worker wrappers own execution facts; transport owns delivery and diagnostics;
  settlement owns lifecycle and eligibility.
- Use configured Codex `config.toml` and `auth.json` through `CODEX_HOME`; never
  print, copy, parse into receipts, or commit secret values.
- Use provider `9router` only. Missing route, missing auth, missing runtime
  identity, or missing receipt is a capability failure, not permission to invent
  fallback transport or provider behavior.
- Do not add a background service, scheduler, database, event bus, dashboard,
  autonomous retries, duplicate workflow state, or permanent adapter beyond
  this supervised bounded launch and receipt surface.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`
- Isolation: `optional worktree`; use fresh paired worktrees for trial arms
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed files, run declared local tests and validators, read configured Codex runtime metadata without exposing secrets, and create sanitized pilot artifacts
- User-approval actions: push, merge, publication, authentication changes, provider changes, installation, destructive cleanup, or any external write
- Parallel ownership: none; launch, receipt, smoke, and trial tasks share runtime and evidence contracts
- Sequential fallback: stop at the first missing runtime capability, record `BLOCKED_CAPABILITY`, and do not continue into comparative claims

## Coordination State

- Coordination owner: single lead controller.
- Coordination schema: `1`
- Branch: controller-selected `codex/secretary-live-runtime-evidence-surface`.
- Base commit: `581844d` (merged Secretary live-evidence pilot baseline).
- Expected workspace: tracked clean before execution; preserve unrelated untracked files and prior pilot artifacts.
- Next action: preserve validated smoke receipt and explicit trial disposition.
- Blockers: live Secretary runtime completion receipt unavailable; configured `9router` route only produced submission/target-resolution evidence.
- Residual disposition: `BLOCKED_CAPABILITY`; no attributable live Secretary execution or efficiency claim.

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | owned launch boundary and route inventory | `capability-inventory.json` |
| Task 2 | `completed` | current | `codex` | Task 1 | bounded Herdr/Codex launch and binding tests | launch tests and sanitized launch receipt |
| Task 3 | `completed` | current | `codex` | Task 2 | producer-bound sanitized receipt contract | `receipt-schema.json` and focused tests |
| Task 4 | `blocked` | current | `codex` | Task 2, Task 3 | one attributable live smoke receipt | `smoke-receipt.json` (`BLOCKED_CAPABILITY`) |
| Task 5 | `blocked` | current | `codex` | Task 4 | correctness-gated matched trials | `workload-manifest.json` and `comparison-report.md` (`BLOCKED_CAPABILITY`, 0 pairs) |
| Task 6 | `completed` | current | `codex` | Task 1–5 | final reconciliation and fresh verification | test and validator output |

## Task Breakdown

### Task 1: Establish runtime capability and launch contract

**Purpose:**
- Identify the existing Codex/Herdr process boundary and define the smallest
  owned Secretary launch request without guessing a provider, endpoint, or
  persistence layer.

**Task Function:**
- Source-first runtime capability inventory and contract definition.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: local source inspection and configured-runtime boundary are
  authoritative; no delegated execution is needed before the contract is fixed.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: contract is validated in Tasks 2–4 by direct tests and smoke
  evidence.

**Specification Coverage:**
- Owned Codex/Herdr launch path, `9router`-only routing, configured
  `config.toml`/`auth.json`, and required identity bindings.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_codex_runtime()`;
  `_codex_environment()`; `_codex_mcp_selection()`; `build_parser()`;
  `resolve_launch()`; `main()`
- Inspect: `scripts/dcode_project.py:_config_path()` and runtime-provider
  loading; `docs/operating_system/tooling/runtime-tool-resolution.md`
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md` Secretary and
  Herdr ownership sections
- Modify: `pilot_artifacts/secretary-live-runtime/capability-inventory.json`

**Dependencies:**
- Merged pilot baseline `581844d`.

**Authority:**
- Preauthorized local actions: inspect source and configured metadata, run
  non-mutating `--help`/capability probes, and write sanitized inventory JSON.
- Stop for: absent or ambiguous Secretary entrypoint, provider other than
  `9router`, unavailable configured Codex credentials, or any request to add
  fallback transport or external authentication.

**Steps:**
- [ ] Step 1: Map the existing Herdr Codex launch arguments, `CODEX_HOME`,
  `config.toml`, `auth.json`, provider/model resolution, and current receipt
  producers.
- [ ] Step 2: Define launch request fields: `task_id`, `plan_revision`,
  `attempt_id`, `run_id`, repository, workstream, plan identity, Git revision,
  worktree, controller ID, session ID, provider, and model.
- [ ] Step 3: Record route ownership, secret-handling rules, failure states,
  and the exact stop condition in `capability-inventory.json`.

**Verification:**
- [ ] `py -B scripts/herdr_main_launcher.py --help`
- Expected: current launcher exposes the inspected native path; inventory
  identifies exact owner and does not contain credential material.

**Exit Criteria:**
- Launch boundary, provider route, identity bindings, and capability gap are
  explicit. No implementation starts against an invented runtime.

### Task 2: Implement bounded Secretary launch through Herdr/Codex

**Purpose:**
- Launch one supervised Secretary attempt through existing native runtime
  ownership and return a sanitized launch identity without granting workflow or
  acceptance authority.

**Task Function:**
- Runtime boundary implementation with admission and failure handling.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: choose the lowest discovered profile that can modify the
  launcher safely and prove subprocess/runtime behavior.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent review of launch ownership, provider pinning,
  secret exclusion, and identity binding.

**Specification Coverage:**
- Owned launch path through Codex/Herdr; exact `9router` route; required
  `task_id`, `plan_revision`, `attempt_id`, and `run_id` binding.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:build_parser()`;
  `resolve_launch()`; `main()`; `_codex_runtime()`; `_codex_environment()`
- Modify: `scripts/herdr_main_launcher.py` launch request/result path
- Add or modify: `scripts/secretary_live_runtime.py` bounded
  request normalization and runtime identity projection
- Verify: `tests/test_herdr_main_launcher.py` and
  `tests/test_secretary_live_runtime.py`

**Dependencies:**
- Task 1 capability inventory and launch contract.

**Authority:**
- Preauthorized local actions: add bounded launch/request code, focused tests,
  and sanitized local launch fixtures; use configured runtime only.
- Stop for: missing live Secretary command or runtime identity, provider route
  mismatch, raw secret exposure, autonomous retry/authority behavior, or any
  need for new persistent transport state.

**Steps:**
- [ ] Step 1: Add explicit Secretary launch request validation and reject missing
  or conflicting `task_id`, `plan_revision`, `attempt_id`, and `run_id`.
- [ ] Step 2: Reuse Herdr's existing Codex home/environment resolution and
  subprocess ownership. Read `config.toml`/`auth.json` only through the native
  Codex path; keep raw credential content out of arguments, logs, and receipts.
- [ ] Step 3: Pin provider selection to `9router`; reject fallback or implicit
  provider substitution. Return runtime identity, provider, model, run ID, and
  timestamps as sanitized facts.
- [ ] Step 4: Preserve bounded grant, deadline, pane/session ownership, and
  controller-only acceptance semantics. Do not add scheduler, retry loop, or
  second task ledger.

**Verification:**
- [ ] `py -B -m pytest tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py`
- Expected: valid launch binds all four IDs and exact provider; missing IDs,
  route mismatch, malformed runtime identity, and secret-like output fail closed.

**Exit Criteria:**
- One owned supervised launch path exists or Task 2 records
  `BLOCKED_CAPABILITY` with the missing runtime fact and no guessed substitute.

### Task 3: Emit and validate producer-bound sanitized receipts

**Purpose:**
- Make live Secretary evidence trustworthy enough for comparison by binding
  every source, timestamp, counter, outcome, and cost field to one attempt.

**Task Function:**
- Backend evidence contract and redaction implementation.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: schema and security risk require a profile able to preserve
  existing receipt invariants while adding live runtime fields.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent check that receipt validation rejects stale,
  duplicated, mismatched, or secret-bearing evidence.

**Specification Coverage:**
- Sanitized receipts with timestamps, CoS turns, Secretary turns, human
  interventions, publication, settlement, acceptance, token usage, cost, and
  identity bindings.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/secretary_evidence.py:EvidenceSnapshot`;
  `build_evidence_snapshot()`
- Inspect: `scripts/secretary_live_pilot.py:validate_receipt()`;
  `compare_records()`; `prepare_manifest()`
- Add: `scripts/project_os_runtime/secretary_receipts.py` receipt dataclass,
  redaction, producer validation, source digest, and monotonic timestamp checks
- Modify: `scripts/secretary_live_pilot.py` to accept the live Secretary source
  and preserve explicit `unknown` token/cost values
- Verify: `tests/test_secretary_receipts.py`,
  `tests/test_secretary_evidence.py`, and `tests/test_secretary_live_pilot.py`

**Dependencies:**
- Task 2 launch result shape and producer identity.

**Authority:**
- Preauthorized local actions: add schema and validators, update focused tests,
  and write sanitized schema fixtures.
- Stop for: any design that copies Plan/Git/Worker state into a second ledger,
  accepts unbound counters, stores raw prompts or credentials, or promotes
  receipt validity to CoS acceptance.

**Steps:**
- [ ] Step 1: Define receipt envelope with `schema_version`, `pair_id`, `arm`,
  `run_id`, `attempt_id`, `task_id`, `plan_revision`, repository/workstream/
  worktree bindings, provider/model, controller/session identity, and source
  producer metadata.
- [ ] Step 2: Define monotonic ISO-8601 timestamps for `cos_entry`,
  `secretary_entry`, `worker_entry`, `publication`, `settlement`,
  `acceptance`, `secretary_exit`, `cos_exit`, and `run_finished`; permit null
  only where a phase was not reached and record the reason.
- [ ] Step 3: Define counters for `cos_turns`, `secretary_turns`,
  `human_interventions`, `publication_success`, `settlement_proven`,
  `acceptance_decision`, `token_usage`, and `cost`; token/cost use numeric
  values or literal `unknown`, never guessed zero.
- [ ] Step 4: Validate source ownership, all identity bindings, unique
  `run_id`/`attempt_id`, source digests, timestamp ordering, correctness flags,
  and secret redaction before comparison.

**Verification:**
- [ ] `py -B -m pytest tests/test_secretary_receipts.py tests/test_secretary_evidence.py tests/test_secretary_live_pilot.py`
- Expected: valid live receipts normalize to `live-attributed`; missing,
  mismatched, stale, duplicate, secret-bearing, or correctness-defective
  receipts are rejected or classified without benefit claims.

**Exit Criteria:**
- Receipt schema and validator prove producer-bound live evidence, with explicit
  `unknown` economics and no authority transfer.

### Task 4: Smoke-test one live Secretary receipt

**Purpose:**
- Prove the configured runtime can produce one attributable Secretary receipt
  before spending trial budget.

**Task Function:**
- Direct runtime boundary verification and capability disposition.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: smoke test requires controller-owned configured credentials
  and must not be delegated without explicit runtime access proof.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independently inspect sanitized receipt provenance and
  provider/model attribution.

**Specification Coverage:**
- Codex/Herdr launch through configured `config.toml` and `auth.json`, exact
  `9router` route, runtime identity, and all required bindings.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: Task 2 launcher and Task 3 receipt producer/validator
- Modify: `pilot_artifacts/secretary-live-runtime/smoke-receipt.json` only with
  sanitized output; update capability inventory on failure
- Verify: `scripts/secretary_live_runtime.py` and Herdr launch
  result boundary

**Dependencies:**
- Tasks 2 and 3 complete.

**Authority:**
- Preauthorized local actions: run one bounded local smoke attempt through the
  configured Codex/Herdr route and write sanitized evidence.
- Stop for: no attributable runtime receipt, provider/model mismatch, missing
  required timestamp/counter, auth/config failure, or any raw secret output.

**Steps:**
- [x] Step 1: Create one disposable smoke request with unique `task_id`,
  `plan_revision`, `attempt_id`, and `run_id`; do not reuse pilot receipts.
- [x] Step 2: Launch Secretary through Herdr using existing `CODEX_HOME`,
  `config.toml`, and `auth.json`; verify provider is exactly `9router`.
- [x] Step 3: Capture runtime identity and sanitized entry/exit receipt; validate
  producer bindings, timestamps, counters, publication, settlement, and
  acceptance outcome.
- [x] Step 4: If receipt is absent or incomplete, record `BLOCKED_CAPABILITY`;
  do not synthesize timestamps, token counts, cost, or Secretary turns.

**Verification:**
- [x] `py -B scripts/secretary_live_runtime.py smoke --output .\pilot_artifacts\secretary-live-runtime\smoke-receipt.json`
- Expected: one validated `live-attributed` receipt bound to all four IDs and
  provider `9router`, or a sanitized `BLOCKED_CAPABILITY` record naming the
  missing fact.

**Exit Criteria:**
- One live receipt exists and passes validation, or the plan stops before trials
  with an explicit capability disposition.

### Task 5: Run correctness-gated matched trials

**Purpose:**
- Measure paired coordination deltas only after live attribution is proven.

**Task Function:**
- Supervised matched-trial execution and evidence analysis.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: choose a profile able to preserve frozen workload identity,
  paired worktrees, and correctness-first analysis.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent review of pair matching, correctness gate, and
  metric calculation.

**Specification Coverage:**
- CoS-only baseline versus CoS-plus-Secretary candidate with shared workload,
  fresh worktrees, identity bindings, correctness gate, and separate economics.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_pilot.py:prepare_manifest()`;
  `validate_receipt()`; `compare_records()`
- Modify: `scripts/secretary_live_pilot.py` only where live receipt fields or
  trial disposition require it
- Add: `pilot_artifacts/secretary-live-runtime/workload-manifest.json` and
  `comparison-report.md`
- Verify: `tests/test_secretary_live_pilot.py` and normalized receipt records

**Dependencies:**
- Task 4 must return one validated live receipt; otherwise stop with
  `BLOCKED_CAPABILITY`.

**Authority:**
- Preauthorized local actions: execute bounded paired trials in fresh worktrees,
  write sanitized receipts and comparison report, and run local analysis.
- Stop for: incorrect result, stale evidence acceptance, unauthorized write,
  duplicate execution, publication failure, missing paired arm, or exhausted
  trial cap without three valid pairs.

**Steps:**
- [x] Step 1: Freeze one genuine cross-workstream dependency, plan revision,
  inputs, task order, Worker profile, correctness gate, and environment in the
  workload manifest.
- [x] Step 2: Run up to five paired trials: CoS-only baseline and CoS-plus-
  Secretary candidate. Bind each arm to unique `pair_id`, `run_id`, and
  `attempt_id`; keep all other inputs identical.
- [x] Step 3: Apply correctness gate before comparing interventions, turns,
  completion intervals, publication, settlement, acceptance, tokens, or cost.
- [x] Step 4: Report paired deltas and medians. Keep token/cost claims separate
  from turn/intervention claims; preserve `unknown` when provider omits them.

**Verification:**
- [x] `py -B scripts/secretary_live_pilot.py compare --manifest .\pilot_artifacts\secretary-live-runtime\workload-manifest.json --records-dir .\pilot_artifacts\secretary-live-runtime\records --output .\pilot_artifacts\secretary-live-runtime\comparison-report.md --capability-status AVAILABLE`
- Expected: `VERIFIED_BENEFIT`, `NO_MEASURED_BENEFIT`, or `INCONCLUSIVE` only
  after correctness and attribution gates; no invalid pair contributes to the
  comparison.

**Exit Criteria:**
- Three valid matched pairs produce an honest paired disposition, or the cap,
  correctness gate, or evidence gap produces explicit `INCONCLUSIVE` or
  `BLOCKED_CAPABILITY`.

### Task 6: Reconcile evidence and complete fresh verification

**Purpose:**
- Reconcile implementation, docs, receipts, test output, and plan state without
  overstating Secretary capability or efficiency.

**Task Function:**
- Final artifact verification and plan-state reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance and plan ledger remain controller-owned.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent final review of runtime boundary, receipt
  provenance, and trial disposition.

**Specification Coverage:**
- Completion criteria, explicit capability outcomes, maintained runtime docs,
  and clean distinction between live evidence and deterministic contract proof.

**Required Skills:**
- `skill-verification-before-completion`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: all Task 1–5 outputs and changed runtime/docs/tests
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`;
  `docs/operating_system/tooling/runtime-tool-resolution.md`; plan ledger and
  final artifacts
- Verify: repository contract, lifecycle, required-section, adapter-sync, and
  runtime-drift validators

**Dependencies:**
- Tasks 1–5 complete or explicitly dispositioned.

**Authority:**
- Preauthorized local actions: reconcile docs, plan evidence, sanitized
  artifacts, and run fresh local verification.
- Stop for: stale plan state, unresolved required task, failed required check,
  undocumented scope deviation, or any unsupported live-benefit claim.

**Steps:**
- [x] Step 1: Update runtime docs with the owned launch path, receipt producer
  boundaries, secret exclusions, failure states, and no-authority rule.
- [x] Step 2: Reconcile every task row with evidence, including explicit
  `BLOCKED_CAPABILITY` or `INCONCLUSIVE` records where applicable.
- [x] Step 3: Run focused tests, full suite, repository validators, and
  `git diff --check`; record fresh outputs before any completion status change.

**Verification:**
- [x] `py -B -m pytest tests/test_herdr_main_launcher.py tests/test_secretary_adapter.py tests/test_secretary_evidence.py tests/test_secretary_receipts.py tests/test_secretary_live_runtime.py tests/test_secretary_live_pilot.py`
- [x] `py -B -m pytest` (1011 passed, 1 skipped)
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope preflight --plan .\docs\superpowers\plans\2026-10-08-secretary-live-runtime-and-evidence-surface-plan.md`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope audit`
- [x] `py -B scripts/validate_planning_lifecycle.py --repo-root . --plan .\docs\superpowers\plans\2026-10-08-secretary-live-runtime-and-evidence-surface-plan.md --strict`
- [x] `py -B scripts/validate_template_required_sections.py --repo-root . --require-template-selection --document .\docs\superpowers\plans\2026-10-08-secretary-live-runtime-and-evidence-surface-plan.md`
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- [x] `git diff --check`
- Expected: fresh checks pass; docs and plan distinguish `live-attributed`,
  `BLOCKED_CAPABILITY`, `INCONCLUSIVE`, `VERIFIED_BENEFIT`, and
  `NO_MEASURED_BENEFIT` without private data.

**Exit Criteria:**
- Every required task has fresh proof or explicit capability disposition; no
  stale status, hidden blocker, secret, authority expansion, or unsupported
  efficiency claim remains.

## Decision Rules

Apply classifications in this order:

1. `BLOCKED_CAPABILITY`: no owned Secretary launch, no configured `9router`
   route, no attributable runtime identity, or no producer-bound receipt. Stop
   before matched trials.
2. `INCONCLUSIVE`: live receipts exist but fewer than three correctness-valid
   pairs remain after at most five attempted pairs, or required comparison
   counters remain `unknown`.
3. `VERIFIED_BENEFIT`: at least three valid pairs pass correctness and the
   existing pilot thresholds are met using paired medians; provider token/cost
   data is reported separately and never inferred.
4. `NO_MEASURED_BENEFIT`: at least three valid pairs pass correctness but the
   frozen intervention or completion thresholds are not met.

Any incorrect result, stale-evidence acceptance, unauthorized write, duplicate
execution, or publication failure invalidates the affected pair. Invalid pairs
cannot satisfy the minimum valid-pair requirement.

## Security and Ownership Checklist

- [ ] `config.toml` and `auth.json` are used only through configured Codex
  runtime resolution.
- [ ] No credential, token, authorization header, raw prompt, raw response, or
  raw transport body enters tracked files, logs, or receipts.
- [ ] `9router` is explicit; no provider fallback exists.
- [ ] `run_id`, `attempt_id`, `task_id`, and `plan_revision` bind every source.
- [ ] Receipt validity never implies task acceptance.
- [ ] Secretary cannot mutate Plan, Git, Worker settlement, or CoS acceptance.
- [ ] Pilot artifacts remain evidence, not workflow state.

## Verification

Final artifact verification runs the focused runtime, receipt, and pilot tests;
the full suite; repository contract, planning lifecycle, required-section,
adapter-sync, and runtime-drift validators; and `git diff --check` listed in
Task 6. Task-local smoke and comparison commands remain the source of trial
disposition and are not replaced by source inspection.

## Completion Criteria

The plan may move from `proposed` to `completed` only after
`skill-verification-before-completion` returns `verified`, all task rows have
fresh evidence or explicit capability dispositions, runtime documentation
matches source behavior, and the final report honestly states whether matched
Secretary efficiency was verified. A missing runtime closes as
`BLOCKED_CAPABILITY`; it does not become an implicit retry loop or an inferred
benefit.
