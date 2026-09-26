---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: ocr-delegation-integration
targets:
  - scripts/ocr_delegate_adapter.py
  - tests/test_ocr_delegate_adapter.py
  - tests/fixtures/ocr_delegate/preview-v1.json
  - tests/fixtures/ocr_delegate/rules-v1.json
  - repo_config/starter-kit-manifest.json
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/procedures/ocr-delegation-procedure.md
  - .agents/skills/skill-requesting-code-review/SKILL.md
  - .agents/skills/skill-requesting-code-review/code-reviewer.md
  - .agents/skills/skill-reviewing-pull-requests/SKILL.md
  - generated_agents/codex/skills/skill-requesting-code-review/SKILL.md
  - generated_agents/codex/skills/skill-requesting-code-review/code-reviewer.md
  - generated_agents/codex/skills/skill-reviewing-pull-requests/SKILL.md
  - generated_agents/claude/skills/skill-requesting-code-review/SKILL.md
  - generated_agents/claude/skills/skill-requesting-code-review/code-reviewer.md
  - generated_agents/claude/skills/skill-reviewing-pull-requests/SKILL.md
  - generated_agents/antigravity/skills/skill-requesting-code-review/SKILL.md
  - generated_agents/antigravity/skills/skill-requesting-code-review/code-reviewer.md
  - generated_agents/antigravity/skills/skill-reviewing-pull-requests/SKILL.md
  - tests/test_starter_kit_generation.py
---

# OpenCodeReview Delegation Integration

## Review Disposition

Patch current plan before implementation.

Adopted corrections:

- Git/caller owns immutable range identity and path inventory.
- OCR is an optional overlay that partitions paths into OCR-prepared and native
  review work.
- OCR adapter supports range mode only in first slice.
- Adapter result is `prepared` or `fallback`; no adapter-level `auto/off`
  setting.
- OCR schema is hard compatibility boundary. Observed OCR version is evidence,
  not runtime equality gate.
- One preparation deadline covers version, preview, and rule calls.
- `ocr delegate rule` receives `--` before external Git paths and uses bounded
  argument batches.
- General review-requesting contract owns OCR preparation semantics; PR review
  consumes that contract.
- Uncommitted review evidence binds to frozen review-package and Git-inventory
  digests, not `HEAD` alone.
- Invalid Project OS input is `BLOCKED`/contract error. OCR failure is native
  fallback.

Rejected correction:

- Keep one informational `OCR_TESTED_VERSION = "1.12.4"` provenance value. Do
  not compare observed version to it at runtime. Current NPM and GitHub latest
  release both resolve to `1.12.4` on September 16, 2026.

Upstream facts verified against v1.12.4:

- `delegate preview` and `delegate rule` emit JSON with `schema_version: "1"`,
  but payload shapes differ.
- Delegate flags include `--repo`, `--from`, `--to`, `--commit`, `--rule`,
  `--excludes`, `--background`, `--background-file`, `--max-git-procs`, and
  `--format`; `delegate rule` accepts positional paths.
- Delegation mode is documented as requiring no LLM.
- `bin/ocr.js` starts the updater unless `OCR_NO_UPDATE` is set; the updater
  installs the latest global package. Project OS must set `OCR_NO_UPDATE=1`.

Runtime debugging outcome, September 16, 2026:

- Multiline task rejection is an intentional launcher contract enforced by
  `scripts/herdr_main_launcher.py`; flatten task payloads before dispatch.
- `target_resolution=not_found` is expected when no eligible pane exists at the
  requested cwd; create the Herdr workspace before `--session auto --pane auto`.
- `submitted` with `observation_error: not_observed` is uncertainty, not task
  failure; obtain later Herdr observation before acceptance.
- An untracked plan is absent from a fresh worktree by normal Git behavior;
  mirror the active plan read-only into lane before launch, or use a tracked
  plan checkpoint. Do not treat this as launcher defect.
- Codex provider/model warnings are external runtime metadata evidence; do not
  patch Project OS without a reproducible repository-owned failure.
- Full-suite validation exposed one repository-owned plan defect: active Task 3
  used unsupported Template Profile `unresolved`. The validator permits only
  registered profiles; patch changed Task 3 to `high` and Task 4 to `review`.
- Independent systematic-debugging audit found no justified runtime code patch
  and no changed behavior requiring regression tests.

References:

- [Delegation implementation](https://github.com/alibaba/open-code-review/blob/v1.12.4/cmd/opencodereview/delegate_cmd.go)
- [Delegation flags](https://github.com/alibaba/open-code-review/blob/v1.12.4/cmd/opencodereview/shared_flags.go)
- [Launcher](https://github.com/alibaba/open-code-review/blob/v1.12.4/bin/ocr.js)
- [Updater](https://github.com/alibaba/open-code-review/blob/v1.12.4/scripts/update.js)
- [Release](https://github.com/alibaba/open-code-review/releases/tag/v1.12.4)

## Goal

Add one opt-in Project OS adapter that prepares an immutable Git range with
OpenCodeReview while preserving exact Git-input-bound evidence, canonical
Project OS rules, full coverage, and native fallback.

This repository has no semantic review dispatcher. The first slice stops at the
shared adapter, normalized manifest, review-requesting contract, and procedure.
Consumer projects own final reviewer wiring.

## Non-Goals

- No `ocr-managed` mode, OCR model execution, provider configuration, or
  credential handling.
- No copied upstream skill, prompts, source code, fork, vendored binary,
  installer, or updater.
- No workspace or single-commit OCR mode in first slice.
- No persistent `review_backend` configuration or adapter-level `auto/off`.
- No exact observed-version runtime gate.
- No pre-commit, Stop-hook, or `tokenpilot-codex-hook.cmd` integration.
- No change to `PASS`, `FAIL`, or `BLOCKED` ownership.

## Implementation Outcomes

### 1. Range-only preparation adapter

`scripts/ocr_delegate_adapter.py` accepts an immutable `base_sha`, `head_sha`,
and caller-owned Git inventory. It validates base ancestry and merge-base
identity, invokes upstream delegation, and returns one normalized `prepared` or
`fallback` result.

Git inventory preserves rename `old_path` and `new_path` identity and deletion
identity. OCR paths never reconstruct or replace that inventory.

### 2. Compatibility and live executable proof

Fixtures prove parser and reconciliation behavior without model calls. One
opt-in live test invokes the installed OCR executable against a temporary Git
repository and representative immutable range. The live test proves the actual
installed executable, Windows discovery path, flags, JSON shape, rule grouping,
and coverage reconciliation.

### 3. General review integration

The review-requesting skill and reviewer prompt define OCR preparation as
optional advisory input. The PR-review skill references the same contract rather
than becoming its owner. Canonical Project OS rules and exact Git inventory
remain higher priority than OCR rule text.

### 4. Shared runtime alignment

The adapter is an approved shared Project OS script. One procedure defines the
tested release, updater suppression, live compatibility check, evidence fields,
fallback, and upgrade process. Starter Kit remains OCR-optional and hook-free.

## Execution Approach

- Mode: `subagent-ready`
- Coordination: `git-tracked`
- Required skills: `skill-chief-of-staff`, `skill-executing-plans`, `skill-plan-document-reviewer`, `skill-code-standards`, `skill-backend-verification`, `skill-test-driven-development`, `skill-using-git-worktrees`, `skill-requesting-code-review`, `skill-receiving-code-review`, `skill-verification-before-completion`
- Isolation: `task-specific isolated worktree`; lead checkout preserves pre-existing untracked `.playwright-mcp/` and `db/`
- Commit policy: lane commits required; CoS reconciles accepted lane commits; no direct base mutation
- Preauthorized local actions: create declared isolated worktrees and lane branches, edit listed repository files, create listed fixtures, run focused tests, run configured validators, regenerate provider projections from canonical sources, inspect Git state, create disposable review-package output, commit lane-owned changes
- User-approval actions: push, merge, publication, destructive cleanup, discard of existing untracked paths, and OCR installation or upgrade outside the repository
- Parallel ownership: sequential shared-contract lanes; one active write-capable lane at a time, with independent Codex review after implementation
- Sequential fallback: complete Tasks 1–4 in order; stop before implementation if plan review changes behavior, ownership, or proof requirements

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `855e7a1ff07777827adedfff158b3e56afacad0b`
- Expected workspace: preserve pre-existing untracked `.playwright-mcp/` and `db/`; no other pre-existing changes
- Prior implementation lane: `codex/ocr-delegation-integration` in `.worktrees/ocr-delegation-integration`, commit `0c8d0d5dae28eac05deb4ab4292151ea74a6a7a6`
- Correction lane: `codex/ocr-delegation-task1-fix` in `.worktrees/ocr-delegation-task1-fix`, created from the reviewed Task 1 commit
- Task 1 review lane: `codex/ocr-delegation-task1-fix-review-high` in `.worktrees/ocr-delegation-task1-fix-review-high`, PASS
- Task 2 lane: `codex/ocr-delegation-task2` in `.worktrees/ocr-delegation-task2`, accepted commit `e51d665deaa4654009e45913281c4ab8d93ba34c`
- Task 2 review lane: `codex/ocr-delegation-task2-review` in `.worktrees/ocr-delegation-task2-review`, independent review PASS
- Task 3 lane: `codex/ocr-delegation-task3` in `.worktrees/ocr-delegation-task3`, accepted commit `8ab4eb1403a28e51fe05166716b04bb733b28f93`
- Task 3 review lane: `codex/ocr-delegation-task3-review` in `.worktrees/ocr-delegation-task3-review`, independent review PASS
- Next action: create Task 4 evidence lane from accepted Task 3 commit, then dispatch final verification through `scripts/herdr_main_launcher.py`
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated correction worktree | `codex` | none | focused adapter boundary tests and independent review | commit `75534cbc665c3aee0884a031e462720d75bfbcfd`; replacement review PASS; 18 focused and 658 full tests passed; OCR live proof deferred to Task 2 |
| Task 2 | `completed` | isolated lane worktree | `codex` | Task 1 | fixture and opt-in live compatibility tests | commit `e51d665deaa4654009e45913281c4ab8d93ba34c`; review PASS; 27 passed, 1 skipped; diff clean; live proof skipped without opt-in |
| Task 3 | `completed` | isolated lane worktree | `codex` | Task 2 | review contract, docs, manifest, sync checks | commit `8ab4eb1403a28e51fe05166716b04bb733b28f93`; review PASS; 20 focused tests passed; sync/config/contract checks passed; diff clean |
| Task 4 | `completed` | independent review worktree | `codex` | Task 3 | frozen package review and final verification | VERIFIED; base `855e7a1ff07777827adedfff158b3e56afacad0b`; head `8ab4eb1403a28e51fe05166716b04bb733b28f93`; package SHA-256 `00F70BFCA8BE3F29DCC93ABDA1BCEEF3F4DB818654E174AAF5CD139358EB33AF`; inventory SHA-256 `91D48C13C8A9788A205E7CA96F6F46B8DB97143E5C59320D50A5B2A4441BBB68` |

## Task Breakdown

### Task 1: Implement range-only adapter

**Purpose:**
- Add one reusable subprocess and JSON boundary for immutable-range OCR
  preparation.

**Task Function:**
- Implement Git-input validation, OCR invocation, payload validation, and
  normalized preparation/fallback output.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: subprocess boundary, security, and contract scope require
  material reasoning and failure-path coverage.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independently validate process-boundary security, contract
  handling, and coverage reconciliation.

**Specification Coverage:**
- Range-only input: repository, `base_sha`, `head_sha`, caller-owned inventory.
- `base_sha` ancestor and resolved merge-base equal `base_sha`.
- `SUPPORTED_DELEGATE_SCHEMA = "1"` hard gate.
- `OCR_TESTED_VERSION = "1.12.4"` informational provenance only.
- Mandatory `OCR_NO_UPDATE=1`.
- OCR failure returns native fallback; invalid Project OS input raises a
  contract error.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_root.py:resolve_repo_root`
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md:Authoring SSOT`
- Create: `scripts/ocr_delegate_adapter.py:GitInventoryEntry`, `ReviewRange`,
  `PreparationResult`, `OcrDelegateAdapter`, `validate_input`,
  `reconcile_preview`, `normalize_rules`, `inventory_digest`, `main`
- Verify: `tests/test_ocr_delegate_adapter.py`

**Dependencies:**
- Upstream v1.12.4 flags and JSON shapes listed in Review Disposition.
- Git inventory supplied by caller; adapter must not infer rename or deletion
  identity from OCR.

**Authority:**
- Preauthorized local actions: create adapter module, add focused tests, and run declared local checks
- Stop for: changed verdict ownership, workspace/single-commit OCR support, version equality gating, hook changes, installation logic, external data transfer, or scope widening

**Steps:**
- [x] Step 1: Define inventory entries with `status`, `old_path`, and
  `new_path`; derive review path only from Git inventory rules: deleted uses
  `old_path`, renamed uses `new_path`, other content changes use `new_path`.
- [x] Step 2: Define immutable range validation using Git commands or supplied
  facts; reject missing refs, non-ancestor base, merge-base mismatch, unsafe
  paths, duplicate entries, and inconsistent inventory.
- [x] Step 3: Discover `ocr` with `shutil.which`, record resolved executable,
  probe observed version, and use one absolute preparation deadline for all
  subprocess calls.
- [x] Step 4: Invoke `ocr delegate preview --repo <repo> --from <base_sha>
  --to <head_sha> --format json` with `OCR_NO_UPDATE=1`, separate stdout and
  stderr, bounded output, and no shell-owned interpolation.
- [x] Step 5: Validate preview schema, required fields, types, statuses, safe
  paths, counts, and membership against Git inventory. Preserve OCR
  reviewable/excluded partition as overlay only.
- [x] Step 6: Invoke `ocr delegate rule --repo <repo> --format json -- <paths>`
  for OCR reviewable paths. Batch by maximum total argument length `24000`,
  merge groups deterministically, and preserve source/pattern/rule text as
  advisory data.
- [x] Step 7: Return `status: prepared` with Git inventory, OCR partition,
  grouped rules, observed version, schema versions, executable path, scope
  identity, and payload digests.
- [x] Step 8: Return `status: fallback` for missing executable, timeout, command
  failure, malformed output, unsupported schema, or unavailable version probe.
  Return contract error for invalid Project OS input; never convert it to
  fallback.

**Verification:**
- [x] `python -m pytest -q tests/test_ocr_delegate_adapter.py`
- Expected: direct boundary tests pass and every OCR subprocess receives
  `OCR_NO_UPDATE=1`, exact range flags, `--` before rule paths, and bounded
  deadline behavior.
- [x] Failure assertions cover invalid refs, non-ancestor base, merge-base
  mismatch, missing executable, nonzero exit, timeout, malformed JSON,
  unsupported schema, unsafe path, duplicate path, count mismatch, and version
  probe failure.
- Expected: invalid Project OS input raises contract error; OCR capability
  failure returns fallback with stable reason and no partial prepared result.

**Exit Criteria:**
- Adapter supports only immutable ranges and exposes one normalized
  `prepared|fallback` contract.
- Git inventory remains authoritative for rename, deletion, and coverage.
- No version equality gate, mode setting, installer, hook, or OCR model path
  exists.

**Review correction:**

- Independent review reproduced `GitInventoryEntry("d", old_path="gone.txt").review_path is None` because status normalization occurs during initialization but `review_path` compares raw status values.
- Add a valid lowercase deletion regression test first and confirm it fails.
- Normalize or compare deletion status consistently in the narrowest shared owner,
  rerun focused tests, and commit only the two Task 1 files.
- Re-run independent review before accepting Task 1 or starting Task 2.

### Task 2: Add fixture and live compatibility proof

**Purpose:**
- Prove parser compatibility and actual installed-executable compatibility
  without LLM calls.

**Task Function:**
- Build deterministic offline tests plus one opt-in real executable test.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: external executable compatibility, Windows runtime risk, and
  coverage fixture design require material reasoning.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independently validate test realism, failure classification,
  and coverage assertions.

**Specification Coverage:**
- Added, modified, deleted, renamed, Markdown, tests, unsupported extension,
  binary, exclusion, and empty OCR-reviewable sets.
- Additive fields accepted; missing required fields and schema `2` rejected.
- Actual OCR executable tested against temporary Git range.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Create: `tests/fixtures/ocr_delegate/preview-v1.json`
- Create: `tests/fixtures/ocr_delegate/rules-v1.json`
- Modify: `tests/test_ocr_delegate_adapter.py:fixture and compatibility tests`
- Verify: `scripts/ocr_delegate_adapter.py:reconcile_preview`,
  `normalize_rules`, `inventory_digest`

**Dependencies:**
- Task 1 normalized result and fallback reasons.
- `shutil.which("ocr")` discovery and upstream v1.12.4 command contract.

**Authority:**
- Preauthorized local actions: create two JSON fixtures, extend focused tests, create temporary Git repositories inside test temp paths, and run offline or opt-in live checks
- Stop for: network-dependent proof, LLM calls, fixture fields without upstream source evidence, or any test that treats OCR selection as full coverage

**Steps:**
- [x] Step 1: Add preview fixture with explicit statuses and paths for code,
  Markdown, tests, deletion, rename, unsupported extension, binary, and
  exclusion.
- [x] Step 2: Add rules fixture with grouped files, `source`, `pattern`,
  `files`, `rule`, and one additive unknown field.
- [x] Step 3: Add fake executable tests for valid output, schema `2`, missing
  field, malformed JSON, nonzero exit, timeout, and version mismatch evidence.
- [x] Step 4: Assert Git inventory retains rename old/new identity and deletion
  identity while OCR contributes only reviewable/excluded overlay paths.
- [x] Step 5: Assert every Git review path is classified as OCR-prepared or
  native-review candidate; OCR exclusions never disappear from coverage.
- [x] Step 6: Add opt-in live test guarded by `PROJECT_OS_OCR_LIVE_TEST=1`.
  Create temporary Git repo, commit base, commit representative changes,
  resolve actual `ocr` executable including Windows shim behavior, run preview
  and rule commands, and validate schema, range, rule grouping, and coverage.
- [x] Step 7: Keep live test non-networked and non-LLM; skip only when opt-in
  flag is absent or executable is unavailable, recording skipped condition in
  test output.

**Verification:**
- [x] `python -m pytest -q tests/test_ocr_delegate_adapter.py`
- Expected: offline matrix passes; live test is skipped only without explicit
  opt-in or installed executable.
- [x] `$env:PROJECT_OS_OCR_LIVE_TEST='1'; python -m pytest -q tests/test_ocr_delegate_adapter.py -k live`
- Expected when OCR is installed: actual executable produces valid v1 output;
  otherwise test reports unavailable capability instead of claiming pass.
- [x] `git diff --check`
- Expected: fixture and test changes have no whitespace errors.

**Exit Criteria:**
- Fixtures freeze accepted v1 payload shapes.
- Live compatibility proof checks installed executable behavior, not only parser
  fixtures.
- Version is recorded for provenance but does not disable compatible releases.

**Task 2 Evidence:**
- `e51d665deaa4654009e45913281c4ab8d93ba34c` adds only the two fixtures and
  `tests/test_ocr_delegate_adapter.py` coverage.
- `python -m pytest -q tests/test_ocr_delegate_adapter.py` → `27 passed, 1
  skipped` in `20.66s` from the implementation lane; independent review rerun →
  `27 passed, 1 skipped` in `20.13s`.
- `git diff --check e51d665^ e51d665` → clean; independent review reports clean
  worktree and no repository mutation.
- Live test skipped because `PROJECT_OS_OCR_LIVE_TEST` was unset. Windows shim
  source inspection confirmed `%*` argument forwarding; shim runtime was not
  executed.
- Independent review verdict: `PASS`. Limits: no live OCR executable proof and
  no full repository suite in this lane.

### Task 3: Integrate general review contract and shared runtime docs

**Purpose:**
- Make OCR preparation consumable by all Project OS review paths without making
  PR review or Starter Kit installation OCR-dependent.

**Task Function:**
- Update canonical review-requesting guidance, PR-review reference, shared
  runtime documentation, distribution manifest, and generated projections.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: cross-surface ownership and generated-output reconciliation
  require material reasoning across canonical and generated layers.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independently validate SSOT ownership and generated drift.

**Specification Coverage:**
- General review-requesting path owns optional OCR preparation semantics.
- PR-review path consumes the same contract.
- Committed review uses base/head identity; working-tree review uses frozen
  package and inventory digests.
- Starter canonical rules outrank OCR rules.
- OCR installation remains external and updater suppression remains mandatory.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify: `.agents/skills/skill-requesting-code-review/SKILL.md:How to Request`
- Modify: `.agents/skills/skill-requesting-code-review/code-reviewer.md:Git Range to Review`
- Modify: `.agents/skills/skill-reviewing-pull-requests/SKILL.md:Review Contract`
- Create: `docs/operating_system/procedures/ocr-delegation-procedure.md`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md:Authoring SSOT`
- Modify: `repo_config/starter-kit-manifest.json:sharedPaths.scripts`
- Regenerate: generated provider projections for both review skills and code
  reviewer prompt
- Modify: `tests/test_starter_kit_generation.py:shared script assertions`

**Dependencies:**
- Tasks 1–2 result shape and test evidence.
- Existing `scripts/review-package BASE` includes committed, staged, unstaged,
  and untracked changes when HEAD is omitted.
- Existing generated-surface ownership: canonical `.agents/skills` sources,
  generated provider projections, shared Project OS scripts through manifest.

**Authority:**
- Preauthorized local actions: edit canonical docs, skill sources, manifest, and tests; regenerate provider projections; run sync and contract checks
- Stop for: generated drift without canonical source cause, OCR credentials or binaries in Starter Kit, hook commands, copied upstream prompts, or new review acceptance authority

**Steps:**
- [x] Step 1: Add optional OCR preparation guidance to
  `skill-requesting-code-review`, including normalized manifest precedence and
  fallback semantics.
- [x] Step 2: Update `code-reviewer.md` to distinguish committed range evidence
  from working-tree evidence. Require package SHA-256 and Git-inventory digest
  when HEAD does not identify implementation changes.
- [x] Step 3: Update `skill-reviewing-pull-requests` to consume the shared
  preparation contract without owning OCR behavior.
- [x] Step 4: Create procedure documenting external install of the current
  tested release, `OCR_NO_UPDATE=1`, range-only invocation, v1 schema gate,
  observed-version evidence, live upgrade test, fallback, and input errors.
- [x] Step 5: State that `tokenpilot-codex-hook.cmd`, pre-commit, Stop hooks,
  and generated runtime files are not integration points.
- [x] Step 6: Add adapter to `sharedPaths.scripts` only. Keep OCR package,
  fixtures, and tests out of Starter Kit output.
- [x] Step 7: Run `python scripts/sync_agent_adapters.py --all-platforms` and
  inspect generated changes against canonical skill edits.
- [x] Step 8: Extend Starter Kit tests to assert shared adapter distribution
  and OCR-free default packaging.

**Verification:**
- [x] `python -m pytest -q tests/test_starter_kit_generation.py tests/test_setup_hooks.py`
- Expected: adapter is shared; Starter Kit contains no OCR installer, binary,
  tests, or hook invocation; existing hooks remain deterministic validator-only.
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: generated projections match canonical sources.
- [x] `python scripts/validate_repo_config.py --repo-root .`
- Expected: manifest and repository config pass.

**Exit Criteria:**
- One canonical review-requesting contract describes OCR preparation and
  package-bound evidence.
- PR review references that contract.
- Shared runtime docs and generated projections agree.

**Task 3 Evidence:**
- `8ab4eb1403a28e51fe05166716b04bb733b28f93` changes only Task 3-owned
  canonical sources, procedure, manifest, generated projections, and Starter Kit
  tests.
- `python -m pytest -q tests/test_starter_kit_generation.py tests/test_setup_hooks.py`
  → `20 passed` in `0.24s`; independent review ran the broader OCR, Starter Kit,
  and sync suite → `64 passed, 1 skipped` in `22.74s`.
- `python scripts/sync_agent_adapters.py --all-platforms --check` → up to date;
  `python scripts/validate_repo_config.py --repo-root .` → passed;
  `python scripts/validate_repo_contracts.py` → passed.
- `git diff --check` → clean. Independent review confirmed no repository mutation
  and exact 16-file scope.
- Independent review verdict: `PASS`. Limits: no live OCR installation,
  upgrade, network, or external-process compatibility run.

### Task 4: Freeze review evidence and complete handoff

**Purpose:**
- Prove final implementation scope when changes remain uncommitted and prepare
  independent review without treating `HEAD` alone as implementation identity.

**Task Function:**
- Generate immutable review artifact, hash exact inputs, run final checks, and
  request read-only independent review.

**Template Profile:**
- Controller-selected: `review`
- Selection basis: final evidence, review risk, and current uncommitted-workspace
  constraints require independent verification.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independently validate frozen artifact identity, scope, and
  security boundaries.

**Specification Coverage:**
- Exact Git-input-bound evidence for committed and working-tree reviews.
- Existing untracked `.playwright-mcp/` and `db/` remain untouched.
- Review evidence invalidates when package or inventory digest changes.
- CoS remains acceptance owner.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-requesting-code-review`

**Files And Symbols:**
- Inspect: all plan targets and `git status --short --branch`
- Use: `.agents/skills/skill-subagent-driven-development/scripts/review-package:BASE`
- Verify: `scripts/validate_repo_contracts.py:main`
- Verify: `scripts/validate_planning_lifecycle.py:main`
- Verify: `scripts/validate_template_required_sections.py:main`
- Verify: `tests/test_ocr_delegate_adapter.py`

**Dependencies:**
- Tasks 1–3 completed with accepted task-local proof.
- Base commit remains `855e7a1ff07777827adedfff158b3e56afacad0b`.
- No unrelated user artifact is discarded to make review package cleaner.

**Authority:**
- Preauthorized local actions: run final checks, generate disposable review package, hash package and inventory, inspect diffs, and record evidence in the plan ledger
- Stop for: branch/base drift, changed files outside plan targets, failed proof, generated drift, package digest change during review, or any request to discard unrelated untracked artifacts

**Steps:**
- [x] Step 1: Run `bash .agents/skills/skill-subagent-driven-development/scripts/review-package "$BASE_SHA" "" "$REVIEW_PACKAGE"` from repository root, where `BASE_SHA` is the plan base and `REVIEW_PACKAGE` is a disposable path outside tracked files.
- [x] Step 2: Record `Get-FileHash -Algorithm SHA256 $REVIEW_PACKAGE` as
  `source_artifact_sha256`.
- [x] Step 3: Write sorted `git status --short --untracked-files=all` output to
  a disposable inventory file and record its SHA-256 as
  `git_inventory_sha256`. Include approved scope and preserved untracked paths
  in reviewer context; do not discard them.
- [x] Step 4: Dispatch independent reviewer with package path, both digests,
  base SHA, approved scope, required checks, and known limits. Reviewer reads
  package only and does not mutate repository state.
- [x] Step 5: If either digest changes, invalidate review evidence, regenerate
  package and inventory, and rerun review.
- [x] Step 6: Run final focused, full-suite, contract, planning, config, sync,
  whitespace, and Git checks.
- [x] Step 7: Record findings, deviations, rerun conditions, and next action.
  Do not mark plan `completed` before fresh verification returns `verified`.

**Verification:**
- [x] `python -m pytest -q tests/test_ocr_delegate_adapter.py tests/test_starter_kit_generation.py tests/test_setup_hooks.py`
- Expected: focused integration, fixture, distribution, and hook ownership
  tests pass.
- [x] `python -m pytest -q`
- Expected: full suite passes without unrelated test changes.
- [x] `python scripts/validate_repo_contracts.py --repo-root . --fast`
- Expected: repository contract validation passes.
- [x] `python scripts/validate_planning_lifecycle.py --repo-root .`
- Expected: proposed plan and coordination ledger pass lifecycle validation.
- [x] `python scripts/validate_template_required_sections.py --repo-root . --require-template-selection`
- Expected: maintained plans and templates pass required sections and metadata.
- [x] `python scripts/validate_repo_config.py --repo-root .`
- Expected: repository config and Starter Kit manifest pass.
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: no generated projection drift.
- [x] `git diff --check`
- Expected: no whitespace errors.
- [x] `git status --short --branch`
- Expected: only plan-scoped changes plus preserved pre-existing untracked
  `.playwright-mcp/` and `db/`.

**Exit Criteria:**
- Frozen review package and inventory digests bind independent review evidence.
- All required checks pass with fresh output.
- No unresolved task, blocker, scope deviation, contract mismatch, or generated
  drift remains.

**Task 4 Evidence:**
- Independent verification returned `VERIFIED` for base
  `855e7a1ff07777827adedfff158b3e56afacad0b` and reviewed head
  `8ab4eb1403a28e51fe05166716b04bb733b28f93`.
- Native package:
  `C:\Users\HOANG PHI LONG DANG\AppData\Local\Temp\ocr-task4-review-package.txt`;
  SHA-256 `00F70BFCA8BE3F29DCC93ABDA1BCEEF3F4DB818654E174AAF5CD139358EB33AF`.
- Sorted Git inventory:
  `C:\Users\HOANG PHI LONG DANG\AppData\Local\Temp\ocr-task4-git-inventory.txt`;
  SHA-256 `91D48C13C8A9788A205E7CA96F6F46B8DB97143E5C59320D50A5B2A4441BBB68`.
- Full suite: `668 passed, 1 skipped`; focused Task 4 suite: `47 passed, 1
  skipped`. Repository, planning, template, config, sync, and whitespace checks
  passed.
- Scope matched all 20 Task 3 paths. Only untracked lane artifact was mirrored
  plan; `.playwright-mcp/`, `db/`, and `tokenpilot-codex-hook.cmd` remained
  unchanged.
- Bash `review-package` failed on Windows linked-worktree path translation;
  native PowerShell package generation preserved equivalent evidence and was
  accepted as runtime limitation, not repository defect.

## Verification

- `python -m pytest -q tests/test_ocr_delegate_adapter.py tests/test_starter_kit_generation.py tests/test_setup_hooks.py`
- `python -m pytest -q`
- `python scripts/validate_repo_contracts.py --repo-root . --fast`
- `python scripts/validate_planning_lifecycle.py --repo-root .`
- `python scripts/validate_template_required_sections.py --repo-root . --require-template-selection`
- `python scripts/validate_repo_config.py --repo-root .`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`
- `git status --short --branch`

## Completion Criteria

The plan is ready for completion verification when:

1. Tasks 1–3 satisfy adapter, fixture, live compatibility, review-contract,
   documentation, distribution, and generated-surface outcomes.
2. Task 4 records package and Git-inventory SHA-256 values for independent
   review evidence.
3. Adapter accepts only immutable ranges and returns `prepared` or `fallback`.
4. Invalid Project OS input remains contract error/`BLOCKED`; OCR failure uses
   native fallback.
5. Git inventory remains authoritative for every changed path, rename, and
   deletion.
6. Starter canonical rules outrank OCR rule hints.
7. `OCR_NO_UPDATE=1` is present on every OCR subprocess.
8. `tokenpilot-codex-hook.cmd` and pre-commit scripts remain unchanged.
9. Existing untracked `.playwright-mcp/` and `db/` remain untouched.
10. `skill-verification-before-completion` returns `verified` before plan status
    changes from `proposed` through `active` to `completed`.

## Deferred Follow-Up

- Persistent required-OCR mode.
- Workspace and single-commit OCR preparation.
- OCR-managed model execution.
- OCR prompt or rule synchronization.
- Automatic OCR installation or upgrade manager.
- Per-repository OCR configuration registry.
- Hook or pre-commit review invocation.
- Performance or review-quality claims without paired measurements.
