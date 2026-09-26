---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: ocr-delegation-hardening
targets:
  - scripts/ocr_delegate_adapter.py
  - scripts/owned_process.py
  - scripts/review_content_policy.py
  - scripts/validate_env_gitignore_contract.py
  - scripts/dcode_project.py
  - tests/test_ocr_delegate_adapter.py
  - tests/test_owned_process.py
  - tests/test_review_content_policy.py
  - tests/test_dcode_project.py
  - tests/test_skill_subagent_driven_development_assets.py
  - tests/fixtures/ocr_delegate/preview-v1.json
  - tests/fixtures/ocr_delegate/rules-v1.json
  - docs/operating_system/procedures/ocr-delegation-procedure.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - .agents/skills/skill-requesting-code-review/SKILL.md
  - .agents/skills/skill-requesting-code-review/code-reviewer.md
  - .agents/skills/skill-reviewing-pull-requests/SKILL.md
  - .agents/skills/skill-subagent-driven-development/SKILL.md
  - .agents/skills/skill-subagent-driven-development/task-reviewer-prompt.md
  - .agents/skills/skill-subagent-driven-development/scripts/review-package
  - generated_agents/codex/skills/skill-requesting-code-review/SKILL.md
  - generated_agents/codex/skills/skill-requesting-code-review/code-reviewer.md
  - generated_agents/codex/skills/skill-reviewing-pull-requests/SKILL.md
  - generated_agents/codex/skills/skill-subagent-driven-development/SKILL.md
  - generated_agents/codex/skills/skill-subagent-driven-development/task-reviewer-prompt.md
  - generated_agents/codex/skills/skill-subagent-driven-development/scripts/review-package
  - generated_agents/claude/skills/skill-requesting-code-review/SKILL.md
  - generated_agents/claude/skills/skill-requesting-code-review/code-reviewer.md
  - generated_agents/claude/skills/skill-reviewing-pull-requests/SKILL.md
  - generated_agents/claude/skills/skill-subagent-driven-development/SKILL.md
  - generated_agents/claude/skills/skill-subagent-driven-development/task-reviewer-prompt.md
  - generated_agents/claude/skills/skill-subagent-driven-development/scripts/review-package
  - generated_agents/antigravity/skills/skill-requesting-code-review/SKILL.md
  - generated_agents/antigravity/skills/skill-requesting-code-review/code-reviewer.md
  - generated_agents/antigravity/skills/skill-reviewing-pull-requests/SKILL.md
  - generated_agents/antigravity/skills/skill-subagent-driven-development/SKILL.md
  - generated_agents/antigravity/skills/skill-subagent-driven-development/task-reviewer-prompt.md
  - generated_agents/antigravity/skills/skill-subagent-driven-development/scripts/review-package
  - repo_config/starter-kit-manifest.json
---

# OpenCodeReview Delegation Hardening

## Verdict Review

**Review verdict:** revise once more, then implement.

The supplied verdict preserves correct architecture: OCR stays optional,
range-only, schema-gated, externally installed, and advisory. Eight justified
corrections remain before another implementation pass:

- Bound Git validation, version probing, preview, and rule resolution under one
  deadline; terminate the complete OCR process tree on timeout.
- Derive complete inventory from the exact Git range. Caller inventory, when
  supplied, must equal that complete review-path set; subset review is deferred.
- Preserve exclusion reasons. `secret_exclude` paths remain accounted for but
  their contents never enter native LLM review.
- Preserve OCR rule provenance. Canonical Project OS rules outrank OCR; only
  `system` OCR rules become advisory hints in this slice. OCR
  project/custom/global rules remain data.
- Pass `--from BASE --to HEAD` to `delegate rule`, matching `delegate preview`.
- Replace mutable `_last_reason` and text-mode decoding with explicit bounded
  subprocess results. Handle `null`, non-object JSON, invalid UTF-8, nonzero
  exit, timeout, and oversized output as stable fallback reasons.
- Preserve independently validated range identity and Git inventory on fallback;
  discard incomplete OCR partitions and rules.
- Make opt-in live compatibility tests fail closed and cover deletion,
  rename/copy, exclusions, and `-leading-name` paths.
- Make protected-content policy Project OS-owned and apply it before OCR,
  including both old and new paths for renames and copies.
- Scope `review-package` to exact approved inventory and omit protected content;
  this also excludes preserved unrelated untracked files.
- Extract one small owned-process primitive for OCR and `dcode_project.py`.
  Timeout and output overflow terminate its process tree; unconfirmed cleanup is
  `BLOCKED`, not native fallback.
- Remove caller-subset semantics for this slice: caller paths must equal the
  complete Git-derived review-path set.
- Separate executor (`codex`) from registered template profiles and validators.
- Regenerate and check all managed platforms, not only default `codex` output.
- Use system-only OCR hints now. Retain project/custom/global provenance as
  data; defer configurable trust until a real owner and identity contract exist.
- Add independent final review over frozen scoped package and inventory digests.

Keep range-only OCR. Do not add managed mode, workspace mode, hooks, installer
logic, OCR package files, an OCR fork, or a new process framework.

## Goal

Harden existing `scripts/ocr_delegate_adapter.py` so immutable Git-range review
keeps Git as identity and inventory authority, contains subprocess failure,
protects secret exclusions, preserves rule trust boundaries, and hands the
existing reviewer a complete `prepared` or identity-preserving `fallback`
manifest.

## Implementation Outcomes

### Safe adapter contract

Adapter validates and derives the selected inventory from `base_sha..head_sha`,
passes exact range identity to both OCR commands, bounds the full preparation
lifecycle, terminates descendants on timeout, and returns stable fallback
reasons without partial OCR evidence.

### Trust-preserving review handoff

Project OS content policy classifies protected environment/private/local paths
before OCR. Preparation output retains OCR exclusion evidence and rule
provenance. A scoped `review-package` consumes exact inventory plus policy,
omits protected content and unrelated untracked files, and produces the frozen
artifact consumed through one `[REVIEW_PREPARATION_FILE]` handoff.

### Compatibility proof

Focused offline tests and one opt-in live test prove schema compatibility,
Git-range behavior, output/error handling, process cleanup, exclusion policy,
rule provenance, Windows executable discovery, and coverage for added,
modified, deleted, renamed, copied, unsupported, binary, excluded, and
`-leading-name` paths. Generated agent views remain synchronized from canonical
skill sources.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: skill-chief-of-staff, skill-executing-plans, skill-writing-plans, skill-systematic-debugging, skill-test-driven-development, skill-backend-verification, skill-code-standards, skill-verification-before-completion
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed canonical files, update fixtures and focused tests, run declared local validation, regenerate all managed agent views, and create temporary scope/package artifacts
- User-approval actions: push, merge, publication, destructive cleanup, discard of preserved untracked files, or external OCR installation changes
- Parallel ownership: none; adapter, tests, docs, and generated sync share contract changes
- Sequential fallback: Task 1 → Task 2 → Task 3 → Task 4

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `053a8c94df1b161a3f87c94c3b329388a358a918`
- Expected workspace: `main` with preserved untracked `.playwright-mcp/`, `db/`, and the completed OCR integration plan
- Next action: none; Tasks 1–4 verified
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | completed | current | codex | none | focused adapter/runtime tests | Herdr lane `duplicate-owner-hardening`: root cause confirmed in `scripts/owned_process.py`; `167 passed, 1 skipped`; `py_compile` and `git diff --check` passed |
| Task 2 | completed | current | `codex` | Task 1 | exclusion/trust contract tests | Herdr lane `ocr-hardening-task-2`; `45 passed, 1 skipped`; `py_compile`, env gitignore validation, and `git diff --check` passed; generated views deferred to Task 3 |
| Task 3 | completed | current | `codex` | Task 1, Task 2 | docs and generated-surface checks | Herdr lane `ocr-hardening-task-3`; `38 passed, 1 skipped`; opt-in live compatibility `1 passed`; all-platform sync and sync check passed; `git diff --check` passed |
| Task 4 | completed | current | `codex` | Task 1–3 | full suite and opt-in live proof | Herdr lane `ocr-hardening-task-4`; focused `102 passed, 1 skipped`; full `689 passed, 1 skipped`; validators passed; scoped package/inventory frozen; independent retry reviewer `PASS` |

## Task Breakdown

### Task 1: Make Git and subprocess boundaries authoritative

**Purpose:**
- Remove inventory ambiguity and make every OCR preparation failure bounded and deterministic.

**Task Function:**
- Harden immutable-range validation, Git inventory derivation, process lifetime, output decoding, and fallback construction.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: backend boundary, Windows process-tree behavior, Git identity, and failure-state correctness.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independently check caller impact, timeout behavior, and contract-preserving fallback.

**Specification Coverage:**
- Exact `base_sha..head_sha` is source of inventory truth.
- Caller inventory, when supplied, must equal the complete Git-derived review-path set; subset review is deferred.
- Valid copy cases may reuse an old path across entries; review-path uniqueness remains enforced.
- Git identity/inventory failures remain contract errors; OCR capability/output failures remain native fallback.
- One deadline covers Git checks, version, preview, and all rule batches.
- OCR and `dcode_project.py` use one small owned-process primitive with explicit
  success, timeout, output-limit, nonzero-exit, spawn-failure, and
  cleanup-unconfirmed outcomes.
- Timeout and output overflow terminate the complete child process tree. If
  cleanup cannot be confirmed, surface hard lifecycle failure as `BLOCKED`;
  never continue as native fallback.
- Every invocation sets `OCR_NO_UPDATE=1`.
- `delegate rule` receives `--from`, `--to`, and `--` before paths.
- Explicit subprocess result distinguishes success, timeout, command failure, output limit, decode failure, and JSON failure.
- Fallback retains only validated repository, range, canonical inventory/digest, executable, and observed version facts.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/ocr_delegate_adapter.py:GitInventoryEntry`, `validate_input`, `OcrDelegateAdapter.prepare`, `_run`, `_run_json`, `_run_jsonless`
- Inspect: `scripts/dcode_project.py:_run_bounded_worker`, `_kill_windows_process_tree`
- Create: `scripts/owned_process.py:run_owned_process`
- Modify: `scripts/dcode_project.py:_run_bounded_worker` and `scripts/ocr_delegate_adapter.py:inventory derivation, deadline handling, subprocess result, fallback result`
- Verify: `tests/test_owned_process.py`, `tests/test_dcode_project.py`, and `tests/test_ocr_delegate_adapter.py`

**Dependencies:**
- Current `main` at `053a8c94df1b161a3f87c94c3b329388a358a918`.
- Existing adapter schema and `prepared|fallback` result contract.

**Authority:**
- Preauthorized local actions: modify adapter and focused adapter tests, inspect existing process-lifetime code, and run `python -m pytest -q tests/test_ocr_delegate_adapter.py`
- Stop for: changed accepted range semantics, missing process-tree proof, unrelated runtime failures, or required external installation/authentication

**Steps:**
- [x] Step 1: Add failing tests for complete Git-derived inventory, valid copy/rename/deletion identity, exact rule range flags, deadline coverage, descendant cleanup, invalid UTF-8, `null`, non-object JSON, oversized output, identity-preserving fallback, and `BLOCKED` cleanup failure.
- [x] Step 2: Derive canonical inventory with NUL-delimited Git range diff/status output, explicit rename/copy detection, and both old/new path identity; require caller paths to equal the complete review-path set.
- [x] Step 3: Extract `scripts/owned_process.py:run_owned_process` with POSIX process-group and Windows Job Object ownership, bounded stdout/stderr, and confirmed tree termination.
- [x] Step 4: Migrate `dcode_project.py` and the OCR adapter to the helper; replace mutable `_last_reason` and text-mode decoding with explicit bytes/results.
- [x] Step 5: Thread one deadline through Git and OCR calls, pass range flags to rules, and construct fallback from validated facts only.
- [x] Step 6: Run focused tests and inspect diff for no new installer, hook, model, or managed-mode path.

Root-cause follow-up: Windows Job Object cleanup was treated as successful when
the close operation failed, and timeout cleanup released the same job handle
twice. The shared helper now closes each handle once and reports
`cleanup_unconfirmed` as `BLOCKED`; text input is encoded before byte capture.
Shared callers were `scripts/dcode_project.py` and
`scripts/ocr_delegate_adapter.py`. Herdr launcher and parallel dispatcher use
separate subprocess paths; no matching defect was confirmed there.

**Verification:**
- [x] `python -m pytest -q tests/test_ocr_delegate_adapter.py`
- [x] `python -m pytest -q tests/test_owned_process.py tests/test_dcode_project.py tests/test_ocr_delegate_adapter.py` — `167 passed, 1 skipped`
- [x] `py -m py_compile scripts/owned_process.py scripts/dcode_project.py scripts/ocr_delegate_adapter.py scripts/herdr_main_launcher.py scripts/herdr_parallel_dispatch.py`
- [x] `git diff --check`
- Expected: all focused tests pass; valid copy cases no longer fail duplicate-path validation; ordinary OCR failures fallback; cleanup uncertainty blocks; no timed-out or overflowed descendant survives.

**Exit Criteria:**
- Adapter has one authoritative range/inventory path, bounded process lifecycle, explicit result handling, exact rule identity, and no partial fallback evidence.

### Task 2: Preserve exclusions and rule trust boundaries

**Purpose:**
- Prevent protected OCR exclusions and branch-controlled rule text from becoming unsafe reviewer input.

**Task Function:**
- Extend normalized preparation metadata and canonical review-consumer instructions without changing verdict ownership.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: security boundary and cross-artifact review contract.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: verify protected-path non-disclosure, provenance handling, and canonical-rule precedence.

**Specification Coverage:**
- Project OS owns content eligibility before OCR. Reuse one security SSOT for
  `.env`, `.env.*`, `*.private.*`, and `*.local.*` path protection; do not copy
  OCR's secret-pattern list.
- Evaluate both old and new paths for renames and copies. A protected old path
  remains protected after rename or copy.
- Preserve `exclude_reason` as additional OCR evidence and expose protected
  paths separately from ordinary exclusions.
- All changed paths remain accounted for; ordinary exclusions use documented
  semantic/native handling; protected paths are never loaded into LLM review.
- Preserve OCR `source` provenance (`system`, `project`, `custom`, `global`) as data.
- Canonical Project OS rules outrank OCR rules. Only `system` OCR rules may
  become advisory reviewer hints; `project`, `custom`, and `global` rules stay
  provenance-bearing data and are never promoted to instructions in this slice.
- Requester writes one preparation JSON file and passes `[REVIEW_PREPARATION_FILE]`; reviewer verifies `base_sha`, `head_sha`, inventory digest, and preparation status before consuming hints.
- Scoped `review-package` consumes exact inventory plus content policy, includes
  metadata for protected entries, omits protected content, and excludes
  unrelated untracked files.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/validate_env_gitignore_contract.py:REQUIRED_ENTRIES`, `scripts/ocr_delegate_adapter.py:PreparationResult`, `reconcile_preview`, `normalize_rules`
- Create: `scripts/review_content_policy.py:protected path policy`
- Modify: `scripts/validate_env_gitignore_contract.py:shared security-pattern import`
- Modify: `scripts/ocr_delegate_adapter.py:exclusion metadata`
- Modify: `tests/test_review_content_policy.py`, `tests/test_ocr_delegate_adapter.py:protected old/new paths and provenance assertions`
- Modify: `.agents/skills/skill-subagent-driven-development/scripts/review-package:scoped inventory/content-policy input`
- Modify: `tests/test_skill_subagent_driven_development_assets.py:scoped package and protected-content assertions`
- Modify: `.agents/skills/skill-requesting-code-review/SKILL.md:Optional OCR Preparation`
- Modify: `.agents/skills/skill-requesting-code-review/code-reviewer.md:Review Evidence Identity and OCR handoff`
- Modify: `.agents/skills/skill-reviewing-pull-requests/SKILL.md:PR-specific identity and OCR boundary`
- Modify: `.agents/skills/skill-subagent-driven-development/SKILL.md`, `.agents/skills/skill-subagent-driven-development/task-reviewer-prompt.md:review-package invocation`
- Verify: all generated platform projections listed in plan frontmatter

**Dependencies:**
- Task 1 result contract and canonical inventory.
- Existing OCR v1 preview/rules fixtures.

**Authority:**
- Preauthorized local actions: modify listed policy, package, canonical skill, adapter, and test files, regenerate all managed agent views, and run focused tests
- Stop for: exposing protected file contents, adding trust configuration without an owning contract, direct edits to generated files, or changing PASS/FAIL/BLOCKED ownership

**Steps:**
- [x] Step 1: Add failing policy tests for protected basenames, nested paths, old/new rename and copy paths, and non-protected ordinary files.
- [x] Step 2: Make `scripts/review_content_policy.py` the shared security-pattern SSOT and make `validate_env_gitignore_contract.py` consume it.
- [x] Step 3: Add adapter tests and metadata for OCR exclusion reasons; treat `secret_exclude` as corroborating evidence, never protection authority.
- [x] Step 4: Extend `review-package` with required scoped inventory/content-policy input; emit status metadata only for protected entries and omit their content and unrelated untracked files.
- [x] Step 5: Add `[REVIEW_PREPARATION_FILE]` handoff and identity verification; enforce system-only OCR hints and canonical-rule precedence.
- [x] Step 6: Keep PR review exact-head semantics; state working-tree SDD task review uses scoped native review package, while final committed-range review may prepare OCR once.
- [x] Step 7: Regenerate all managed agent views and run all-platform sync checks.

**Verification:**
- [x] `python -m pytest -q tests/test_ocr_delegate_adapter.py`
- [x] `python -m pytest -q tests/test_review_content_policy.py tests/test_skill_subagent_driven_development_assets.py`
- [x] `python scripts/sync_agent_adapters.py --all-platforms`
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: protected paths are accounted for without content disclosure; old/new protected paths stay protected; untrusted OCR rule text cannot become instructions; scoped package excludes unrelated untracked files; all generated views match canonical sources.

**Exit Criteria:**
- Preparation metadata and review instructions enforce exclusion protection, rule provenance, one-file handoff, and exact identity checks.

### Task 3: Make procedure and fixtures operationally complete

**Purpose:**
- Keep operational documentation and compatibility fixtures aligned with actual adapter behavior.

**Task Function:**
- Replace duplicated implementation prose with one consumer-facing procedure and deterministic fixture coverage.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: contract documentation, fixture fidelity, and generated-surface ownership.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: verify docs describe executable behavior without duplicating version or schema SSOT.

**Specification Coverage:**
- Normal consumer invokes Project OS adapter, not direct OCR commands.
- Procedure documents prepared/fallback/contract-error interpretation, identity fields, schema compatibility, rule trust, protected exclusions, `OCR_NO_UPDATE=1`, and exact live-test command.
- Remove unused `OCR_TESTED_VERSION`; observed executable version remains runtime provenance and no operational document hard-codes a release.
- `runtime-surfaces.md` stays a short ownership/link entry.
- Fixtures cover code, Markdown, tests, unsupported extension, binary, exclusion, deletion, rename, copy, and `-leading-name` path cases.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `tests/fixtures/ocr_delegate/preview-v1.json`
- Modify: `tests/fixtures/ocr_delegate/rules-v1.json`
- Modify: `tests/test_ocr_delegate_adapter.py:fixture and live compatibility tests`
- Modify: `docs/operating_system/procedures/ocr-delegation-procedure.md`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: `repo_config/starter-kit-manifest.json:shared adapter, process, and content-policy paths`

**Dependencies:**
- Tasks 1–2 normalized fields and reviewer contract.

**Authority:**
- Preauthorized local actions: update listed fixtures, tests, and docs, run fixture/live checks, and inspect starter-kit inclusion
- Stop for: changing public distribution scope, adding OCR binaries/credentials, network or LLM-dependent tests, or duplicate operational SSOT

**Steps:**
- [x] Step 1: Expand offline fixtures and assertions for all listed path classes and provenance/exclusion metadata.
- [x] Step 2: Add opt-in live test behavior where `PROJECT_OS_OCR_LIVE_TEST=1` fails when `ocr` is missing or incompatible; ordinary runs may skip only because opt-in is absent.
- [x] Step 3: Build temporary Git range containing deletion, rename/copy, exclusion, and `-leading-name` cases; prove preview/rule range identity and coverage.
- [x] Step 4: Thin procedure/runtime docs around adapter ownership and link canonical review-package path under `.agents/skills/skill-subagent-driven-development/scripts/review-package`.
- [x] Step 5: Remove dead tested-version constant and repeated release text; keep schema compatibility as the only OCR compatibility gate.
- [x] Step 6: Confirm manifest distributes adapter, owned-process helper, and content-policy helper as shared paths, without OCR binaries or credentials.

**Verification:**
- [x] `python -m pytest -q tests/test_ocr_delegate_adapter.py`
- [x] `$env:PROJECT_OS_OCR_LIVE_TEST='1'; python -m pytest -q tests/test_ocr_delegate_adapter.py -k live`
- [x] `python scripts/sync_agent_adapters.py --all-platforms`
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: offline tests pass; opt-in live test passes with compatible OCR and fails closed when executable or contract is unavailable; no network or model call occurs; all platform projections match canonical sources.

**Exit Criteria:**
- Docs, fixtures, live-test gate, and distribution manifest describe one stable adapter contract with no version drift.

### Task 4: Final acceptance proof

**Purpose:**
- Prove no regression across adapter, generated surfaces, planning lifecycle, and repository behavior.

**Task Function:**
- Run fresh final verification and reconcile plan scope against Git.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: final acceptance, generated output reconciliation, and repository-wide regression risk.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent final evidence review.

**Specification Coverage:**
- All task-local proof is fresh and complete.
- Generated views derive from canonical skills.
- No preserved untracked state is deleted or modified without ownership.
- Independent final review consumes exact scoped package, package SHA-256, and inventory SHA-256.
- Any package or inventory digest change invalidates review evidence and requires rerun.
- No unresolved required task, stale generated output, or undocumented deviation remains.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all changed files from Tasks 1–3
- Verify: `.playwright-mcp/`, `db/`, and prior completed plan remain untouched

**Dependencies:**
- Tasks 1–3 completed and focused proof accepted.

**Authority:**
- Preauthorized local actions: run final read-only checks, build disposable scoped review package, inspect Git diff/status, and record evidence in this plan
- Stop for: unrelated changes, failed required proof, stale generated outputs, or any need to discard preserved untracked state

**Steps:**
- [x] Step 1: Run focused adapter tests and all-platform generated-surface check again.
- [x] Step 2: Run actual repository, planning, environment-security, and full test validators.
- [x] Step 3: Derive exact approved working-tree inventory and apply Project OS content policy.
- [x] Step 4: Build scoped frozen review package; include protected path/status metadata, omit protected content and unrelated untracked files; record package and inventory SHA-256 values.
- [x] Step 5: Dispatch independent final reviewer with `[REVIEW_PREPARATION_FILE]`, exact package path, base/head, and both digests.
- [x] Step 6: Reject stale review evidence when either digest changes; record reviewer `PASS`, `FAIL`, or `BLOCKED`.
- [x] Step 7: Inspect `git diff --check`, changed-file scope, and preserved untracked state; do not merge or clean branches from this plan.

**Verification:**
- [x] `python scripts/sync_agent_adapters.py --all-platforms`
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `python scripts/validate_repo_config.py`
- [x] `python scripts/validate_repo_contracts.py`
- [x] `python scripts/validate_env_gitignore_contract.py`
- [x] `python scripts/validate_planning_lifecycle.py`
- [x] `python -m pytest -q tests/test_ocr_delegate_adapter.py tests/test_owned_process.py tests/test_review_content_policy.py tests/test_skill_subagent_driven_development_assets.py tests/test_starter_kit_generation.py tests/test_validate_planning_lifecycle.py`
- [x] `python -m pytest -q`
- [x] `git diff --check`
- [x] Independent reviewer returns `PASS` for exact reviewed head and scoped package digests.
- Expected: all required checks pass, generated surfaces are current, full suite preserves baseline behavior, review evidence is fresh, and only approved files change.

**Exit Criteria:**
- Fresh evidence supports implementation handoff; plan remains `proposed` until explicitly activated and later verified by the lead controller.

## Verification

- `python scripts/sync_agent_adapters.py --all-platforms`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_repo_config.py`
- `python scripts/validate_repo_contracts.py`
- `python scripts/validate_env_gitignore_contract.py`
- `python scripts/validate_planning_lifecycle.py`
- `python -m pytest -q tests/test_ocr_delegate_adapter.py tests/test_starter_kit_generation.py tests/test_validate_planning_lifecycle.py`
- `python -m pytest -q`
- `git diff --check`
- Independent final review: exact head, scoped package SHA-256, inventory SHA-256, and `PASS`.
- With OCR installed: `$env:PROJECT_OS_OCR_LIVE_TEST='1'; python -m pytest -q tests/test_ocr_delegate_adapter.py -k live`

## Completion Criteria

The plan is ready for completion verification when:

1. Git-derived inventory, Project OS-owned protected content policy, rule provenance, bounded
   subprocesses, exact range flags, and identity-preserving fallback are
   implemented and covered by focused tests.
2. Canonical review skills and procedure describe one preparation-file handoff,
   exact PR identity, native working-tree SDD review, and OCR trust boundaries.
3. Fixtures and opt-in live checks prove upstream-compatible behavior without
   network or LLM calls.
4. Scoped `review-package` output protects content and excludes unrelated
   untracked files; package and inventory digests bind independent review.
5. Generated agent views pass all-platform sync checks and starter-kit
   distribution contains only approved shared runtime paths, never OCR binaries
   or credentials.
6. Full verification is fresh, reproducible, and free of unresolved required
   work or scope drift.
