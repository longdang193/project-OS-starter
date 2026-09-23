---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: next-harness-optimization
targets:
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_main_launcher.py
  - tests/test_deepagents_result_contract.py
  - tests/test_dcode_project.py
  - tests/test_validate_repo_contracts.py
  - tests/test_validate_agent_runtime_drift.py
  - tests/test_setup_deepagents_runtime_contract.py
  - .github/workflows/repo-contracts.yml
  - .github/workflows/runtime-contracts.yml
  - scripts/setup_deepagents_runtime.ps1
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - README.md
---

# Next Harness Optimization Plan

## Review Verdict

The supplied consolidated verdict is substantially correct and points to one
bounded convergence pass, not a new architecture. Source review against
`origin/main` at `b980c6b` confirms:

- `_deepagents_completion_evidence()` returns pane-derived evidence after a
  receipt arrives during polling or receipt grace, instead of routing every
  confirmed receipt through one normalized observation.
- The managed pane path calculates `task_verified`, `completed`, execution,
  task-result, cleanup, failure, exit, and reconciliation values before
  `emit_assignment()` runs the canonical structured classifier.
- A confirmed receipt without confirmed structured task-result evidence can
  still be converted into pane-derived `reported_completed` evidence when the
  delayed-receipt branch returns its earlier snapshot.
- Removing embedded pytest left four validator regression modules without an
  explicit workflow owner: `test_manage_switchyard_runtime.py`,
  `test_validate_repo_config.py`, `test_validate_planning_lifecycle.py`, and
  `test_validate_repo_contracts.py`.
- `test_validate_agent_runtime_drift.py` and
  `test_setup_deepagents_runtime_contract.py` were not in the previous workflow
  test lists; add them as new explicit coverage, not restored coverage.
- `_executable()` resolves `dcode-project` through arbitrary `PATH`, while
  setup defines a user-local managed wrapper location. DeepAgents needs a
  dedicated managed-path resolver without changing Codex or Herdr resolution.
- Setup output reports `$binRoot\dcode.exe` although validation uses
  `$managedDcodePath`; wrapper and configuration writes are unconditional.
- Runtime guidance still describes pane observation as the normal DeepAgents
  completion path and needs ownership-aligned wording.

Review disposition: implementation-ready after these corrections are included
in task scope. Preserve receipt schema, CoS acceptance authority, legacy
fallback behavior, validator independence from pytest, generated adapter
ownership, and all unrelated user files.

## Goal

Converge managed DeepAgents execution and verification around one authoritative
completion protocol:

```text
Lifecycle receipt      owns worker execution and settlement facts
Structured task result owns reported task outcome
Pane observation       supplies diagnostics and legacy fallback evidence
CoS                    owns engineering acceptance
```

Restore explicit CI ownership for validator regressions, add portable setup
contract coverage, remove unmanaged DeepAgents executable selection, correct
setup diagnostics and idempotence, and align canonical runtime guidance.

## Implementation Outcomes

### Receipt-authoritative managed completion

Confirmed lifecycle receipts use one normalized observation path. Managed
classification never promotes pane text to task success when structured task
result evidence is absent.

### Explicit regression ownership

Repository and runtime workflows explicitly execute validator, drift, setup,
and lifecycle regression modules. `validate_repo_contracts.py` remains a state
validator and does not invoke pytest.

### Managed runtime and setup convergence

DeepAgents dispatch uses the setup-owned user-local wrapper, fails closed when
that wrapper is absent, reports actual managed paths, and avoids unchanged
artifact writes.

### Canonical guidance

Runtime surfaces, tool-resolution guidance, adapter procedure, and README
verification commands describe one ownership model and one non-duplicated
verification sequence.

## Non-goals

- No new lifecycle coordinator.
- No persistent verification cache or readiness registry.
- No new result schema, verification CLI, or CI workflow.
- No broad rewrite of completed plans.
- No changes to Codex executable resolution, Tura delegation, Herdr target
  resolution, or CoS acceptance semantics.
- No real package installation, provider authentication, MCP calls, or user
  runtime mutation in tests.

## Invariants

- Every confirmed lifecycle receipt produces equivalent final observation facts
  regardless of arrival timing.
- Managed success does not require `pane read` or `wait-output` after receipt
  confirmation.
- Missing or invalid structured task-result evidence remains `unverified`; pane
  text cannot promote it to task success on managed runs.
- Cleanup or descendant uncertainty keeps reconciliation required.
- Legacy runs without the structured receipt contract retain bounded fallback
  behavior and explicit non-authoritative diagnostics.
- Repository validation checks repository state; pytest workflows test validator
  implementations. Neither command owns the other.
- Canonical sources change before generated outputs. Generated adapter output is
  refreshed only through `scripts/sync_agent_adapters.py`.
- Existing unrelated tracked and untracked workspace state remains untouched.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-plan-document-reviewer`, `skill-code-standards`,
  `skill-test-driven-development`, `skill-backend-verification`,
  `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: create a clean implementation worktree from `origin/main` before
  execution; current checkout contains unrelated untracked files
- Commit policy: no commits during execution
- User-approval actions: commit, push, merge, destructive cleanup, provider
  authentication, real runtime installation, and discard of preserved files
- Parallel ownership: none; launcher, CI, setup, tests, and guidance share one
  authority contract
- Order: baseline → lifecycle convergence → CI/setup coverage → managed runtime
  boundary → guidance → full verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/next-optimization` (create before execution)
- Base commit: `b980c6b50ada54463ab1fbf5409d82d35621057e`
- Expected workspace: preserve current untracked files and do not edit them
- Next action: none; implementation and verification complete
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | fresh worktree | `codex` | none | baseline and ownership map | baseline focused suite: 348 passed; source/workflow inventory complete |
| Task 2 | `completed` | fresh worktree | `codex` | Task 1 | receipt timing and classifier regressions | focused launcher/result suite: 176 passed |
| Task 3 | `completed` | fresh worktree | `codex` | Task 1 | explicit CI coverage and portable setup tests | workflow ownership added; validator/drift/setup suite: 39 passed |
| Task 4 | `completed` | fresh worktree | `codex` | Tasks 1, 3 | managed executable and setup idempotence tests | launcher/dcode/setup suite: 312 passed; managed-path and write-if-changed coverage |
| Task 5 | `completed` | fresh worktree | `codex` | Tasks 2–4 | canonical guidance and verification composition | runtime docs, README, and workflow ownership aligned; validator passed |
| Task 6 | `completed` | fresh worktree | `codex` | Task 5 | focused, CI-equivalent, broad, generated, and Git proof | focused 356 passed; full 804 passed, 1 skipped; validator, adapter, kit, diff checks passed |

## Task Breakdown

### Task 1: Establish baseline and exact ownership

**Purpose:** Confirm current source, tests, workflow ownership, and preserved
workspace state before editing shared runtime code.

**Files And Symbols:**

- Inspect `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`.
- Inspect `scripts/herdr_main_launcher.py:_classify_deepagents_outcome`.
- Inspect managed dispatch around `completion_marker` and `emit_assignment`.
- Inspect `scripts/validate_repo_contracts.py:build_subprocess_steps`.
- Inspect both workflow files and all named test modules.
- Inspect `scripts/setup_deepagents_runtime.ps1` and runtime guidance files.

**Template Profile:**

- Controller-selected: `normal`
- Selection basis: bounded source, workflow, and workspace inventory.

**Authority:**

- Preauthorized local actions: inspect source, tests, Git state, and run the
  declared baseline suite.
- Stop for: a conflicting current contract, missing source owner, or baseline
  failure that prevents trustworthy comparison.

**Steps:**

1. Confirm `origin/main` resolves to `b980c6b50ada54463ab1fbf5409d82d35621057e`.
2. Record `git status --short`, `git worktree list`, and existing untracked
   files without modifying them.
3. Run the focused baseline suite:

   ```powershell
   py -3 -m pytest -q tests/test_herdr_main_launcher.py tests/test_deepagents_result_contract.py tests/test_dcode_project.py tests/test_validate_repo_contracts.py tests/test_validate_agent_runtime_drift.py
   ```

4. Record which four validator modules were formerly embedded in the validator
   and which two modules are new explicit CI coverage.
5. Record the managed wrapper paths emitted by setup on Windows and the
   corresponding user-local path expected on POSIX.

**Exit Criteria:** Baseline result, source owners, workflow gaps, and preserved
workspace state are recorded in task evidence.

### Task 2: Normalize receipt-authoritative completion

**Purpose:** Make every confirmed receipt produce one equivalent observation
and prevent pane evidence from replacing missing structured task results.

**Files And Symbols:**

- Modify `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`.
- Add a private normalization helper beside the completion helpers, reusing
  existing observation keys and receipt fields.
- Modify `scripts/herdr_main_launcher.py:_classify_deepagents_outcome` only
  where required to consume normalized receipt evidence.
- Modify `tests/test_herdr_main_launcher.py`.
- Extend `tests/test_deepagents_result_contract.py` only when receipt/result
  correlation proof belongs there.

**Template Profile:**

- Controller-selected: `high`
- Selection basis: shared lifecycle classification, timing-sensitive evidence,
  and managed/legacy authority boundaries.

**Authority:**

- Preauthorized local actions: edit launcher and focused tests; run declared
  focused checks with fixture-only subprocesses.
- Stop for: receipt schema incompatibility, settlement ambiguity, or a required
  change to CoS acceptance authority.

**Steps:**

1. Add one helper that maps a validated confirmed receipt to the existing
   observation shape with `receipt_authoritative: True`, lifecycle receipt,
   receipt-derived state, no pane report, and optional diagnostic snapshot.
2. Route the initial receipt branch, post-snapshot receipt branch, terminal
   wait branch, and deadline grace branch through that helper.
3. Stop pane reads and `wait-output` after confirmed receipt detection; retain
   pane reads only before receipt confirmation or on legacy fallback paths.
4. Keep prior pane evidence under diagnostic metadata only; never use it to
   set managed task-result state.
5. Add tests for immediate, polling-delayed, terminal-grace, and deadline-grace
   receipt arrival. Assert normalized state and authoritative fields match.
6. Add a regression test that passes the actual confirmed task-result evidence
   into `_classify_deepagents_outcome()` and proves a completed worker does not
   receive `completion_evidence_missing` when task-result evidence is confirmed.
7. Add a missing-task-result test proving managed classification remains
   `unverified`, non-zero, and reconciliation-required even when pane text says
   `COMPLETED`.
8. Assert no `pane read` or `wait-output` command occurs after a confirmed
   receipt in the managed success path.

**Verification:**

```powershell
py -3 -m pytest -q tests/test_herdr_main_launcher.py tests/test_deepagents_result_contract.py
```

**Exit Criteria:** Receipt arrival timing cannot change managed observation or
task-result authority, and legacy fallback remains explicitly diagnostic.

### Task 3: Restore and expand explicit CI test ownership

**Purpose:** Close the validator pytest coverage gap without returning pytest
execution to `validate_repo_contracts.py`.

**Files And Symbols:**

- Modify `.github/workflows/repo-contracts.yml`.
- Modify `.github/workflows/runtime-contracts.yml`.
- Modify `tests/test_setup_deepagents_runtime_contract.py`.
- Modify `tests/test_validate_repo_contracts.py` only for coverage-contract tests.
- Modify `tests/test_validate_agent_runtime_drift.py` only for missing CI cases.

**Template Profile:**

- Controller-selected: `normal`
- Selection basis: bounded workflow and regression-test ownership changes.

**Authority:**

- Preauthorized local actions: edit workflow YAML and named tests; run local
  pytest collection and focused suites.
- Stop for: a required new workflow, unavailable Windows proof, or a change to
  repository validator ownership.

**Steps:**

1. Add one named repository-workflow step running these five modules:

   ```text
   tests/test_manage_switchyard_runtime.py
   tests/test_validate_repo_config.py
   tests/test_validate_planning_lifecycle.py
   tests/test_validate_repo_contracts.py
   tests/test_validate_agent_runtime_drift.py
   ```

   The first four restore coverage previously supplied by the validator; the
   fifth adds explicit drift-test coverage.
2. Add `tests/test_setup_deepagents_runtime_contract.py` to the existing runtime
   matrix. Do not create another workflow.
3. Keep portable setup source-contract tests runnable on Ubuntu and Windows.
4. Guard the Windows PowerShell parser test with an in-test executable check
   using `shutil.which("pwsh") or shutil.which("powershell")`; skip only that
   test when neither executable exists.
5. Add Windows-only setup behavior tests using temporary directories and fake
   commands. Cover managed runtime reuse, forced reinstall, config migration,
   and repeated setup output stability without reading credentials or running a
   real installer.
6. Keep `validate_repo_contracts.py` free of pytest subprocess construction and
   preserve `--fast` behavior.

**Verification:**

```powershell
py -3 -m pytest -q tests/test_validate_repo_contracts.py tests/test_validate_agent_runtime_drift.py tests/test_setup_deepagents_runtime_contract.py
```

**Exit Criteria:** CI owns every restored and new regression module, Linux can
collect the setup module, Windows exercises setup behavior, and repository
validation remains independent of pytest.

### Task 4: Enforce managed DeepAgents runtime ownership

**Purpose:** Prevent DeepAgents dispatch from selecting an unrelated executable
from `PATH` while preserving existing Codex and Herdr executable lookup.

**Files And Symbols:**

- Modify `scripts/herdr_main_launcher.py:_executable` callers for
  `executor == "deepagents"`.
- Add one private managed DeepAgents wrapper resolver beside `_executable`.
- Modify `tests/test_herdr_main_launcher.py`.
- Modify `tests/test_dcode_project.py`.
- Modify `scripts/setup_deepagents_runtime.ps1`.

**Template Profile:**

- Controller-selected: `high`
- Selection basis: cross-platform executable resolution, PowerShell setup, and
  runtime-boundary failure behavior.

**Authority:**

- Preauthorized local actions: edit launcher, setup script, and named tests;
  use disposable fake runtime fixtures only.
- Stop for: a path contract that differs between setup and launcher, a need for
  real runtime installation, or destructive changes under the user home.

**Steps:**

1. Define the managed wrapper contract from setup-owned paths:
   `Path.home() / ".local" / "bin" / "dcode-project"` on POSIX and
   `Path.home() / ".local" / "bin" / "dcode-project.cmd"` on Windows.
2. Resolve DeepAgents only through that managed path and fail closed with a
   setup-directed error when it is absent. Do not call `shutil.which` for
   DeepAgents after this change. Keep `_executable("herdr")` and
   `_executable("codex")` unchanged.
3. Test managed-path selection, missing managed runtime, and a conflicting
   `PATH` executable. The conflicting executable must never be selected.
4. Correct setup output to report `$managedDcodePath`, while separately
   reporting the wrapper path where `dcode-project` is installed.
5. Add a small PowerShell write-if-changed helper and route config plus wrapper
   writes through it. Preserve existing encodings and file contents.
6. Extend setup tests to prove repeated setup does not rewrite unchanged
   configuration or wrappers and forced reinstall still performs installation.

**Verification:**

```powershell
py -3 -m pytest -q tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_setup_deepagents_runtime_contract.py
```

**Exit Criteria:** Managed DeepAgents dispatch has one runtime authority,
diagnostics name actual managed paths, and repeated setup is byte-stable.

### Task 5: Align canonical guidance and verification composition

**Purpose:** Make documentation and command ownership describe the implemented
runtime protocol without duplicating competing procedures.

**Files And Symbols:**

- Modify `docs/operating_system/runtime/runtime-surfaces.md`.
- Modify `docs/operating_system/tooling/runtime-tool-resolution.md`.
- Modify `docs/operating_system/procedures/runtime-adapter-procedure.md`.
- Modify `README.md` only where verification command ownership is documented.
- Regenerate adapter outputs only when canonical `.agents/skills` sources change.

**Template Profile:**

- Controller-selected: `normal`
- Selection basis: bounded canonical documentation and command-ownership
  reconciliation.

**Authority:**

- Preauthorized local actions: edit named canonical docs and run declared
  validators and adapter checks.
- Stop for: a generated-source ownership conflict or documentation contract
  that contradicts executable behavior.

**Steps:**

1. Describe structured receipt observation as the normal DeepAgents completion
   path. Describe pane observation as pre-receipt diagnostics and legacy
   fallback only.
2. State that lifecycle receipt owns execution and settlement, structured task
   result owns reported task outcome, pane text is non-authoritative, and CoS
   owns acceptance.
3. Document the managed `dcode-project` wrapper path and fail-closed behavior;
   remove wording that permits arbitrary executable fallback.
4. Define one verification sequence:
   repository validation runs once; its owned drift step runs once; explicit
   pytest steps run regression modules; adapter generation runs only after
   canonical adapter-source edits; the adapter check is not repeated unchanged.
5. Remove stale mandatory pane-observation commands while retaining commands
   required for legacy fallback diagnostics.

**Verification:**

```powershell
py -3 scripts/validate_repo_contracts.py
py -3 scripts/sync_agent_adapters.py --all-platforms --check
```

**Exit Criteria:** Guidance, validator ownership, runtime paths, and adapter
surfaces have one consistent source of truth.

### Task 6: Final verification and handoff

**Purpose:** Prove implementation outcomes, cross-platform workflow ownership,
generated consistency, and preserved workspace state.

**Template Profile:**

- Controller-selected: `high`
- Selection basis: final cross-platform, generated-surface, and Git-state proof.

**Authority:**

- Preauthorized local actions: run declared tests, validators, kit generation,
  adapter checks, and Git inspection.
- Stop for: any failed required proof, unexpected changed file, or unresolved
  preserved-workspace conflict.

**Steps:**

1. Run focused tests:

   ```powershell
   py -3 -m pytest -q tests/test_herdr_main_launcher.py tests/test_deepagents_result_contract.py tests/test_dcode_project.py tests/test_validate_repo_contracts.py tests/test_validate_agent_runtime_drift.py tests/test_setup_deepagents_runtime_contract.py
   ```

2. Run the full suite:

   ```powershell
   py -3 -m pytest -q
   ```

3. Run repository validation once:

   ```powershell
   py -3 scripts/validate_repo_contracts.py
   ```

4. Check adapter drift once when canonical adapter sources changed:

   ```powershell
   py -3 scripts/sync_agent_adapters.py --all-platforms --check
   ```

5. Build and validate a disposable starter kit outside tracked source:

   ```powershell
   $kitParent = Join-Path $env:TEMP "project-os-starter-next-optimization-kit"
   py -3 scripts/build_starter_kit.py --output-root $kitParent
   py -3 scripts/validate_starter_kit.py --kit-root (Join-Path $kitParent "project-OS-starter-kit")
   ```

6. Run `git diff --check` and inspect staged, unstaged, and untracked state.
   Preserve unrelated files and generated disposable output ownership.
7. Reconcile plan task evidence, branch, base, `HEAD`, worktree, and proof.

**Required Final Evidence:**

- Focused and full pytest results.
- Repository validation result.
- Adapter drift result.
- Starter-kit build and validation result.
- `git diff --check` result.
- CI-equivalent Ubuntu and Windows workflow results.
- Exact final Git state with unrelated files preserved.

## Verification

Required command composition:

```powershell
py -3 -m pytest -q tests/test_herdr_main_launcher.py tests/test_deepagents_result_contract.py tests/test_dcode_project.py tests/test_validate_repo_contracts.py tests/test_validate_agent_runtime_drift.py tests/test_setup_deepagents_runtime_contract.py
py -3 -m pytest -q
py -3 scripts/validate_repo_contracts.py
py -3 scripts/sync_agent_adapters.py --all-platforms --check
$kitParent = Join-Path $env:TEMP "project-os-starter-next-optimization-kit"
py -3 scripts/build_starter_kit.py --output-root $kitParent
py -3 scripts/validate_starter_kit.py --kit-root (Join-Path $kitParent "project-OS-starter-kit")
git diff --check
git status --short
```

CI proof must show the repository-contract workflow and both runtime matrix
jobs passed on Ubuntu and Windows.

## Acceptance Criteria

- Confirmed receipts produce timing-independent authoritative observations.
- Managed successful execution requires no post-receipt pane read or
  `wait-output`.
- Missing structured task results cannot become managed success through pane
  text.
- Cleanup and descendant uncertainty still require reconciliation.
- Four previously embedded validator test modules have explicit CI ownership.
- Drift and setup contract tests have explicit CI ownership.
- Setup tests collect on Ubuntu and exercise PowerShell behavior on Windows.
- DeepAgents cannot silently select an unrelated `PATH` executable.
- Setup reports actual managed installation paths and avoids unchanged writes.
- Canonical runtime guidance and verification commands match implementation.
- No new workflow, schema, registry, cache, or coordinator exists.
- Full proof passes with unrelated workspace files preserved.

## Completion Criteria

- All six task-local exit criteria are proven with fresh command output.
- Required focused and broad checks pass on the implementation worktree.
- Repository validator, adapter generation/check, and starter-kit validation
  report success without duplicate ownership claims.
- Generated surfaces match canonical inputs.
- No required task, blocker, failed proof, stale plan state, or unexpected
  in-scope change remains.
- Branch, base commit, `HEAD`, worktree, staged state, unstaged state, and
  untracked state reconcile with the plan and preserved-workspace contract.

## Deliberate Deferrals

- No live DeepAgents installation or provider-backed runtime probe in CI; tests
  use disposable fixtures and fake commands.
- No migration of historical plan artifacts; only current canonical guidance
  changes.
- No performance benchmark until receipt classification and CI ownership are
  stable; timing claims remain unmeasured.

## Self-Review

- Every P0/P1 finding maps to Tasks 2–4 and has named regression proof.
- The CI coverage correction distinguishes restored modules from new coverage.
- Managed runtime path policy is explicit for POSIX and Windows.
- Canonical sources precede generated outputs; no generated file is edited by
  hand.
- No placeholder paths, unnamed owners, speculative infrastructure, or
  unresolved task dependencies remain.
- Final verification proves runtime, CI, starter-kit, adapter, and Git outcomes.
