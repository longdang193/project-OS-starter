---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: coordination-overhead-and-refill-safety
targets:
  - docs/superpowers/plans/2026-10-16-16-21-coordination-overhead-and-refill-safety-plan.md
  - scripts/herdr_parallel_dispatch.py
  - scripts/benchmark_dispatch.py
  - scripts/project_os_runtime/acceptance.py
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/secretary_live_runtime.py
  - scripts/benchmark_completion_monitoring.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - generated_agents/
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - .agents/skills/skill-project-secretary/SKILL.md
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_benchmark_dispatch.py
  - tests/test_project_os_runtime.py
  - tests/test_plan_preparation.py
  - tests/test_evidence_release.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_live_pilot.py
  - tests/test_skill_chief_of_staff.py
  - tests/test_skill_project_secretary.py
  - tests/test_benchmark_completion_monitoring.py
---

# Coordination Overhead And Refill Safety Plan

## Goal

Address the remaining stability and maintenance issues identified after PR #92
without expanding the coordination architecture:

1. prevent the opt-in parallel refill path from treating unresolved occupied
   runtime capacity as reusable;
2. make all acceptance consumers reuse one semantic acceptance-proof validator
   while keeping settlement, retention, and artifact release independent;
3. remove only proven unreachable Secretary result code and keep managed
   Secretary execution explicitly blocked until an attributable structured
   result channel exists;
4. strengthen the existing completion-monitoring benchmark so future Task 5
   decisions use genuinely different implementations and representative busy,
   delayed, and unresolved cases; and
5. reduce mandatory coordination and repeated evidence reconstruction for clear,
   local, and single-executor work without weakening sequential ownership,
   independent review, exact candidate binding, or retirement proof.

The plan does not enable managed Secretary execution, remove sequential target
acquisition, replace Markdown-plan revision checks, introduce a second task or
acceptance registry, or claim a monitoring performance improvement.
The suggested deterministic exact-head merge/cleanup tool is also deferred; the
existing review, integration, and finishing skills remain the owners of those
actions.

## Implementation Outcomes

### Fail-closed refill admission

`run_parallel(..., enable_refill=True)` launches a deferred lane only after the
completed lane provides explicit retirement evidence: `capacity == "retired"`
and `unresolved is False`. `failure_kind` is not part of refill eligibility;
an attempt may settle safely after a classified failure while still proving
that its capacity is retired. Timeout, coordinator exception, occupied
capacity, or unresolved retirement leaves deferred lanes unstarted and visible
in the returned evidence. The default `enable_refill=False` behavior remains
unchanged. The implementation first inventories supported operational callers;
if none exists, the plan removes the unused refill surface rather than adding a
caller solely to justify hardening it.

### One semantic acceptance validator

The existing top-level acceptance decision keeps its compatibility shape, but a
shared non-mutating validator checks the whole decision: `controller`, `task`,
`task_transition`, `acceptance_proof`, and their common identity, state,
condition, freshness, Git, candidate, and attempt facts. Each consumer retains
its boundary-specific checks for dependency membership/state, Plan target,
expected revision and atomic writes, or settlement/retention/artifact identity.
`evaluate_acceptance()` no longer makes settlement part of semantic proof;
settlement remains a separate runtime boundary. No new proof schema or
lifecycle registry is introduced.

### Bounded Secretary maintenance surface

The managed normal capability remains `BLOCKED_CAPABILITY`; the implementation
does not flip the capability gate. Unreachable statements after
`_project_semantic_result()` are removed only after call-site and regression
coverage confirms they are dead. Used compatibility helpers remain intact.

### Honest monitoring evidence

The existing benchmark distinguishes a real implementation delta from a
baseline-only characterization. It models busy workers lasting across multiple
diagnostic intervals, delayed receipts, diagnostic stalls, and unresolved
retirement. It reports no optimization claim when baseline and candidate source
hashes are identical.

### Proportional coordination guidance

Canonical Secretary and CoS skills retain the routing policy already validated
by PR #92. Task 5 is gap-driven and is a no-op unless inventory finds a concrete
missing rule or duplicated reconstruction. If a gap is found, only derived or
static capability evidence may be reused, keyed by freshly checked repository,
worktree, branch, HEAD, plan revision, and attempt anchors. Process, pane,
receipt, settlement, HEAD, and task-state observations remain fresh at their
owning boundaries.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `optional worktree`; use an isolated worktree from the merged PR #92 main commit before implementation and preserve the dirty local main checkout
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit the named canonical source, skill, benchmark, and test files; run the declared local tests and validators; inspect source, Git, and recorded benchmark evidence; refresh generated agent adapters when canonical skill files change
- User-approval actions: branch creation, worktree creation, commits, push, pull request publication, merge, cleanup, discard, external writes, and any scope expansion
- Parallel ownership: `none`; the lead controller owns the ordered ledger and shared verification
- Sequential fallback: complete Tasks 1 through 5 in order; if a task changes a shared contract unexpectedly, stop, record the mismatch, and revise the plan before continuing

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/coordination-overhead-and-refill-safety`
- Base commit: `1910ea292883dec90dfcfdd55d3549f7520e9e56`
- Expected workspace: `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\coordination-overhead-refill-safety\project-OS-starter` from merged PR #92 main; preserve the existing dirty main checkout and its unrelated changes
- Next action: `handoff to skill-finishing-a-development-branch for authorized Git disposition`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated worktree | `codex` | none | refill safety tests and dispatcher diff | caller inventory; 86 focused tests passed |
| Task 2 | `completed` | isolated worktree | `codex` | Task 1 | shared validator and consumer regression tests | 121 passed, 1 skipped; runtime docs updated |
| Task 3 | `completed` | isolated worktree | `codex` | Task 2 | Secretary result/capability tests and dead-code inspection | 323 passed; compilation passed |
| Task 4 | `completed` | isolated worktree | `codex` | Task 3 | benchmark harness tests and characterized output | 3 focused tests passed; nine deterministic cases; identical hashes classified as characterization-only; zero correctness mismatches |
| Task 5 | `completed` | isolated worktree | `codex` | Tasks 1–4 | skill tests, adapter synchronization, and final policy inspection | no-op: canonical routing, optional Secretary, sequential ownership, independent review, exact binding, and reconstruction-first guidance already explicit |

## Task Breakdown

### Task 1: Gate deferred-lane refill on proven resource retirement

**Purpose:**
- Prevent `enable_refill=True` from launching a new lane while the completed
  lane still reports occupied or unresolved runtime resources.

**Task Function:**
- Harden the existing bounded dispatcher refill decision without creating a new
  scheduler or changing default non-refill execution.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small sequential plan; the lead controller retains execution
  and acceptance authority without delegated profile selection.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: task-local regression proof is sufficient; independent review
  remains a later integration gate if the plan requires it.

**Specification Coverage:**
- Review finding that an occupied or unresolved timeout must not be treated as
  available runtime capacity.
- Existing invariant that semantic uncertainty and resource retirement are
  separate facts.
- Existing default `enable_refill=False` behavior.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:run_parallel`, `run_lane`,
  `_prepare_admission`
- Modify: `scripts/herdr_parallel_dispatch.py:run_parallel` and a private helper
  `_can_refill_after_result` owned by that module
- Verify: `tests/test_herdr_parallel_dispatch.py` refill, timeout, exception,
  and capacity-state tests

**Dependencies:**
- Existing `run_lane` result fields remain the source of resource state:
  `capacity` and `unresolved`; `failure_kind` is diagnostic classification, not
  refill eligibility.

**Authority:**
- Preauthorized local actions: edit the dispatcher and its focused tests; run
  the focused dispatcher suite and `git diff --check`.
- Stop for: missing retirement evidence, a change to default refill-disabled
  behavior, a new scheduler/resource registry, or a requirement to launch live
  workers.

**Steps:**
- [x] Step 1: Inventory every supported operational caller of `enable_refill`
  across runtime code, tests, and benchmark/documentation references. Record
  that only synthetic benchmark/test references exist and no normal operational
  consumer is supported; do not add a caller merely to justify keeping the
  feature.
- [x] Step 2: Remove `enable_refill` from `run_parallel`, reject stale callers
  explicitly instead of forwarding the option to `run_lane`, and remove the
  refill submission branch while preserving default bounded dispatch and its
  result/event contracts.
- [x] Step 3: Remove the synthetic benchmark's refill mode and update its tests
  and documentation to measure the supported bounded dispatcher only.
- [x] Step 4: Add regression coverage proving stale `enable_refill` callers are
  rejected, deferred lanes remain deferred under supported dispatch, and
  callback, sibling, exception, stop-event, and capacity evidence remain
  unchanged.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_benchmark_dispatch.py`
- Expected: if refill remains supported, clean retired results—including
  classified failures with retired capacity—refill deferred lanes, while
  occupied or unresolved results never refill; if no caller exists, removal is
  covered by the recorded inventory and default execution remains unchanged.
- [x] Direct assertion inspection of stale-option rejection, deferred evidence,
  and emitted `refill_admitted` events for each failure case.

**Exit Criteria:**
- If the caller inventory retains the feature, no deferred lane starts from an
  occupied, unresolved, or exceptional result, while safely retired classified
  failures may refill; the focused dispatcher suite passes without changing the
  default path. If no caller exists, the supported surface is removed and the
  no-caller evidence is recorded.

### Task 2: Consolidate semantic acceptance-proof validation

**Purpose:**
- Remove duplicated semantic proof checks while keeping each mutation or release
  boundary responsible for its own additional safety conditions.

**Task Function:**
- Extract a shared, non-mutating validator for the existing acceptance-proof
  mapping and route all three consumers through it.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small sequential plan; the lead controller retains execution
  and acceptance authority without delegated profile selection.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused contract tests plus final verification cover the
  bounded refactor.

**Specification Coverage:**
- Review finding that authority, task/plan identity, required conditions,
  freshness, and candidate checks drift across consumers.
- PR #92 invariant that semantic acceptance does not contain settlement or
  resource-retirement proof.
- No parallel proof schema or registry.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`,
  `authorize_dependent_transition`, `authorize_evidence_release`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`
- Modify: `scripts/project_os_runtime/acceptance.py:_validate_acceptance_decision_contract`
  (new private shared validator over the whole decision mapping—`controller`,
  `task`, `task_transition`, and `acceptance_proof`—with expected task/plan/
  binding values supplied by each caller),
  `authorize_dependent_transition`, and `authorize_evidence_release`
- Modify: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`
- Modify: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance` and
  `docs/operating_system/runtime/runtime-surfaces.md` to remove or deprecate
  the `settlement=` coupling and describe settlement as a separate runtime
  proof boundary.
- Verify: `tests/test_project_os_runtime.py`, `tests/test_plan_preparation.py`,
  `tests/test_evidence_release.py`, and `tests/test_reconciliation.py`

**Dependencies:**
- Existing top-level decision and `acceptance_proof` dictionary shapes remain
  compatibility contracts except that semantic proof no longer embeds
  settlement. The validator returns deterministic failure labels and does not
  mutate or replace the decision mapping.

**Authority:**
- Preauthorized local actions: edit the named acceptance/Plan consumers and
  focused tests; run acceptance, Plan transition, release, reconciliation, and
  `git diff --check` proof.
- Stop for: a new proof schema, a lifecycle registry, settlement fields added
  back to semantic proof, changed release/retention semantics, or an inability
  to preserve existing fail-closed reasons.

**Steps:**
- [x] Step 1: Inventory the full acceptance decision fields checked by the
  producer and all consumers: `controller`, `task`, `task_transition`,
  `acceptance_proof`, task ID, plan identity, task state, required/artifact
  conditions, freshness, Git repository/candidate/checkpoint/assignment/attempt
  binding, and accepted candidate identity. Inventory every caller of
  `evaluate_acceptance(settlement=...)` at the same time.
- [x] Step 2: Implement `_validate_acceptance_decision_contract` as a
  non-mutating helper that returns stable validation failures for those common
  fields and accepts expected task/plan/binding values from the caller.
- [x] Step 3: Replace duplicated shared checks in dependent transition, Plan
  mutation, and evidence release with the helper while retaining boundary-local
  checks: prerequisite membership/current states; target Plan identity and
  expected revision/atomic write; settlement, retention, acknowledgement, and
  physical artifact identity.
- [x] Step 4: Remove the unused `settlement` parameter and internal passing from
  `evaluate_acceptance()` if all callers can be updated without compatibility
  breakage. Otherwise make it optional/deprecated, explicitly unused, and stop
  treating it as semantic proof; in both cases remove the generated
  `acceptance_proof["settlement"]` member and update terminology/docs.
- [x] Step 5: Preserve the settlement/resource boundary: release must receive
  same-attempt runtime settlement independently, and no semantic validator may
  infer settlement from acceptance proof.
- [x] Step 6: Add parameterized regressions proving each shared mismatch is
  rejected consistently by every applicable consumer and each boundary-specific
  mismatch remains rejected at its owning consumer.
- [x] Step 7: Update only claims that imply immutable proof representation; do
  not describe the existing mutable mapping as immutable until a compatible
  representation is separately specified.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_evidence_release.py tests/test_reconciliation.py`
- Expected: all consumers reject the same malformed or mismatched semantic proof
  consistently; release still requires independent settlement and artifact proof.
- [x] `rg -n 'acceptance_proof.*settlement|settlement.*acceptance_proof' scripts/project_os_runtime tests`
- Expected: no semantic acceptance-proof producer or regression fixture embeds a
  settlement member; runtime settlement remains explicit at the release boundary.

**Exit Criteria:**
- One shared validator owns common semantic proof shape checks, all consumers
  invoke it, boundary-specific checks remain local, and the existing acceptance,
  settlement, retention, and artifact contracts pass unchanged.

### Task 3: Remove proven unreachable Secretary result code and preserve the capability block

**Purpose:**
- Reduce maintenance surface in the experimental managed Secretary adapter
  without enabling an unsupported execution path.

**Task Function:**
- Delete unreachable code only after call-site inventory and tests prove it is
  not part of the supported result contract.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small sequential plan; the lead controller retains execution
  and acceptance authority without delegated profile selection.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: direct regression tests cover the blocked capability and used
  result-source compatibility paths.

**Specification Coverage:**
- Review finding that `_project_semantic_result()` has unreachable statements
  after its return and that managed normal execution intentionally remains
  unavailable.
- No capability-flag flip and no ordinary execution dependency on managed
  Secretary.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_project_semantic_result`,
  `_result_evidence`, `_result_source_content`, `_snapshot_result_content`,
  `_select_authoritative_result_source`, `_result_source_authoritative`,
  `_normal_managed_result_capability_available`
- Modify: `scripts/secretary_live_runtime.py:_project_semantic_result` and only
  compatibility statements proven unreachable or unused by the inventory
- Verify: `tests/test_secretary_live_runtime.py`,
  `tests/test_secretary_live_pilot.py`, and `tests/test_dcode_project.py`

**Dependencies:**
- Current capability behavior returns explicit `BLOCKED_CAPABILITY` from
  `run_normal` while `_normal_managed_result_capability_available()` returns
  `False`.

**Authority:**
- Preauthorized local actions: inspect call sites, remove unreachable code in
  the named module, update focused regression tests, and run syntax/tests.
- Stop for: any need to enable managed execution, change the structured result
  contract, remove a helper with live callers, or add a fallback semantic source.

**Steps:**
- [x] Step 1: Record every in-repository caller of the named result helpers and
  distinguish live compatibility handling from statements unreachable after
  `_project_semantic_result()` returns.
- [x] Step 2: Remove the unreachable post-return block and no other compatibility
  branch unless its call-site inventory and tests prove it dead.
- [x] Step 3: Keep `_normal_managed_result_capability_available()` fail-closed and
  preserve the explicit blocked result fields and error classification.
- [x] Step 4: Add or update tests for blocked normal capability, structured
  result projection, authoritative result-source selection, and terminal-format
  rejection where those paths remain supported.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_live_pilot.py tests/test_dcode_project.py`
- Expected: blocked managed capability remains explicit; supported result-source
  paths retain their current outputs; no unreachable post-return statements remain.
- [x] `py -3 -m py_compile scripts/secretary_live_runtime.py`
- Expected: compilation succeeds.

**Exit Criteria:**
- Proven unreachable code is removed, used compatibility behavior is preserved,
  and managed Secretary remains explicitly blocked with fresh regression proof.

### Task 4: Make completion-monitoring evidence representative and honest

**Purpose:**
- Improve the existing Task 5 benchmark so it can distinguish no implementation
  delta from no optimization benefit and model the busy/unresolved cases that
  the original deterministic harness omitted.

**Task Function:**
- Extend the current boundary harness without changing production monitoring or
  introducing a second benchmark framework.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small sequential plan; the lead controller retains execution
  and acceptance authority without delegated profile selection.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: benchmark self-tests and reproducible output are the bounded
  validation contract.

**Specification Coverage:**
- Review finding that the prior baseline and candidate source hashes were
  identical, the fake process-info response never modeled a busy worker, and
  repeated deterministic runs did not measure production variability.
- Retain Task 5 production deferral until a genuinely different monitoring
  implementation and representative workload prove the declared threshold.

**Required Skills:**
- `skill-performance-optimization`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `scripts/benchmark_completion_monitoring.py:CASES`,
  `FakeHerdr`, `run_case`, and report assembly
- Verify: `tests/test_benchmark_completion_monitoring.py`
- Measure: `.tmp-tests/coordination-overhead-completion-monitoring.json`

**Dependencies:**
- Existing source-hash comparison, subprocess/timing metrics, lifecycle mismatch
  checks, and the existing harness remain the only benchmark framework. The
  harness must distinguish characterization with identical baseline/candidate
  source hashes from before/after evidence using genuinely different revisions.

**Authority:**
- Preauthorized local actions: edit the named benchmark and tests; run the
  deterministic benchmark with the fixed base commit and record local output.
- Stop for: a production monitoring change, live worker launch, a new benchmark
  framework, missing comparable implementation revisions, or a result that
  claims operational benefit from identical source hashes.

**Steps:**
- [x] Step 1: Parameterize `completion_wait_seconds` and
  `diagnostic_poll_seconds` per case instead of relying on one global budget.
  Make the busy-worker case span at least three diagnostic intervals before a
  delayed receipt appears, so it measures repeated polling rather than a single
  timeout.
- [x] Step 2: Add delayed-receipt and unresolved-retirement cases that exercise
  diagnostic stalls, late authoritative receipts, and no-safe-retirement paths.
- [x] Step 3: Make the harness report `implementation_delta` from the baseline
  and candidate launcher source hashes and classify identical hashes as
  `characterization_only`, not as evidence that an optimization failed. Keep
  identical-hash characterization separate from before/after optimization
  evidence, which requires a genuinely different candidate revision.
- [x] Step 4: Preserve the existing retention gate: at least 20% median
  subprocess reduction, no more than 5% p95 completion-detection regression,
  and zero lifecycle/cleanup/reconciliation mismatches.
- [x] Step 5: Add tests for the new case outcomes, identical-hash reporting,
  delayed receipt timing, and fail-closed unresolved retirement.
- [x] Step 6: Run deterministic fake-clock cases with only 1–3 repetitions
  (default to one); do not treat repeated deterministic runs as production
  variability. Reserve repeated sampling for real/runtime measurements if an
  applicable runtime mode is available.
- [x] Step 7: Reconcile the recorded runtime-observation sample as an
  observational baseline only, separating worker wait time from orchestration
  and subprocess measures; record `INCONCLUSIVE` when representative direct,
  single-Worker, and coordinated workloads are unavailable rather than inferring
  a handoff or monitoring benefit.

Task-local evidence:

- `py -3 -m pytest -q tests/test_benchmark_completion_monitoring.py` → `3 passed`.
- `py -3 scripts/benchmark_completion_monitoring.py --baseline-revision 1910ea292883dec90dfcfdd55d3549f7520e9e56 --repetitions 1 --output .tmp-tests/coordination-overhead-completion-monitoring.json` → nine deterministic cases, `implementation_delta.status=characterization_only`, `optimization_claim_allowed=false`, three busy-worker observations before the delayed receipt, and zero lifecycle/cleanup/reconciliation mismatches.
- The runtime observation summary is measured but homogeneous: 20 managed DeepAgents attempts, observation-dominated duration, unavailable delivery/retirement/worker-initialization phase attribution, and decision `runtime_optimization=deferred`; it is observational baseline evidence, not proof of a monitoring or handoff benefit.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_benchmark_completion_monitoring.py`
- Expected: all cases are deterministic, busy-worker behavior is represented,
  and identical baseline/candidate sources cannot produce an improvement claim.
- [x] `py -3 scripts/benchmark_completion_monitoring.py --baseline-revision 1910ea292883dec90dfcfdd55d3549f7520e9e56 --repetitions 1 --output .tmp-tests/coordination-overhead-completion-monitoring.json`
- Expected: output records source hashes, implementation-delta status, named
  metrics, and correctness results without claiming a production improvement.
- [x] Inspect `artifacts/runtime-observation/2026-10-12-stable-architecture-operational-baseline-summary.json`
  and record whether direct, single-Worker, and coordinated workload evidence is
  representative, observational, or inconclusive.

**Exit Criteria:**
- The existing benchmark can characterize the current implementation honestly
  and can evaluate a future changed monitoring implementation against realistic
  busy and unresolved cases without changing production behavior.

### Task 5: Encode proportional routing and evidence reuse in canonical skills

**Purpose:**
- Review whether a concrete routing or evidence-reconstruction gap remains after
  PR #92; make no policy change when inventory finds none.

**Task Function:**
- Inventory the canonical guidance and tests first. Only if a justified gap is
  found, make the smallest canonical-skill change and synchronize generated
  adapter surfaces.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small sequential plan; the lead controller retains execution
  and acceptance authority without delegated profile selection.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: skill contract tests and generated adapter synchronization
  provide the required proof.

**Specification Coverage:**
- Review recommendation to inspect current routing and evidence guidance before
  changing it, reuse only narrow derived/static evidence when anchors remain
  valid, consume launcher evidence instead of rediscovering it, and retain
  sequential ownership and independent review.
- Existing PR #92 routing policy and the rule that Secretary is optional and does
  not add a mandatory Secretary-to-CoS hop remain authoritative.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Modify: `.agents/skills/skill-chief-of-staff/SKILL.md` attention-audit,
  plan-binding, and review/integration guidance
- Modify: `.agents/skills/skill-project-secretary/SKILL.md` activation and routing
  guidance
- Verify: `tests/test_skill_chief_of_staff.py`,
  `tests/test_skill_project_secretary.py`, `tests/test_sync_agent_adapters.py`
- Generated owner: `scripts/sync_agent_adapters.py` and its declared adapter
  outputs; edit canonical skill files before refreshing generated surfaces

**Dependencies:**
- Tasks 1–4 preserve the runtime contracts that the skill guidance must route
  toward; no new execution owner or persistent coordination registry is added.

**Authority:**
- Preauthorized local actions: inventory the two canonical skill files and their
  tests; if a concrete gap is proven, edit only the canonical skill files,
  update contract tests, refresh generated adapters, and run synchronization
  checks. A no-op is the default outcome.
- Stop for: weakening independent review, removing sequential automatic target
  acquisition before ownership is safe, changing acceptance/lifecycle authority,
  adding a scheduler/heartbeat, creating a second durable evidence store, or
  broadening evidence reuse beyond derived/static capability facts.

**Steps:**
- [x] Step 1: Inventory current canonical skill text, tests, generated adapters,
  and the PR #92 routing-policy assertions. Record a no-op if the requested
  direct/single-executor path and optional Secretary behavior are already
  explicit.
- [x] Step 2: If a concrete gap exists, add only the smallest routing rule and
  decision table needed to close it; do not rewrite validated PR #92 policy.
- [x] Step 3: If evidence reuse is justified, limit it to derived/static
  capability evidence keyed by freshly checked repository, worktree, branch,
  HEAD, plan revision, and attempt anchors. Keep process, pane, receipt,
  settlement, HEAD, and task-state observations fresh at their owning
  dispatch, acceptance, mutation, and retirement boundaries.
- [x] Step 4: Require consumers to use existing launcher/Herdr evidence rather
  than rediscovering pane, process, Git, or receipt facts, while preserving the
  current canonical owners and failure taxonomy.
- [x] Step 5: Preserve the existing direct-path exceptions, sequential target
  acquisition, independent review, exact-head integration, and retirement proof.
- [x] Step 6: Treat any cold-start reconstruction reduction as measurement-gated:
  preserve current behavior unless paired tool-call or latency evidence shows
  material duplication; otherwise record a no-op.
- [x] Step 7: Keep the deterministic exact-head merge/cleanup-tool suggestion
  deferred; existing review, integration, and finishing skills retain ownership.
- [x] Step 8: Only when a concrete gap was proven, update canonical skill tests
  and run
  `py -3 scripts/sync_agent_adapters.py --all-platforms` so generated surfaces
  are derived from the canonical files.

Task-local evidence: inventory found no justified canonical-skill gap. Existing
skill text and tests already state proportional direct routing, optional
Secretary behavior, reconstruction from canonical evidence first, launcher/Herdr
evidence ownership, sequential target acquisition, independent review, exact
binding, and the prohibition on mandatory Secretary-to-CoS routing. Task 5 is
therefore a recorded no-op; no canonical skill or generated adapter changed.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_skill_chief_of_staff.py tests/test_skill_project_secretary.py tests/test_sync_agent_adapters.py`
- Expected: existing routing assertions remain intact; if a gap was found, its
  narrow rule is explicit; Secretary remains optional; CoS retains acceptance
  and review authority; no forbidden direct subagent or parallel ownership path
  is introduced.
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: generated adapter outputs match the canonical skills.

**Exit Criteria:**
- Canonical skills and generated adapters either remain unchanged with a
  recorded no-op or contain only a justified narrow gap fix; all existing
  ownership and safety gates pass their contract tests.

## Verification

Final artifact-level verification must run from the same isolated worktree after
all retained changes are complete:

- [x] `py -3 -m pytest -q` → `1328 passed, 2 skipped`
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root . --fast` → passed
- [x] `py -3 scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-16-16-21-coordination-overhead-and-refill-safety-plan.md` → passed
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check` → outputs up to date
- [x] `py -3 scripts/benchmark_completion_monitoring.py --baseline-revision 1910ea292883dec90dfcfdd55d3549f7520e9e56 --repetitions 1 --output .tmp-tests/coordination-overhead-completion-monitoring.json` → passed with characterization-only status and zero correctness mismatches
- [x] `git diff --check` → passed
- [x] `git status --short --branch`, confirming only declared plan/worktree changes
  are present and unrelated local main changes remain preserved outside the
  implementation worktree.
  are present and unrelated local main changes remain preserved outside the
  implementation worktree.

## Completion Criteria

The plan is ready for completion verification when:

1. opt-in refill never treats unresolved occupied capacity as reusable;
2. shared semantic acceptance validation is used by all named consumers without
   changing settlement, retention, artifact, or atomic-write boundaries;
3. Secretary dead-code cleanup is limited to proven unreachable code and managed
   normal execution remains explicitly blocked;
4. the monitoring harness reports implementation delta honestly and retains the
   Task 5 production deferral unless a future changed implementation meets the
   declared performance and correctness thresholds;
5. proportional direct/single-executor routing and evidence reuse are canonical
   without weakening sequential ownership, independent review, exact binding,
   or retirement proof;
6. generated adapters, tests, validators, and documentation are synchronized;
7. all task-local proof and final verification output are recorded in this plan;
8. deviations, blockers, and deferrals are explicit; and
9. `skill-verification-before-completion` returns `verified` before the plan
   changes from `proposed` or `active` to `completed`.
