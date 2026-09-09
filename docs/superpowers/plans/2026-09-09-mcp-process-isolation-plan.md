---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: mcp-process-isolation
targets:
  - scripts/herdr_main_launcher.py
  - scripts/mcp_selection.py
  - tests/test_herdr_main_launcher.py
  - tests/test_mcp_selection.py
  - tools/local-patch-hub/Start-OpenDesignMcp.ps1
  - tests/test_open_design_local_patch.py
  - tools/local-patch-hub/README.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
---

# MCP Process Isolation

## Goal

Close remaining MCP startup and process-isolation gaps after `bc7a8dc` while
preserving controller MCP access, DeepAgents direct-MCP behavior, OpenDesign
update-safe overlays, and fail-closed delivery reconciliation.

## Implementation Outcomes

### Explicit executor MCP contract

Both executors validate and report effective MCP selection. No selection means
no enabled worker MCPs. Codex accepts only server-level selection until native
tool-level narrowing is proven; unsupported tool selectors fail before launch.
Unknown, disabled, or unauthorized servers fail before launch.

### Worker-wide MCP isolation

Native Codex workers disable every MCP server inherited from global or
project-local Codex configuration, not only `chrome-devtools` and `playwright`.
The launcher also discovers runtime-provided MCP servers through Codex's own
`mcp list --json` boundary; runtime-only servers receive inert transport fields
before disablement so Codex accepts the override. The top-level controller
keeps its existing configuration and MCP access.

### Serialized OpenDesign bootstrap

OpenDesign daemon discovery and startup use one startup owner. Concurrent MCP
wrappers recheck readiness after acquiring the owner lock and do not launch
duplicate daemons. Startup timeout ownership is documented and aligned with
Codex `startup_timeout_sec`.

### Regression and runtime proof

Tests prove selection, future-MCP isolation, ownership-verified failed-start
reconciliation, lock/recheck behavior, and preservation of fail-closed delivery
semantics. A bounded Windows smoke run records startup latency, process counts,
MCP failures, overlap after initialization, and owned-process retirement
without changing unrelated workspace artifacts. Handshake closure remains a
symptom; resource exhaustion is recorded only when host/process evidence proves
it.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`, `skill-plan-document-reviewer`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed launcher, wrapper, test, README, and runtime-documentation files; run focused tests, validators, and bounded local process inspection; preserve existing uncommitted changes and untracked artifacts
- User-approval actions: Codex configuration writes, live MCP/daemon startup, authentication, commits, pushes, merges, destructive cleanup, or edits outside listed targets
- Parallel ownership: none; launcher and wrapper tasks share MCP contract and must remain sequential
- Sequential fallback: complete Codex contract and worker isolation before OpenDesign changes; complete focused proof before runtime smoke and final validation

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `3e76fb0`
- Expected workspace: tracked files clean at `3e76fb0`; preserve untracked `.playwright-mcp/` and `db/`; do not stage, delete, or rewrite them
- Next action: none; implementation and verification complete
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | launcher selector tests | `182 passed`; runtime selector tests added |
| Task 2 | `completed` | current | `codex` | Task 1 | selection and isolation tests | global/project/runtime MCP isolation; live Codex parser probe |
| Task 3 | `completed` | current | `codex` | Task 2 | failed-start ownership tests | ownership and fail-closed reconciliation tests pass |
| Task 4 | `completed` | current | `codex` | Task 3 | OpenDesign patch tests and timeout contract | `178+` focused tests; one daemon PID across concurrent wrappers |
| Task 5 | `completed` | current | `codex` | Task 4 | full suite, validators, smoke evidence | live worker returned `LIVE_MCP_ISOLATION_OK`; zero new MCP child processes; drift clean |

## Task Breakdown

### Task 1: Define executor-neutral MCP selection contract

**Purpose:**
- Give both executors one selection contract and prevent unsupported selectors
  from being accepted, recorded, and silently ignored.

**Task Function:**
- Extract existing MCP capability and selector validation into one shared helper
  without creating a provider registry.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small Python contract change with direct existing tests.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent review of executor symmetry and evidence fields.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_normalize_runtime_grant`, `resolve_launch`
- Add: `scripts/mcp_selection.py`
- Add: `tests/test_mcp_selection.py`
- Modify: `scripts/herdr_main_launcher.py:_normalize_runtime_grant`, `resolve_launch`
- Modify: `tests/test_herdr_main_launcher.py`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- Preserve DeepAgents server/tool selection behavior after moving shared parsing.
- Define Codex capability as server-level selection only until native tool
  narrowing is proven.

**Authority:**
- Preauthorized local actions: edit listed Python/test/runtime-doc files and run focused tests.
- Stop for: provider changes, config writes, or tool-level Codex projection that
  cannot be proven by installed Codex behavior.

**Steps:**
- [x] Write failing tests for no selection, server selection, tool selection,
  unknown server, disabled server, and unauthorized server.
- [x] Move capability/selection normalization into the shared helper.
- [x] Make Codex reject unsupported tool selectors before launch; retain a
  temporary fail-closed guard for any selector form not yet projected.
- [x] Report requested and effective selection separately in launcher evidence.

**Verification:**
- `py -m pytest tests/test_mcp_selection.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py -q`
- Expected: both executors reject unsupported/unknown selectors; supported
  selections report effective access; existing DeepAgents tests remain green.

**Exit Criteria:**
- No executor claims effective MCP access from an ignored selector.
- DeepAgents direct-MCP behavior remains unchanged.
- Child-agent grants preserve or narrow parent effective access; no child path
  broadens it without an explicit validated selection.

### Task 2: Apply effective worker-wide MCP isolation

**Purpose:**
- Prevent `open-design`, renamed servers, and future configured MCPs from being
  inherited by native Codex workers.

**Task Function:**
- Derive the effective worker MCP set from all applicable configuration and
  runtime overrides, then project only the validated selection into worker
  arguments.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded launcher change using Python `tomllib`; no new dependency.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: inspect config-source coverage and fail-closed behavior.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_codex_runtime`, `_codex_arguments`, `resolve_launch`
- Modify: `scripts/mcp_selection.py`, `scripts/herdr_main_launcher.py:_codex_runtime`, `_codex_arguments`
- Modify: `tests/test_herdr_main_launcher.py`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- Task 1 complete.
- Resolve every applicable Codex source used by the worker, including global
  `CODEX_HOME`, project-local configuration, command-line `-c` overrides, and
  runtime-provided MCP definitions. Do not assume global TOML is complete.
- Reuse existing server definitions; do not create a second MCP catalog or
  provider classification.
- If effective configuration cannot be determined, fail closed instead of
  launching with partial isolation.

**Authority:**
- Preauthorized local actions: edit listed launcher/test/runtime-doc files, parse temporary TOML fixtures, and run focused tests.
- Stop for: changing global Codex configuration, changing authentication, introducing a new config file, or changing controller MCP behavior.

**Steps:**
- [x] Write failing tests with `open-design`, a future server, project-local
  configuration, and runtime overrides.
- [x] Make no-selection project zero enabled worker MCPs.
- [x] Make server selection disable all effective servers, then enable only the
  selected validated server.
- [x] Replace the hardcoded browser-only assertion with all-server assertions
  while retaining explicit browser coverage.
- [x] Include requested/effective selection and config-source digest in evidence
  without exposing credentials.
- [x] Preserve current model/provider/developer-instruction overrides and controller `CODEX_HOME` behavior.

**Verification:**
- `py -m pytest tests/test_herdr_main_launcher.py -q`
- Expected: no-selection starts zero configured MCPs; selected server starts
  only that server; configured `chrome-devtools`, `playwright`, `open-design`,
  and invented future names cannot bypass isolation; malformed or unresolved
  effective config blocks launch.

**Exit Criteria:**
- Native workers cannot inherit a configured MCP merely because its name was
  not in a hardcoded denylist or because it came from a non-global source.
- No new provider catalog, scheduler, or MCP config source exists.

### Task 3: Reconcile failed starts by verified lane ownership

**Purpose:**
- Prevent replacement launches from leaving an earlier owned attempt running,
  while never killing a shared or uncertain process.

**Task Function:**
- Add ownership-verified reconciliation before retry or replacement after a
  failed start.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: existing Herdr observation and termination primitives cover
  the boundary; no new supervisor needed.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent review of ownership proof and fail-closed paths.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_agent_name_taken`, `_terminate_codex_lane`, `main`
- Inspect: `docs/operating_system/procedures/runtime-adapter-procedure.md:Delivery Reconciliation`
- Modify: `scripts/herdr_main_launcher.py:main` and reconciliation helper path
- Modify: `tests/test_herdr_main_launcher.py`
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md`

**Dependencies:**
- Task 2 complete.
- Existing session, pane, agent identity, task hash, and process evidence
  remain the ownership facts.

**Authority:**
- Preauthorized local actions: edit listed launcher/test/procedure files and run mocked Herdr reconciliation tests.
- Stop for: generic process-tree killing, uncertain ownership, shared-daemon cleanup, or automatic replay after unknown delivery.

**Steps:**
- [x] Write failing tests for active owned attempt, absent attempt, unrelated
  attempt, missing process evidence, and failed cleanup verification.
- [x] Before replacement, inspect the existing exact session/pane/agent and
  task identity through Herdr.
- [x] Retire only verified lane-owned processes through existing termination
  verification; record process IDs and cleanup result.
- [x] If ownership or process state is uncertain, return
  `reconciliation_required` and do not retry.
- [x] Preserve existing `delivery_uncertain` behavior: no automatic kill or
  replay for transport uncertainty alone.

**Verification:**
- `py -m pytest tests/test_herdr_main_launcher.py -q`
- Expected: replacement never kills unrelated/shared processes; uncertain
  evidence blocks retry; verified cleanup produces explicit evidence.

**Exit Criteria:**
- Failed-start replacement has a verified ownership decision.
- No generic auto-kill or replay path exists.

### Task 4: Serialize OpenDesign daemon bootstrap and align timeout ownership

**Purpose:**
- Prevent concurrent wrappers from observing no daemon and launching duplicate
  OpenDesign instances.

**Task Function:**
- Add a narrowly scoped Windows startup lock, readiness recheck, and explicit
  timeout contract to the update-safe wrapper.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded PowerShell wrapper change with existing local-patch tests.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: inspect lock release, timeout, and existing-daemon preservation.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `tools/local-patch-hub/Start-OpenDesignMcp.ps1:Find-OpenDesignDaemon`
- Inspect: `tools/local-patch-hub/Apply-OpenDesignPatch.ps1:withMcpBootstrapLock`
- Modify: `tools/local-patch-hub/Start-OpenDesignMcp.ps1`
- Modify: `tests/test_open_design_local_patch.py`
- Modify: `tools/local-patch-hub/README.md`

**Dependencies:**
- Task 3 complete.
- Preserve existing daemon reuse and active-run protection.
- Codex `[mcp_servers.open-design].startup_timeout_sec` is policy owner. Set
  it above the wrapper readiness budget, with a documented margin; do not
  silently raise every timeout.

**Authority:**
- Preauthorized local actions: edit listed PowerShell/test/README files, run static wrapper tests, and inspect local named-pipe behavior without killing existing OpenDesign processes.
- Stop for: force-stopping OpenDesign, changing active run state, modifying installed OpenDesign files, or writing Codex config without explicit approval.

**Steps:**
- [x] Write failing static tests requiring a named startup owner, lock release,
  readiness recheck, and existing-daemon reuse.
- [x] Add one named Windows mutex or equivalent lock around the
  `Find-OpenDesignDaemon`/`Start-Process` decision.
- [x] Re-run daemon discovery after lock acquisition before starting a process.
- [x] Keep daemon preparation conditional: ordinary code/review workers do not
  trigger OpenDesign; only a task with explicit OpenDesign need does.
- [x] Keep wrapper readiness deadline below the configured Codex startup timeout
  and document the required margin in `tools/local-patch-hub/README.md`.
- [x] Add explicit manual configuration step for the user-owned Codex timeout;
  do not commit credentials or user-local config into the repository.

**Verification:**
- `py -m pytest tests/test_open_design_local_patch.py -q`
- Expected: static contract proves lock/recheck behavior and no force-stop path.
- Manual bounded check: start two wrapper invocations concurrently with an
  already-running daemon and with no daemon; inspect that only one owner starts
  the daemon and both clients converge on the same endpoint.

**Exit Criteria:**
- Concurrent wrappers do not multiply OpenDesign daemon startup.
- Existing daemon and active-run safety remain intact.
- Timeout ownership is explicit: Codex config controls client budget; wrapper
  uses a smaller readiness sub-budget.

### Task 5: Full verification, startup barrier, and runtime evidence

**Purpose:**
- Prove resource isolation and preserve unrelated workspace state.

**Task Function:**
- Run focused tests, repository validators, and one bounded before/after smoke
  comparison.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: verification-only task; no delegation benefit.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: final diff, proof, and non-regression review.

**Required Skills:**
- `skill-performance-optimization`
- `skill-verification-before-completion`
- `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: all task-owned diffs and existing reconciliation tests
- Modify: none unless verification finds a task-owned defect

**Dependencies:**
- Tasks 1–4 complete.
- Capture baseline `git status --short`, `git diff`, and untracked path list
  before any verification that starts processes.

**Authority:**
- Preauthorized local actions: run tests, validators, dry-run launcher commands, and bounded process inspection; preserve baseline artifacts.
- Stop for: deleting processes or files, changing unrelated diffs, live MCP authentication, or external config writes.

**Steps:**
- [x] Run focused suites for launcher, DeepAgents projection, and OpenDesign patch contracts.
- [x] Run repository validators and `git diff --check`.
- [x] Run bounded native worker isolation probe with browser MCPs configured globally.
- [x] Record MCP startup failures and residual owned processes; no new MCP child processes appeared.
- [x] Confirm no worker starts configured MCP servers; controller behavior remains available.
- [x] Retain existing controller startup barrier; no new shared limit added without measured pressure.
- [x] Confirm `reconciliation_required` still remains fail-closed and no generic auto-kill/replay was added.
- [x] Compare final tracked diff and preserve untracked `.playwright-mcp/` and `db/` artifacts.

**Verification:**
- `py -m pytest tests/test_mcp_selection.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_open_design_local_patch.py -q`
- `py scripts/validate_repo_contracts.py --repo-root . --fast`
- `py scripts/validate_repo_config.py --repo-root .`
- `py scripts/validate_agent_runtime_drift.py --platform codex`
- `git diff --check`
- Performance target: zero configured MCP child processes from native workers;
  no residual worker-owned browser processes after retirement; measured overlap
  begins only after initialization/assignment acknowledgement. Threshold owner:
  lead controller acceptance evidence.

**Exit Criteria:**
- All focused tests and validators pass.
- Runtime smoke confirms worker-wide MCP isolation without treating handshake
  text alone as proof of resource exhaustion. Resource exhaustion is reported
  only with process-exit, memory-pressure, or crash evidence.
- Existing uncommitted launcher/test changes and untracked artifacts remain
  unchanged except for explicitly task-owned hunks.

## Non-Goals

- No broad resource scheduler or permanent concurrency limit; add only a
  measurement-driven startup limit if Task 5 proves sustained pressure.
- No generic cleanup on `reconciliation_required`; only verified lane-owned
  failed-start reconciliation is allowed.
- No broad timeout increase without local verification of configured client
  deadline.
- No new MCP registry, provider catalog, dependency, or authentication flow.
- No live lifecycle test as a mandatory CI test; runtime smoke remains bounded
  acceptance evidence.

## Verification

- `py -m pytest tests/test_mcp_selection.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_open_design_local_patch.py -q`
- `py scripts/validate_repo_contracts.py --repo-root . --fast`
- `py scripts/validate_repo_config.py --repo-root .`
- `py scripts/validate_agent_runtime_drift.py --platform codex`
- `git diff --check`
- Bounded Windows smoke evidence for concurrency 1 and 2, process counts,
  startup failures, and residual process cleanup.

## Completion Criteria

1. Both executors validate and report effective MCP selection; unsupported selectors fail before launch.
2. No-selection native workers start zero configured MCP servers.
3. Selected native workers start only selected authorized server-level MCPs.
4. Native workers cannot bypass isolation through project or runtime-provided MCP configuration.
5. Failed-start replacement reconciles exact lane ownership before retry and never kills shared or uncertain processes.
6. OpenDesign bootstrap has one startup owner, conditional preparation, and readiness recheck after lock acquisition.
7. Codex startup timeout owns policy; wrapper readiness remains below it with documented margin.
8. Initialization is sequential while post-ack worker execution may overlap; any added limit is measurement-driven.
9. Resource exhaustion claims include direct host/process evidence, not handshake closure alone.
10. Focused tests, validators, diff checks, and bounded runtime evidence pass.
11. Existing uncommitted changes and untracked `.playwright-mcp/` and `db/` remain preserved.
