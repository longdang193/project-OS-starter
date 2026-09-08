---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: herdr-launcher-reliability
targets:
  - scripts/herdr_main_launcher.py
  - scripts/setup_deepagents_runtime.ps1
  - tests/test_herdr_main_launcher.py
  - tests/test_dcode_project.py
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - tests/test_runtime_tool_resolution_contract.py
---

# Herdr Launcher Reliability

## Goal

Remove false timeout failures, broken shared-runtime wrapper paths, and unsafe
pane eligibility from Starter launcher dispatch while preserving sequential
`auto` target acquisition, existing observation boundaries, and current
consumer working directories.

## Implementation Outcomes

### Reliable assignment state

`herdr_main_launcher.py` distinguishes assignment phase, failure kind, delivery
certainty, and reconciliation requirement. Compatibility states remain, but
`prompt_accepted` is never `false` when delivery is unknown. Uncertain delivery
produces reconciliation evidence and never triggers automatic lane termination
or replay.

### Consumer-safe DeepAgents wrappers

Generated `dcode-project` and `project-delegate` wrappers resolve the launcher
from the consumer repository when present, otherwise from the shared Project OS
installation. Both wrappers preserve caller working directory and return clear
failure output when neither source exists.

### Safe pane discovery

DeepAgents discovery accepts only panes compatible with its PowerShell launch
syntax. Missing or malformed process evidence blocks launch instead of treating
the pane as idle. Discovery keeps candidate rejection causes and a bounded
operation deadline.

### Economical runtime guidance

Runtime resolution documentation permits transient reuse of unchanged immutable
capability evidence and safe retry rules without weakening fresh Git, ownership,
or process checks required by CoS.

Asynchronous post-acceptance delivery is deferred. This patch keeps `--wait`
until Herdr acceptance and settlement ownership are directly verified.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Required skills: `skill-code-standards`, `skill-backend-verification`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit named launcher, wrapper, test, and runtime-documentation files; run focused tests and repository validators; inspect Herdr command contracts without installation or authentication
- User-approval actions: provider installation, authentication, external runtime writes, commits, pushes, merges, destructive cleanup, or changes outside listed targets
- Parallel ownership: none
- Sequential fallback: complete timeout contract before wrapper and discovery changes; complete focused tests before documentation and final validation

## Task Breakdown

### Task 1: Separate delivery certainty from timeout handling

**Purpose:**
- Prevent transport timeout text from being misclassified as execution deadline expiry or from triggering premature lane termination.

**Task Function:**
- Define launcher assignment-state contract and implement failure classification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded Python runtime change with existing tests and no delegation benefit.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent review of failure-state transitions and backward-compatible evidence.

**Specification Coverage:**
- Verdict findings 1 and 2, plus Runtime Grant evidence integrity.
- CoS sequential acquisition remains unchanged until Herdr acceptance semantics are proven.
- Missing, stale, or timed-out observation remains `unknown` and never authorizes kill, retry, or plan advancement.
- `assignment_task_sha256` remains original task identity; delivery evidence binds `delivery_task_sha256` and `grant_digest` to the projected Runtime Grant task.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_run`, `_codex_assignment_command`, `main`
- Inspect: `docs/operating_system/procedures/runtime-adapter-procedure.md:Herdr Observation`
- Modify: `scripts/herdr_main_launcher.py:_run`, assignment handling in `main`
- Modify: `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Existing Herdr observation commands remain `agent get`/`agent read` for Codex.
- Verify `agent prompt --wait` semantics before changing command sequencing. If Herdr exposes no distinct acceptance acknowledgment, retain `--wait`; do not remove it speculatively.

**Authority:**
- Preauthorized local actions: inspect source/docs, run available Herdr help or isolated command probes, edit listed Python/test files, run focused tests.
- Stop for: provider installation/authentication or changes to CoS policy outside launcher evidence. If Herdr acceptance semantics remain unavailable or undocumented, defer only Step 5; complete Steps 1–4 and 6.

**Steps:**
- [x] Step 1: Record current assignment phases and output keys; preserve existing keys while adding explicit failure kind, delivery certainty, runtime identity, and reconciliation requirement.
- [x] Step 2: Preserve original task identity, projected Runtime Grant, delivery-task identity, and grant digest. Make `assignment_request.redacted_prompt_argv` describe the projected delivery task.
- [x] Step 3: Replace substring-based timeout detection with typed transport timeout handling and separate `phase`, `failure_kind`, `delivery_certainty`, and `reconciliation_required` fields. Preserve compatibility states `transport_timeout`, `watchdog_expired`, `delivery_failed`, `delivery_uncertain`, and `delivered`. Use elapsed watchdog budget only for deadline expiry; do not add a cancellation API.
- [x] Step 4: On uncertain delivery, require existing Codex lane reconciliation through Herdr observation before any retry decision; do not terminate solely because transport failed.
- [x] Step 5: Deferred unless Herdr exposes a verified acceptance acknowledgment plus an independently owned post-acceptance watchdog, interruption behavior, and process-retirement cleanup proof. Keep `--wait` otherwise.
- [x] Step 6: Add regression tests for start-command failure, DeepAgents `pane run` failure, transport timeout with and without a numeric grant, watchdog expiry with cleanup success and failure, uncertain delivery, and delivery-task evidence.

**Verification:**
- [x] `py -m pytest tests/test_herdr_main_launcher.py -q`
- Expected: existing launcher tests pass; transport timeout does not call termination; watchdog expiry still returns exit code `124` only after verified cleanup.
- [x] Inspect emitted assignment JSON for each new failure state.
- Expected: phase, delivery certainty, runtime identity, and reconciliation status are machine-readable and consistent.

**Exit Criteria:**
- Transport failures cannot cause automatic execution timeout cleanup.
- Proven watchdog expiry retains current cleanup guarantees; cancellation remains outside this patch.
- No retry occurs without lane reconciliation evidence.

### Task 2: Resolve shared launcher paths in generated wrappers

**Purpose:**
- Make installed wrappers work for consumers that intentionally omit shared scripts from their local repository.

**Task Function:**
- Align wrapper generation with Starter shared-script ownership.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded PowerShell generation change with existing wrapper tests.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: consumer-boundary validation for local/shared path selection and cwd preservation.

**Specification Coverage:**
- Verdict finding 3.
- `repo_config/starter-kit-manifest.json` remains the SSOT for shared script ownership.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/setup_deepagents_runtime.ps1:$wrapper`, `$delegateWrapper`
- Inspect: `repo_config/starter-kit-manifest.json:sharedPaths.scripts`
- Modify: `scripts/setup_deepagents_runtime.ps1:$wrapper`, `$delegateWrapper`
- Modify: `tests/test_dcode_project.py:test_setup_launcher_uses_current_repository_source`, `test_generated_project_delegate_guard_returns_contract_exit_code`

**Dependencies:**
- Task 1 complete.
- Shared installation convention remains `~/.agents/project-os/scripts` as defined by repository instructions.

**Authority:**
- Preauthorized local actions: edit listed PowerShell/test files, generate wrappers in temporary test directories, run PowerShell subprocess tests when available.
- Stop for: changing installer layout, copying shared scripts into consumers, modifying manifest ownership model, or external installation/authentication.

**Steps:**
- [x] Step 1: Add one wrapper-local launcher resolver that checks consumer `<repoRoot>\scripts\dcode_project.py` first, then `$HOME\.agents\project-os\scripts\dcode_project.py`, without changing process cwd.
- [x] Step 2: Use the same resolver in both generated wrappers and preserve executor-specific flags and guard messages.
- [x] Step 3: Fail with an explicit missing-launcher message when neither path exists.
- [x] Step 4: Extend wrapper tests for local hit when both paths exist, shared fallback, missing source, paths containing spaces, executor flags, exit-code propagation, and cwd preservation. Run actual PowerShell wrapper execution when PowerShell is available.

**Verification:**
- [x] `py -m pytest tests/test_dcode_project.py -q`
- Expected: wrapper generation and existing guard tests pass; new consumer-without-local-script case invokes shared path.
- [x] `py scripts/validate_repo_config.py --repo-root .`
- Expected: manifest still validates with shared script ownership unchanged.

**Exit Criteria:**
- Both wrappers launch from local or shared source.
- No wrapper assumes `scripts/dcode_project.py` exists in every consumer repository.
- Consumer cwd remains unchanged.

### Task 3: Align pane eligibility with launch syntax and bound discovery

**Purpose:**
- Prevent DeepAgents launch commands from entering incompatible shells or panes with missing process evidence.

**Task Function:**
- Tighten pane validation and preserve useful discovery failure evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: localized launcher validation and discovery refactor.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent check of fail-closed eligibility and call-count behavior.

**Specification Coverage:**
- Verdict findings 4 and 5.
- Exact target validation and final live check remain intact.
- No reservation registry or monitoring subsystem is added.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_herdr_pane`, `_resolve_target_selector`
- Modify: `scripts/herdr_main_launcher.py:_herdr_pane`, `_resolve_target_selector`, executor call sites
- Modify: `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 1 complete.
- DeepAgents launch syntax remains PowerShell command syntax beginning with `&`.

**Authority:**
- Preauthorized local actions: edit listed Python/test files, run isolated JSON probe tests, measure Herdr command calls through existing mocks.
- Stop for: changing Herdr pane command semantics, adding shell-specific launchers beyond PowerShell, or adding persistent discovery state.

**Steps:**
- [x] Step 1: Keep `_resolve_target_selector()` responsible for one snapshot per discovery operation, cwd filtering, cheap candidate eligibility, and deterministic selection; keep `_herdr_pane()` responsible for final fresh exact-target validation.
- [x] Step 2: Pass executor-specific shell requirements into pane validation; require `powershell.exe` or `pwsh.exe` for DeepAgents while preserving the existing shell-only rule for Codex.
- [x] Step 3: Require `process_info` to be an object and `foreground_processes` to be a present list; missing or malformed evidence raises a distinct blocked/unknown result.
- [x] Step 4: Reuse one pane list during auto discovery, inspect candidate process details only for matching-cwd candidates, and keep the final `_herdr_pane` live check immediately before launch. Reuse applies across sessions represented in that snapshot.
- [x] Step 5: Validate every pane entry and define empty-list behavior. Preserve candidate rejection reasons separately from snapshot/schema/transport failures. Enforce one monotonic whole-discovery deadline and cap each subprocess timeout to remaining budget; expired or incomplete discovery is not definitive `not_found`.
- [x] Step 6: Add tests for non-PowerShell rejection, missing process evidence, malformed JSON, empty and malformed pane entries, rejection-cause retention, multiple sessions, exhausted discovery budget, target becoming busy before launch, and bounded call reuse.

**Verification:**
- [x] `py -m pytest tests/test_herdr_main_launcher.py -q`
- Expected: exact selector addressing remains unchanged; strengthened eligibility applies to exact and automatic selection. Auto selector fails closed on missing evidence and reports transport/schema failures distinctly.
- [x] Inspect mocked command-call count for multi-candidate auto discovery.
- Expected: pane list is reused; final live eligibility check still occurs before launch.

**Exit Criteria:**
- DeepAgents cannot launch through incompatible shell syntax.
- Missing process evidence never produces an idle/eligible result.
- Discovery remains deterministic, bounded, and observable without a new registry.

### Task 4: Add economical reuse and retry guidance

**Purpose:**
- Reduce repeated immutable capability checks and unsafe retries without weakening fresh execution identity checks.

**Task Function:**
- Update canonical runtime-tool policy and add contract assertions.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: documentation and contract-test maintenance.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: policy consistency against CoS and runtime procedure sources.

**Specification Coverage:**
- Verdict findings 6 and 7.
- CoS fresh checks for repository, worktree, branch, HEAD, ownership, profile, model, and process state remain mandatory.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `docs/operating_system/tooling/runtime-tool-resolution.md:Requirement Contract`, `Evidence Reuse`, `Security Boundary`, `Executor Boundary`
- Inspect: `docs/operating_system/procedures/runtime-adapter-procedure.md:Herdr Observation`, `Delivery Reconciliation`
- Inspect: `.agents/skills/skill-chief-of-staff/SKILL.md:Runtime Gates`, `Context Continuity And Dispatch Gate`
- Modify: `docs/operating_system/tooling/runtime-tool-resolution.md`
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Modify: `tests/test_runtime_tool_resolution_contract.py`

**Dependencies:**
- Tasks 1–3 complete.
- No generated adapter owns this runtime-tool document.

**Authority:**
- Preauthorized local actions: edit listed canonical doc/test files and run contract tests.
- Stop for: provider catalog additions, MCP permission changes, credential handling, or generated-surface edits.

**Steps:**
- [x] Step 1: Define reuse within one explicit controller turn only for executable version/hash, immutable CLI capability/help, static schema, unchanged config digest, and unchanged provider capability metadata.
- [x] Step 2: State that pane/process state, task assignment, Git HEAD/base, worktree, lane ownership, task authority, and delivery state are never reused merely from a prior turn.
- [x] Step 3: Add new `Delivery Reconciliation` guidance in `runtime-adapter-procedure.md`; require plausible transient failure, idempotency, and fresh write reconciliation before replay. Add new `Evidence Reuse` guidance in `runtime-tool-resolution.md`.
- [x] Step 4: Add contract assertions proving immutable capability evidence is cacheable while mutable execution identity remains fresh.

**Verification:**
- [x] `py -m pytest tests/test_runtime_tool_resolution_contract.py -q`
- Expected: new reuse/retry guidance passes without weakening existing observation and security rules.

**Exit Criteria:**
- Runtime policy gains reuse and retry rules without provider catalog or monitoring subsystem.
- Immutable evidence reuse is clearly separated from mutable execution identity.

## Verification

- `py -m pytest tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_runtime_tool_resolution_contract.py tests/test_starter_kit_generation.py tests/test_validate_repo_config.py -q`
- `py scripts/validate_repo_contracts.py --repo-root . --fast`
- `py scripts/validate_repo_config.py --repo-root .`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. Timeout classification no longer conflates transport failure with execution deadline.
2. Uncertain delivery produces reconciliation evidence and never causes automatic kill or replay.
3. Both generated wrappers work with local and shared launcher sources.
4. DeepAgents pane eligibility matches PowerShell launch syntax and fails closed on missing process evidence.
5. Auto discovery reuses safe snapshot evidence, preserves rejection causes, retains final live validation, and obeys one bounded deadline.
6. Runtime guidance adds safe evidence reuse and retry rules without weakening CoS freshness requirements.
7. Focused tests, repository validators, config validation, and diff checks pass.
8. Existing uncommitted `.playwright-mcp/` and `db/` remain untouched.
9. Asynchronous post-acceptance delivery remains explicitly deferred unless its watchdog and cleanup ownership are proven.

## Execution Evidence

- `413` repository tests passed on September 8, 2026.
- `validate_repo_contracts.py --fast`, `validate_repo_config.py`,
  `validate_planning_lifecycle.py`, and `git diff --check` passed.
- PowerShell wrapper tests passed when PowerShell was available.
- Asynchronous post-acceptance delivery remains deferred because Herdr
  acceptance and independent watchdog ownership are not verified.
