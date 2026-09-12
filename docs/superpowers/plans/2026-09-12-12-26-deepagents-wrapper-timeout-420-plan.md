---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: deepagents-wrapper-timeout-420
targets:
  - scripts/dcode_project.py
  - tests/test_dcode_project.py
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
---

# DeepAgents Wrapper Timeout 420s

## Goal

Bound DeepAgents launches at `420` seconds when callers omit `--timeout`, while preserving explicit timeout overrides, existing process-tree cleanup, existing `--max-turns`, and explicit timeout failure reporting.

## Implementation Outcomes

### Finite default lifecycle bound

Canonical `scripts/dcode_project.py` applies one `_DEEPAGENTS_DEFAULT_TIMEOUT = 420.0` value at both DeepAgents launch branches. Omitted `--timeout` reaches `_run_bounded_worker()` as `420.0`; explicit `--timeout N` remains authoritative. The deployed `~/.agents/project-os` copy is verified as derived output.

### Regression and contract proof

`tests/test_dcode_project.py` proves the `420.0` default, explicit override precedence, normal worker completion, and timeout cleanup/error facts. Operating-system documentation distinguishes the wrapper safety ceiling from CoS runtime grants and Herdr's outer watchdog.

### Shared runtime alignment

Marker-owned `~/.agents/project-os` scripts mirror canonical repository scripts after deployment. No TokenPilot adapter, shell allow-list, retry policy, heartbeat, lease store, scheduler, or new lifecycle state machine changes.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-code-standards`, `skill-backend-verification`, `skill-verification-before-completion`, `skill-executing-plans`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed canonical files, run focused tests and validators, and use the existing deployment command for marker-owned shared runtime assets
- User-approval actions: push, merge, publication, destructive recovery, unrelated cleanup, and deployment collision resolution
- Parallel ownership: `none`
- Sequential fallback: complete Tasks 1 and 2 before Task 3 deployment and final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `e22f3e48ca932bb48487f41d8fa9e842a7e7bc63`
- Expected workspace: `main` with preserved untracked `.playwright-mcp/` and `db/` directories
- Next action: `implementation and verification complete; branch disposition remains user-controlled`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | canonical compile and diff check | `py -3 -m compileall -q scripts/dcode_project.py`; `119 passed` |
| Task 2 | `completed` | current | `codex` | Task 1 | stale-contract search and diff check | stale unset claim absent; `420`/`1800` wording aligned |
| Task 3 | `completed` | current | `codex` | Tasks 1-2 | deployment drift check and focused lifecycle tests | dry-run, deploy/check, `245 passed`, validators passed; normalized shared content matches; deployment normalizes line endings |

## Task Breakdown

### Task 1: Set canonical 420-second default

**Purpose:**
- Close indefinite DeepAgents wrapper waits without changing explicit timeout behavior or cleanup code.

**Task Function:**
- Apply bounded lifecycle default at shared launcher boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: single-file, low-ambiguity, shared lifecycle boundary; delegation adds no benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused tests and final verification provide independent proof.

**Specification Coverage:**
- Approved `420s` default; explicit `--timeout` override; existing process-tree cleanup and timeout status remain unchanged.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_worker_timeout`, `scripts/dcode_project.py:_run_bounded_worker`, `scripts/dcode_project.py:main`
- Modify: `scripts/dcode_project.py:_DEEPAGENTS_DEFAULT_TIMEOUT`, both DeepAgents `_worker_timeout()` call sites
- Modify: `tests/test_dcode_project.py:test_worker_timeout_defaults_are_executor_specific` and one focused omitted-timeout call-site test
- Verify: `scripts/dcode_project.py`, `tests/test_dcode_project.py`

**Dependencies:**
- Current `main` at `e22f3e48ca932bb48487f41d8fa9e842a7e7bc63`; approved verdict and `420s` adjustment.

**Authority:**
- Preauthorized local actions: modify only listed source/test symbols and run compile or diff checks.
- Stop for: changed source ownership, required behavior beyond `420s`, or unrelated working-tree edits.

**Steps:**
- [x] Step 1: Add `_DEEPAGENTS_DEFAULT_TIMEOUT = 420.0` beside launcher constants.
- [x] Step 2: Pass that constant as `default` in both DeepAgents `_worker_timeout()` calls; leave `_worker_timeout()` parsing and `_run_bounded_worker()` cleanup unchanged.
- [x] Step 3: Update default expectation to `420.0`, retain explicit `--timeout=600` coverage, and add parametrized or two-case assertions that omitted timeout reaches DeepAgents worker boundary as `420.0` for both the `--no-mcp` and selected-MCP branches.

**Verification:**
- [x] `py -3 -m compileall -q scripts/dcode_project.py`
- Expected: command exits `0`.
- [x] `git diff --check`
- Expected: no whitespace errors; only declared source and test changes appear.

**Exit Criteria:**
- Canonical launcher has one `420.0` default used by both DeepAgents branches, explicit overrides remain intact, and tests encode the new contract.

### Task 2: Align timeout documentation

**Purpose:**
- Remove stale documentation that says the DeepAgents wrapper timeout is unset.

**Task Function:**
- Reconcile launcher lifecycle documentation with executable behavior.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one maintained documentation file and one narrow contract update.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: targeted text checks plus final repository validators.

**Specification Coverage:**
- Document `420s` as direct-wrapper safety ceiling, preserve `native` CoS grant terminology, and retain Herdr's `1800s` grant/watchdog limit.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `docs/operating_system/procedures/personal-local-worktree-procedure.md` DeepAgents timeout paragraphs
- Modify: `docs/operating_system/procedures/personal-local-worktree-procedure.md` timeout contract wording only
- Verify: same file and repository contract validators

**Dependencies:**
- Task 1 establishes executable `420s` behavior.

**Authority:**
- Preauthorized local actions: modify only the named timeout paragraphs in the maintained procedure document.
- Stop for: documentation changes requiring Herdr grant semantics, new policy, or unrelated procedure edits.

**Steps:**
- [x] Step 1: Replace “wrapper timeout unset” wording with `420s` wrapper safety-ceiling wording.
- [x] Step 2: State that direct `dcode-project` accepts any positive explicit `--timeout N`; Herdr-mediated grants project `--timeout N`, reject `N > 1800`, and retain the `1800s` outer watchdog.
- [x] Step 3: Preserve distinction between CoS runtime grant value `native` and launcher safety deadline.

**Verification:**
- [x] Search `personal-local-worktree-procedure.md` for `wrapper timeout unset` and `420`.
- Expected: stale unset claim absent; `420` wrapper ceiling documented; `native` and `1800` semantics remain present.
- [x] `git diff --check`
- Expected: no whitespace errors.

**Exit Criteria:**
- Documentation states current behavior without redefining CoS grants or Herdr watchdog policy.

### Task 3: Deploy shared runtime and verify lifecycle contract

**Purpose:**
- Propagate canonical scripts to marker-owned shared runtime and prove source, deployed runtime, cleanup, and failure behavior.

**Task Function:**
- Execute controlled shared-runtime deployment and acceptance verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deployment, Git, and acceptance authority remain with controller.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: fresh automated tests and drift validators are sufficient for this bounded change.

**Specification Coverage:**
- Shared runtime mirrors canonical source; success path exits normally; timeout path raises explicit lifecycle error after process-tree cleanup; no unrelated capability expansion occurs.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/deploy_agent_runtime.py:run`, `scripts/dcode_project.py:_run_bounded_worker`, `tests/test_dcode_project.py` timeout and cleanup tests
- Modify: `~/.agents/project-os/scripts/dcode_project.py` only through deployment command
- Verify: `~/.agents/project-os/scripts/dcode_project.py`, deployment markers, focused test suite, validators

**Dependencies:**
- Tasks 1 and 2 complete; no deployment before canonical source and docs are ready.

**Authority:**
- Preauthorized local actions: run `py -3 scripts/deploy_agent_runtime.py --target codex` and declared local verification commands against marker-owned assets.
- Stop for: unowned shared-asset collision, deployment failure, failed required test, or any request to discard unrelated `.playwright-mcp/` or `db/` state.

**Steps:**
- [x] Step 1: Preview marker-owned shared deployment with `py -3 scripts/deploy_agent_runtime.py --target codex --dry-run`; confirm only expected shared docs/scripts changes and no platform runtime mutation is required.
- [x] Step 2: Deploy canonical shared docs and scripts with `py -3 scripts/deploy_agent_runtime.py --target codex`.
- [x] Step 3: Verify marker-owned deployment with `py -3 scripts/deploy_agent_runtime.py --target codex --check`.
- [x] Step 4: Run focused lifecycle proof with `py -3 -m pytest tests/test_dcode_project.py tests/test_herdr_main_launcher.py tests/test_starter_lifecycle_contract.py -q`.
- [x] Step 5: Run repository contract proof with `py -3 scripts/validate_repo_contracts.py --repo-root . --fast` and `py -3 scripts/validate_agent_runtime_drift.py --platform codex --skip-deploy-check`.
- [x] Step 6: Inspect Git status and diff; preserve pre-existing untracked `.playwright-mcp/` and `db/` directories.

**Verification:**
- [x] `py -3 scripts/deploy_agent_runtime.py --target codex --check`
- Expected: no shared-asset drift.
- [x] `py -3 -m pytest tests/test_dcode_project.py tests/test_herdr_main_launcher.py tests/test_starter_lifecycle_contract.py -q`
- Expected: all tests pass, including `420.0` default, explicit override, normal exit, timeout error, and cleanup evidence.
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- Expected: repository contract validation passes.
- [x] `py -3 scripts/validate_agent_runtime_drift.py --platform codex --skip-deploy-check`
- Expected: runtime adapter drift validation passes.

**Exit Criteria:**
- Canonical and shared `dcode_project.py` both use `420.0`; explicit timeout override and existing cleanup tests pass; docs and deployment checks agree; no unrelated files change.

## Verification

- `py -3 -m pytest tests/test_dcode_project.py tests/test_herdr_main_launcher.py tests/test_starter_lifecycle_contract.py -q`
- `py -3 scripts/deploy_agent_runtime.py --target codex --check`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- `py -3 scripts/validate_agent_runtime_drift.py --platform codex --skip-deploy-check`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. both DeepAgents launch branches use `_DEEPAGENTS_DEFAULT_TIMEOUT = 420.0`
2. explicit `--timeout N` remains authoritative
3. existing timeout cleanup and error facts remain unchanged and pass fresh tests
4. documentation distinguishes the direct `420s` wrapper ceiling from CoS `native` grants and Herdr's `1800s` grant/watchdog rules
5. marker-owned shared runtime passes deployment drift check
6. required focused tests and repository validators pass
7. pre-existing untracked `.playwright-mcp/` and `db/` state remains untouched
8. deviations, blockers, and any deployment collision are recorded before final verification

Plan status changes to `completed` only after `skill-verification-before-completion` returns `verified`.
