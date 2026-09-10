---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: herdr-lifecycle-evidence-follow-up
targets:
  - scripts/herdr_main_launcher.py
  - scripts/dcode_project.py
  - scripts/deepagents_result_contract.py
  - tests/test_herdr_main_launcher.py
  - tests/test_dcode_project.py
  - repo_config/starter-kit-manifest.json
  - docs/operating_system/governance/repo-governance.md
---

# Herdr Lifecycle Evidence Follow-Up Plan

## Goal

Repair lifecycle classification and producer evidence after commit
`3dfab60ab32b23e44632c0fa79c430693d27bfd7` without reopening or editing the
completed historical plan
`docs/superpowers/plans/2026-09-10-herdr-lifecycle-timing-completion-plan.md`.

Make DeepAgents outcomes single-path, cleanup receipts truthful, task
verification separate from execution, and performance evidence usable. Reduce
post-run observation only after receipt ordering is proven. Preserve Codex
acknowledge-and-return behavior, DeepAgents MCP isolation, role-view locking,
attempt correlation, legacy output fields, and unrelated workspace state.

## Implementation Outcomes

- Herdr classifies delivery, execution, observation, task result, cleanup, and
  return status from one final outcome record.
- Missing or conflicting DeepAgents receipts produce uncertain execution and
  reconciliation evidence instead of a false successful completion.
- `dcode-project` reports actual cleanup and descendant facts; modified role
  views retain recovery evidence.
- Receipt schema, validation, and serialization have one maintained owner.
- Task output distinguishes reported completion from independently verified task
  acceptance.
- Performance phases use observable boundaries, current monotonic time, and
  attempt-attributed occurrences.
- Observation reduction lands only when bounded evidence proves receipt and
  wrapper ordering; otherwise the optimization is recorded as deferred.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-receiving-code-review`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-performance-optimization`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared launcher, receipt contract, tests, manifest, and governance documentation; run focused tests, validators, adapter checks, and bounded task-owned Herdr probes without authentication, destructive cleanup, or external writes
- User-approval actions: commits, pushes, merges, authentication, external configuration writes, process termination outside task-owned probes, destructive cleanup, and edits outside declared targets
- Parallel ownership: none; launcher, worker, contract, tests, and docs share one lifecycle contract
- Sequential fallback: baseline and semantics, shared contract, canonical classification, producer truth, timing, measured observation, low-priority alignment, final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `3dfab60ab32b23e44632c0fa79c430693d27bfd7`
- Expected workspace: preserve current unrelated changes in `scripts/validate_planning_lifecycle.py`, `tests/test_validate_planning_lifecycle.py`, `.playwright-mcp/`, and `db/`; do not stage, delete, or rewrite them
- Next action: final verification gate
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | source/test contract map and behavior matrix | `203 passed`; planning validator passed; baseline failure initially exposed missing task profile metadata and was fixed in this plan |
| Task 2 | `completed` | current | `codex` | Task 1 | shared contract tests and clean bundle import | shared contract added; `231 passed` focused suite; starter-kit import path passes |
| Task 3 | `completed` | current | `codex` | Tasks 1–2 | conflicting-evidence lifecycle tests | `211 passed`; outcome matrix and legacy-field regression proof passed |
| Task 4 | `completed` | current | `codex` | Tasks 1–2 | cleanup and descendant-state tests | `113 passed`; modified owned view remains with marker and recovery paths |
| Task 5 | `completed` | current | `codex` | Task 3 | timing boundary and current-clock tests | `101 passed`; retry attribution, current finalization clock, unavailable readiness, and overlap union covered |
| Task 6 | `completed` | current | `codex` | Tasks 3–5 | bounded observation baseline and safe reduction or explicit deferral | optimization deferred; Herdr `0.9.0` help output does not prove pane-return ordering; bounded observation unchanged |
| Task 7 | `completed` | current | `codex` | Tasks 2–5; Task 6 completed or deferred | docs/config alignment and final verification | final focused tests, validators, adapter checks, drift checks, diff check, and Herdr API snapshot pass |

Only lead controller updates ledger. A checked item records accepted proof, not
intent.

## Task Breakdown

### Task 1: Establish current contract and behavior matrix

**Purpose:** Freeze current behavior before editing and define lifecycle
semantics that prevent a second result decision.

**Files And Symbols:** Inspect
`scripts/herdr_main_launcher.py:_read_deepagents_receipt`,
`_build_assignment_result`, `emit_assignment` inside `_main_body`,
  `_deepagents_completion_evidence`, `_record_performance_phase`,
  `_finalize_performance`; inspect
  `scripts/dcode_project.py:_remove_role_views`, `_run_bounded_worker`,
  `_publish_result_receipt`, `_controller_options`, `_result_options`; inspect
  `tests/test_herdr_main_launcher.py` and `tests/test_dcode_project.py`.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded source/test contract mapping with direct repository evidence.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent check of lifecycle semantics and preserved workspace state.

**Dependencies:** None.

**Steps:**
- [x] Record current field ownership for `delivery`, `execution`,
  `observation`, `task_result`, `cleanup`, `status`, `exit_code`, and
  `reconciliation_required`.
- [x] Define one outcome rule: receipt and observation facts are collected
  first; one classifier derives lifecycle fields, legacy aliases, and return
  code; serialization happens once.
- [x] Define the outcome matrix explicitly:
  - valid receipt, nonzero worker exit, completion marker: execution failed;
    marker cannot override it;
  - valid receipt, exit zero, report absent: execution completed; task
    acceptance remains unverified;
  - valid receipt, exit zero, cleanup preserved: execution completed; cleanup
    requires recovery; task acceptance is evaluated separately;
  - producer confirms process never started: start failed; never label it
    exited;
  - worker exit known, descendant termination unknown: preserve known exit and
    report descendant uncertainty;
  - missing, malformed, stale, or invalid receipt: execution unknown unless
    another authoritative producer fact establishes it;
  - confirmed prompt acceptance plus observation timeout: prompt acceptance
    remains confirmed; completion requires reconciliation.
- [x] Define return-code meaning: DeepAgents returns `0` for confirmed delivery
  plus worker exit `0` when no unresolved cleanup or lifecycle evidence remains;
  it returns `2` for missing/conflicting lifecycle evidence, preserved cleanup,
  or missing completion evidence, and preserves a known nonzero worker exit code
  for worker failure. The return code reports launch/lifecycle settlement, not
  independent task acceptance.
- [x] Define the existing task-verification boundary: this launcher receives no
  independent verifier input on the DeepAgents path. `task_result.state` may be
  `reported_completed` or `unverified`; `verified` can appear only when a
  caller supplies authoritative task acceptance evidence. No new verifier is
  added by this plan.
- [x] Define task verification: marker, report, worker exit, and cleanup alone
  cannot produce `verified`; legacy `task_accepted` derives from the classifier
  and cannot override it.
- [x] Define cleanup states: `removed`, `preserved`, and `unverified`; a
  preserved modified role view keeps ownership/recovery evidence.
- [x] Define return-code mapping: Codex acknowledged dispatch keeps existing
  zero-return behavior; DeepAgents missing/conflicting lifecycle evidence
  returns nonzero; confirmed nonzero worker exit cannot return successful
  completion.

**Authority:**
- Preauthorized local actions: inspect source, tests, Git state, and existing plans; record the matrix in this plan without editing implementation files.
- Stop for: unresolved status or return-code semantics that require product-owner input, evidence that current consumers require a conflicting contract, or unexpected workspace changes.

**Verification:** Confirm `HEAD`, current branch, and unrelated paths with
`git status --short --branch`; run
`py -3 scripts/validate_planning_lifecycle.py --repo-root .` and record any
failure caused by the pre-existing changes in
`scripts/validate_planning_lifecycle.py` and
`tests/test_validate_planning_lifecycle.py`; confirm no earlier plan is edited.

**Exit Criteria:** Matrix names every affected field, producer, consumer, and
terminal case required by Tasks 2–6.

### Task 2: Create one DeepAgents receipt contract

**Purpose:** Remove schema drift while keeping producer and consumer ownership
separate.

**Files And Symbols:** Add
`scripts/deepagents_result_contract.py`; modify
`scripts/dcode_project.py:_publish_result_receipt` and
`scripts/herdr_main_launcher.py:_read_deepagents_receipt`; modify
  `repo_config/starter-kit-manifest.json`; extend receipt tests in
  `tests/test_dcode_project.py` and `tests/test_herdr_main_launcher.py`.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: small shared-module change with focused contract tests.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent schema, import, and deployment-boundary review.

**Dependencies:** Task 1 complete and not blocked.

**Steps:**
- [x] Move schema identifier `dcode-project.result.v1`, 16 KiB limit, age
  limit, worker-state vocabulary, cleanup-state vocabulary, required fields,
  atomic encoding, and parsing/validation rules into the shared module.
- [x] Expose small functions only: `encode_result_receipt(payload)` and
  `parse_result_receipt(path, attempt_id)`. Parsing performs one bounded file
  read and validation with no sleep or retry loop; Herdr owns observation
  deadlines. Keep worker and cleanup facts owned by `dcode-project` and
  assignment classification owned by Herdr.
- [x] Make producer and consumer use the shared constants and functions.
- [x] Add the shared module to `sharedPaths.scripts` in
  `repo_config/starter-kit-manifest.json`.
- [x] Keep atomic publication owned by
  `dcode_project.py:_publish_result_receipt`, which writes a temporary file,
  flushes and syncs it, then replaces the destination. Encoding alone does not
  claim atomicity.
- [x] Test valid receipts, stale receipts, oversized receipts, malformed JSON,
  schema mismatch, attempt mismatch, invalid worker state, invalid cleanup
  state, invalid exit code, atomic replacement, and receipt cleanup.
- [x] Verify a generated bundle imports both `dcode_project.py` and
  `herdr_main_launcher.py` with the shared module present.

**Authority:**
- Preauthorized local actions: add the shared contract, update the two callers, update the manifest, and run focused contract and starter-kit tests.
- Stop for: deployment import failure, public receipt-field expansion beyond the matrix, or any need for a generic schema framework.

**Verification:**

```powershell
py -3 -m pytest tests/test_dcode_project.py tests/test_herdr_main_launcher.py -q
py -3 -m pytest tests/test_starter_kit_generation.py -q
py -3 scripts/validate_repo_config.py --repo-root .
```

**Exit Criteria:** One contract module owns receipt vocabulary and encoding;
producer and consumer pass focused tests; starter-kit import proof passes.

### Task 3: Add one canonical lifecycle classifier

**Purpose:** Prevent pane markers, receipt facts, and legacy fields from making
independent decisions.

**Files And Symbols:** Modify
`scripts/herdr_main_launcher.py:emit_assignment` inside `_main_body`; add
  `_classify_deepagents_outcome`; update
  `_build_assignment_result`; extend `tests/test_herdr_main_launcher.py`.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded lifecycle refactor with direct terminal-path tests.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent conflicting-evidence and legacy-field review.

**Dependencies:** Tasks 1–2 complete and not blocked.

**Steps:**
- [x] Collect delivery, pane observation, receipt, and wrapper-return facts
  before classification.
- [x] Make `_classify_deepagents_outcome` return execution, task result,
  cleanup, lifecycle status, failure kind, reconciliation requirement, and
  launcher exit code as one record.
- [x] Preserve prompt/delivery acceptance independently from task completion;
  completion timeout cannot erase confirmed prompt acceptance.
- [x] Treat a missing receipt as unknown execution, not successful completion.
- [x] Treat receipt worker exit `7` or any other nonzero exit as failure even
  when marker evidence says `COMPLETED`.
- [x] Treat a valid receipt with exit zero and no report as completed execution
  with unverified task acceptance, not as a failed worker.
- [x] Treat a valid receipt with exit zero and preserved cleanup as completed
  execution plus recovery-required cleanup; return `2` until cleanup ownership
  is settled.
- [x] Treat producer `start_failed` as start failure and preserve known worker
  exit separately from unknown descendant termination.
- [x] Treat cleanup state as independent from task result; cleanup failure or
  preservation cannot by itself decide task acceptance.
- [x] Make `_build_assignment_result` derive legacy aliases only from the
  classified record. Remove later field mutation that can leave status `completed`
  beside unknown or failed execution.
- [x] Keep receipt discard after classification only for a consumed terminal
  receipt with no recovery dependency. If wrapper lifetime or late publication
  remains uncertain, retain the receipt destination, attempt ID, and result-file
  path for the existing lifecycle owner; do not add a cleanup service.

**Authority:**
- Preauthorized local actions: edit Herdr classification and result construction and add focused regression tests for every matrix row.
- Stop for: a required consumer depends on contradictory legacy fields, automatic replay becomes necessary, or classifier logic needs a second serializer.

**Verification:** Add tests covering marker plus missing receipt, marker plus
conflicting worker exit, confirmed delivery plus completion timeout, receipt
worker exit `0`, receipt worker exit nonzero, malformed receipt, and
reconciliation output. Run:

```powershell
py -3 -m pytest tests/test_herdr_main_launcher.py -q
```

**Exit Criteria:** Every DeepAgents terminal path calls one classifier and one
result builder; no test permits successful completion with unknown or failed
worker evidence.

### Task 4: Make producer cleanup and descendant evidence truthful

**Purpose:** Publish facts established by the component that owns cleanup and
process termination.

**Files And Symbols:** Modify
`scripts/dcode_project.py:_unlink_if_exact`, `_remove_role_views`,
  `_run_bounded_worker`, `_run_tura_worker`, `_run_deepagents_worker`, and the
  `main` cleanup/finally block; extend `tests/test_dcode_project.py`.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: producer-owned cleanup and process-state correction with focused tests.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent recovery, preservation, and termination-state review.

**Dependencies:** Tasks 1–2 complete and not blocked.

**Steps:**
- [x] Make cleanup inspect each owned view after attempted removal and return
  explicit state plus remaining owned paths and marker state.
- [x] Preserve the ownership marker when modified or otherwise unverified files
  remain; publish `preserved` or `unverified`, set `recovery_required`, and keep
  exact recovery identities.
- [x] Publish `removed` only after all owned views and the marker are absent.
- [x] Make worker execution expose descendant evidence only after the bounded
  worker owner establishes it. Use `not_started` for failures before process
  creation, `terminated` only after confirmed wait/termination, and
  `unknown` when process lifetime is not established.
- [x] Keep timeout cleanup and Windows process-tree behavior unchanged unless
  required to make receipt facts accurate.
- [x] Publish the receipt from actual cleanup and worker facts, including
  recovery state.
- [x] Prove idempotency: repeat cleanup after user modification preserves the
  modified file and recovery marker.

**Authority:**
- Preauthorized local actions: edit worker and cleanup fact production and run mocked process/role-view tests plus bounded Windows-safe probes.
- Stop for: process-tree termination cannot be proven on the supported Windows path, cleanup would delete user-modified content, or recovery evidence would be lost.

**Verification:** Add tests for exact-content removal, modified-content
preservation, missing marker, malformed marker, cleanup failure, worker start
failure, worker timeout, descendant termination, and receipt contents. Run:

```powershell
py -3 -m pytest tests/test_dcode_project.py -q
```

**Exit Criteria:** Receipt cleanup and descendant fields match observed owner
facts; modified role views remain recoverable.

### Task 5: Correct timing boundaries and finalization

**Purpose:** Make performance output usable for later optimization decisions.

**Files And Symbols:** Modify
`scripts/herdr_main_launcher.py:_PERFORMANCE_PHASES`,
  `_record_performance_phase`, `_record_performance_attempt`,
  `_finalize_performance`, and `resolve_launch`; extend
  `tests/test_herdr_main_launcher.py`.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: deterministic timing correction with no external dependency.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent boundary, overlap, and retry-attribution review.

**Dependencies:** Task 3 complete and not blocked.

**Steps:**
- [x] Rename the current pre-command `worker_initialization` measurement to
  `launch_preparation`.
- [x] Keep `worker_initialization` unavailable until an observable worker
  start/readiness boundary exists; do not infer readiness from preparation.
- [x] Preserve delivery timing around the actual delivery operation, not around
  earlier worker-preparation work.
- [x] Attribute pre-attempt `preflight` and `target_discovery` phases to the
  existing invocation/dispatch identity and explicitly omit `attempt_id` until
  the worker attempt exists. Attribute delivery, observation, retirement, and
  retry phases to their attempt.
- [x] Add `attempt_id` to every attempt-owned phase occurrence and keep
  aggregate counts derived from those occurrences.
- [x] Mark phase durations as inclusive operation durations. Do not calculate
  `unattributed_duration_ms` by subtracting overlapping phase sums; derive it
  from non-overlapping timeline segments, or set it to `None` with an explicit
  overlap reason.
- [x] Make `_finalize_performance` sample `time.monotonic()` at finalization
  unless an explicit test clock is passed; never reuse `_last_monotonic` as the
  default final timestamp.
- [x] Include receipt parsing, result construction, and cleanup in total
  duration and retain unattributed duration when phase ownership is absent.

**Authority:**
- Preauthorized local actions: edit timing helpers and phase callers and run deterministic clock tests.
- Stop for: no observable boundary exists for a proposed measured phase, a public phase rename breaks an undeclared consumer, or timing changes alter lifecycle classification.

**Verification:** Add deterministic tests that advance the clock after the last
phase record, verify current finalization time, verify attempt attribution, and
verify DeepAgents readiness remains unavailable. Run:

```powershell
py -3 -m pytest tests/test_herdr_main_launcher.py -q
```

**Exit Criteria:** Phase names match observable work, final duration includes
trailing work, and every measured occurrence identifies its attempt.

### Task 6: Measure and conditionally reduce DeepAgents observation work

**Purpose:** Remove redundant pane polling only when command and receipt
ordering are proven.

**Files And Symbols:** Inspect and, only after baseline proof, modify
`scripts/herdr_main_launcher.py:_deepagents_completion_snapshot`,
  `_deepagents_completion_evidence`, `_read_deepagents_receipt`, and the
  DeepAgents branch of `_main_body`; extend
  `tests/test_herdr_main_launcher.py`.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: conditional optimization gated by measured runtime evidence.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent ordering, subprocess-count, and semantic-regression review.

**Dependencies:** Tasks 3–5 complete and not blocked.

**Steps:**
- [x] Establish baseline using existing subprocess metrics for receipt-present,
  receipt-absent, delayed-receipt, wrapper-failure, and worker-live cases.
- [x] Prove whether successful `pane run` return establishes wrapper
  termination and receipt publication ordering on the supported Windows path.
- [x] Record the installed Herdr version and the exact `pane run` command
  behavior used for the probe. One successful probe is evidence for that
  invocation, not a general command guarantee.
- [x] If proven, check the attempt-owned receipt immediately after return, stop
  redundant lifecycle polling, and take at most one final pane snapshot for
  required report/diagnostic evidence.
- [x] If not proven, retain one bounded observer loop and make receipt
  availability a cheap input without adding a second timeout budget.
- [x] Never resubmit on receipt absence or transport ambiguity; emit
  reconciliation evidence.
- [x] Keep the existing 60-second observation bound for paths that still need
  observation; no watcher, daemon, cache, or event bus.
- [x] Compare before/after subprocess counts and classification across the same
  deterministic matrix. The optimization passes only if terminal-receipt paths
  use no more than one final `process-info` and one final `pane read`, with no
  lifecycle regression.

**Authority:**
- Preauthorized local actions: run bounded mocked and task-owned Windows probes; edit observation code only after ordering proof and baseline capture.
- Stop for: subprocess counts do not improve without semantic loss, or live probing requires authentication or unrelated process termination. If blocking-return semantics cannot be established, defer immediate-return optimization, preserve bounded observation, and allow receipt-aware early termination only where attributable evidence justifies it.

**Verification:** Run focused tests and record baseline/current subprocess
metrics in this plan. If safe reduction is not proven, record explicit
deferral and leave observation behavior unchanged.

**Exit Criteria:** Safe reduction lands with regression proof, or measured
deferral is recorded without changing semantics. Tasks 1–5 remain deliverable
when Task 6 defers optimization.

**Measured Deferral (2026-09-10):** Installed Herdr reports `0.9.0`. `herdr
pane run --help` exposes only the pane-command shape; it does not establish
that a successful return means wrapper termination or receipt-publication
ordering. Deterministic observation probes against the current implementation
used two pane subprocesses for receipt-present terminal text, receipt-absent
terminal text, and one worker-live snapshot; delayed reports cost two
subprocesses per observation snapshot. Wrapper failure returns before pane
observation. No before/after reduction claim is made. Immediate-return
optimization is deferred; bounded observation and reconciliation semantics stay
unchanged until a task-owned Windows probe proves ordering without
authentication or unrelated process termination.

### Task 7: Align low-priority ownership and complete verification

**Purpose:** Remove confirmed documentation drift and parser duplication after
runtime correctness is stable.

**Files And Symbols:** Modify
`scripts/dcode_project.py:_controller_options`, `_result_options`, and
`_resolve_executor`; update
`tests/test_dcode_project.py`; update
  `docs/operating_system/governance/repo-governance.md`; update
  `repo_config/starter-kit-manifest.json` only when Task 2 changes require it.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: narrow parser and canonical-document alignment after runtime fixes.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent compatibility and generated-surface review.

**Dependencies:** Tasks 2–5 complete; Task 6 completed or explicitly deferred.

**Steps:**
- [x] Make `_controller_options()` return one parsed options record containing
  child arguments, MCP selections, handoff file, role, executor, result file,
  and attempt ID; remove the second scan in `_result_options()`.
- [x] Inspect the `dcode-project` wrapper contract before changing propagation.
  Keep direct `dcode-project` default-executor compatibility until all internal
  callers pass explicit `--executor`; add the flag only when the wrapper does
  not already supply it, and test that exactly one executor argument reaches the
  worker.
- [x] Remove stale `compatibility` ownership from
  `docs/operating_system/governance/repo-governance.md`; keep provider protocol
  compatibility owned by runtime configuration documentation.
- [x] Do not change topology policy, add caches, trim instructional skills, or
  introduce a registry/framework in this plan.
- [x] Run generated-surface checks only if a canonical generated input changed.

**Authority:**
- Preauthorized local actions: edit parser, explicit internal executor propagation, and canonical governance text; run parser, metadata, config, and generated-surface checks.
- Stop for: direct compatibility callers are not identified, generated ownership is unclear, or documentation requires reopening a completed historical plan. Repair routine bundle/import failures within declared scope; escalate only when the deployment boundary or consumer contract must change.

**Verification:**

```powershell
py -3 -m pytest tests/test_dcode_project.py -q
py -3 scripts/validate_repo_contracts.py --repo-root . --fast
py -3 scripts/validate_repo_config.py --repo-root .
py -3 scripts/validate_agent_metadata_schema.py
py -3 scripts/validate_generated_header_format.py
py -3 scripts/sync_agent_adapters.py --all-platforms --check
py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check
```

**Exit Criteria:** Parser has one source of truth, internal executor selection
is explicit, governance no longer assigns compatibility to profiles, and all
affected generated/config surfaces pass checks.

## Non-Goals

- No edits to completed historical plans.
- No new watcher, daemon, cache, scheduler, janitor, event bus, registry, or
  generic lifecycle framework.
- No automatic replay after uncertain delivery or missing receipt.
- No change to Codex prompt acknowledgement semantics.
- No POSIX/WSL process-tree expansion without a separate support decision.
- No provider credentials, MCP project configuration, external authentication,
  or unrelated cleanup.
- No topology-policy consolidation or skill-content rewrite.
- No performance claim without identical before/after workload and evidence.

## Verification

Run once after Tasks 2–7 complete; rerun focused tests only after relevant code
changes:

```powershell
py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_dcode_project.py -q
py -3 -m pytest tests/test_starter_kit_generation.py -q
py -3 scripts/validate_repo_contracts.py --repo-root . --fast
py -3 scripts/validate_repo_config.py --repo-root .
py -3 scripts/validate_agent_metadata_schema.py
py -3 scripts/validate_generated_header_format.py
py -3 scripts/validate_planning_lifecycle.py --repo-root .
py -3 scripts/sync_agent_adapters.py --all-platforms --check
py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check
git diff --check
git status --short --branch
herdr api snapshot
```

Direct boundary proof must cover the actual `_main_body()` DeepAgents path with
attempt-owned receipt input and final JSON output. Mocked proof covers malformed,
missing, delayed, conflicting, nonzero-worker, preserved-cleanup, and observer
failure cases. Final state proof confirms receipt discard, role-marker
retention when recovery is required, and no changes to the pre-existing
unrelated paths.

Use `skill-verification-before-completion` before changing this plan to
`status: completed`. Failed mandatory proof leaves the affected task `blocked`.

## Completion Criteria

1. One classifier derives DeepAgents lifecycle fields, legacy aliases,
   reconciliation, and return code.
2. Missing or conflicting receipt evidence cannot produce successful completed
   execution.
3. Modified role views remain recoverable and cleanup receipts state actual
   results.
4. Task verification is not inferred from worker exit, marker, report, or
   cleanup alone.
5. Receipt schema and serialization have one maintained owner and clean bundle
   imports pass.
6. Timing phases use observable boundaries, current finalization time, and
   attempt-attributed occurrences.
7. Observation reduction is measured and safe, or explicitly deferred while
   bounded observation remains unchanged.
8. Parser and governance updates pass focused and repository validators.
9. Historical plans and current unrelated tracked/untracked paths remain
   unchanged.
10. `skill-verification-before-completion` returns `verified` before plan status
    changes from `proposed` to `completed`.
