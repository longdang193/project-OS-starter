---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: deepagents-windows-runtime-evidence
targets:
  - scripts/setup_deepagents_runtime.ps1
  - scripts/herdr_main_launcher.py
  - tests/test_dcode_project.py
  - tests/test_herdr_main_launcher.py
  - generated_agents/codex/
---

# DeepAgents Windows Runtime Evidence

## Goal

Make supported Windows DeepAgents launch UTF-8 safe and evidence-backed at its
canonical Project OS boundary. Do not change JOB-PROJECT, Scan product code,
LightMem2, or create another launcher source.

## Implementation Outcomes

### Canonical Windows runtime boundary

- Generated user-local `dcode-doctor` wrapper contains UTF-8 environment
  assignments before invoking pinned isolated DeepAgents Code.
- Focused test protects assignment presence and ordering.
- Herdr injects one run-scoped completion marker into each DeepAgents task and
  rejects completion when marker/report observations are missing or uncertain.
- Codex runtime deployment and adapter views derive from repository canonical
  sources only.

### Evidence-based acceptance

- `dcode-doctor.cmd` diagnostic proof is separate from `dcode-project` task proof.
- `--print-config` is discovery-only, never task completion.
- Direct task and Herdr probes capture wrapper path, executable path/version,
  probe ID/root, profile/model/provider, stdout, stderr, exit code, elapsed time,
  process state, terminal state, report marker, encoding result, `.deepagents/`
  state, and cleanup result.
- Delivery, running, completed, failed, and no-report remain distinct.
  Provider transport failure, child nonzero exit, timeout, no-report, and
  encoding failure remain classified failures.

### Explicit boundaries and deferrals

- Unmanaged direct `dcode doctor` is unsupported acceptance because it may resolve
  another executable and bypass the pinned wrapper.
- Herdr completion requires controller-injected run marker paired with
  `COMPLETED` in terminal output. Runtime footers may follow the pair; marker
  derives from current task identity; stale or foreign output without current
  marker is `no-report`.
- LightMem2 is a hard non-goal. No LightMem2 smoke, adapter change, or evidence
  is required here.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-writing-plans`, `skill-plan-document-reviewer`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace` for source/tests; OS temporary Git roots for live probes
- Commit policy: `no commits during execution`
- Preauthorized local actions: `edit listed canonical files and plan, run repository tests/validators, write only C:\Users\HOANG PHI LONG DANG\.agents\project-os and generated_agents\codex through approved sync scripts, run bounded native Windows probes in exact OS temporary roots, store probe evidence under .tmp-tests\deepagents-probes, inspect Git state`
- User-approval actions: `push, merge, publication, destructive cleanup, discard, credential/config changes, or writes outside C:\Users\HOANG PHI LONG DANG\.agents\project-os, generated_agents\codex, .tmp-tests\deepagents-probes, and exact resolved temporary probe roots`
- Parallel ownership: `none`
- Sequential fallback: `source/test proof, codex runtime sync, doctor/config/task/Herdr probes, final verification`

## Task Breakdown

### Task 1: Protect canonical Windows encoding boundary

**Purpose:**
- Prevent Windows code-page decoding from corrupting supported DeepAgents doctor output.

**Task Function:**
- Canonical launcher hardening and focused regression proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: narrow source-owned change; controller retains acceptance authority.

**Validator Profile:**
- Controller-selected: `xhigh`
- Selection basis: independently challenge SSOT, symmetry, and ordering claims.

**Specification Coverage:**
- Keep UTF-8 settings in canonical generated `dcode-doctor` wrapper only.
- Set settings before `& $dcodePath doctor`; do not duplicate settings in a second wrapper source.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/setup_deepagents_runtime.ps1:dcode-doctor wrapper`
- Modify: `scripts/setup_deepagents_runtime.ps1:dcode-doctor wrapper`
- Modify: `tests/test_dcode_project.py:test_setup_launcher_uses_current_repository_source`
- Verify: `scripts/dcode_project.py:_runtime_environment`

**Dependencies:**
- Existing working-tree changes are candidate fix; confirm no JOB-PROJECT or Scan files are in scope.

**Authority:**
- Preauthorized local actions: edit listed canonical script/test and run focused tests.
- Stop for: any shared-wrapper source change, credential/provider change, or product-repo edit.

**Steps:**
- [x] Step 1: Confirm prior `UnicodeDecodeError` boundary and current wrapper invocation order.
- [x] Step 2: Keep UTF-8 assignments in canonical wrapper; add assertions that both assignments precede doctor invocation.
- [x] Step 3: Run focused test and inspect approved diff.

**Verification:**
- [x] `py -m pytest tests/test_dcode_project.py -q`
- Expected: focused suite passes; test proves assignment ordering.

**Exit Criteria:**
- One canonical wrapper source owns doctor encoding behavior and regression proof passes.

### Task 2: Reconcile Codex runtime surfaces

**Purpose:**
- Prevent canonical launcher changes from drifting in supported Codex runtime surfaces.

**Task Function:**
- Deploy and validate generated runtime surfaces.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic repository maintenance.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent generated-surface and SSOT inspection.

**Specification Coverage:**
- Codex-only deployment and adapter scope matches current supported boundary.

**Required Skills:**
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: `scripts/deploy_agent_runtime.py`, `scripts/sync_agent_adapters.py`, `scripts/validate_agent_runtime_drift.py`
- Modify: `generated_agents/codex/` and `C:\Users\HOANG PHI LONG DANG\.agents\project-os` only through approved scripts
- Verify: generated codex files, shared runtime files, and Git status

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: run approved codex-targeted deployment, adapter-sync, and drift-validation commands.
- Stop for: unmarked external files, credential/config changes, or writes outside named codex destinations.

**Steps:**
- [x] Step 1: `py scripts/deploy_agent_runtime.py --target codex`.
- [x] Step 2: `py scripts/sync_agent_adapters.py --platform codex`.
- [x] Step 3: `py scripts/validate_agent_runtime_drift.py --platform codex`.

**Verification:**
- [x] All three commands exit `0`.
- Expected: codex runtime matches canonical source; unrelated files remain untouched.

**Exit Criteria:**
- No codex generated/deployed drift remains.

### Task 3: Prove supported Windows runtime boundaries

**Purpose:**
- Separate executable discovery, diagnostics, delivery, execution, report, and encoding failures.

**Task Function:**
- Bounded native Windows runtime probe and evidence reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: live acceptance and Git/runtime evidence remain controller-owned.

**Validator Profile:**
- Controller-selected: `xhigh`
- Selection basis: adversarial review of false completion, provider failure, and cleanup claims.

**Specification Coverage:**
- Run `dcode-doctor.cmd --help` separately; it proves supported wrapper/path
  execution, not UTF-8 by itself.
- Run `dcode-project --print-config` separately; record config/discovery only.
- Build each disposable probe root with `.git`, `AGENTS.md`, and copied
  `agents/normal.toml` fixture; commit fixture before execution.
- Run direct buffered task with `--no-stream`, direct streaming task without
  `--no-stream`, one Herdr DeepAgents task, and one declared invalid-role
  failure probe. Use unique markers and capture evidence outside probe roots in
  `.tmp-tests/deepagents-probes/<probe-id>.json` before deleting exact roots.
- Keep `--quiet` supported and unremoved; do not use it as completion evidence.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py`, `scripts/herdr_main_launcher.py`, `scripts/setup_deepagents_runtime.ps1`
- Modify: `scripts/herdr_main_launcher.py:resolve_launch`, `scripts/herdr_main_launcher.py:_deepagents_task_state`, `scripts/herdr_main_launcher.py:_deepagents_completion_snapshot`, `scripts/herdr_main_launcher.py:main`, `tests/test_herdr_main_launcher.py`
- Verify: `C:\Users\HOANG PHI LONG DANG\.local\bin\dcode-project.ps1`, `C:\Users\HOANG PHI LONG DANG\.local\bin\dcode-doctor.cmd`, pinned isolated executable, probe evidence files, and exact temporary-root cleanup

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: run bounded read-only probes in exact OS temporary roots and write probe evidence under `.tmp-tests\deepagents-probes`.
- Stop for: credentials, provider installation, external publication, ambiguous/no-report result, or cleanup outside exact resolved root.

**Steps:**
- [x] Step 1: Run `C:\Users\HOANG PHI LONG DANG\.local\bin\dcode-doctor.cmd --help`; capture wrapper path, raw stdout/stderr bytes, UTF-8 decode result, pinned executable path, isolated `dcode.exe --version`, and separate launcher exit code.
- [x] Step 2: Run `C:\Users\HOANG PHI LONG DANG\.local\bin\dcode-project.ps1 --print-config`; record resolved provider/profile/model as discovery-only; read expected DeepAgents pin from `scripts/setup_deepagents_runtime.ps1`, then resolve and verify `C:\Users\HOANG PHI LONG DANG\.local\share\dcode-project\bin\dcode.exe --version` matches that pin; reject PATH fallback.
- [x] Step 3: Create fixture root and run `C:\Users\HOANG PHI LONG DANG\.local\bin\dcode-project.ps1 --role normal --no-mcp --json --no-stream --max-turns 4 --timeout 120 -n "Return exactly <unique-marker>"`; repeat without `--no-stream`; capture direct child exit separately from task marker.
- [x] Step 4: Run Herdr with `py scripts/herdr_main_launcher.py --profile normal --session auto --pane auto --cwd <probe-root> --expected-base <fixture-commit> --executor deepagents --grant-turns 4 --grant-wall-clock-seconds 120 --task "Return the requested result" --name <probe-name>`; launcher injects current run marker/report instructions; capture delivery exit separately from terminal task state, process observation, report marker, and pane read. Auto-discovery first classified `not_found`; a task-owned Herdr workspace and explicit pane rerun produced `completed` evidence.
- [x] Step 5: Run invalid-role failure, stale/foreign-marker, and failed `pane read`/`process-info` proofs; verify nonzero/classified result, stale marker becomes `no-report`, observer errors cannot become completion, process cleanup, post-probe Git status, and exact-root cleanup. Preserve redacted evidence in `.tmp-tests\\deepagents-probes` before cleanup; delete only exact successful disposable roots.
- [x] Step 6: Classify every result using evidence precedence: wrapper/config failure, `provider-transport-failure` for `OpenAIConnectionError`/transport stderr or request trace, `child-nonzero` for task-process nonzero without provider evidence, `timeout` only after cleanup proof, `no-report` for missing/uncertain terminal evidence, `encoding-failure` for failed UTF-8 decode, otherwise `completed` only under the explicit completion gate.

**Verification:**
- [x] Supported diagnostic, discovery, direct task, Herdr, and failure probes execute or return a classified blocker; none is silently skipped.
- [x] Direct completion is claimed only for direct task exit `0`, unique marker in final output, pinned version matching canonical setup pin, and absent `.deepagents/` state.
- [x] Herdr completion is claimed only when pane-run delivery exit is recorded separately, terminal state is `completed`, `COMPLETED` and current injected marker are present, both observations are clean (`observation_error == None`), pinned version matches canonical setup pin, and `.deepagents/` is absent.
- Expected: UTF-8 output decodes cleanly when non-ASCII bytes are emitted; delivery-only, no-report, provider, observer-error, invalid-role, and unmanaged-runtime outcomes never become completion.

**Exit Criteria:**
- Runtime acceptance is evidence-backed; external provider failures remain distinct from launcher defects.

### Task 4: Final verification

**Purpose:**
- Reconcile source, tests, generated surfaces, plan state, and preserved workspace state.

**Task Function:**
- Fresh final verification and plan closure.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: controller owns final acceptance.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent scope and evidence check.

**Specification Coverage:**
- Focused, broad, contract, drift, and diff checks pass.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all changed files, plan, generated Codex surfaces, probe evidence, Git state
- Verify: commands below and before/after untracked path/content snapshots

**Dependencies:**
- Tasks 1–3 complete.

**Authority:**
- Preauthorized local actions: run final verification commands and update plan evidence/status.
- Stop for: failed proof, stale generated output, unexpected tracked changes, or branch disposition request.

**Steps:**
- [x] Step 1: Run focused and broad Project OS tests.
- [x] Step 2: Run repository/config/drift validators and `git diff --check`.
- [x] Step 3: Compare before/after `git status --short --untracked-files=all`; verify `.playwright-mcp/` and `db/` path sets/content remain unchanged.
- [x] Step 4: Mark plan `completed` only after fresh verification returns `verified`.

**Verification:**
- [x] `py -m pytest tests/test_dcode_project.py tests/test_herdr_main_launcher.py tests/test_runtime_tool_resolution_contract.py tests/test_starter_kit_generation.py tests/test_validate_repo_config.py -q` (`187 passed`)
- [x] `py scripts/validate_repo_contracts.py --repo-root . --fast`
- [x] `py scripts/validate_repo_config.py --repo-root .`
- [x] `py scripts/validate_agent_runtime_drift.py --platform codex`
- [x] `git diff --check`
- [x] Before/after untracked path/content comparison for `.playwright-mcp/` and `db/`
- Expected: all checks pass; unrelated tracked and untracked files remain untouched.

**Exit Criteria:**
- Plan evidence and repository truth agree; no unresolved required task or unrecorded deviation remains.

## Verification

- `py -m pytest tests/test_dcode_project.py tests/test_herdr_main_launcher.py tests/test_runtime_tool_resolution_contract.py tests/test_starter_kit_generation.py tests/test_validate_repo_config.py -q`
- `py scripts/validate_repo_contracts.py --repo-root . --fast`
- `py scripts/validate_repo_config.py --repo-root .`
- `py scripts/validate_agent_runtime_drift.py --platform codex`
- `git diff --check`
- native `dcode-doctor.cmd`, direct disposable-root `dcode-project`, Herdr, and invalid-role probes with captured evidence

## Completion Criteria

The plan is ready for completion verification when:

1. Canonical `dcode-doctor` wrapper sets UTF-8 environment before invocation.
2. Focused test protects assignment ordering.
3. Codex shared runtime and generated adapter surfaces are synced and drift-free.
4. Separate diagnostic, discovery, buffered, streaming, Herdr, and failure probes produce classified evidence.
5. Completion requires exit `0`, current run marker, exact `COMPLETED` terminal pair, clean observation, pinned version, and no `.deepagents/` state.
6. Direct unmanaged `dcode doctor` remains unsupported acceptance.
7. JOB-PROJECT, Scan, and LightMem2 remain untouched and out of scope.
8. `.playwright-mcp/` and `db/` remain untouched and untracked.
9. Fresh final verification passes before plan status changes to `completed`.

## Execution Evidence

- Plan review: two `xhigh` reviewers and one `review` reviewer assigned; user
  requested final review be skipped.
- Initial review findings incorporated: hard LightMem2 non-goal, exact codex
  destinations, temporary fixture roots, Herdr coverage, failure cleanup,
  preservation snapshots, and current marker-binding ceiling.
- Plan accepted by user; source/test fix, codex sync, probes, cleanup, and final
  verification completed.
- Root cause found during live Herdr probe: multiline completion instructions
  were split by pane transport, so `dcode-project` never launched. Fixed by
  keeping injected instructions single-line.
- Second runtime mismatch found: DeepAgents appends usage footer after the
  `COMPLETED`/marker pair. Fixed completion parsing to accept the verified pair
  with trailing runtime output while retaining run-scoped marker and observer
  gates.
- Evidence: `supported-boundary-20260909-100538/evidence.json`,
  `direct-20260909-100635/evidence-precleanup.json`, and
  `herdr-20260909-102223/launcher-final.stdout.txt` under
  `.tmp-tests/deepagents-probes/`. Final Herdr status: `completed`, delivery
  confirmed, report present, observation clean, exit `0`; invalid-role probe
  exit `2`; exact disposable roots and task metadata cleaned.
