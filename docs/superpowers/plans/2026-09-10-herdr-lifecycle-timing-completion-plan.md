---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: herdr-lifecycle-timing-completion
targets:
  - scripts/herdr_main_launcher.py
  - scripts/dcode_project.py
  - tests/test_herdr_main_launcher.py
  - tests/test_dcode_project.py
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - generated_agents/claude/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/codex/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md
---

# Herdr Lifecycle And Timing Completion Plan

## Goal

Complete correctness work identified in the review of commit
`53ab34b1c298fcdbd526b4cbe9e1e98a7adf5093`. Make Herdr terminal evidence
single-path, producer-owned, truth-preserving, and correctly timed. Repair the
canonical CoS grant contract and apply only measured, low-risk repeated-work
reductions.

Do not reopen or edit completed historical plans. Do not add caching, polling
daemons, broader orchestration, unsupported watchdog behavior, or POSIX worker
cleanup without a separate support decision.

## Review Disposition

- **P1 accepted:** duplicate production result construction.
- **P1 accepted:** DeepAgents worker exit, cleanup, and task verification are
  inferred from insufficient pane evidence.
- **P1 accepted:** performance phases overlap or start at the wrong boundaries;
  repeated phases and trailing work are not represented safely.
- **P2 accepted:** canonical CoS instructions still claim unsupported numeric
  Codex wall-clock enforcement.
- **P2 accepted conditionally:** repeated subprocess and observation work needs
  measurement first; optimize only where evidence preserves semantics.
- **Deferred:** POSIX/WSL child-tree cleanup. Current repository evidence does
  not establish Linux/WSL as a supported execution target. Reopen as a separate
  plan if support becomes explicit.

## Implementation Outcomes

### One terminal result contract

Every `_main_body()` terminal path uses `_build_assignment_result()`. Delivery,
execution, observation, task result, cleanup, and performance remain independent;
legacy aliases derive from those facts in one place.

### Producer-owned DeepAgents lifecycle evidence

`dcode-project` reports attributable worker exit and role-view cleanup facts only
after it knows the result. Herdr consumes a versioned receipt and reports
`unknown` when receipt, process evidence, or task verification is missing or
ambiguous. Marker and report text remain observation evidence only.

### Non-overlapping performance evidence

Preparation, target discovery, worker start/readiness, submission, observation,
and retirement use actual boundaries. Repeated occurrences remain attributable
to attempts and aggregate explicitly. Final duration uses current monotonic time.

### Canonical instruction alignment

CoS, runtime documentation, and generated adapters name one supported policy for
numeric Codex wall-clock grants. No unsupported outer-watchdog behavior remains.

### Measured efficiency only

Existing invocation metrics establish a baseline. Only reductions proven safe by
that baseline land; otherwise the optimization remains explicitly deferred.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-receiving-code-review`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-performance-optimization`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared launcher, DeepAgents runtime, tests, canonical docs, and managed generated adapters; run declared tests, validators, sync checks, and bounded local Herdr probes without authentication or destructive cleanup
- User-approval actions: commit, push, merge, authentication, external configuration writes, process termination outside task-owned probes, destructive cleanup, and edits outside declared targets
- Parallel ownership: none; launcher, runtime, tests, and docs share one evidence contract
- Sequential fallback: baseline and contract map, result builder, lifecycle receipt, timing correction, canonical sync, measured optimization, final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `53ab34b1c298fcdbd526b4cbe9e1e98a7adf5093`
- Expected workspace: declared tracked changes only; preserve unrelated untracked `.playwright-mcp/` and `db/`
- Next action: handoff; commit and push require separate authorization
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | baseline contract and support map | focused launcher/runtime tests `199 passed`; live Herdr → dcode-project run returned `DELEGATED_WORKER_LIVE_OK`, exposed lifecycle/timing defects; scope preserved |
| Task 2 | `completed` | current | `codex` | Task 1 | all launcher terminal paths use one builder | production paths normalized through `_build_assignment_result`; focused tests `92 passed` |
| Task 3 | `completed` | current | `codex` | Task 2 | producer-owned DeepAgents receipt and unknown fallbacks | focused tests `203 passed`; live receipt confirmed worker exit, descendant termination, cleanup, and task verification |
| Task 4 | `completed` | current | `codex` | Tasks 2–3 | deterministic non-overlap and retry timing tests | full tests `483 passed`; phase occurrence, aggregate, retry, pane-run, and trailing-work evidence added |
| Task 5 | `completed` | current | `codex` | Task 4 | canonical/generated parity and no watchdog contradiction | canonical wording repaired; adapter sync and runtime drift checks passed |
| Task 6 | `completed` | current | `codex` | Task 4 | measured repeated-work decision and regression proof | measurement-first deferral recorded; no safe acknowledgement or optimization change justified |
| Task 7 | `completed` | current | `codex` | Task 5, Task 6 | fresh full verification and preserved workspace proof | verified: focused `203 passed`; full `483 passed`; validators, adapter sync/drift, `git diff --check`, and `herdr api snapshot` passed; live Herdr → `dcode-project` proof and exact task-owned cleanup confirmed; `.playwright-mcp/` and `db/` preserved |

Only lead controller updates this ledger. A checked item records accepted proof,
not intent.

## Task Breakdown

### Task 1: Establish current contract and support boundary

**Purpose:** Confirm review claims against current source and capture a baseline
before edits.

**Files And Symbols:** Inspect `scripts/herdr_main_launcher.py` functions
`_build_assignment_result`, `_main_body`, `_deepagents_completion_snapshot`,
`_record_performance_phase`, `_record_performance_attempt`, and
`_finalize_performance`; inspect `scripts/dcode_project.py` functions
`_run_bounded_worker`, `_run_deepagents_worker`, role-view cleanup, and `main`;
inspect current tests and runtime documents. Do not edit completed historical
plans.

**Task Function:** Baseline and contract mapping.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded source/test inspection and deterministic baseline.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent finding-to-source and plan-scope check.

**Authority:**
- Preauthorized local actions: inspect declared files, run focused existing tests, capture Git/status and supported-runtime evidence, and record the baseline in this plan.
- Stop for: missing source contract, unsupported proposed behavior, unexpected tracked changes, or required scope outside declared targets.

**Exit Criteria:** Each accepted finding maps to a current symbol and test gap;
POSIX cleanup is classified as deferred or explicitly supported; baseline counts,
workspace preservation, and current generated-surface state are recorded.

### Task 2: Unify production result construction

**Purpose:** Remove divergent defaults and legacy-field decisions from normal
dispatch output.

**Files And Symbols:** Modify `scripts/herdr_main_launcher.py:_build_assignment_result`,
`scripts/herdr_main_launcher.py:_main_body`, and only required classifier/helper
code. Update `tests/test_herdr_main_launcher.py` to exercise `_main_body()` output,
not only the standalone builder.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded single-lane refactor with direct production-path tests.

**Behavior:**
- Route success, rejection, uncertain submission, transport failure, target
  failure, retirement failure, Codex, and DeepAgents terminal paths through the
  same builder.
- Pass established lifecycle facts into the builder; do not derive
  `task_result.state` from generic `status`.
- Derive legacy aliases once, preserve existing consumers, and keep unknown
  values explicit.
- Keep dry-run evidence separate from terminal assignment evidence.

**Verification:** Mock Herdr and executor responses at `_main_body()` and assert
one stable JSON shape for success, known rejection, uncertain post-submit error,
target-resolution failure, and retirement failure. Assert independent lifecycle
fields and compatibility aliases.

**Authority:**
- Preauthorized local actions: edit launcher and launcher tests within named symbols.
- Stop for: compatibility fields requiring new semantics, consumer breakage outside declared tests, or a second result serializer.

**Exit Criteria:** No production call to a nested or alternate result formatter
remains; focused result-path tests pass.

### Task 3: Make DeepAgents lifecycle evidence producer-owned

**Purpose:** Stop Herdr from claiming worker exit, cleanup, or verified task
results from marker text and incomplete process observations.

**Files And Symbols:** Modify `scripts/dcode_project.py` worker execution and
role-view cleanup paths, `scripts/herdr_main_launcher.py` DeepAgents receipt
parsing/classification, and `tests/test_dcode_project.py` plus
`tests/test_herdr_main_launcher.py`.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded cross-owner lifecycle contract with direct boundary tests.

**Behavior:**
- Add one compact versioned `dcode-project` terminal receipt for task execution.
  Herdr creates one attempt-owned absolute result-file path, passes it through
  `--result-file <path>`, and retains it until Herdr has consumed it. The wrapper
  publishes only after worker return and role-view cleanup or preservation
  decision.
- Publish through the exact result file, not terminal output. Write a bounded
  JSON payload to a producer-created sibling temporary file, flush it, then
  atomically replace the destination. Cap receipt size at 16 KiB. Use schema
  `dcode-project.result.v1` and existing launch `attempt_id` as correlation.
- Receipt carries only worker exit, actual worker exit code, descendant cleanup,
  role-view cleanup, and recovery-required facts. It carries no task output or
  credentials. Worker exit and zero exit code never imply task verification.
- Missing, duplicate, conflicting, stale, oversized, malformed, or failed
  publication yields `unknown`/`unverified`; Herdr never replays the task.
- The wrapper owns receipt creation and publication. Direct `dcode-project`
  execution without `--result-file` remains supported without a receipt;
  `--print-config` and Tura remain receipt-free.
- Receipt carries correlation ID, worker state and exit code, cleanup state,
  role-view state, and recovery-required state. It carries no raw task output or
  credentials. `--print-config` emits no task receipt.
- Herdr trusts receipt facts only when schema and correlation match. Missing,
  malformed, stale, or ambiguous receipt yields `unknown` for the affected fact.
- Marker presence, `COMPLETED` text, report presence, and shell-only process
  state remain observation facts. They cannot prove worker exit, cleanup, or
  verified task result.
- Classify `pane run` failures by known phase. Unknown nonzero results remain
  `delivery_uncertain` unless rejection is established.
- Preserve role-view lock ownership, cleanup-on-known-exit behavior, and
  recovery preservation when worker lifetime is unproven.

**Verification:** Test successful worker exit with verified cleanup, worker
failure with cleanup, recovery-blocked worker lifetime, marker plus live worker,
shell-only observation, missing process observation, malformed receipt, and
unknown pane-run failure. Assert Herdr never upgrades unknown facts.

**Compatibility:** Extend dcode argument validation and the Herdr command only
where required. Test current launcher with an older wrapper, a new wrapper with
an older launcher, direct wrapper invocation, `--print-config`, Tura, and
machine-readable stdout. Unsupported receipt support produces explicit
`unknown`/`unsupported`, never fabricated success.

**Failure Cases:** Cover launcher crash before publication, worker-start failure,
cleanup exception, and receipt-publication failure. A missing receipt preserves
uncertainty and does not authorize replay.

**Authority:**
- Preauthorized local actions: edit declared DeepAgents runtime, launcher parsing, and lifecycle tests.
- Stop for: receipt requiring raw output, credential/config changes, runtime ownership ambiguity, or inability to represent unavailable cleanup as `unknown`/`unverified`.

**Exit Criteria:** `dcode-project` owns worker and cleanup facts; Herdr consumes
them without reconstructing them from terminal text; focused runtime tests pass.

### Task 4: Correct timing boundaries and retry accounting

**Purpose:** Publish durations that do not overlap and do not omit trailing work.

**Files And Symbols:** Modify `scripts/herdr_main_launcher.py` performance helpers,
`resolve_launch`, and `_main_body`; update deterministic timing tests in
`tests/test_herdr_main_launcher.py`.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded correctness refactor with deterministic clock proof.

**Behavior:**
- Keep preparation and target discovery in their own phases.
- Measure Codex worker initialization around `agent start`; measure submission
  only from prompt submission through acknowledgement.
- For DeepAgents, keep `delivery` and `worker_initialization` unavailable unless
  Herdr has real submission/readiness acknowledgements. Do not label blocking
  `pane run` duration as delivery or observation; record it as an explicit
  per-attempt `pane_run_duration_ms` measurement and include it in total
  invocation duration.
- Measure observation only around process/read observation, and retirement only
  around retirement operations.
- Store phase occurrences instead of overwriting repeated phases; expose an
  explicit aggregate without breaking the stable top-level shape.
- Phase occurrences are exclusive. Total invocation duration is inclusive;
  expose nonnegative `unattributed_duration_ms` for measured gaps and overhead.
- Herdr aggregates only its own monotonic clock. Never combine wrapper receipt
  durations or monotonic timestamps from another process into Herdr phases.
- Record each attempt from its own start through its terminal attempt event.
- Finalize with current `time.monotonic()`, including work after the last phase.
- Keep subprocess counts invocation-scoped; final counts include retries.

**Verification:** Use a deterministic clock to assert preparation is not worker
initialization, delivery excludes observation, repeated phases aggregate,
attempts remain distinct, and total duration includes trailing work. Run a
mocked five-second worker plus seven-second observation and assert no twelve-

Measure blocking `pane run` as `pane_run_duration_ms`, leave unavailable phase
subdurations unavailable, and assert uninstrumented overhead remains visible.

**Authority:**
- Preauthorized local actions: edit performance helpers and named launcher tests.
- Stop for: public schema changes without compatibility mapping, timing semantics that cannot be tied to an observable boundary, or optimization mixed into correctness fixes.

**Exit Criteria:** Timing tests prove boundary ownership, aggregate behavior,
retry attribution, and finalization correctness.

### Task 5: Repair canonical CoS grant instructions

**Purpose:** Remove the unsupported watchdog claim and keep generated adapters in
sync.

**Files And Symbols:** Modify the numeric Codex wall-clock section in
`.agents/skills/skill-chief-of-staff/SKILL.md`; align
`docs/operating_system/runtime/runtime-surfaces.md` and
`docs/operating_system/procedures/runtime-adapter-procedure.md`; regenerate
managed `generated_agents/claude/skills/skill-chief-of-staff/SKILL.md`,
`generated_agents/codex/skills/skill-chief-of-staff/SKILL.md`, and
`generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md`.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: canonical documentation correction with deterministic generation checks.

**Behavior:** One canonical rule states that numeric Codex wall-clock grants
fail closed until a named runtime owner can enforce interruption and cleanup.
Documentation distinguishes implementation evidence from live Herdr proof.

**Verification:** Run adapter sync check, runtime drift validation, planning and
metadata validators, and search for stale `outer-watchdog` claims. Confirm old
plans remain unchanged.

**Authority:**
- Preauthorized local actions: edit canonical documentation and regenerate only managed adapter outputs.
- Stop for: generated drift with no canonical source, unsupported runtime policy, or edits to historical plans.

**Exit Criteria:** Canonical and generated instructions agree; no stale watchdog
claim remains in maintained surfaces.

### Task 6: Measure and reduce repeated work only where safe

**Purpose:** Address the efficiency finding without adding speculative machinery.

**Files And Symbols:** Inspect invocation metrics and subprocess call sites in
`scripts/herdr_main_launcher.py`; modify only the smallest proven-safe launcher
path and adjacent tests. Do not add cache, observer daemon, scheduler, or
orchestration code.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded measurement-first optimization with no new machinery.

**Steps:**
- Capture baseline counts and durations for DeepAgents observation, Git preflight,
  final pane validation, and wrapper startup using existing invocation-scoped
  metrics and deterministic mocks.
- Prove which operation acknowledges DeepAgents submission before changing any
  observation barrier. If no acknowledgement exists, retain current ordering and
  record the deferral.
- Consolidate only compatible Git queries when measured Windows process-start
  cost justifies it and evidence fields stay equivalent.
- Move final pane validation later only if target identity and safety checks stay
  intact.
- Remove stale helpers only after caller search proves they are disconnected and
  no runtime contract depends on them.

**Verification:** Compare before/after counts for representative success and
failure paths; assert no lifecycle or evidence regression; run focused tests and
the bounded Herdr API snapshot. No percentage threshold is required; retain
the baseline and decision.

**Authority:**
- Preauthorized local actions: run bounded measurements and make only evidence-justified edits in declared launcher/test files.
- Stop for: unclear acknowledgement semantics, semantic timing changes, unsupported performance claim, or need for new machinery.

**Exit Criteria:** Safe reduction lands with regression proof, or measured
deferral is recorded without changing behavior.

### Task 7: Final verification and handoff

**Purpose:** Reconcile implementation, runtime ownership, docs, generated files,
tests, and Git state.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded final verification with no implementation scope.

**Dependencies:** Tasks 2–6 complete and not blocked.

**Verification:**

```powershell
py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_dcode_project.py -q
py -3 -m pytest -q
py -B scripts/validate_repo_contracts.py --repo-root . --fast
py -B scripts/validate_repo_config.py --repo-root .
py -B scripts/validate_agent_metadata_schema.py
py -B scripts/validate_generated_header_format.py
py -B scripts/validate_planning_lifecycle.py --repo-root .
py -B scripts/sync_agent_adapters.py --all-platforms --check
py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check
git diff --check
herdr api snapshot
```

Run bounded mocked lifecycle probes for every required terminal case. The live
boundary probe must launch one controlled task-owned worker through the actual
Herdr → `dcode-project` path, then observe its attempt-owned receipt, wrapper
exit status, role-view cleanup disposition, and final launcher JSON. Use a
deterministic fixture/stub worker where provider/model behavior is irrelevant.
The probe validates transport assumptions that mocks cannot establish. Do not
claim delegation, streaming, or task verification from source tests or an API
snapshot alone.

Confirm `HEAD`, branch, staged/unstaged/untracked state, historical plan hashes,
and preservation of `.playwright-mcp/` and `db/`. Do not commit, push, merge,
clean, or delete unrelated paths during plan execution.

**Authority:**
- Preauthorized local actions: run final checks, inspect Git state, and update this plan ledger after accepted proof.
- Stop for: failed mandatory proof, generated drift, unexpected scope, unresolved lifecycle ambiguity, commit, push, merge, or destructive cleanup.

**Exit Criteria:** Every task has accepted proof; plan status changes to
`completed` only after fresh verification returns `verified`. Missing mandatory
runtime proof leaves the affected task `blocked` and this plan incomplete.

## Non-Goals

- No caching, observer daemon, heartbeat store, scheduler, janitor, or broader
  orchestration.
- No unsupported Herdr watchdog implementation or numeric Codex wall-clock
  enforcement claim.
- No POSIX/WSL process-tree change unless repository support is explicitly
  established in a separate approved scope.
- No changes to completed historical plans, provider credentials, MCP project
  configuration, normal profiles, databases, or unrelated untracked paths.
- No raw task output or secrets in lifecycle receipts or plan evidence.

## Verification

Use focused launcher and DeepAgents tests, one final full repository test run,
repository contract/config validators, metadata and generated-header validators,
adapter sync/drift checks, `git diff --check`, deterministic timing probes, and
one bounded actual Herdr → `dcode-project` boundary probe. Reuse unchanged
focused results and do not repeat validators already covered by the aggregate
gate unless a separate gate requires them. Preserve every pre-existing
unrelated path, including `.playwright-mcp/` and `db/`, and all historical plans.
Mocks prove counts/classification; they do not prove Windows process-start
latency. Keep optimization optional.

## Completion Criteria

1. `_main_body()` terminal paths use one result builder.
2. Legacy compatibility fields derive from canonical lifecycle facts only.
3. DeepAgents worker exit and cleanup facts come from producer-owned evidence;
   marker/report text cannot prove them.
4. Missing or ambiguous lifecycle evidence remains `unknown` or uncertain.
5. Performance durations use non-overlapping observable boundaries, preserve
   retry attribution, and include trailing work.
6. Canonical and generated CoS/runtime instructions contain no unsupported
   watchdog contradiction.
7. Repeated-work changes have measured baseline and regression proof, or a
   recorded deferral.
8. Focused tests, full tests, validators, adapter checks, diff checks, and
   bounded Herdr proof pass.
9. Historical plans and every unrelated tracked/untracked path remain unchanged.
