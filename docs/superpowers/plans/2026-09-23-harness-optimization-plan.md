---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
targets:
  - scripts/herdr_main_launcher.py
  - scripts/validate_repo_contracts.py
  - scripts/validate_agent_runtime_drift.py
  - scripts/setup_deepagents_runtime.ps1
  - tests/test_herdr_main_launcher.py
  - tests/test_validate_repo_contracts.py
  - tests/test_validate_agent_runtime_drift.py
  - tests/test_setup_deepagents_runtime_contract.py
  - .github/workflows/runtime-contracts.yml
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - .agents/skills/skill-verification-before-completion/SKILL.md
  - docs/operating_system/rules/command-execution-rule.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - README.md
---

# Harness Optimization Plan

## Verdict Review

Direction is correct. Proposal is not execution-ready without these corrections:

- Pane text still changes outcome in `_classify_deepagents_outcome()`; P0 must
  remove that mutation, not only reorder reads.
- `validate_repo_contracts.py --fast` is used by hooks, CoS guidance, tests, and
  adoption docs. Keep flag as compatibility input while removing embedded
  pytest; do not delete it in this change.
- All-platform drift currently launches one deploy check per platform. Replace
  only that path with `deploy_agent_runtime.py --target all --check`; preserve
  explicit single-platform behavior.
- Setup idempotence needs an ownership rule and proof. Managed runtime path is
  authoritative; unrelated `dcode` on `PATH` must not satisfy setup.
- Evidence reuse is operation-scoped. Do not add a readiness registry, test
  cache, or new coordinator. HEAD alone is not a valid evidence key for dirty
  worktrees.
- Performance claims need call-count and focused latency evidence first. Live
  p50/p95 comparison is optional when no repeatable worker fixture exists.

## Goal

Reduce duplicate observation, validation, deployment, and setup work without
weakening lifecycle settlement, cleanup recovery, CoS acceptance, generated
surface consistency, or legacy compatibility.

## Implementation Outcomes

### Receipt-authoritative DeepAgents completion

Structured lifecycle receipts and validated task-result records own execution
and reported task outcome when present. Pane output remains diagnostic or an
explicit legacy fallback. Execution completion never implies engineering
acceptance.

### Non-overlapping validation commands

Repository contract validation checks repository contracts only. Pytest runs
behavioral tests separately. Runtime drift checks adapter synchronization once
and deploy shared assets once for all-platform validation.

### Idempotent managed setup

Setup skips package installation when the managed executable already matches the
requested version, supports explicit forced reinstall, preserves unrelated
configuration, and performs targeted config migration only when requested.

### Evidence-aware operating guidance

CoS consumes launcher technical evidence and retains authorization and
acceptance authority. Completion verification reuses evidence only while its
relevant source, environment, ownership, and worktree inputs remain valid.
Canonical guidance and generated adapters stay synchronized.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-plan-document-reviewer`, `skill-writing-plans`,
  `skill-systematic-debugging`, `skill-test-driven-development`,
  `skill-backend-verification`, `skill-code-standards`,
  `skill-verification-before-completion`
- Isolation: `current workspace` for planning; create a clean implementation
  worktree before execution
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed files, regenerate generated adapters,
  and run listed local checks
- User-approval actions: push, merge, publication, destructive cleanup, or
  discard of preserved unrelated changes
- Parallel ownership: `none`; launcher, validator, setup, and guidance changes
  share contracts and land sequentially
- Sequential fallback: complete Tasks 1–2 before Tasks 3–5; complete Task 6
  only after canonical source edits pass focused checks

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/harness-optimization` (create before activation)
- Base commit: `59b4166`
- Expected workspace: current checkout has preserved unrelated untracked
  artifacts; implementation must not modify or delete them
- Next action: create isolated implementation worktree, then run Task 1
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | fresh worktree | `codex` | none | baseline and contract inventory | 201 passed; HEAD `59b4166` |
| Task 2 | `completed` | fresh worktree | `codex` | Task 1 | launcher regression suite and call-count assertions | 183 passed; py_compile passed |
| Task 3 | `completed` | fresh worktree | `codex` | Task 1 | validator and drift tests | 68 passed |
| Task 4 | `completed` | fresh worktree | `codex` | Task 1 | runtime CI matrix inspection and patcher test inclusion | 157 runtime tests passed; matrix preserved |
| Task 5 | `completed` | fresh worktree | `codex` | Task 1 | Windows setup contract and idempotence proof | 3 setup contract tests passed; PowerShell parse passed |
| Task 6 | `completed` | fresh worktree | `codex` | Tasks 2–5 | adapter sync, drift, repository contracts, full tests | 799 passed, 1 skipped; all validators passed |

## Task Breakdown

### Task 1: Lock current contracts and baseline

**Purpose:** Record current behavior before changing shared runtime authority.

**Files And Symbols:**

- Inspect: `scripts/herdr_main_launcher.py:_classify_deepagents_outcome`
- Inspect: `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`
- Inspect: `scripts/herdr_main_launcher.py:_deepagents_completion_snapshot`
- Inspect: `scripts/validate_repo_contracts.py:build_subprocess_steps`
- Inspect: `scripts/validate_agent_runtime_drift.py:main`
- Inspect: `scripts/setup_deepagents_runtime.ps1`
- Inspect: current launcher, validator, drift, and runtime tests

**Template Profile:**

- Controller-selected: `normal`
- Selection basis: bounded repository-contract inventory and baseline capture.

**Authority:**

- Preauthorized local actions: inspect source, tests, Git state, and run focused baseline checks.
- Stop for: a conflicting current contract not covered by this plan or a required wire-schema change.

**Steps:**

1. Confirm `59b4166` as base and preserve unrelated workspace artifacts.
2. Record current focused test results when environment permits.
3. Inventory all non-historical references to `--fast`, embedded pytest,
   adapter drift commands, and runtime setup commands.
4. Confirm task-result and lifecycle receipt schemas before editing; preserve
   existing receipt fields unless Task 2 proves a compatibility defect.

**Verification:**

- `git status --short`
- `git rev-parse HEAD`
- `py -3 -m pytest -q tests/test_herdr_main_launcher.py tests/test_validate_repo_contracts.py tests/test_validate_agent_runtime_drift.py`

**Exit Criteria:** Current authority, callers, compatibility flags, and baseline
failures are recorded in task evidence.

### Task 2: Make DeepAgents completion receipt-first

**Purpose:** Remove competing completion authorities and unnecessary pane reads.

**Files And Symbols:**

- Modify: `scripts/herdr_main_launcher.py:_classify_deepagents_outcome`
- Modify: `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`
- Modify: `scripts/herdr_main_launcher.py:_deepagents_completion_snapshot`
  only as needed for diagnostic fallback
- Modify: structured DeepAgents dispatch path around `completion_marker` and
  `delivery_task`
- Test: `tests/test_herdr_main_launcher.py`
- Verify: `tests/test_deepagents_result_contract.py`,
  `tests/test_project_os_runtime.py`

**Template Profile:**

- Controller-selected: `high`
- Selection basis: shared lifecycle authority, receipt semantics, and recovery behavior.

**Authority:**

- Preauthorized local actions: edit launcher completion handling and focused regression tests; run declared checks.
- Stop for: new receipt states, changed settlement ownership, or a required change to `scripts/dcode_project.py` wire output.

**Steps:**

1. Treat confirmed lifecycle receipt as authoritative for worker exit,
   descendant retirement, cleanup, and recovery state.
2. Treat validated structured task result as authoritative for reported task
   outcome when present; treat missing result as `unverified`, not success.
3. Ensure pane text cannot turn confirmed execution success into failure because
   of an earlier `ERROR:` or `FAIL` line, and cannot turn pane `COMPLETED` into
   structured success when the task result reports failure.
4. In the structured receipt path, poll the receipt first and skip mandatory
   `pane read`, marker polling, and marker generation after confirmed settlement.
5. Preserve conditional `process-info` checks for missing, malformed, or
   contradictory receipts, unresolved descendants, live workers, and cleanup
   uncertainty.
6. Keep no-receipt invocation as an explicit legacy diagnostic fallback; do not
   let it overwrite receipt-derived outcomes.
7. Preserve `Execution completed` versus `task accepted`; launcher does not
   judge engineering acceptance.

**Required regression cases:**

- structured success without marker
- structured success with earlier `ERROR:` text
- structured failure with `COMPLETED` text
- worker exit `0` with missing task result
- worker exit `0` with incomplete cleanup
- nonzero worker exit
- missing receipt with live worker
- confirmed receipt with pane transport failure
- contradictory structured records
- normal receipt path observation-call count excludes mandatory pane read

**Verification:**

- `py -3 -m pytest -q tests/test_herdr_main_launcher.py tests/test_deepagents_result_contract.py tests/test_project_os_runtime.py`
- `python -m py_compile scripts/herdr_main_launcher.py`

**Exit Criteria:** Identical lifecycle/task-result evidence yields identical
execution and settlement output regardless of irrelevant pane text.

### Task 3: Separate repository contracts from pytest and consolidate drift

**Purpose:** Remove deterministic duplicate test execution while preserving all
behavioral coverage.

**Files And Symbols:**

- Modify: `scripts/validate_repo_contracts.py:build_subprocess_steps`
- Modify: `tests/test_validate_repo_contracts.py`
- Modify: `scripts/validate_agent_runtime_drift.py:main`
- Modify: `tests/test_validate_agent_runtime_drift.py`
- Modify: `README.md`
- Modify affected maintained procedure docs found in Task 1

**Template Profile:**

- Controller-selected: `normal`
- Selection basis: bounded command composition and compatibility migration.

**Authority:**

- Preauthorized local actions: edit validator/drift command composition, compatibility tests, and maintained command documentation.
- Stop for: removal of a public flag or validator behavior without a caller migration and regression proof.

**Steps:**

1. Remove embedded pytest steps from `validate_repo_contracts.py`.
2. Keep `--fast` accepted as a compatibility flag; redefine it as a no-op
   compatibility input or preserve its hook-facing subset meaning without any
   pytest execution. Update help and tests accordingly.
3. Remove now-unused pytest-basetemp orchestration helpers only after caller
   search proves they have no remaining use.
4. For `--all-platforms`, emit one deploy command:
   `deploy_agent_runtime.py --target all --check`.
5. Preserve explicit `--platform` and default single-target behavior.
6. Test command shape and failure propagation; do not weaken deploy checks.
7. Document canonical broad verification as contract validation, then pytest,
   then `git diff --check`; retain focused commands for debugging.

**Verification:**

- `py -3 -m pytest -q tests/test_validate_repo_contracts.py tests/test_validate_agent_runtime_drift.py tests/test_deploy_agent_runtime.py`
- Assert no repository-contract command includes pytest.
- Assert all-platform drift emits one all-target deploy check.
- Assert explicit single-platform selection remains unchanged.

**Exit Criteria:** Contract validation and pytest have one owner each, and
all-platform drift preserves findings while scanning shared content once.

### Task 4: Close runtime CI patcher coverage

**Purpose:** Make the DeepAgents patch boundary changed by `59b4166` part of
the maintained runtime matrix.

**Files And Symbols:**

- Modify: `.github/workflows/runtime-contracts.yml`
- Verify: `tests/test_deepagents_runtime_patch.py`

**Template Profile:**

- Controller-selected: `low`
- Selection basis: isolated CI test-list change with existing coverage.

**Authority:**

- Preauthorized local actions: update existing runtime workflow test selection; run local equivalent tests.
- Stop for: a new workflow, new OS matrix, or dependency installation change.

**Steps:**

1. Add `tests/test_deepagents_runtime_patch.py` to the existing runtime pytest
   command.
2. Preserve Ubuntu and Windows matrix coverage.
3. Keep patcher tests in the existing runtime job; do not create a second CI
   workflow.

**Verification:**

- `py -3 -m pytest -q tests/test_deepagents_runtime_patch.py tests/test_dcode_project.py tests/test_project_os_runtime.py`
- Inspect workflow YAML for both matrix entries and patcher test path.

**Exit Criteria:** Runtime CI exercises the patcher on both existing matrix OSes.

### Task 5: Make managed DeepAgents setup idempotent

**Purpose:** Avoid reinstalling an unchanged managed runtime and prevent PATH
   ambiguity while preserving explicit repair and migration behavior.

**Files And Symbols:**

- Modify: `scripts/setup_deepagents_runtime.ps1`
- Add: `tests/test_setup_deepagents_runtime_contract.py`
- Update setup references in `README.md` if command behavior changes

**Template Profile:**

- Controller-selected: `high`
- Selection basis: cross-platform setup, installation ownership, config migration, and idempotence proof.

**Authority:**

- Preauthorized local actions: edit setup script, add no-dependency contract tests, and run disposable Windows checks.
- Stop for: changing secret values, reading credentials, deleting existing user config, or relying on an unrelated PATH executable.

**Steps:**

1. Add `-ForceReinstall`; retain `-SkipInstall` and `-ResetConfig` for
   compatibility.
2. Treat `$runtimeRoot\bin\dcode.exe` as managed authority. If it exists and
   reports the requested version, skip install unless `-ForceReinstall` is set.
3. Install only when managed executable is absent, version-mismatched, or
   forced. With `-SkipInstall`, fail rather than falling back to arbitrary
   `dcode` on `PATH`.
4. Keep patch application idempotent and verify version after patching.
5. Add explicit `-MigrateConfig` for targeted updates to owned `[paths]` keys;
   preserve unrelated TOML sections and keys. Keep full rewrite behind
   `-ResetConfig` only.
6. Report whether install, patch, config migration, or wrapper refresh changed
   state.
7. Test important failure paths: missing managed executable with
   `-SkipInstall`, version mismatch, forced reinstall, unrelated PATH binary,
   config migration preserving unrelated content, and repeated setup.

**Verification:**

- `py -3 -m pytest -q tests/test_setup_deepagents_runtime_contract.py`
- Disposable Windows PowerShell smoke: first setup, repeated setup, forced
  reinstall, targeted migration, and missing-managed-runtime failure.

**Exit Criteria:** Repeated setup performs no package reinstall when managed
runtime and config are unchanged, and setup never accepts unrelated PATH state.

### Task 6: Align CoS, verification guidance, docs, and generated adapters

**Purpose:** Make evidence ownership and reuse rules executable in maintained
guidance without creating a second authority.

**Files And Symbols:**

- Modify: `.agents/skills/skill-chief-of-staff/SKILL.md`
- Modify: `.agents/skills/skill-verification-before-completion/SKILL.md`
- Modify: `docs/operating_system/rules/command-execution-rule.md`
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Modify: `README.md`
- Regenerate: `generated_agents/` through `scripts/sync_agent_adapters.py`

**Template Profile:**

- Controller-selected: `normal`
- Selection basis: canonical guidance migration and generated-surface synchronization.

**Authority:**

- Preauthorized local actions: edit canonical guidance, update maintained command references, regenerate adapters, and run drift checks.
- Stop for: direct edits to generated adapters or creation of a persistent evidence/readiness registry.

**Steps:**

1. State that Herdr owns delivery and diagnostic observation, `dcode-project`
   owns worker lifecycle and receipts, and CoS owns authorization, acceptance,
   reconciliation, and continuation.
2. Tell CoS to compare launcher evidence with the approved task contract rather
   than rediscovering executable, profile, Git, or pane facts already proven by
   the active launch operation.
3. Require fresh checks for mutable worktree, branch, lane ownership, and
   acceptance state.
4. Permit operation-scoped evidence reuse only when command, relevant changed
   files, environment/config, worktree identity, and ownership inputs remain
   valid. Never key validity on HEAD alone.
5. Update canonical command sequences and preserve `--fast` compatibility
   references until a later removal plan proves all callers migrated.
6. Run adapter generation from canonical sources; never hand-edit generated
   outputs.

**Verification:**

- `py -3 scripts/sync_agent_adapters.py --all-platforms`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- `rg -n "embedded pytest|readiness registry|completion marker" .agents/skills docs/operating_system README.md --glob '*.md'`

**Exit Criteria:** Canonical guidance, maintained docs, and generated adapters
agree on authority, command ownership, and evidence freshness.

## Verification

### Focused proof

- Run each task-local command after its task changes.
- Confirm receipt authority, missing-result behavior, cleanup uncertainty, and
  observation-call counts through launcher tests.
- Confirm validator command composition and drift target selection through unit
  tests.
- Confirm runtime CI includes patcher tests in both existing OS matrix jobs.
- Confirm setup idempotence and migration behavior through contract tests and
  disposable Windows PowerShell smoke.

### Broad proof

- Run repository contract validation after canonical docs, scripts, or planning
  surfaces change.
- Regenerate and check all adapters after canonical skill or rule changes.
- Run full pytest and `git diff --check` before completion.
- Inspect final Git state for unrelated changes, stale paths, generated drift,
  temporary files, and preserved untracked artifacts.

## Completion Criteria

- Structured receipt evidence wins over pane text for managed DeepAgents runs.
- Missing task-result evidence remains unverified; no false success is created.
- Cleanup and descendant uncertainty remain reconciliation-required.
- `validate_repo_contracts.py` no longer runs pytest internally.
- `--fast` callers remain valid during this change.
- All-platform drift uses one all-target deploy check; explicit target behavior
  remains intact.
- Runtime CI includes patcher tests on existing Ubuntu and Windows jobs.
- Managed setup is idempotent, explicit about reinstall and migration, and
  rejects unrelated PATH executables.
- CoS retains acceptance authority; launcher and worker evidence are reused,
  not duplicated or promoted into acceptance.
- Canonical sources and generated adapters are synchronized.
- Required focused checks, runtime matrix tests, repository contracts, full
  pytest, and `git diff --check` pass in final verification.
- No unrelated untracked artifacts are changed or deleted.

## Final Verification

Run after all tasks:

```powershell
py -3 -m pytest -q tests/test_herdr_main_launcher.py tests/test_deepagents_result_contract.py tests/test_project_os_runtime.py tests/test_validate_repo_contracts.py tests/test_validate_agent_runtime_drift.py tests/test_deploy_agent_runtime.py tests/test_deepagents_runtime_patch.py tests/test_dcode_project.py tests/test_setup_deepagents_runtime_contract.py
py -3 scripts/validate_repo_contracts.py --repo-root .
py -3 scripts/sync_agent_adapters.py --all-platforms --check
py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check
py -3 -m pytest -q
git diff --check
git status --short
```

Do not claim performance improvement from source inspection alone. Record
focused mocked Herdr call counts and setup command counts. Add live p50/p95
comparison only when repeatable worker runs and identical environment are
available.
