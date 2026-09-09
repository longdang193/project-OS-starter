---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: deepagents-launcher-binding-ownership
targets:
  - scripts/dcode_project.py
  - tests/test_dcode_project.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/governance/repo-governance.md
---

# DeepAgents Launcher Binding And Ownership

## Goal

Close confirmed follow-up defects after `aa70d7295aafcdab5beb5e7483a530093f018ec2`:
make one invocation-local runtime snapshot, bind evidence to the selected worker,
prevent concurrent role-view cleanup including crash-recovery gaps, and align
ownership documentation. Preserve provider-owned `wire_api`, native DeepAgents
protocol projection, MCP isolation, all canonical role views, and the absence of
Starter-level transport translation.

External adapter changes remain outside this plan. Starter records bounded runtime
evidence only; the adapter repository owns adapter implementation and revision.

## Implementation Outcomes

### Consistent launch binding

`dcode-project` loads Codex configuration once per invocation, derives provider,
endpoint, protocol parameters, MCP capabilities, and launch evidence from that
snapshot, and reads credentials only on an execution path. `--print-config` does
not require secret-file access.

### Safe role-view lifecycle

One same-worktree DeepAgents launch owns shared generated role views for its full
worker lifetime. A second launch fails before replacing or deleting those views.
Cleanup removes only the owning attempt's generated views and directories it
created that are now empty. Pre-existing `.deepagents` content remains unchanged.
Active ownership is not represented by a stale marker; any lock file outside
`.deepagents` is an implementation detail and does not prove a live owner.

### Truthful evidence and documentation

Runtime evidence distinguishes controller model from selected worker model and
the effective DeepAgents parameters. Runtime surfaces identify `dcode_project.py`
as DeepAgents projection owner, Herdr as top-level lane/lifecycle owner, and
profiles as owners of identity/model/instruction facts only.

### Delegated protocol proof

Focused tests and one bounded probe against the already-installed pinned runtime
prove protocol behavior for the primary model and a delegated role with an
explicit model, prove delegation occurred, and report tool-call and streaming
coverage separately. Evidence names tested model, runtime or adapter revision,
and covered behavior; untested behavior remains unverified.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed Starter source, tests, canonical docs, and this plan; run focused tests, repository validators, drift checks, and bounded probes using already-installed runtimes and existing credentials
- User-approval actions: adapter-repository edits, provider installation, authentication, credential changes, external configuration writes, process termination outside task-owned probes, commits, pushes, merges, destructive cleanup, and edits outside listed targets
- Parallel ownership: none; launcher, tests, and ownership docs share the same binding contract
- Sequential fallback: reconcile existing plans first, then implement binding and evidence, then role ownership, then docs, then runtime proof and final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `aa70d7295aafcdab5beb5e7483a530093f018ec2`
- Expected workspace: preserve unrelated untracked `.playwright-mcp/` and `db/`; do not stage, delete, or rewrite them
- Next action: run final focused suite and repository validators
- Blockers: none
- Reconciliation: `2026-09-09-launcher-reliability-performance-hardening-plan.md` remains active and owns overlapping runtime documentation requirements. This plan changed only ownership/protocol clauses, preserved its pending reliability requirements, and uses one final aggregate validation pass.

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | baseline, actual plan-status reconciliation, and pinned-runtime propagation inspection | `99 passed`; prior reliability plan remains `active` on overlapping docs; pinned `deepagents-code 0.1.59` loads explicit subagent models but no visible CLI model-parameter propagation path |
| Task 2 | `completed` | current | `codex` | Task 1 | binding, digest, and print-config tests | `107 passed`; one immutable binding snapshot; deferred secret reads; worker digest and role-less evidence semantics verified |
| Task 3 | `completed` | current | `codex` | Task 2 | same-worktree ownership, crash, and cleanup tests | synchronized subprocess lock tests pass; lock keyed by resolved worktree; lock file retained; unproven Windows worker lifetime preserves views |
| Task 4 | `completed` | current | `codex` | Task 2 | canonical ownership and provenance docs | canonical runtime, procedure, and governance docs aligned; external adapter ownership remains out of scope |
| Task 5 | `completed` | current | `codex` | Task 3, Task 4 | direct launcher proof, delegated runtime probe, final checks | `206 passed`; print-config succeeds without secret file; pinned `deepagents-code 0.1.59` / SDK `0.7.8` smokes pass for `combo-high` and selected `combo-normal`; tool-call and stream-delta coverage recorded separately as `0` observed/unverified; validators pass |

## Task Breakdown

### Task 1: Reconcile scope and baseline

**Purpose:**
- Establish current Git state, actual plan statuses, completed-plan overlap, source ownership, focused baseline, and pinned-runtime propagation behavior before edits.

**Task Function:**
- Change-scope and implementation-readiness reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small local scope; controller owns Git and plan reconciliation.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent overlap, ownership, and acceptance review.

**Specification Coverage:**
- Preserve unrelated workspace changes, `aa70d72` protocol direction, canonical generated-surface rules, and external adapter boundary.

**Required Skills:**
- `skill-plan-document-reviewer`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_runtime_binding`, `scripts/dcode_project.py:_codex_config`, `scripts/dcode_project.py:_runtime_binding_digest`, `scripts/dcode_project.py:_write_role_views`, `scripts/dcode_project.py:_remove_role_views`, `scripts/dcode_project.py:main`
- Inspect: `tests/test_dcode_project.py`
- Inspect: `docs/superpowers/plans/2026-09-09-deepagents-explicit-responses-support-plan.md`
- Inspect: `docs/superpowers/plans/2026-09-09-starter-verdict-follow-up-plan.md`
- Inspect: installed pinned DeepAgents runtime's role/model propagation path without modifying runtime files
- Verify: Git branch, base, worktree, and untracked-path state

**Dependencies:**
- Current repository at base commit `aa70d7295aafcdab5beb5e7483a530093f018ec2`.

**Authority:**
- Preauthorized local actions: inspect listed files, run read-only Git commands, run the focused launcher test baseline, and inspect the already-installed pinned runtime without changing external files.
- Stop for: unexpected tracked changes, plan overlap that assigns the same symbols to another active task, branch/base mismatch, or any request to modify external adapter files.

**Steps:**
- [x] Step 1: Record `git status --short --branch`, `git rev-parse HEAD`, and preserved untracked paths.
- [x] Step 2: Read actual status and coordination state from every overlapping plan; confirm no active plan owns the listed launcher symbols. The active reliability plan owns overlapping documentation until reconciled.
- [x] Step 3: Inspect the pinned runtime's role/model propagation path and record whether primary `--model-params` reach delegated explicit-model roles. Explicit subagent specs carry model names; no visible propagation of CLI model parameters was found.
- [x] Step 4: Run the focused baseline test command and record result without changing unrelated workspace state: `99 passed`.

**Verification:**
- [x] `py -3 -m pytest tests/test_dcode_project.py -q`
- Expected: baseline result recorded; unrelated `.playwright-mcp/` and `db/` remain unchanged.

**Exit Criteria:**
- Scope, ownership, base, actual plan statuses, baseline, and delegated propagation finding are recorded before Task 2 starts.

### Task 2: Resolve one binding snapshot and truthful evidence

**Purpose:**
- Remove mixed configuration snapshots and make launch evidence describe effective controller and worker bindings.

**Task Function:**
- Runtime binding correction.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded Python refactor with existing focused tests; no delegated benefit.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: binding shape and evidence semantics need independent review.

**Specification Coverage:**
- Codex provider configuration remains protocol SSOT.
- `chat` maps to `use_responses_api=false`; `responses` maps to `use_responses_api=true`.
- One invocation uses one provider/configuration snapshot.
- Secrets stay out of config evidence and are loaded only for execution.
- Worker evidence uses selected role model, not controller model alone.
- DeepAgents alone validates `wire_api` and derives DeepAgents parameters.
- Tura preserves its existing provider and credential behavior.
- Invocation without a selected role has defined evidence semantics.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_runtime_binding`, `scripts/dcode_project.py:_deepagents_model_params`, `scripts/dcode_project.py:_codex_config`, `scripts/dcode_project.py:_runtime_binding_digest`, `scripts/dcode_project.py:main`
- Modify: `scripts/dcode_project.py:_runtime_binding` and the `main` binding/evidence path
- Modify: `tests/test_dcode_project.py` binding, digest, print-config, and launch assertions

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: modify the listed launcher symbols, directly replaced helpers, and focused tests; run Python unit tests and static checks.
- Stop for: provider schema changes, external adapter behavior changes, secret exposure in evidence, or a need for persistent cache or new provider registry.

**Steps:**
- [x] Step 1: Replace separate `_runtime_binding` and `_codex_config` reads with one invocation-local binding containing loaded Codex config, provider name, controller model, endpoint, secret path/key, and DeepAgents parameters only when executor is `deepagents`.
- [x] Step 2: Keep secret path/key in the binding, but defer secret-file read until Tura or DeepAgents execution constructs its environment; preserve Tura's current provider and credential path.
- [x] Step 3: Define `--print-config` as read-only: no credential read, role generation, lock acquisition, child launch, or worker digest when no role is selected.
- [x] Step 4: Include controller and selected worker models as separate evidence fields; compute worker binding evidence from provider, endpoint, selected worker model, and effective DeepAgents parameters, and omit worker digest when no role is selected.
- [x] Step 5: Remove `_validate_deepagents_provider_binding()` and move its tests to `_deepagents_model_params()` or the new production resolver.

**Verification:**
- [x] `py -3 -m pytest tests/test_dcode_project.py -q`
- [x] Assert `--print-config` succeeds when configured secret file is absent and does not emit secret values.
- [x] Assert changing selected worker model changes `runtime_binding_digest` while controller binding stays unchanged.
- [x] Count Codex TOML loader calls and assert exactly one load per invocation on both DeepAgents and Tura paths.
- Expected: one Codex config load per invocation; exact `--model-params` serialization remains unchanged; no role-less print-config worker digest is emitted.

**Exit Criteria:**
- All launch argv, MCP projection, protocol parameters, and evidence fields derive from one immutable invocation snapshot; no dead validation wrapper remains.

### Task 3: Enforce attempt ownership for shared role views

**Purpose:**
- Prevent concurrent same-worktree launches from replacing or deleting each other's generated role views.

**Task Function:**
- Cross-process resource ownership and cleanup hardening.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: security/data-safety-adjacent lifecycle fix with narrow file scope.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: concurrent cleanup failure needs independent race-focused review.

**Specification Coverage:**
- One launch owns shared role views from before write through worker exit and cleanup.
- Second same-worktree launch fails before mutating role views.
- Lock acquisition is non-blocking and occurs before any role-view mutation.
- Lock identity uses canonical resolved worktree identity, preserving separate-worktree concurrency.
- Worker descendants cannot unintentionally inherit the lock handle.
- A launcher crash cannot permit replacement while its worker may still consume shared views; when existing process-lifetime proof is unavailable, preserve views and report a recovery blocker.
- Shared lock files are not unlinked while another process could hold or acquire them.
- Existing user-owned files remain protected.
- Separate worktrees remain usable concurrently.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_write_role_views`, `scripts/dcode_project.py:_remove_role_views`, `scripts/dcode_project.py:main`
- Modify: `scripts/dcode_project.py` role-view lifecycle and private lock context
- Modify: `tests/test_dcode_project.py` role-view lifecycle and launch cleanup tests

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: modify listed role-view lifecycle code and tests; run task-owned synchronized subprocess tests using temporary directories.
- Stop for: deleting user-owned files, age-only stale cleanup, changing DeepAgents runtime installation, or modifying shared paths outside task-owned temporary fixtures.

**Steps:**
- [x] Step 1: Add a standard-library OS-level non-blocking lock keyed by canonical resolved worktree identity, stored outside `.deepagents`, and acquire it before any role-view mutation.
- [x] Step 2: Hold the lock through worker exit and cleanup; configure child process creation so the worker and descendants do not inherit the lock handle.
- [x] Step 3: Never unlink a shared lock file while another process could hold or acquire it; release the OS lock through handle close, and treat lock-file presence as non-authoritative for live ownership.
- [x] Step 4: Fail closed with a clear `RuntimeError` when another same-worktree launch holds the lock. If launcher failure cannot prove all worker descendants stopped, preserve generated views and report a recovery blocker instead of permitting replacement.
- [x] Step 5: Keep existing marker/content checks for user-owned role protection. Cleanup removes only this attempt's generated views and directories it created that are now empty; pre-existing `.deepagents` content remains unchanged.
- [x] Step 6: Add deterministic synchronized subprocess regressions for normal exit, child-start failure, competing launch, launcher crash, and separate-worktree concurrency. Use events/pipes, not sleeps; prove the worker cannot consume shared views after crash before replacement is allowed.

**Verification:**
- [x] `py -3 -m pytest tests/test_dcode_project.py -q`
- [x] Inspect temporary fixture after normal exit, child-start failure, second-launch rejection, and crash recovery.
- Expected: cleanup removes only generated views and launcher-created empty directories; pre-existing `.deepagents` content remains unchanged; failed ownership acquisition leaves first launch's views intact; user-owned content is never deleted.

**Exit Criteria:**
- Shared role-view lifecycle has exclusive attempt ownership and cleanup cannot cross launch boundaries.

### Task 4: Align canonical documentation and adapter provenance

**Purpose:**
- Remove stale ownership claims without duplicating executable protocol truth or importing external adapter ownership into Starter.

**Task Function:**
- Canonical documentation reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: narrow documentation changes with source ownership already established.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: generated/canonical ownership and cross-repository boundary need independent review.

**Specification Coverage:**
- `agents/*.toml` owns profile identity, provider, model, rank, description, and instructions.
- `scripts/herdr_main_launcher.py` owns top-level Herdr target and lifecycle.
- `scripts/dcode_project.py` owns DeepAgents projection and worker lifecycle.
- Runtime procedure owns detailed `wire_api` mapping explanation.
- External adapter repository owns adapter code and revision evidence.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify: `docs/operating_system/runtime/runtime-surfaces.md:Authoring SSOT`, `docs/operating_system/runtime/runtime-surfaces.md:Deployment Targets`, and `docs/operating_system/runtime/runtime-surfaces.md:Policy`
- Modify: `docs/operating_system/governance/repo-governance.md:Source Of Truth`
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md:DeepAgents protocol and compatibility evidence`
- Inspect: generated runtime outputs only through existing drift checks; do not hand-edit generated files

**Dependencies:**
- Task 2 complete; Task 3 may run before or after this task, but final docs must describe the shipped lifecycle.

**Authority:**
- Preauthorized local actions: edit only the listed canonical Markdown sections and run documentation, generated-surface, and repository contract checks.
- Stop for: edits to generated agent files without their canonical source, unknown adapter revision claims, or changes to external repositories.

**Steps:**
- [x] Step 1: Add `scripts/dcode_project.py` to the Authoring SSOT table as DeepAgents projection owner.
- [x] Step 2: Narrow the Herdr row to top-level target resolution, lane selection, session/pane lifecycle, task delivery, and outer observation.
- [x] Step 3: Remove profile `compatibility` ownership from `repo-governance.md`.
- [x] Step 4: Keep exact protocol mapping in `runtime-adapter-procedure.md`; state that adapter implementation and accepted revision belong to external adapter evidence, not Starter source or plan state.

**Verification:**
- [x] `rg -n "agents/\\*\\.toml.*compatibility|herdr_main_launcher.py.*DeepAgents.*projection" docs scripts tests`
- Expected: canonical docs agree with source ownership; no stale profile compatibility ownership remains. Aggregate validators run once in Task 5 on the unchanged candidate.

**Exit Criteria:**
- Documentation describes one owner per fact and does not claim Starter owns external adapter implementation.

### Task 5: Direct boundary proof and final verification

**Purpose:**
- Prove launcher behavior, delegated protocol propagation, scope, and preserved workspace state.

**Task Function:**
- Final backend/runtime verification and acceptance preparation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance belongs to controller.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent final evidence review.

**Specification Coverage:**
- Success and failure paths prove binding, role ownership, cleanup, and evidence semantics.
- Primary and delegated models receive expected native protocol behavior.
- External adapter proof remains bounded and reproducible.
- Unrelated workspace paths remain untouched.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all changed files, current Git state, pinned runtime setup, and existing runtime procedure
- Verify: `scripts/dcode_project.py:main`, `tests/test_dcode_project.py`, and the bounded DeepAgents launch boundary

**Dependencies:**
- Tasks 3 and 4 complete.

**Authority:**
- Preauthorized local actions: run declared tests, validators, drift checks, `git diff --check`, and bounded probes using already-installed runtimes and existing credentials; update this plan's evidence.
- Stop for: missing runtime or credentials, failed required proof, external provider installation/authentication, unexpected tracked changes, or any destructive cleanup request.

**Steps:**
- [x] Step 1: Run focused launcher and profile tests.
- [x] Step 2: Run direct `dcode-project --role normal --print-config` with a temporary config whose secret file is absent; record successful non-secret output.
- [x] Step 3: Run bounded pinned-runtime DeepAgents smokes for `combo-high` and delegated `combo-normal`; record model, runtime revision, endpoint class, tool-call/stream coverage, exit code, and output marker without recording credentials.
- [x] Step 4: Run repository validators and inspect changed paths against declared targets plus preserved `.playwright-mcp/` and `db/` state.
- [x] Step 5: Record accepted evidence, deferrals, and any blocker; do not mark this plan completed until fresh verification returns `verified`.

**Verification:**
- [x] `py -3 -m pytest tests/test_agent_profile_registry.py tests/test_dcode_project.py tests/test_herdr_main_launcher.py -q`
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- [x] `git diff --check`
- [x] `git status --short`
- Expected: focused tests and validators pass; runtime smoke proves primary and delegated protocol behavior; tool-call and streaming coverage remain separately recorded and unverified when not observed; no unrelated path changes.

**Exit Criteria:**
- Fresh automated proof covers every shipped behavior, runtime evidence names its bounded compatibility surface, and preserved workspace state is reconciled.

## Verification

- `py -3 -m pytest tests/test_agent_profile_registry.py tests/test_dcode_project.py tests/test_herdr_main_launcher.py -q`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- `git diff --check`
- `git status --short`
- Bounded pinned-runtime primary plus delegated DeepAgents smoke with recorded revision and covered behavior.

## Non-Goals

- No changes to `C:\Users\HOANG PHI LONG DANG\.local\share\lightrsi\codex-adapter` or any external adapter repository.
- No Starter-level Chat Completions-to-Responses translator.
- No `deepagents_compatible` profile field, provider registry, compatibility matrix, persistent capability cache, supervisor, janitor, or new coordination schema.
- No reduction of generated roles to the selected role only.
- No Herdr polling or startup optimization without a separate measured baseline, workload, threshold, and regression proof.
- No edits to generated `AGENTS.md` or generated adapter files by hand.
- No commits, pushes, merges, authentication, provider installation, external configuration writes, or destructive cleanup during execution.

## Completion Criteria

1. Codex configuration loads once per invocation and `--print-config` does not read secret files.
2. Provider `wire_api` remains sole protocol SSOT and maps symmetrically to native DeepAgents parameters.
3. Runtime evidence includes distinct controller and selected worker model facts, with worker binding represented in the digest.
4. Same-worktree role views have exclusive attempt ownership through worker cleanup; a second launch cannot replace or delete active views.
5. Existing user-owned role content and separate-worktree concurrency remain protected.
6. `_validate_deepagents_provider_binding()` is removed and tests exercise production behavior.
7. Canonical docs assign Herdr, `dcode_project.py`, profiles, and external adapters distinct ownership.
8. Focused tests, repository validators, drift checks, and diff checks pass.
9. Pinned-runtime proof covers primary and delegated explicit-model protocol behavior, proves delegation occurred, and records tool-call and streaming coverage separately. Missing or failed mandatory proof blocks Task 5 and leaves the plan incomplete.
10. `.playwright-mcp/` and `db/` remain untouched.
