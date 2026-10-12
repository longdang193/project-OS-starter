---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: final-normal-coordination-convergence-sequence
targets:
  - scripts/herdr_main_launcher.py
  - scripts/secretary_live_runtime.py
  - scripts/benchmark_secretary_architecture.py
  - tests/test_herdr_main_launcher.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_benchmark.py
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/superpowers/plans/2026-10-12-managed-invocation-semantic-provenance-closure-plan.md
  - .github/workflows/repo-contracts.yml
  - .github/workflows/runtime-contracts.yml
---

# Final Normal Coordination Convergence Sequence

## Verdict Review

Adopt the consolidated verdict with one scope correction: this is the final
normal-coordination convergence pass, not a requirement to make every managed
executor universally capable of producing semantic results.

The target invariant is:

> Direct reasoning is the ordinary path. Managed execution is selected only
> when it provides concrete value. Each managed executor has one authoritative
> result boundary. If that boundary cannot attribute a result to the current
> attempt, the managed semantic result is unavailable and is never reconstructed
> from terminal UI. Cleanup uncertainty affects resource reuse, not valid
> semantic work. Git and GitHub remain durable integration truth.

The completed Normal Coordination and invocation-correlation plans remain
historical evidence. This plan records only the remaining convergence work and
does not reopen their task ledgers.

### Source-truth record

| Evidence | Recorded fact |
| --- | --- |
| Current implementation baseline | `cbe684edd29897bf92625b25358ee1436b65b52a` (`origin/main` at activation) |
| Frozen local candidate | `a821c6f11070aedb9b852c7f651c92ebe4d5b077` (final plan-ledger checkpoint) |
| Known blocker | At the cited `cbe684e` baseline, Windows runtime assertion observes `1800.0000000000002 <= 1800.0` in `test_deepagents_main_bounds_native_attempt_and_keeps_acceptance_pending` |
| Architectural mismatch | Codex managed observation supplies lifecycle/terminal diagnostics but no trusted attributable structured semantic result boundary |
| Current safety rule | Terminal/pane output is diagnostic only unless authorship and current-attempt attribution are proven by an accepted structured source |
| Remote follow-up | GitHub branch protection/ruleset administration is separate after local/runtime convergence and is not a new Project OS machinery task |

## Goal

Finish the remaining Normal Coordination convergence sequence by fixing the
Windows timeout boundary, making semantic admission depend on one explicit
structured result contract, preventing unsupported Codex managed dispatch,
retiring redundant terminal-derived semantic heuristics after consumer tracing,
and recording the managed closure limitation as an explicit capability result.

## Implementation Outcomes

### Bounded runtime and truthful semantic admission

The launcher never exposes an effective DeepAgents wall-clock budget above its
configured allowance, including at the maximum boundary. Semantic admission
uses one canonical current-attempt structured executor result; terminal output
cannot independently become semantic content.

### Explicit adapter capability and closure state

Dispatch selects the direct Secretary/CoS path for ordinary advisory work and
only selects managed execution when its required capability is declared and
available. Codex's missing attributable-result capability is reported as
`BLOCKED_CAPABILITY` for that optional managed path without weakening direct
reasoning or reconciliation safety.

### Reduced compatibility surface with proof

Redundant terminal semantic inference and dead compatibility aliases are removed
only after tracing all callers and preserving required diagnostic/resource
behavior. Focused regressions and the exact runtime/contract matrix prove the
result, resource, observation, and timeout boundaries independently.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `fresh managed worktree` from the verified `origin/main` base; use disposable task-owned worktrees for live probes only
- Commit policy: `verified per-task checkpoint commits preauthorized`
- Preauthorized local actions: inspect callers and history, edit listed source/tests/docs, run declared local validators and focused/full test commands, create approved disposable worktrees, and record bounded local evidence
- User-approval actions: change predecessor acceptance semantics, modify remote workflow checkout policy, push the exact candidate branch, create or update the exact-candidate PR for remote verification, merge, GitHub ruleset or branch-protection changes, external publication, destructive recovery, and cleanup outside task-owned disposable resources
- Parallel ownership: none; timeout, admission, dispatch, deletion, and evidence changes share contracts and execute sequentially
- Sequential fallback: if a task reveals a broader contract or base revision change, stop, record the blocker, and re-evaluate the remaining sequence before editing further

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/final-normal-coordination-convergence`
- Base commit: `origin/main` exact SHA recorded at activation
- Expected workspace: `fresh managed worktree`; preserve unrelated primary-checkout changes
- Next action: none; exact-SHA remote proof is complete
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | fresh worktree | `codex` | none | Windows boundary regression and focused launcher suite pass | `tests/test_herdr_main_launcher.py`; boundary was not reproducible at base, so the shared timeout projection was clamped and proven deterministically |
| Task 2 | `completed` | same worktree | `codex` | Task 1 | structured current-attempt result is the only semantic admission source | `tests/test_secretary_live_runtime.py`; terminal `content` remains diagnostic and cannot become semantic content |
| Task 3 | `completed` | same worktree | `codex` | Task 2 | unsupported adapter is blocked before managed semantic dispatch | `tests/test_secretary_live_runtime.py`; zero Herdr/executor calls on normal managed preflight |
| Task 4 | `completed` | same worktree | `codex` | Task 3 | consumer-traced deletion has no diagnostic/resource regression | repository search; all listed helpers remain required for freshness diagnostics |
| Task 5 | `completed` | same worktree | `codex` | Task 4 | docs and predecessor plan are reconciled after final code shape | maintained docs already aligned; predecessor remains explicitly blocked on its live structured-result acceptance gate |
| Task 6 | `completed` | same worktree | `codex` | Tasks 1–5 | workflow checkout policy is included before local verification and candidate freeze | both workflows now check out and assert the immutable PR-head SHA |
| Task 7 | `completed` | same worktree | `codex` | Task 6 | local final matrix passes and candidate SHA is frozen | final local `HEAD`; focused runtime/launcher suites, validators, adapter sync/drift checks, and `git diff --check` passed |
| Task 8 | `completed` | same worktree | `codex` | Task 7 | exact-SHA GitHub checks pass or plan is blocked on authorization | PR #89 at `a821c6f11070aedb9b852c7f651c92ebe4d5b077`; Repository contracts job `114867816864`, Runtime contracts Ubuntu job `114867816752`, Runtime contracts Windows job `114867816763`, and benchmark job `114867817002` all passed; workflow logs verified immutable checkout/assertion |

## Task Breakdown

### Task 1: Clamp the Windows timeout boundary

**Purpose:**
- Fix the floating-point epsilon that lets the effective runtime budget exceed
  the configured maximum.

**Task Function:**
- Diagnose and correct shared attempt-budget projection at the production
  boundary, then prove the exact maximum case.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: narrow arithmetic/runtime defect with an existing failing
  regression and no delegation benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused cross-platform tests and validators provide direct
  proof.

**Specification Coverage:**
- The effective budget must satisfy `0 <= effective <= configured maximum`
  for native and remaining-allowance calculations.
- Fix production clamping/rounding rather than weakening the assertion.
- Preserve pending acceptance and timeout semantics.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:resolve_launch`
- Inspect: `scripts/herdr_main_launcher.py:_main_body`
- Inspect: `scripts/project_os_runtime/attempt.py:resolve_attempt_budget`
- Inspect: the outer timeout projection that subtracts `time.monotonic()` from
  `attempt_deadline`
- Modify: the narrowest production boundary identified by the trace as owning
  the maximum invariant
- Verify: `tests/test_herdr_main_launcher.py:test_deepagents_main_bounds_native_attempt_and_keeps_acceptance_pending`

**Dependencies:**
- Use the exact failing Windows evidence and trace every caller of the shared
  budget helper before editing.

**Authority:**
- Preauthorized local actions: reproduce the boundary, patch the narrowest production boundary that owns the maximum invariant, and add/update focused regression assertions
- Stop for: changing timeout policy, weakening stale/cleanup guarantees, or discovering an unrelated provider/runtime defect

**Steps:**
- [x] Step 1: Reproduce the failure and trace all budget-helper callers,
  including remaining allowance and launcher projection paths.
- [x] Step 2: Correct the narrowest production boundary that prevents epsilon
  above the configured maximum while preserving native sentinel behavior.
- [x] Step 3: Add deterministic clock-controlled maximum and fractional-boundary
  regressions with a strict `effective_timeout <= configured_maximum` assertion;
  do not rely on incidental Windows timing or an epsilon-tolerant assertion.

**Verification:**
- [x] `pytest -q tests/test_herdr_main_launcher.py -k "bounds_native_attempt or wall_clock"`
- Expected: the boundary assertion passes and no unrelated launcher tests regress.

**Exit Criteria:**
- The production boundary that owns the invariant cannot emit a budget above its
  configured bound, and the focused regression passes on the supported runtime
  matrix.

### Task 2: Reduce semantic admission to one structured result boundary

**Purpose:**
- Make current-attempt structured executor results the sole semantic truth and
  keep terminal observation diagnostic.

**Task Function:**
- Trace and simplify admission without creating a new receipt hierarchy or
  result registry.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-cutting result contract change requires source-first
  controller ownership.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused admission/correlation tests are the independent
  proof surface.

**Specification Coverage:**
- Accept only a structured result whose assignment/attempt identity matches the
  submitted attempt, whose producer/source is trusted, and whose result shape is
  valid.
- Return `reported`, `unavailable`, or `ambiguous` deterministically.
- Preserve a valid semantic result when observation or cleanup fails.
- Never infer assistant authorship from bullets, nonce echoes, screen freshness,
  completion markers, output hashes, or answer-like terminal text alone.
- Task 2 removes terminal data from semantic authority; it does not require
  deleting terminal-parser code while diagnostic consumers may still exist.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_observe_submitted_codex`
- Inspect: `scripts/secretary_live_runtime.py:_extract_codex_semantic_content`
- Inspect: `scripts/secretary_live_runtime.py:_normalize_invocation_outcome`
- Inspect: `scripts/herdr_main_launcher.py:_codex_completion_snapshot`
- Modify: the smallest shared admission/normalization symbols identified by
  caller tracing
- Verify: `tests/test_secretary_live_runtime.py`,
  `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 1 must pass so semantic changes are not confounded by a failing runtime
  bound.
- Existing trusted TaskResult/runtime result producers remain authoritative;
  do not accept terminal text as a replacement.

**Authority:**
- Preauthorized local actions: trace callers, simplify existing admission logic, and add focused regressions for authoritative, stale, missing, conflicting, and observation-failure cases
- Stop for: new receipt schema, new polling service, provider dependency, or any weakening of stale-output rejection

**Steps:**
- [x] Step 1: Enumerate every caller and consumer of semantic extraction,
  normalized result, and terminal snapshot fields; record fields that remain
  diagnostic-only.
- [x] Step 2: Make the structured current-attempt result predicate canonical and
  derive compatibility projections from it once.
- [x] Step 3: Remove only terminal-derived semantic admission branches that the
  caller trace proves redundant; retain diagnostic and resource evidence.
- [x] Step 4: Add regressions for trusted result, missing result, conflicting
  authoritative results, terminal-only text, and valid result plus observation
  failure.

**Verification:**
- [x] `pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py -k "result or semantic or observe or correlation"`
- Expected: structured results report, terminal-only output is unavailable, and
  conflicts are ambiguous without erasing valid resource facts.

**Exit Criteria:**
- There is one semantic decision boundary and no terminal-only path can publish
  managed semantic content.

### Task 3: Fail fast when managed semantic-result support is unavailable

**Purpose:**
- Prevent an already-selected managed invocation from launching when its required
  attributable structured result capability is absent.

**Task Function:**
- Add the smallest adapter-local preflight check. Execution-selection policy
  remains owned by Secretary/CoS; this task does not implement direct-path
  selection or automatic fallback.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: dispatch policy is coupled to the result contract and should
  remain under the lead controller.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing launcher/Secretary contract tests cover the managed
  result boundary directly.

**Specification Coverage:**
- `SecretaryNormalRequest` and `build_normal_launcher_command` are the existing
  normal-mode contract: this managed invocation requires an attributable
  semantic result, while the general `SecretaryLaunchRequest` path remains
  available for launches that do not require semantic publication.
- Once a normal managed invocation has been selected, the runtime checks only
  whether the selected Codex adapter can satisfy that result boundary.
- An adapter that cannot provide an attributable result fails closed as
  `BLOCKED_CAPABILITY` before executor launch and before futile observation
  polling.
- The caller may independently select a safe direct path; the managed runtime
  does not become a router.
- Do not add an executor capability registry, readiness state, fallback
  dispatch, provider query, or terminal inference.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:SecretaryNormalRequest`
- Inspect: `scripts/secretary_live_runtime.py:build_normal_launcher_command`
- Inspect: `scripts/secretary_live_runtime.py:run_normal`
- Inspect: `scripts/herdr_main_launcher.py:resolve_launch`
- Inspect: the existing structured-result producer/source validation used by
  the normal invocation
- Modify: the normal managed-invocation preflight owner only; do not extend
  `scripts/project_os_runtime/capabilities.py` into a result registry
- Verify: `tests/test_secretary_live_runtime.py`,
  `tests/test_herdr_main_launcher.py`, and capability contract tests

**Dependencies:**
- Task 2 defines the required structured result boundary and its trusted
  producer/source contract.

**Authority:**
- Preauthorized local actions: add the adapter-local preflight gate and focused blocked-before-launch regressions
- Stop for: broad launcher API redesign, direct-path routing inside the runtime, a generic capability registry, provider queries, or treating terminal output as capability proof

**Steps:**
- [x] Step 1: Treat the existing `SecretaryNormalRequest` normal-mode route as
  the result-required invocation contract; preserve the general launch route
  for non-semantic work and do not create a registry.
- [x] Step 2: Return `BLOCKED_CAPABILITY` before executor launch when the
  selected adapter cannot provide attributable structured output.
- [x] Step 3: Prove zero executor launches and zero observation polls on the
  blocked normal path, while the Secretary/CoS role contract separately proves
  direct advisory reasoning remains available when optional telemetry is absent.

**Verification:**
- [x] `pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py -k "capabil or direct or managed"`
- Expected: unsupported normal managed capability returns the bounded blocked
  contract before launch or observation; direct-path policy is proven by the
  role/contract suite in Task 6.

**Exit Criteria:**
- An already-selected managed invocation never launches when its adapter cannot
  satisfy the result boundary, and capability absence is explicit rather than
  misreported as a runtime failure.

### Task 4: Remove redundant compatibility code after consumer tracing

**Purpose:**
- Reduce the semantic compatibility surface only where the call graph proves it
  is no longer needed.

**Task Function:**
- Trace consumers, delete dead terminal heuristics/aliases, and preserve any
  fields still required for diagnostics, cleanup, or backward-compatible output.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deletion is riskier than addition and requires direct caller
  tracing.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused regression suites and static search provide proof.

**Specification Coverage:**
- Task 2 removes terminal data from semantic authority; it does not require
  deleting terminal-parser code while diagnostic consumers may still exist.
- Do not delete a compatibility field until all consumers migrate or are proven
  absent.
- Keep one semantic outcome and independent resource/observability projections.
- Preserve privacy redaction and fail-closed trust-boundary validation.

**Required Skills:**
- `skill-systematic-debugging`, `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: all callers of `_codex_initial_prompt_bullet`,
  `_extract_codex_completion_marker`, `_codex_completion_prefix`, and
  `_codex_has_post_completion_bullet`
- Modify: only helpers/aliases proven dead by the trace
- Verify: `tests/test_secretary_live_runtime.py`,
  `tests/test_herdr_main_launcher.py`, and repository-wide text search

**Dependencies:**
- Task 2 must establish the canonical semantic boundary before deletion.

**Authority:**
- Preauthorized local actions: remove only consumer-free semantic compatibility code and update focused tests
- Stop for: uncertain consumer ownership, public compatibility impact, or any deletion that changes resource/observation semantics

**Steps:**
- [x] Step 1: Search symbol references and inspect dynamic/serialized consumers.
- [x] Step 2: Delete only redundant semantic heuristics or aliases; retain
  diagnostic fields with explicit scope when still consumed.
- [x] Step 3: Run focused tests and `git diff --check`.

**Verification:**
- [x] `rg -n "_codex_initial_prompt_bullet|_extract_codex_completion_marker|_codex_completion_prefix|_codex_has_post_completion_bullet" scripts tests docs`
- Expected: no unjustified consumers remain; required diagnostic paths remain
  covered by tests.

**Exit Criteria:**
- The smallest safe compatibility surface remains, with no deleted consumer or
  regression evidence.

### Task 5: Reconcile maintained docs and close the predecessor plan

**Purpose:**
- Make the final managed Codex limitation explicit without claiming semantic
  closure that the runtime cannot prove, and leave one terminal plan truth.

**Task Function:**
- Verify maintained contracts against the final code shape, make only necessary
  corrections, and terminally close the predecessor plan once result-admission
  safety is proven.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: documentation and plan state must follow the final source and
  test evidence.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository contract validators and plan validation are direct.

**Specification Coverage:**
- `BLOCKED_CAPABILITY` is an acceptable result for the optional structured Codex
  path after result-admission safety is verified.
- Direct reasoning, semantic outcome, resource settlement, and observability
  remain independent facts.
- Existing docs are verify-before-edit: if already aligned, record that fact and
  do not churn the file.
- The predecessor managed-invocation plan is not marked `completed` merely by
  changing its status. Its existing live-probe acceptance remains authoritative
  unless an explicit scope-acceptance decision changes the Goal, ledger,
  completion criteria, and status together.

**Required Skills:**
- `skill-code-standards`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Inspect: `docs/operating_system/tooling/runtime-tool-resolution.md`
- Modify: the two maintained docs only when they contradict final behavior
- Modify: `docs/superpowers/plans/2026-10-12-managed-invocation-semantic-provenance-closure-plan.md`
  only after reconciling its Goal, ledger, completion criteria, and status as one
  change; otherwise preserve its blocked state and record the external-capability
  blocker
- Verify: `scripts/validate_planning_lifecycle.py`,
  `scripts/validate_repo_contracts.py`

**Dependencies:**
- Tasks 2–4 must establish the final source behavior before documentation and
  predecessor-plan reconciliation.

**Authority:**
- Preauthorized local actions: verify and minimally correct maintained docs, inspect the predecessor acceptance contract, and record immutable evidence for its disposition
- Stop for: claiming managed Codex semantic success without a trusted structured result bridge, changing predecessor acceptance semantics without explicit approval, or rewriting historical predecessor plans outside the named active plan

**Steps:**
- [x] Step 1: Inspect both maintained docs against the final source/tests and
  change them only if a contradiction remains.
- [x] Step 2: Compare the predecessor Goal, ledger, and completion criteria with
  the final evidence. Preserve its blocked state if its live-probe requirement
  remains unmet.
- [x] Step 3: If the optional capability-limited outcome is accepted as a new
  scope, obtain explicit approval and update the predecessor Goal, ledger,
  completion criteria, and terminal status together; never change status alone.

**Verification:**
- [x] `python scripts/validate_planning_lifecycle.py`
- [x] `python scripts/validate_repo_contracts.py --fast`
- Expected: maintained docs are aligned or explicitly unchanged, and the
  predecessor disposition is either contract-validly terminal or explicitly
  blocked on the named live/acceptance dependency.

**Exit Criteria:**
- Documentation matches final code behavior, and the predecessor plan has a
  contract-valid disposition with any remaining capability or acceptance gate
  recorded as fact.

### Task 6: Prepare exact-SHA workflow verification

**Purpose:**
- Add and locally inspect the immutable PR-head checkout/assertion policy before
  any candidate verification or freeze.

**Task Function:**
- Update only the named repository/runtime workflow jobs so remote checks can
  prove which source SHA they executed.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance and evidence ownership stay with the lead.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: fresh automated matrix plus bounded live probes.

**Specification Coverage:**
- Validate the Secretary/CoS role and policy contracts for direct reasoning
  without Herdr/provider telemetry.
- Validate no-capability dispatch, terminal-only output, trusted result,
  observation failure, conflicting results, cleanup timeout, ambiguous delivery,
  shared resource ownership, and Windows maximum-bound behavior.
- Live probes, when applicable, record candidate SHA, runtime versions, launch count, useful-result
  latency, total duration, cleanup state, and unresolved owned resources.
- Two functional runs establish path behavior only; they do not justify tail
  latency claims.

**Required Skills:**
- `skill-code-standards`, `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `.github/workflows/repo-contracts.yml`
- Modify: `.github/workflows/runtime-contracts.yml`
- Verify: every required checkout uses the immutable PR-head SHA and asserts
  `git rev-parse HEAD` against the expected SHA

**Dependencies:**
- Tasks 1–5 complete with no unresolved local regressions.

**Authority:**
- Preauthorized local actions: edit and locally inspect the named workflow checkout/assertion steps without changing trigger scope
- Stop for: changing workflow triggers or job scope, adding unrelated CI infrastructure, or any mismatch between expected and asserted source identity

**Steps:**
- [x] Step 1: Update both workflows to check out the immutable PR head SHA for
  pull requests and assert the resolved `HEAD` before tests run.
- [x] Step 2: Verify the workflow diff keeps existing triggers/jobs and does not
  introduce unrelated CI behavior.

**Verification:**
- [x] Workflow YAML/static inspection confirms the expected SHA is explicit and
  asserted in repository, runtime matrix, and benchmark jobs.
- [x] `git diff --check`
- Expected: workflow changes are ready to be included in the candidate commit;
  no candidate SHA has been frozen yet.

**Exit Criteria:**
- Workflow checkout policy is part of the source that will be locally verified
  and frozen; no remote claim is made yet.

### Task 7: Run local final verification and freeze the candidate

**Purpose:**
- Prove the final code and workflow shape locally, then freeze one exact
  candidate SHA before remote publication.

**Task Function:**
- Execute the local matrix, classify unsupported live capability honestly, and
  preserve exact candidate identity and runtime evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final local acceptance and evidence ownership stay with the lead.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: fresh automated matrix plus bounded live probes.

**Specification Coverage:**
- Validate the Secretary/CoS role and policy contracts for direct reasoning
  without Herdr/provider telemetry.
- Validate no-capability dispatch, terminal-only output, trusted result,
  observation failure, conflicting results, cleanup timeout, ambiguous delivery,
  shared resource ownership, and Windows maximum-bound behavior.
- Live probes, when applicable, record candidate SHA, runtime versions, launch
  count, useful-result latency, total duration, cleanup state, and unresolved
  owned resources.
- Two functional runs establish path behavior only; they do not justify tail
  latency claims.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `tests/test_secretary_live_runtime.py`
- Verify: `tests/test_herdr_main_launcher.py`
- Verify: `tests/test_secretary_benchmark.py`
- Verify: `tests/test_benchmark_completion_monitoring.py`
- Verify: `tests/test_reconciliation.py`
- Verify: `tests/test_runtime_tool_resolution_contract.py`
- Verify: `tests/test_skill_project_secretary.py`
- Verify: `tests/test_skill_chief_of_staff.py`
- Verify: `scripts/benchmark_secretary_architecture.py`
- Verify: `scripts/validate_repo_contracts.py`
- Verify: `scripts/validate_planning_lifecycle.py`
- Verify: `scripts/sync_agent_adapters.py`

**Dependencies:**
- Task 6 workflow changes are present in the candidate source.
- Live capability gaps remain classified as blocked/unavailable, never as
  successful semantic evidence.

**Authority:**
- Preauthorized local actions: run the declared local test/validator matrix and bounded local live probes, then record evidence and freeze the candidate SHA
- Stop for: missing trusted result provenance, destructive cleanup, external publication, or a mismatch between observed and claimed outcome

**Steps:**
- [x] Step 1: Run focused tests, full relevant backend/runtime tests, contract
  validators, generated-surface checks, and `git diff --check`.
- [x] Step 2: Run two bounded live probes only if the selected adapter exposes
  the required structured result boundary; otherwise record `BLOCKED_CAPABILITY`
  with the exact missing evidence.
- [x] Step 3: Reconcile semantic, resource, observability, benchmark, workflow,
  and plan evidence; record the exact candidate SHA as the local verification
  checkpoint.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py tests/test_secretary_benchmark.py tests/test_benchmark_completion_monitoring.py tests/test_reconciliation.py tests/test_runtime_tool_resolution_contract.py tests/test_skill_project_secretary.py tests/test_skill_chief_of_staff.py`
- [x] `python scripts/validate_repo_contracts.py --fast`
- [x] `python scripts/validate_planning_lifecycle.py`
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `git diff --check`
- Expected: all applicable checks pass; unsupported live capability is explicit
  and does not become a false success claim.

**Exit Criteria:**
- Fresh local evidence supports the final invariant, every unavailable capability
  is bounded and recorded, and one candidate SHA including workflow changes is
  frozen for remote checks.

### Task 8: Verify the exact candidate remotely after authorization

**Purpose:**
- Complete the checks that cannot run authoritatively until the frozen candidate
  reaches GitHub.

**Task Function:**
- Push only the frozen candidate after explicit user authorization, create or
  update a PR targeting `main`, then verify exact-SHA Repository, Windows,
  Ubuntu, and benchmark checks.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: remote publication and acceptance remain lead-controlled
  external actions.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: GitHub CI is the authoritative remote proof surface.

**Specification Coverage:**
- The candidate SHA tested remotely must equal the locally frozen SHA.
- The PR head SHA and every recorded check run must equal the locally frozen SHA;
  branch-head equality alone is not sufficient evidence.
- Required workflow jobs explicitly check out the immutable PR head SHA and
  assert `git rev-parse HEAD` equals the expected candidate SHA; synthetic PR
  merge identity is not silently treated as candidate-head execution evidence.
- Required checks are Repository contracts, Runtime contracts on Windows and
  Ubuntu, and the benchmark check.
- If push is not authorized, the implementation may be locally verified but the
  plan remains blocked on remote-verification authorization, not on a runtime
  defect.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `.github/workflows/repo-contracts.yml` checkout/assertion steps
- Verify: `.github/workflows/runtime-contracts.yml` checkout/assertion steps
- Verify: GitHub checks for the frozen candidate SHA

**Dependencies:**
- Task 7 must pass and record the immutable candidate SHA.
- User must explicitly authorize pushing that exact candidate for remote proof.
- User must explicitly authorize creating or updating the PR that triggers the
  required checks.

**Authority:**
- Preauthorized local actions: inspect the already-verified workflow checkout/assertion steps and record the PR head SHA, check run IDs, conclusions, and returned immutable results
- Stop for: absent push/PR authorization, SHA mismatch, failed required check, or any request to merge/alter branch protection outside explicit approval

**Steps:**
- [x] Step 1: Present the frozen candidate SHA and request/obtain explicit
  authorization to push the candidate and create or update the PR for remote
  verification.
- [x] Step 2: Push only that candidate and, after explicit authorization, create
  or update one PR targeting `main`; verify its `head.sha` equals the frozen SHA.
- [x] Step 3: Wait for and record the PR number, check run IDs, check names,
  conclusions, and head SHA for Repository, Windows, Ubuntu, and benchmark
  results; do not substitute a different commit or branch-triggered run.

**Verification:**
- [x] `git ls-remote origin <candidate-ref>` matches the frozen SHA
- [x] PR head SHA matches the frozen SHA
- [x] Repository and Runtime workflow logs show checkout of the expected frozen
  SHA and a passing `git rev-parse HEAD` assertion in every required job
- [x] GitHub Repository contracts check passes for the frozen SHA
- [x] GitHub Runtime contracts Windows check passes for the frozen SHA
- [x] GitHub Runtime contracts Ubuntu check passes for the frozen SHA
- [x] GitHub benchmark check passes for the frozen SHA
- Expected: exact-SHA remote proof is complete; otherwise the plan is explicitly
  blocked or failed with the immutable check evidence recorded.

**Exit Criteria:**
- The exact candidate SHA passes all required remote checks, or the plan records
  a precise remote authorization/check blocker without claiming completion.

## Verification

- `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py tests/test_secretary_benchmark.py tests/test_benchmark_completion_monitoring.py tests/test_reconciliation.py tests/test_runtime_tool_resolution_contract.py tests/test_skill_project_secretary.py tests/test_skill_chief_of_staff.py`
- `python scripts/validate_repo_contracts.py --fast`
- `python scripts/validate_planning_lifecycle.py`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- `git diff --check`
- Windows and Ubuntu runtime matrices for the exact candidate SHA after the
  explicit push authorization gate
- Two bounded live probes, or an explicit `BLOCKED_CAPABILITY` record when the
  selected adapter cannot provide a trusted structured result

## Completion Criteria

The plan is ready for completion verification when:

1. the runtime never exceeds an enforced configured deadline;
2. only a trusted structured result bound to the current attempt becomes managed
   semantic truth;
3. unsupported managed semantic paths fail before dispatch without preventing
   ordinary direct reasoning;
4. semantic result, resource settlement, observability, and optional reporting
   remain independent; and
5. the exact candidate SHA passes local verification and required GitHub
   Windows/Ubuntu/contract checks.

The plan may be marked `completed` only after
`skill-verification-before-completion` performs fresh final verification and
records the exact candidate SHA and evidence paths. If Task 7 passes but Task
8 lacks authorization or required remote checks, the plan remains locally
verified but blocked on that remote gate. Push, merge, branch protection, and
ruleset changes require separate user authorization.
