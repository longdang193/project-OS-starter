---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: cos-deepagents-top-level-lane-expansion
targets:
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_main_launcher.py
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - .agents/skills/skill-executing-plans/SKILL.md
  - .agents/skills/skill-deepagents-executing-plans/SKILL.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - tests/test_skill_chief_of_staff.py
  - generated_agents/
---

# CoS DeepAgents Top-Level Lane Expansion

## Goal

Expand CoS to coordinate approved-plan `deepagents` implementation lanes through
Herdr without creating another coordination system or changing durable-state
ownership. Preserve native Codex as controller, plan `Executor` as runtime SSOT,
Git as repository truth, DeepAgents workers as executor-local, and Codex-only
review/integration lanes for V1.

Implementation may exist before policy enables it. CoS policy changes happen only
after the real mixed-runtime adapter smoke passes.

## Implementation Outcomes

### Executor-aware Herdr launcher

The existing `scripts/herdr_main_launcher.py` supports tested `codex` and
`deepagents` adapter paths. Codex keeps its current Herdr-native launch shape.
DeepAgents uses the existing `dcode-project` wrapper, selected profile, bounded
task text, and proven Herdr pane-process supervision. The launcher shares Git,
pane, profile, redaction, and fail-closed validation across both paths.

The launcher selector may accept `--executor codex` or `--executor deepagents`.
It must not forward `--executor` to `dcode-project`; the installed wrapper
selects DeepAgents itself and rejects that option.

### Separated runtime and semantic truth

Herdr owns outer pane, cwd, liveness, output, and pane-retirement evidence.
`dcode-project` owns the DeepAgents worker PID, wait, timeout, exit propagation,
and descendant cleanup through its existing bounded-worker path. CoS reconciles
both evidence sources; neither source substitutes for the other. Herdr stop
behavior must not orphan `dcode-project` or its descendants; if that cannot be
proven, DeepAgents stop remains unsupported and policy stays Codex-only.
The DeepAgents top-level dispatch brief owns its bounded result claim:
`DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED`. CoS normalizes and
accepts that claim only after reconciling Git, plan, and required proof. Process
exit code never becomes a semantic task result by itself.

No CoS-specific result envelope or shared-wrapper output change is added to
`scripts/dcode_project.py` unless Task 1 proves an existing runtime guarantee
cannot be supplied by Herdr plus current wrapper behavior.

### Preserved authority boundaries

`Executor` remains the task-ledger runtime selector. CoS remains native-Codex
controller-only. DeepAgents internal `task` workers remain invisible to CoS.
The Codex controller retains MCP, approval, acceptance, Git coordination,
review/integration, and final verification authority. No new executor, profile
registry, CoS state file, workflow database, or Herdr coordination state is added.

### Policy and distribution alignment

After mixed-runtime adapter proof, canonical CoS, execution, DeepAgents, planning,
and runtime-surface contracts allow `codex | deepagents` for implementation lanes.
Review and integration remain Codex-only in V1. Generated surfaces derive from
canonical sources through `scripts/sync_agent_adapters.py` and are never edited
directly.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve `.playwright-mcp/`, `db/`, and `out/`
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect source and Git state; edit declared launcher, tests, canonical skills, and docs; run declared validators; run adapter sync; perform bounded local Herdr and `dcode-project` probes when installed
- User-approval actions: commit, push, merge, publication, external PR or review actions, credential changes, runtime installation or authentication, destructive recovery, discard, cleanup of preserved untracked paths, and scope expansion
- Parallel ownership: none; runtime proof, launcher, mixed smoke, policy, generated outputs, and final validation are dependency-ordered
- Sequential fallback: stop at any failed runtime gate; retain Codex-only CoS policy and record blocker evidence

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `5b7a84c247da4c754ad6ecd14a559d8da638bb06`
- Expected workspace: clean tracked state with preserved untracked `.playwright-mcp/`, `db/`, and `out/`
- Next action: none — implementation verified and completed
- Blockers: none
- Execution evidence (2026-08-31): `herdr 0.8.2`; Herdr pane run/read/process-info works for normal and bounded long-running commands; process-info reports outer shell identity only; `pane close` returned success and captured descendant PID was not live afterward. Herdr still exposes no child PID, exit-code, or stop-result fields, so split ownership remains required. `dcode-project --print-config --role normal` passed without exposing credentials; `tests/test_dcode_project.py` passed 73 tests. Launcher dry-runs passed for Codex and DeepAgents. Fresh mixed smoke returned `DEEPAGENTS_ADAPTER_SMOKE_OK` and `CODEX_ADAPTER_SMOKE_OK`; Git stayed unchanged and `.deepagents/` was absent after retirement.

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | Split Herdr and `dcode-project` lifecycle smoke | Herdr 0.8.2 outer launch/read/retirement and pane-close cleanup passed; `tests/test_dcode_project.py` 73 passed; no orphan child observed |
| Task 2 | `completed` | current | `codex` | Task 1 | launcher tests and dry-run evidence | `tests/test_herdr_main_launcher.py` 16 passed; Codex and DeepAgents dry-runs passed; DeepAgents command includes fixed bounds and no `--executor` forwarding |
| Task 3 | `completed` | current | `codex` | Task 2 | pre-policy mixed-runtime adapter smoke | DeepAgents returned `DEEPAGENTS_ADAPTER_SMOKE_OK`; Codex returned `CODEX_ADAPTER_SMOKE_OK`; Git unchanged; `.deepagents/` absent; retired Codex PID not live |
| Task 4 | `completed` | current | `codex` | Task 3 | canonical contract tests, sync, and final validators | canonical policy updated; generated adapters synchronized; `tests/test_skill_chief_of_staff.py` 12 passed; repository validators passed |

## Task Breakdown

### Task 1: Prove split runtime lifecycle contract

**Purpose:**
- Establish exact outer-pane and wrapper-owned runtime behavior before changing launcher or CoS policy.

**Task Function:**
- Verify installed Herdr command surface and run disposable non-writing pane processes.

**Template Profile:**
- Controller-selected: `xhigh`
- Selection basis: external runtime ambiguity and material lifecycle/security risk.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent confirmation of process identity, observation, stop, exit, and retirement evidence.

**Specification Coverage:**
- Herdr must support ordinary pane-process launch suitable for `dcode-project`.
- Herdr evidence must cover session, pane, cwd, outer process identity, output read, pane retirement, and no-live outer process.
- `dcode-project` evidence must cover worker wait, normal exit propagation, timeout cleanup, and descendant cleanup.
- A real abort/stop probe must show no `dcode-project` or DeepAgents descendants survive Herdr stop; otherwise DeepAgents stop is unsupported and policy remains Codex-only.
- Failure leaves repository policy unchanged.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_herdr_pane`, `scripts/herdr_main_launcher.py:_json_command`
- Verify: `scripts/dcode_project.py:_run_bounded_worker`, `tests/test_dcode_project.py`
- Inspect: `.agents/skills/skill-chief-of-staff/SKILL.md` runtime and lifecycle sections
- Inspect: `docs/operating_system/tooling/runtime-tool-resolution.md`
- Verify: installed `herdr` and `dcode-project` version/help output

**Dependencies:**
- Current Git state and base commit recorded above.
- No Herdr installation, authentication, or provider change is authorized.

**Authority:**
- Preauthorized local actions: read-only capability probes and disposable non-writing pane processes.
- Stop for: missing Herdr, missing ordinary pane-process support, unknown command semantics, unavailable outer-pane observation, unproven wrapper cleanup, credential prompts, or repository mutation.

**Steps:**
- [x] Step 1: Run `herdr --version` and `herdr --help`; record exact installed version and command surface.
- [x] Step 2: Inspect exact installed help for pane process launch, output read, wait, status, and stop operations.
- [x] Step 3: Launch a disposable non-writing process at the exact repository root; verify pane cwd and process identity.
- [x] Step 4: Verify Herdr output capture, pane retirement, and no-live outer process for normal and non-zero commands.
- [x] Step 5: Verify existing `dcode-project` normal exit, timeout, and Windows descendant-cleanup paths through focused tests and bounded local probes where available.
- [x] Step 6: Run an abort/stop probe; prove no wrapper or DeepAgents descendant survives, or record DeepAgents stop as unsupported.
- [x] Step 7: Return `PASS` only with complete split evidence; return `BLOCKED` without source or policy edits when any mandatory guarantee is absent.

**Verification:**
- [x] `herdr --version`
- [x] `herdr --help`
- [x] Exact Herdr pane/process help commands discovered in Step 2
- [x] Recorded Herdr session, pane, cwd, outer process, output, retirement, and no-live-process evidence
- [x] Recorded `dcode-project` wait, exit propagation, timeout, descendant-cleanup, and abort evidence
- Expected: one repeatable split lifecycle contract exists and tracked files remain unchanged.

**Exit Criteria:**
- Split lifecycle supervision is proven, or plan execution stops at Task 1 with CoS still Codex-only.

### Task 2: Add executor-aware Herdr launcher adapter

**Purpose:**
- Reuse one launcher for Codex and DeepAgents without duplicating runtime, profile, Git, or evidence gates.

**Task Function:**
- Extend launcher command construction and focused tests after the Herdr capability gate.

**Template Profile:**
- Controller-selected: `xhigh`
- Selection basis: shared launcher security boundary and cross-runtime process identity.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent backward-compatibility and fail-closed review.

**Specification Coverage:**
- Add launcher-level `--executor` with default `codex`; reject unsupported values.
- Keep Codex command, environment, hook checks, profile binding, Git identity, and Herdr-native agent lifecycle unchanged.
- DeepAgents launcher path requires bounded task text and selected profile from `agents/*.toml`; never hardcode a profile name.
- DeepAgents invokes existing `dcode-project` with selected profile, task text, `--json`, and `--quiet`; it does not pass `--executor` because the wrapper already selects DeepAgents.
- Shared evidence records executor, profile, provider/model identity, repository/worktree identity, expected base, pane cwd, process binding, and redacted arguments.
- Herdr process exit is runtime evidence only. The launcher does not map exit code to `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`.
- If Task 1 exposes a concrete lifecycle gap not covered by Herdr or current wrapper behavior, record it before changing `scripts/dcode_project.py`; modify shared `_run_bounded_worker` only when that shared owner is the proven defect.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_profile`, `scripts/herdr_main_launcher.py:_git_identity`, `scripts/herdr_main_launcher.py:_herdr_pane`, `scripts/herdr_main_launcher.py:resolve_launch`, `scripts/herdr_main_launcher.py:main`
- Modify: `scripts/herdr_main_launcher.py:resolve_launch`, `scripts/herdr_main_launcher.py:build_parser`, `scripts/herdr_main_launcher.py:main`
- Modify: `tests/test_herdr_main_launcher.py`
- Verify: `scripts/agent_profile_registry.py:load_agent_profiles`
- Conditional inspect/modify only if Task 1 proves required: `scripts/dcode_project.py:_run_bounded_worker` and `tests/test_dcode_project.py`

**Dependencies:**
- Task 1 `PASS` with exact pane-process command and lifecycle evidence.
- Existing `dcode-project` profile, provider, no-MCP, timeout, role-view, and child-cleanup behavior remains the default boundary.

**Authority:**
- Preauthorized local actions: edit launcher and focused tests; use fake runtime commands; run dry-run and bounded local probes.
- Stop for: Codex launch-shape regression, profile compatibility bypass, secret exposure, unresolved process identity, or need for a second launcher.

**Steps:**
- [x] Step 1: Add executor validation and branch only at launcher command construction after shared validation.
- [x] Step 2: Build DeepAgents argv from selected profile and bounded task text; preserve the wrapper's own executor selection.
- [x] Step 3: Capture Herdr process evidence and keep semantic result claims separate from exit codes.
- [x] Step 4: Add tests for Codex default compatibility, DeepAgents command shape, selected-profile propagation, task validation, profile rejection, cwd mismatch, process failure, and redaction.
- [x] Step 5: Run dry-run checks for both executor paths and inspect exact JSON evidence.
- [x] Step 6: If a concrete shared-wrapper lifecycle defect was proven, patch `_run_bounded_worker` symmetrically for Tura and DeepAgents and extend only its focused tests.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py -q`
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_dcode_project.py -q` when Task 1 authorizes a wrapper change
- Expected: Codex behavior remains green; DeepAgents path fails closed on missing or mismatched binding; no exit-code semantic shortcut exists.

**Exit Criteria:**
- One launcher supports tested Codex and DeepAgents process paths with shared safety gates, or execution stops with policy unchanged.

### Task 3: Prove pre-policy mixed-runtime lane readiness

**Purpose:**
- Prove the new adapter works before CoS advertises DeepAgents eligibility.

**Task Function:**
- Run one bounded Codex implementation lane and one bounded DeepAgents implementation lane through the tested launcher paths without changing CoS policy.

**Template Profile:**
- Controller-selected: `xhigh`
- Selection basis: cross-runtime integration and lifecycle evidence.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent read-only validation of exact lane identity, runtime evidence, result claims, and cleanup.

**Specification Coverage:**
- Each lane binds exact repository, worktree, branch, base, `HEAD`, profile, allowed paths, and Herdr supervision identity.
- CoS-level observation covers only the two top-level implementation lanes; DeepAgents internal workers remain opaque.
- DeepAgents dispatch brief returns one of `DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED` as a semantic claim; CoS reconciles it with Git and proof.
- Process exit, process loss, timeout, or missing observation blocks runtime acceptance but does not silently become a semantic result.
- This task proves adapter readiness only; it does not claim full Level-2 readiness and does not exercise PR review, integration, merge, push, or publication.

**Required Skills:**
- `skill-executing-plans`, `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: active task ledger, `scripts/herdr_main_launcher.py`, `scripts/dcode_project.py`, `.agents/skills/skill-chief-of-staff/SKILL.md`
- Verify: Herdr session/pane/process evidence, Git identity, selected profile, semantic dispatch claim, runtime exit evidence, and retirement state
- Do not modify: `.playwright-mcp/`, `db/`, or `out/`

**Dependencies:**
- Tasks 1 and 2 `PASS`.
- Herdr and `dcode-project` versions match Task 1 evidence.
- A disposable local mixed-runtime wave is explicitly approved for execution; this plan does not authorize external writes.

**Authority:**
- Preauthorized local actions: bounded local lane execution, read-only observation, declared tests, and plan/Git evidence recording.
- Stop for: missing approved wave, runtime mismatch, unexpected file changes, process escape, stale head, credential prompt, or failed cleanup.

**Steps:**
- [x] Step 1: Bind the declared current workspace, exact base, task IDs, profiles, allowed paths, and expected checks for sequential no-write smoke lanes.
- [x] Step 2: Launch Codex through Herdr native agent mode and DeepAgents through Herdr pane-process mode.
- [x] Step 3: Capture fresh cwd, process, Git, profile, model/provider, output, exit, and semantic result-claim evidence.
- [x] Step 4: Exercise one DeepAgents runtime failure and confirm it blocks runtime acceptance, while the semantic claim remains separate.
- [x] Step 5: Confirm no CoS policy change, no descent into internal workers, no process escape, and no live process after retirement.
- [x] Step 6: Reconcile plan plus Git state and record the adapter smoke result.

**Verification:**
- [x] Fresh mixed-runtime adapter evidence for Codex and DeepAgents implementation lanes
- [x] Runtime failure evidence with process cleanup and separate semantic claim handling
- [x] Post-retirement no-live-process evidence for both lanes
- Expected: adapter readiness passes before policy promotion; failure leaves policy Codex-only.

**Exit Criteria:**
- Mixed-runtime implementation adapter is proven, or plan remains blocked before any CoS eligibility change.

### Task 4: Promote canonical contracts and generated surfaces

**Purpose:**
- Advertise DeepAgents implementation-lane eligibility only after Task 3 proof and align all canonical documentation and generated outputs.

**Task Function:**
- Update canonical policy contracts, focused tests, generated mirrors, and final validation.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded canonical contract and generated-surface alignment after runtime proof.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent scan for authority expansion, stale Codex-only text, and generated drift.

**Specification Coverage:**
- CoS implementation-lane eligibility becomes `Executor: codex | deepagents`.
- CoS remains native-Codex-controller-only and Herdr-only for top-level lane dispatch.
- CoS consumes task-ledger `Executor`; it does not choose executor or add a registry.
- DeepAgents internal workers remain executor-local and opaque.
- The outer DeepAgents dispatch brief uses the CoS execution-return vocabulary; process evidence and semantic claims remain distinct.
- Review and integration remain independent top-level Codex lanes in V1.
- Level-2 wording is not broadened; document mixed-runtime lane readiness as a separate prerequisite/evidence class.

**Required Skills:**
- `skill-writing-skills`, `skill-code-standards`, `skill-executing-plans`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-chief-of-staff/SKILL.md`, `.agents/skills/skill-executing-plans/SKILL.md`, `.agents/skills/skill-deepagents-executing-plans/SKILL.md`, `.agents/skills/skill-requesting-code-review/SKILL.md`, `docs/operating_system/planning/planning-dispatch.md`, `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: `.agents/skills/skill-chief-of-staff/SKILL.md`, `.agents/skills/skill-executing-plans/SKILL.md`, `.agents/skills/skill-deepagents-executing-plans/SKILL.md`, `docs/operating_system/planning/planning-dispatch.md`, `docs/operating_system/runtime/runtime-surfaces.md`, `tests/test_skill_chief_of_staff.py`
- Verify only: `.agents/skills/skill-requesting-code-review/SKILL.md`; it remains unchanged and Codex-only for V1 review/integration
- Generate only through sync: all adapter outputs derived from changed canonical skills

**Dependencies:**
- Tasks 1–3 `PASS`.
- Mixed-runtime adapter evidence is fresh for the installed Herdr version.
- Sync preflight reports no unrelated generated drift.

**Authority:**
- Preauthorized local actions: edit canonical skill/doc sources and focused tests; run adapter sync and validators; inspect generated diffs.
- Stop for: generated drift outside changed canonical skills, review/integration expansion, new runtime state, new registry, or direct generated-file edit.

**Steps:**
- [x] Step 1: Update canonical CoS and execution policy from Codex-only implementation lanes to executor-aware top-level lanes.
- [x] Step 2: Define DeepAgents top-level dispatch-brief return vocabulary and keep internal worker semantics local.
- [x] Step 3: Update planning dispatch and runtime surfaces; leave review-requesting contract unchanged.
- [x] Step 4: Replace only tests for intentionally changed implementation-lane eligibility; retain controller, Herdr-only, worker-opacity, review-separation, and durable-truth assertions.
- [x] Step 5: Run `py -3 scripts/sync_agent_adapters.py --all-platforms --check`; permit only declared drift from changed canonical skills.
- [x] Step 6: Run `py -3 scripts/sync_agent_adapters.py --all-platforms`; inspect generated headers and changed-skill fan-out.
- [x] Step 7: Run sync check again and all final validators.

**Verification:**
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `py -3 -m pytest tests/test_skill_chief_of_staff.py -q`
- [x] `py -3 scripts/validate_planning_lifecycle.py --strict`
- [x] `py -3 scripts/validate_template_required_sections.py --require-template-selection`
- [x] `py -3 scripts/validate_repo_contracts.py --fast`
- Expected: canonical/generated surfaces agree; only implementation-lane eligibility changes; review/integration remains Codex-only.

**Exit Criteria:**
- Proven runtime behavior and canonical policy agree; generated adapters are synced; no unsupported readiness claim is added.

## Verification

- `py -3 scripts/validate_planning_lifecycle.py --strict`
- `py -3 scripts/validate_template_required_sections.py --require-template-selection`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/build_starter_kit.py --output-root generated_exports`
- `py -3 scripts/validate_starter_kit.py`
- `py -3 scripts/validate_repo_contracts.py --fast`
- `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_skill_chief_of_staff.py tests/test_git_lane_lifecycle.py -q`
- `git diff --check`
- `git status --short --branch`

## Completion Criteria

The plan is ready for completion verification when:

1. Task 1 proves exact Herdr ordinary-process supervision or records a blocking runtime gap with policy unchanged.
2. The single launcher supports tested Codex and DeepAgents process paths; Codex default behavior remains compatible.
3. DeepAgents uses existing `dcode-project` profile/provider/no-MCP/timeout/cleanup boundaries; wrapper changes occur only for a proven shared lifecycle defect.
4. Herdr runtime evidence remains distinct from DeepAgents semantic lane-result claims and CoS acceptance.
5. A fresh mixed-runtime adapter smoke proves exact lane identity, process lifecycle, semantic claim capture, failure handling, retirement, and no-live-process state before policy promotion.
6. CoS implementation-lane policy consumes task-ledger `Executor` and keeps internal DeepAgents workers opaque.
7. Native Codex controller, Git/plan truth, acceptance, review, integration, and durable-state ownership remain unchanged.
8. Review and integration remain Codex-only for V1.
9. Canonical sources and all generated fan-out pass sync and repository validation.
10. `skill-verification-before-completion` returns `verified` before plan status changes from `active` to `completed`; no commit, push, merge, or publication occurs under this plan.

This plan is `completed`; implementation and final verification are complete.
