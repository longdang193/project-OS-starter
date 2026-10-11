---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: normal-invocation-correlation-and-finalization-closure
targets:
  - scripts/secretary_live_runtime.py
  - scripts/herdr_main_launcher.py
  - scripts/benchmark_secretary_architecture.py
  - scripts/benchmark_completion_monitoring.py
  - tests/test_secretary_live_runtime.py
  - tests/test_herdr_main_launcher.py
  - tests/test_secretary_benchmark.py
  - tests/test_benchmark_completion_monitoring.py
  - tests/test_skill_chief_of_staff.py
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/codex/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/claude/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md
---

# Normal Invocation Correlation and Finalization Closure

## Goal

Make one normal Secretary invocation trustworthy from submission through
semantic result capture and resource finalization. A result is accepted only
when it is correlated to the submitted request; cleanup uncertainty never
erases a captured answer; ownership and source truth remain explicit; and
measurement output reports observed facts rather than expectations.

The verdict is adopted with a narrow scope. The earlier assignment/attempt
correlation and `unknown` to `removed` cleanup behavior remain preserved. This
plan does not reopen completed convergence work.

## Implementation Outcomes

### Submission-bound completion correlation

`run_normal()` and its observation path record the submission-bound freshness
anchor before delivery, accept an answer that completed before the first poll,
reject stale recovered output, and keep terminal-rendering compatibility behind
the existing semantic-content adapter.

### Exception-safe finalization and ownership

The invocation envelope exists before acquisition, resource identities are
recorded immediately after creation, cleanup helpers are total/non-throwing,
and captured semantic results survive close or retirement failures. Shared or
pre-existing resources are referenced but never reported as invocation-owned;
authoritative cleanup conflicts quarantine reuse and require recovery.

### Safe semantic output and truthful measurement

Strict metadata sanitization remains in place while semantic prose is filtered
at the value level, preserving ordinary security explanations and redacting
actual bearer tokens/configured secrets. Benchmark and validation CLIs expose
unobserved values as unavailable and return nonzero for incorrect validation
rows.

### Source-of-truth and bounded verification alignment

The CoS advisory wording requires repository identity and exact revision only
where the operation needs exact audit evidence, without making exact SHA a
universal prerequisite. Canonical skill edits regenerate provider mirrors, and
focused deterministic tests plus one disposable live probe prove the normal
path without adding orchestration, registries, retry managers, or provider
telemetry dependencies.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `fresh managed worktree` on a fresh `codex/normal-invocation-correlation-and-finalization-closure` branch from the recorded `origin/main` base; preserve all primary-checkout user changes and the historical plan without copying them into the implementation lane
- Commit policy: `checkpoint commits are created by the lead after task-local acceptance`; no push, merge, ruleset administration, or other external publication is part of this plan
- Preauthorized local actions: create the fresh worktree/branch, add the plan as the first workflow checkpoint, inspect and edit listed repository files, run focused tests and repository validators, regenerate declared generated skill mirrors, and run one bounded disposable normal-path probe with no repository mutation
- User-approval actions: push, merge, GitHub ruleset changes, destructive recovery, deleting or discarding user work, adding dependencies, or expanding scope beyond this plan
- Parallel ownership: none; runtime, tests, canonical skill text, generated mirrors, and benchmark truth have ordering and shared-contract dependencies
- Sequential fallback: complete Tasks 1 through 5 in order with the lead controller as the sole ledger writer; if delegation is unavailable, keep all tasks in the isolated worktree

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/normal-invocation-correlation-and-finalization-closure`
- Base commit: `14b0081c70c7a8f2a87846a827ec3a33b6730e1a` (`origin/main` at plan review)
- Expected workspace: fresh managed worktree at the recorded base, clean before the plan checkpoint; primary-checkout changes and `docs/superpowers/plans/2026-10-11-normal-coordination-source-truth-convergence-plan.md` remain preserved outside the implementation lane
- Next action: complete final verification, commit the implementation, and hand off for authorized publication/review
- Blockers: mandatory normal semantic path passed; optional structured receipt/economics qualification is `BLOCKED_CAPABILITY` because the live probe captured the exact semantic answer but no structured runtime receipt was published

Preflight admission requires all of the following before Task 1:

- `git rev-parse HEAD` equals the recorded base SHA and the fresh worktree is
  based on the same `origin/main` revision;
- `git status --short` is empty before adding the plan checkpoint;
- target symbols named in Tasks 1–5 still exist with the expected ownership;
- the implementation branch is created from the verified base, not from the
  dirty primary checkout;
- any movement of `origin/main` stops activation until the base, diff, and
  focused baseline are re-evaluated.

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | fresh worktree | `codex` | none | fast, stale, fresh, partial, and mismatched correlation cases pass | focused runtime and launcher suites pass; 364-test combined suite later passed |
| Task 2 | `completed` | fresh worktree | `codex` | Task 1 | result survives cleanup failure; identities retained; closure uncertainty is explicit | cleanup transport/malformed-response regressions pass; run_probe acquisition envelope added |
| Task 3 | `completed` | fresh worktree | `codex` | Task 1 | prose preserved; actual secret values redacted | semantic redaction and metadata tests pass in focused runtime suite |
| Task 4 | `completed` | fresh worktree | `codex` | Task 2 | ownership and authoritative resource evidence reconcile; CoS mirrors pass sync/check | monotonic reducer, ownership, reconciliation, adapter sync/check, and header validation pass |
| Task 5 | `completed` | fresh worktree | `codex` | Tasks 1–4 | incorrect benchmark row exits nonzero; unavailable values are not fabricated | completion monitor and secretary benchmark regressions pass; CLI exits nonzero on injected mismatch |

## Task Breakdown

### Task 1: Correlate normal completion to submission

**Purpose:**
- Make response freshness depend on the submission boundary rather than on
  observing an intermediate `working` state.

**Task Function:**
- Implement and test the smallest submission-bound observation contract.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded but cross-cutting runtime correctness; keep control
  with the lead controller.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: task-local focused tests provide the required independent
  assertions.

**Specification Coverage:**
- Capture assignment/invocation identity, pre-submit state sequence, and
  pre-submit output fingerprint before delivery.
- Accept a fresh answer that is already idle/done on the first poll.
- Reject idle or recovered output that predates submission.
- Accept semantic output only when all three conditions hold: assignment/attempt
  identity matches the submitted invocation; at least one submission-bound
  freshness proof exists; and semantic output is terminal and complete.
- Use freshness evidence in this order: assignment-bound structured result,
  assignment-bound result identity absent before submission, sequence/revision
  greater than the pre-submit anchor, or another existing authoritative
  submission-bound identity. Terminal output alone never proves freshness.
- Keep terminal rendering markers behind one adapter.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_observe_submitted_codex`
- Inspect: `scripts/secretary_live_runtime.py:_normalize_invocation_outcome`
- Inspect: `scripts/secretary_live_runtime.py:_extract_codex_semantic_content`
- Inspect: `scripts/herdr_main_launcher.py:_codex_completion_snapshot`
- Modify: `scripts/secretary_live_runtime.py:_observe_submitted_codex`
- Modify: `scripts/secretary_live_runtime.py:_normalize_invocation_outcome`
- Modify: `scripts/secretary_live_runtime.py:_extract_codex_semantic_content`
- Modify: `tests/test_secretary_live_runtime.py`
- Modify: `tests/test_herdr_main_launcher.py` only when the launcher snapshot
  contract must expose the pre-submit anchor

**Dependencies:**
- Current Herdr/Codex snapshot fields and existing assignment/attempt identity
  must remain the source of truth.
- Do not add a mandatory receipt or new polling service.

**Authority:**
- Preauthorized local actions: change the listed observer/normalizer/adapter symbols and add focused deterministic tests
- Stop for: new receipt schemas, launcher API redesign, provider dependency, or any change that weakens stale-output rejection

**Steps:**
- [x] Step 1: Trace all callers and tests of `_observe_submitted_codex`,
  `_normalize_invocation_outcome`, and semantic extraction; record the current
  identity and snapshot fields used by each caller.
- [x] Step 2: Capture the pre-submit freshness anchor before dispatch and pass it
  through observation without requiring a witnessed `working` transition.
- [x] Step 3: Encode the acceptance predicate as identity match AND
  submission-bound freshness proof AND terminal-complete semantic content; do
  not accept a terminal snapshot by itself.
- [x] Step 4: Make the terminal rendering parser the sole boundary that turns a
  rendered snapshot into a semantic candidate; keep normalizer logic unaware of
  UI markers.
- [x] Step 5: Add regressions for fast completion, stale idle output, read-error
  recovery with old output, fresh post-submit output, partial/stopped output,
  and unrelated output changes whose assignment/attempt identity does not match.

**Verification:**
- [x] `pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py`
- Expected: the first post-submit idle/done observation with matching identity,
  valid freshness evidence, and complete content is `reported` without deadline
  waiting; stale, mismatched, partial, stopped, or read-error-recovered
  pre-submit output is `unavailable`.

**Exit Criteria:**
- The observer proves freshness from submission-bound evidence and every listed
  response-correlation case has focused passing tests.

### Task 2: Make acquisition, execution, and cleanup exception-safe

**Purpose:**
- Ensure cleanup cannot erase a captured result or lose the identity of a
  resource created before a later failure.

**Task Function:**
- Harden the normal invocation envelope and totalize resource finalization.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: material backend failure-path work with shared cleanup
  helpers; lead-controlled serialization avoids inconsistent lifecycle edits.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct boundary tests cover success, failure, and final state.

**Specification Coverage:**
- Initialize the invocation envelope before resource acquisition.
- Record workspace, session, pane, and agent identities immediately after each
  acquisition succeeds.
- Make close and retirement helpers non-throwing for transport errors,
  malformed JSON, null payloads, and nonzero exits.
- Preserve captured semantic results through `OSError`, timeout, and cleanup
  uncertainty; quarantine resources when closure is unproven.
- Represent semantic and finalization facts independently:
  `semantic_outcome` is `reported`, `unavailable`, or `failed`;
  `finalization_outcome` is `settled`, `recovery_required`, or `blocked`.
- Keep the internal invocation envelope small and local: submission identity and
  pre-submit anchor; semantic outcome, result identity, and content; resource
  identities, ownership kind, and authoritative state; finalization outcome and
  recovery flag; and measurement evidence kind/status. Do not persist it as a
  new schema or service.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:run_normal`
- Inspect: `scripts/secretary_live_runtime.py:run_probe`
- Inspect: `scripts/secretary_live_runtime.py:_close_herdr_workspace`
- Inspect: `scripts/secretary_live_runtime.py:_release_codex_agent`
- Inspect: `scripts/secretary_live_runtime.py:_prepare_herdr_target`
- Inspect: `scripts/secretary_live_runtime.py:_create_herdr_workspace`
- Inspect: `scripts/secretary_live_runtime.py:_owned_resources`
- Inspect: `scripts/secretary_live_runtime.py:_reduce_resource_evidence`
- Inspect: `scripts/secretary_live_runtime.py:main`
- Inspect: `scripts/herdr_main_launcher.py:_terminate_codex_lane`
- Modify: `scripts/secretary_live_runtime.py:run_normal`
- Modify: `scripts/secretary_live_runtime.py:run_probe`
- Modify: `scripts/secretary_live_runtime.py:_close_herdr_workspace`
- Modify: `scripts/secretary_live_runtime.py:_release_codex_agent`
- Modify: `tests/test_secretary_live_runtime.py`
- Verify: `tests/test_herdr_main_launcher.py` for launcher-side lifecycle evidence

**Dependencies:**
- Task 1 response capture must be stable before finalization is rearranged.
- Existing `unknown` to `removed` settlement behavior remains valid and must
  not be replaced with optimistic closure.

**Authority:**
- Preauthorized local actions: edit the listed lifecycle symbols and add direct failure-path tests with fake Herdr boundaries
- Stop for: new cleanup daemon/registry, automatic retry, deletion of shared resources, or treating unknown closure as verified removal

**Steps:**
- [x] Step 1: Map every acquisition and cleanup call in `run_normal()` and
  `run_probe()` and identify where an exception can bypass identity recording.
- [x] Step 2: Initialize one invocation envelope before acquisition and update
  ownership facts immediately after each successful creation.
- [x] Step 3: Preserve a creation-side-effect fact when remote creation may have
  succeeded but the local response is null, malformed, or unparseable; record
  acquisition as uncertain, ownership as unknown, and finalization as
  `recovery_required` instead of claiming that nothing was created.
- [x] Step 4: Convert close and retirement helpers into total result-producing
  functions; preserve malformed/null responses as explicit unproven evidence.
- [x] Step 5: Reconcile `semantic_outcome` before cleanup, then retain it while
  attaching independent `finalization_outcome`, quarantine, and recovery
  evidence. Answer consumers may consume `reported`; invocation/controller
  completion is incomplete when finalization is `recovery_required` or `blocked`.
- [x] Step 6: Verify the existing resource-selection/reuse gate rejects a
  resource marked `recovery_required`; do not add a quarantine registry.
- [x] Step 7: Add regressions for cleanup `OSError`, cleanup timeout, null or
  malformed close responses, bootstrap failure after known creation,
  creation-success with malformed/null identity response, execution failure
  followed by successful cleanup, and a next invocation attempting to reuse a
  quarantined resource.

**Verification:**
- [x] `pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py`
- Expected: `semantic_outcome = reported` remains consumable when cleanup fails
  while `finalization_outcome = recovery_required`; resources with unproven
  closure are rejected by the next reuse decision; resource identities remain
  present after bootstrap or creation-response failure; cleanup helpers never
  raise for the listed malformed or transport outcomes.

**Exit Criteria:**
- Every acquisition path has durable identity evidence, every cleanup helper is
  total, and cleanup uncertainty constrains reuse rather than semantic result
  delivery.

### Task 3: Separate semantic content from metadata sanitization

**Purpose:**
- Preserve useful normal prose while preventing secret-bearing values from
  crossing the invocation result boundary.

**Task Function:**
- Refine the existing sanitization boundary without broadening output exposure.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: security-sensitive but local to existing sanitizer and
  semantic extraction paths.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused value-level regression cases are sufficient.

**Specification Coverage:**
- Keep strict metadata sanitization for assignment and evidence fields.
- Apply value-level redaction to semantic content for actual bearer tokens and
  configured secret values.
- Preserve explanations that merely mention `password`, `credentials`,
  `authorization`, or similar security terms.
- Cover narrow value-level cases: password/authorization explanations are
  preserved; bearer token values, configured secrets embedded in prose, and
  URL query token values are redacted; applying redaction twice is idempotent.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_safe_text`
- Inspect: `scripts/secretary_live_runtime.py:_safe_assignment`
- Inspect: `scripts/secretary_live_runtime.py:_extract_codex_semantic_content`
- Modify: `scripts/secretary_live_runtime.py:_safe_text` and the owning
  semantic-value boundary only where the current contract requires it
- Modify: `tests/test_secretary_live_runtime.py`

**Dependencies:**
- Task 1 must leave semantic extraction behind one adapter.
- Preserve existing allowlisted metadata keys and do not invent a general
  secret-management subsystem.

**Authority:**
- Preauthorized local actions: change existing sanitization/extraction logic and add secret/non-secret semantic fixtures
- Stop for: logging raw secrets, broad keyword removal, changing public schema without consumer evidence, or adding a secret store

**Steps:**
- [x] Step 1: Trace all callers of `_safe_text`, `_safe_assignment`, and
  `_extract_codex_semantic_content` and classify metadata versus semantic values.
- [x] Step 2: Keep metadata rejection strict while applying redaction only to
  detected secret values in semantic prose.
- [x] Step 3: Add tests for `Never put passwords in source code.`,
  `Authorization headers should be redacted.`, bearer-token values, configured
  secrets embedded in otherwise valid prose, and URL query token values.
- [x] Step 4: Add an idempotency assertion that applying semantic redaction
  twice produces the same output as applying it once.

**Verification:**
- [x] `pytest -q tests/test_secretary_live_runtime.py`
- Expected: security explanations remain usable; only actual configured secret,
  bearer-token, and URL-token values are removed; repeated redaction is stable;
  metadata sanitization tests remain green.

**Exit Criteria:**
- Semantic content and metadata use distinct filtering rules with regression
  proof for both preservation and redaction.

### Task 4: Reconcile CoS source truth and resource ownership

**Purpose:**
- Remove the last contradictory exact-SHA advisory wording and make resource
  evidence reflect actual invocation ownership and authoritative conflicts.

**Task Function:**
- Align canonical coordination guidance, generated mirrors, and resource
  settlement semantics.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: canonical-source and lifecycle-contract work must be
  serialized before generated-surface verification.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing skill and reconciliation tests plus sync/check
  commands provide direct proof.

**Specification Coverage:**
- Exact repository revision is required for exact audit evidence, not for every
  advisory answer.
- `owned_resources` contains only resources created or made retirable by this
  invocation; shared/pre-existing sessions and panes remain referenced only.
- `unknown -> removed` settles when the authoritative response proves removal;
  removed versus authoritative still-present evidence becomes quarantined or
  recovery-required rather than silently settled.
- `_reduce_resource_evidence` must reduce state monotonically according to this
  table:

  | Prior state | New authoritative evidence | Result |
  | --- | --- | --- |
  | `unknown` | `removed` | `removed` |
  | `unknown` | `present` | `present` |
  | `present` | `removed` | `removed` |
  | `removed` | `removed` | `removed` |
  | `removed` | `present` | `conflict` / `recovery_required` |
  | `unknown` | unavailable | `unknown` |

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_owned_resources`
- Inspect: `scripts/secretary_live_runtime.py:_reduce_resource_evidence`
- Inspect: `scripts/secretary_live_runtime.py:_prepare_herdr_target` as the
  existing session/pane selection and reuse gate
- Inspect: `scripts/herdr_main_launcher.py:_terminate_codex_lane` as the
  existing ownership/recovery enforcement boundary
- Modify: `scripts/secretary_live_runtime.py:_owned_resources`
- Modify: `scripts/secretary_live_runtime.py:_reduce_resource_evidence`
- Modify: `.agents/skills/skill-chief-of-staff/SKILL.md`
- Regenerate: `generated_agents/codex/skills/skill-chief-of-staff/SKILL.md`
- Regenerate: `generated_agents/claude/skills/skill-chief-of-staff/SKILL.md`
- Regenerate: `generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md`
- Modify: `tests/test_skill_chief_of_staff.py`
- Verify: `tests/test_reconciliation.py` and relevant runtime tests

**Dependencies:**
- Task 2 establishes cleanup evidence that ownership reduction consumes.
- `.agents/skills` is canonical; generated provider surfaces must be produced by
  `scripts/sync_agent_adapters.py`, never edited directly.

**Authority:**
- Preauthorized local actions: edit the canonical CoS skill and listed runtime ownership reducers, regenerate mirrors, and run sync/check validators
- Stop for: GitHub ruleset administration, new local source-of-truth databases, or deleting pre-existing/shared sessions or panes

**Steps:**
- [x] Step 1: Trace ownership inputs from acquisition through `_owned_resources`
  and enumerate shared/pre-existing versus invocation-created resources.
- [x] Step 2: Make the ownership list invocation-bound and add conflict handling
  that preserves authoritative `still present` evidence as quarantine/recovery.
- [x] Step 3: Implement and test the monotonic resource-state reduction table;
  ensure a `recovery_required` resource is rejected by the existing next-use
  selection/reuse predicate.
- [x] Step 4: Correct the exact-SHA advisory wording in the canonical CoS skill
  without changing the broader Secretary/CoS/Worker model.
- [x] Step 5: Run `python scripts/sync_agent_adapters.py --all-platforms` and
  verify generated mirrors with `--check`; then compare `git diff --name-only`
  and untracked paths against the declared canonical skill, three expected
  generated mirrors, and task-owned test files. Stop if synchronization touches
  any undeclared generated surface.
- [x] Step 6: Add focused regressions for distinct assignment/attempt IDs,
  same-field identity conflict, shared/pre-existing resources, `unknown ->
  removed`, removed versus authoritative still-present evidence, every row of
  the monotonic reduction table, and reuse rejection for quarantined resources.

**Verification:**
- [x] `pytest -q tests/test_skill_chief_of_staff.py tests/test_reconciliation.py tests/test_secretary_live_runtime.py`
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: canonical and generated CoS wording agree; shared resources are
  never owned; authoritative conflicts quarantine; the reduction table is
  monotonic; the reuse gate rejects quarantined resources; sync/check reports no
  drift and no undeclared generated file changed.

**Exit Criteria:**
- Source truth, ownership semantics, and generated skill surfaces agree with the
  runtime evidence model and pass focused reconciliation proof.

### Task 5: Make benchmark and validation output truthful

**Purpose:**
- Ensure measurement output distinguishes observed facts from unavailable
  values and cannot report incorrect validation rows with exit code zero.

**Task Function:**
- Repair benchmark truthfulness and add the smallest path-level proof needed
  after runtime correctness is established.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded benchmark/CLI work with correctness gates; defer
  broader performance architecture.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: benchmark tests and CLI exit-code assertions cover the
  contract directly.

**Specification Coverage:**
- Never populate unobserved counters from expected dictionaries.
- Mark unavailable counters explicitly when the measurement layer cannot observe
  them.
- Add machine-readable `evidence_kind` to each benchmark row/report using only
  `deterministic_contract`, `fake_boundary_observation`, or
  `disposable_live_probe`; add `measurement_status` as `observed` or
  `unavailable` where a metric is not observable.
- Validation-bearing CLI modes return nonzero when any row has `correct = false`.
- Keep the existing normalizer/reporting measurement named as such. Defer a new
  `measure-path` command; it is not required to close this correctness pass.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/benchmark_secretary_architecture.py:ContractMetric`
- Inspect: `scripts/benchmark_secretary_architecture.py:run_contract_benchmark`
- Inspect: `scripts/benchmark_secretary_architecture.py:main`
- Inspect: `scripts/benchmark_completion_monitoring.py:run_case`
- Inspect: `scripts/benchmark_completion_monitoring.py:main`
- Modify: `scripts/benchmark_completion_monitoring.py:main` and its correctness
  summary/exit contract
- Modify: `scripts/benchmark_secretary_architecture.py:ContractMetric` and
  constructors only to expose deterministic evidence provenance
- Modify: `tests/test_secretary_benchmark.py` only for deterministic contract
  evidence provenance assertions
- Create: `tests/test_benchmark_completion_monitoring.py` for CLI mismatch
  exit-code regression
- Verify: `scripts/benchmark_secretary_architecture.py` remains deterministic
  contract evidence and does not claim empirical latency or token improvement

**Dependencies:**
- Tasks 1–4 define the runtime states and resource facts that benchmark rows
  may truthfully observe.
- `measure-path` remains deferred; it is not needed for this correctness pass.

**Authority:**
- Preauthorized local actions: edit benchmark measurement/validation code and focused benchmark tests; add only bounded fake-boundary instrumentation
- Stop for: claiming latency/token/provider improvements without observation, private launcher decoupling, or broad benchmark redesign

**Steps:**
- [x] Step 1: Keep `benchmark_secretary_architecture.py` labeled as deterministic
  contract evidence; do not present its baseline/target rows as observed
  production measurements.
- [x] Step 2: In `benchmark_completion_monitoring.py`, classify each emitted
  counter as observed by the fake-Herdr harness or unavailable; never copy a
  desired value into an observed field.
- [x] Step 3: Add machine-readable `evidence_kind` and
  `measurement_status` fields to benchmark rows/reports so deterministic
  contract values cannot be consumed as production observations.
- [x] Step 4: Make the completion-monitoring CLI return nonzero whenever its
  correctness summary contains lifecycle, cleanup, reconciliation, or outcome
  mismatches; add a subprocess-level regression that injects one mismatch.
- [x] Step 5: Preserve the current normalizer/reporting benchmark scope and
  defer `measure-path`, private launcher decoupling, and broad benchmark
  redesign.

**Verification:**
- [x] `pytest -q tests/test_secretary_benchmark.py tests/test_benchmark_completion_monitoring.py`
- [x] `python scripts/benchmark_completion_monitoring.py --baseline-revision 14b0081c70c7a8f2a87846a827ec3a33b6730e1a --repetitions 1 --output artifacts/completion-monitoring/normal-invocation-finalization-final.json`
- Expected: deterministic contract rows retain their evidence provenance,
  unobserved fields are unavailable rather than fabricated, and a completion
  monitoring validation result containing an incorrect row exits nonzero.

**Exit Criteria:**
- Benchmark output is honest about evidence provenance, validation failures are
  CI-visible, and no speculative performance claim is introduced.

## Verification

Task-local proof must pass before the next task is activated. After all five
tasks, run the focused suites and repository validators from a clean diff
except for declared plan/worktree artifacts:

- `pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py tests/test_secretary_benchmark.py tests/test_skill_chief_of_staff.py tests/test_reconciliation.py`
- `pytest -q tests/test_benchmark_completion_monitoring.py`
- `python scripts/benchmark_completion_monitoring.py --baseline-revision 14b0081c70c7a8f2a87846a827ec3a33b6730e1a --repetitions 1 --output artifacts/completion-monitoring/normal-invocation-finalization-final.json`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_generated_header_format.py`
- `python scripts/validate_planning_lifecycle.py`
- `python scripts/validate_repo_contracts.py`
- `git diff --check`

Then run one bounded disposable normal-path probe with a unique nonce:

`Return exactly SECRETARY_PROBE_<nonce>. Do not modify repository files. Do not create another Worker.`

Capture the submission baseline before delivery and require all of the
following: exact nonce returned; no 120-second false wait; semantic result
survives cleanup uncertainty; task-owned agent/process/workspace retires;
shared/pre-existing resources remain untouched; no automatic second dispatch;
and no provider telemetry is required for normal semantic success. Keep strict
receipt/economics qualification separate. If the normal Secretary/Herdr/Codex
path cannot execute or the probe cannot establish the required semantic and
resource evidence, plan completion is `BLOCKED_CAPABILITY` because the live
criterion is mandatory. If the normal semantic path succeeds but optional
receipt/economics telemetry is unavailable, the normal result remains valid and
only receipt/economics qualification is `BLOCKED_CAPABILITY`.

Final verification must also confirm the repository remains unchanged by the
probe, the pre-existing historical plan is untouched, and no excluded
orchestration, registry, daemon, event bus, global retry manager, GitHub
ruleset, or private launcher adapter work was introduced.

## Completion Criteria

The plan is ready for completion verification when:

1. preflight proves the isolated worktree and branch are based on the recorded
   `origin/main` SHA, with target symbols and allowed write set verified;
2. submission-bound correlation passes fast, stale, fresh, partial, mismatched
   identity, and read-error recovery cases;
3. acquisition, execution, and cleanup have one exception-safe envelope,
   `semantic_outcome` and `finalization_outcome` remain independent, and
   captured results survive cleanup failures;
4. semantic redaction preserves ordinary security prose and removes actual
   secret values without weakening metadata filtering;
5. CoS source truth, generated mirrors, owned resources, authoritative
   cleanup conflicts reconcile through tests and validators;
6. benchmark rows carry machine-readable evidence provenance, counters are
   observed or explicitly unavailable, and incorrect validation rows produce
   nonzero exit status;
7. the disposable live probe meets its bounded acceptance matrix, or the plan
   records `BLOCKED_CAPABILITY` for an unavailable mandatory normal path;
8. all required task and final verification evidence is recorded in this plan,
   with deviations, substitutions, and blocked capabilities explicit;
9. `skill-verification-before-completion` returns `verified` before the plan is
   marked `completed`.

The following are explicitly out of scope: GitHub ruleset administration,
private launcher API decoupling, new orchestration/result/registry/daemon/event
bus/retry layers, new receipt schema, CoS-to-CoS messaging, and 9router
attribution as a normal execution gate.
