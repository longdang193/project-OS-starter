---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: shared-project-os-runtime-assets
targets:
  - scripts/deploy_agent_runtime.py
  - scripts/setup_hooks.ps1
  - scripts/setup_hooks.sh
  - scripts/project_root.py
  - scripts/build_starter_kit.py
  - scripts/validate_starter_kit.py
  - scripts/opendesign_profile_adapter.py
  - scripts/validate_agent_metadata_schema.py
  - scripts/validate_env_gitignore_contract.py
  - scripts/validate_learning_materials_format.py
  - scripts/validate_planning_lifecycle.py
  - scripts/validate_prompt_metadata_schema.py
  - scripts/validate_repo_contracts.py
  - scripts/validate_starter_kit.py
  - scripts/validate_template_required_sections.py
  - repo_config/starter-kit-manifest.json
  - tests/test_deploy_agent_runtime.py
  - tests/test_project_root.py
  - tests/test_starter_kit_generation.py
  - tests/test_validate_repo_config.py
  - tests/test_validate_repo_contracts.py
  - tests/project_os_test_paths.py
  - tests/test_setup_hooks.py
  - tests/test_agent_profile_registry.py
  - tests/test_dcode_project.py
  - tests/test_deepagents_runtime_patch.py
  - tests/test_herdr_main_launcher.py
  - tests/test_opendesign_profile_adapter.py
  - tests/test_validate_agent_metadata_schema.py
  - tests/test_validate_learning_materials_format.py
  - tests/test_validate_planning_lifecycle.py
  - tests/test_validate_template_required_sections.py
  - tests/test_starter_lifecycle_contract.py
  - tests/test_runtime_tool_resolution_contract.py
  - tests/test_skill_chief_of_staff.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/procedures/starter-kit-procedure.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - generated_agents/antigravity/GEMINI.md
  - generated_agents/claude/CLAUDE.md
  - generated_agents/codex/AGENTS.md
  - AGENTS.md
  - ~/.agents/project-os/docs
  - ~/.agents/project-os/scripts
---

## Goal

Move reusable Project OS runtime documentation and approved tooling scripts into
one user-global Project OS installation at `Path.home() / ".agents" / "project-os"`,
matching the existing shared-skill deployment model. Runtime consumers use the
global installation; project-specific plans, specs, configuration, code, tests,
and scripts remain local. No per-project version pinning is introduced initially.

## Implementation Outcomes

### Shared runtime bundle

`deploy_agent_runtime.py` synchronizes only approved `docs/operating_system`
content and an explicit reusable Project OS script allowlist into
`~/.agents/project-os`. Marker-owned files record source commit/digest metadata
and receive drift checks, stale-file cleanup, collision protection, adoption
behavior, and idempotent updates equivalent to shared skills.

### Runtime path resolution

Generated runtime text resolves shared `docs/` and approved `scripts/` paths to
the global installation in hardcode mode, with project-local fallback for
portability. Shared scripts resolve the active project through explicit
`--repo-root`, then `git rev-parse --show-toplevel`, and block when neither is
available. Existing skill paths, generated provider artifacts, and the
`tokenpilot-codex-hook.cmd` launcher remain unchanged.

### Starter-kit distribution

The starter-kit manifest records shared source paths without copying them into
each generated kit. The kit remains a thin project bootstrap containing local
`AGENTS.md`, `agents/`, `repo_config/`, `docs/intent/`,
`docs/superpowers/`, project code/tests, and project-specific scripts.
Validation proves shared paths are source-valid and absent from kit output.

### Documentation and regression proof

Runtime-surface and starter-kit procedures describe global bundle installation,
fallback behavior, ownership boundaries, and rebuild checks. Focused tests cover
sync safety, path rewriting, manifest validation, and kit shape.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-central-config-layer`, `skill-code-standards`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed source, test, config, and documentation files; run focused Python tests and repository validators
- User-approval actions: publish, push, merge, delete unrelated generated output, or discard existing workspace changes
- Parallel ownership: none; `deploy_agent_runtime.py`, manifest parsing, and kit validation share contracts
- Sequential fallback: complete manifest contract before deploy logic, deploy logic before shared-script repo resolution, repo resolution before path rendering, path rendering before kit migration, then documentation and final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `ea8e9021c7e5c19d3fdc1513b3f299869e9d194a`
- Expected workspace: preserve existing modified and untracked files; add this plan only during planning
- Next action: none; completed after deployment and verification
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | focused manifest and config tests | `146 passed`; manifest and starter-kit validators passed |
| Task 2 | `completed` | current | `codex` | Task 1 | shared sync and collision tests | `18 passed`; global deployment completed |
| Task 3 | `completed` | current | `codex` | Task 2 | shared-script repo-root tests | resolver, dcode, config, and contract tests passed |
| Task 4 | `completed` | current | `codex` | Task 3 | path rewrite and fallback tests | deployment rewrite tests passed |
| Task 5 | `completed` | current | `codex` | Task 4 | starter-kit build and validation tests | kit built and validated; `16 passed` |
| Task 6 | `completed` | current | `codex` | Task 5 | final validators and focused regression suite | contract validation passed; combined suite `145 passed` |

## Task Breakdown

### Task 1: Define shared asset contract

**Purpose:**
- Add one manifest-owned allowlist for global docs and scripts.
- Prevent shared paths from silently overlapping copied, omitted, or forbidden kit paths.

**Task Function:**
- Reconcile manifest schema and source-path ownership before runtime changes.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: low ambiguity, bounded config and parser change.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused local tests cover schema behavior.

**Specification Coverage:**
- Shared bundle contains `docs/operating_system` and the current reusable script allowlist.
- Project-specific plans, specs, and scripts remain local.

**Required Skills:**
- `skill-central-config-layer`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `repo_config/starter-kit-manifest.json`
- Inspect: `scripts/build_starter_kit.py:StarterKitManifest`, `load_manifest`, `build_starter_kit`
- Modify: `repo_config/starter-kit-manifest.json`
- Modify: `scripts/build_starter_kit.py:StarterKitManifest`, `load_manifest`, `build_starter_kit`
- Verify: `tests/test_validate_repo_config.py`, `tests/test_starter_kit_generation.py`

**Dependencies:**
- Existing manifest and current `copyPaths` are source facts.

**Authority:**
- Preauthorized local actions: modify manifest parsing and focused tests.
- Stop for: changing publication boundaries or adding unapproved global asset classes.

**Steps:**
- [x] Step 1: Add `sharedPaths` to the existing manifest with explicit `docs` and `scripts` lists; move shared entries out of `copyPaths` and remove their kit `requiredPaths`; do not add a second runtime-path config file.
- [x] Step 2: Extend `StarterKitManifest` and `load_manifest` to validate non-empty relative shared paths under the repository root.
- [x] Step 3: Reject overlap between `sharedPaths`, `copyPaths`, `omitPaths`, and `forbiddenPaths`; validate every shared source exists before kit generation.
- [x] Step 4: Update manifest fixtures and assertions for the new contract.

**Verification:**
- [x] `py -3 -m pytest tests/test_validate_repo_config.py tests/test_starter_kit_generation.py -q`
- Expected: manifest accepts the canonical allowlist and rejects missing, overlapping, or escaping shared paths.

**Exit Criteria:**
- One manifest owns the shared bundle allowlist and parser enforces it.

### Task 2: Generalize marker-owned shared deployment

**Purpose:**
- Deploy docs and approved scripts to `~/.agents/project-os` without overwriting unrelated user files.

**Task Function:**
- Generalize existing shared-skill copy, marker, drift, adoption, and stale-file behavior to shared trees.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: moderate risk because deployment can overwrite or delete user files.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused filesystem tests exercise collision and stale-file guards.

**Specification Coverage:**
- Marker ownership, collision refusal, adoption, stale cleanup, dry-run, check mode, and idempotency.

**Required Skills:**
- `skill-central-config-layer`, `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/deploy_agent_runtime.py:_shared_skill_marker`, `_plan_shared_skill_deploy`, `_check_shared_skills`, `run`
- Modify: `scripts/deploy_agent_runtime.py:shared deployment constants and helpers`, `run`
- Verify: `tests/test_deploy_agent_runtime.py:shared skill deployment tests`

**Dependencies:**
- Task 1 manifest contract.

**Authority:**
- Preauthorized local actions: add marker-owned global bundle sync and tests under temporary directories.
- Stop for: deleting unmarked files, changing existing shared-skill ownership semantics, or changing platform target locations.

**Steps:**
- [x] Step 1: Add `SHARED_ASSETS_TARGET = Path.home() / ".agents" / "project-os"` and a bundle marker schema containing source root, source relative path, bundle name, and manifest digest.
- [x] Step 2: Implement generic tree enumeration, expected-file calculation, marker reads, ownership checks, collision checks, stale-file detection, and plan generation for `docs` and `scripts` bundles.
- [x] Step 3: Reuse existing `--check`, `--dry-run`, `--backup`, `--force`, and adoption boundaries; keep unrelated global files untouched.
- [x] Step 4: Make normal deployment sync shared assets before platform artifacts; make check mode report shared-asset drift.
- [x] Step 5: Add tests for clean deploy, repeat deploy, owned update, missing file, stale file, unowned collision, foreign marker, and unrelated-file preservation.

**Verification:**
- [x] `py -3 -m pytest tests/test_deploy_agent_runtime.py -q`
- Expected: all shared-tree safety cases pass; existing skill and platform tests remain green.

**Exit Criteria:**
- Global docs/scripts sync is marker-owned, idempotent, collision-safe, and independently checkable.

### Task 3: Make shared scripts repository-independent

**Purpose:**
- Make global scripts operate on the active project instead of treating their installation directory as the project root.

**Task Function:**
- Replace `Path(__file__)` project-root inference in globalized scripts with explicit project-root resolution.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: material cross-project behavior with a bounded resolver contract.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct helper and CLI tests prove explicit root, Git-root fallback, and blocked non-repository behavior.

**Specification Coverage:**
- Shared scripts accept `--repo-root` where they need a project root.
- Without the option, scripts use `git rev-parse --show-toplevel` from the current working directory.
- Scripts block with an actionable error when no Git root exists.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_repo_root`
- Inspect: `scripts/validate_repo_config.py:infer_repo_root`
- Inspect: `scripts/build_starter_kit.py:repo_root`, `scripts/deploy_agent_runtime.py:repo_root`
- Inspect: globalized validator and profile scripts for `Path(__file__)` root inference
- Modify: approved shared scripts that infer project root from `Path(__file__)`
- Verify: corresponding tests under `tests/` and direct CLI error paths

**Dependencies:**
- Task 2 global target and marker contract.

**Authority:**
- Preauthorized local actions: add one stdlib-only project-root resolver and adapt approved global scripts/tests.
- Stop for: changing factory-only scripts that remain local or silently falling back to the global installation as project root.

**Steps:**
- [x] Step 1: Define one resolver contract: explicit `--repo-root`, then Git top-level, otherwise non-zero CLI exit.
- [x] Step 2: Apply the resolver to the approved global script allowlist; preserve factory-only scripts as local source tools.
- [x] Step 3: Add tests proving a globally installed script reads target-project `agents/`, `docs/`, `repo_config/`, and `tests/` rather than `~/.agents/project-os`.
- [x] Step 4: Add failure tests for explicit invalid roots and non-Git working directories.

**Verification:**
- [x] `py -3 -m pytest tests/test_dcode_project.py tests/test_validate_repo_config.py tests/test_validate_repo_contracts.py -q`
- Expected: shared scripts resolve target projects correctly and fail closed without a project root.

**Exit Criteria:**
- Every globalized script has explicit or Git-derived project-root behavior and no `Path(__file__)` project-root dependency.

### Task 4: Resolve shared paths with local fallback

**Purpose:**
- Make generated runtime instructions consume global shared assets without breaking local projects.

**Task Function:**
- Extend existing runtime path rewriting; do not add a second resolver.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded path mapping with direct regression coverage.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: pure rendering tests prove output strings and fallback behavior.

**Specification Coverage:**
- Hardcode mode maps approved docs/scripts to the global bundle.
- Relative mode remains portable and resolves project-local paths first.
- Skills, generated adapters, and hook launcher paths remain unchanged.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/deploy_agent_runtime.py:_looks_like_repo_relative_path`, `_absolute_text_path`, `_rewrite_command_to_absolute_repo_path`, `_rewrite_text_runtime_paths`
- Modify: `scripts/deploy_agent_runtime.py:path classification and shared-root resolution`
- Verify: `tests/test_deploy_agent_runtime.py:test_rewrite_text_runtime_paths_keeps_relative_paths_by_default`, `test_rewrite_text_runtime_paths_rewrites_frontmatter_and_source_lines_in_hardcode_mode`

**Dependencies:**
- Tasks 2–3 global target and repo-root contracts.

**Authority:**
- Preauthorized local actions: modify path rendering and add focused assertions.
- Stop for: rewriting arbitrary commands, URLs, credentials, or project-local plan/spec paths.

**Steps:**
- [x] Step 1: Classify only manifest-approved docs/scripts paths as shared; leave unknown and project-local paths unchanged.
- [x] Step 2: Map shared docs/scripts to `~/.agents/project-os/docs` and `~/.agents/project-os/scripts` in hardcode mode.
- [x] Step 3: Preserve relative mode output and add runtime resolution fallback to project-local paths when the global bundle is absent or fails ownership validation.
- [x] Step 4: Assert `scripts/build_starter_kit.py`, adapter internals, and `tokenpilot-codex-hook.cmd` are not rewritten into the shared bundle.

**Verification:**
- [x] `py -3 -m pytest tests/test_deploy_agent_runtime.py -q`
- Expected: global mappings appear only for approved paths; local fallback and existing path behavior remain intact.

**Exit Criteria:**
- Generated runtime text reaches shared assets without breaking portable relative deployments.

### Task 5: Remove redundant shared files from starter output

**Purpose:**
- Stop generated starter kits from carrying duplicate shared docs/scripts.

**Task Function:**
- Align kit generation and validation with the shared asset manifest.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded generated-output contract change.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: kit generation tests and validators provide direct proof.

**Specification Coverage:**
- Shared docs/scripts are source-owned and globally deployed, not manually copied into each kit.
- Local plans/specs and non-shared project files remain in kit output.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/build_starter_kit.py:build_starter_kit`
- Inspect: `scripts/validate_starter_kit.py:CONTENT_SCAN_ROOTS`, manifest validation, `validate_starter_kit`
- Modify: `scripts/build_starter_kit.py:shared-path exclusion checks`
- Modify: `scripts/validate_starter_kit.py:shared-path absence and source contract checks`
- Modify: `tests/test_starter_kit_generation.py:kit shape and manifest tests`
- Verify: `repo_config/starter-kit-manifest.json`

**Dependencies:**
- Tasks 1–4 complete.

**Authority:**
- Preauthorized local actions: modify generated-kit contract and focused tests.
- Stop for: removing `docs/superpowers/plans`, `docs/superpowers/specs`, or approved local scripts.

**Steps:**
- [x] Step 1: Ensure build output omits every `sharedPaths` entry and rejects accidental shared-tree copies.
- [x] Step 2: Update validator scan roots and forbidden-content checks to match the reduced kit while still validating local governance references.
- [x] Step 3: Update fixtures to prove shared paths are absent, local plan/spec directories remain, and required non-shared files still exist.
- [x] Step 4: Update starter-kit procedure with one global deployment prerequisite and no manual shared-tree copy step.

**Verification:**
- [x] `py -3 scripts/build_starter_kit.py`
- [x] `py -3 scripts/validate_starter_kit.py`
- [x] `py -3 -m pytest tests/test_starter_kit_generation.py -q`
- Expected: generated kit validates, contains no shared docs/scripts, and retains local planning directories and required runtime inputs.

**Exit Criteria:**
- Kit generation no longer duplicates global shared assets.

### Task 6: Reconcile runtime documentation and close out

**Purpose:**
- Make ownership, installation, fallback, and verification discoverable and prove full integration.

**Task Function:**
- Update canonical operating-system documentation and run fresh final checks.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: documentation reconciliation plus deterministic validation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final command set is repository-owned.

**Specification Coverage:**
- Runtime surfaces identify global shared assets and local-only surfaces.
- Starter-kit procedure describes source-first rebuild and global deployment order.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: `docs/operating_system/procedures/starter-kit-procedure.md`
- Verify: `docs/operating_system/governance/repo-governance.md`
- Verify: `scripts/validate_repo_contracts.py`

**Dependencies:**
- Tasks 1–5 complete.

**Authority:**
- Preauthorized local actions: update canonical docs and run validators.
- Stop for: publication, push, merge, or cleanup of unrelated existing changes.

**Steps:**
- [x] Step 1: Document `~/.agents/project-os` as shared runtime asset target and `.agents/skills` as separate shared skill target.
- [x] Step 2: Document local fallback and local-only planning/spec boundaries.
- [x] Step 3: Run focused tests, starter-kit build/validation, metadata validation, and repository contract validation.
- [x] Step 4: Inspect `git diff -- docs scripts repo_config tests` and record any scope deviation before completion review.

**Verification:**
- [x] `py -3 -m pytest tests/test_deploy_agent_runtime.py tests/test_starter_kit_generation.py tests/test_validate_repo_config.py -q`
- [x] `py -3 scripts/validate_repo_config.py`
- [x] `py -3 scripts/build_starter_kit.py`
- [x] `py -3 scripts/validate_starter_kit.py`
- [x] `py -3 scripts/validate_repo_contracts.py`
- Expected: all commands pass; generated output contains no forbidden shared duplicates; existing workspace changes remain untouched.

**Exit Criteria:**
- Plan outcomes are implemented, fresh proof passes, and no required task or contract remains unresolved.

## Post-Review Corrections

- Copied starter-kit tests resolve scripts and operating-system docs from the
  global runtime when local copies are absent.
- Starter-kit hook setup scripts remain local and invoke the global contract
  validator when no local copy exists.
- Agent metadata validation accepts approved global rule references while still
  rejecting missing project-local references.
- DeepAgents setup documentation uses the installed global script path instead
  of a missing consumer-project `./scripts` path.

## Verification

- `py -3 -m pytest tests/test_deploy_agent_runtime.py tests/test_project_root.py tests/test_dcode_project.py tests/test_validate_repo_config.py tests/test_validate_repo_contracts.py tests/test_starter_kit_generation.py` — 146 passed before review corrections
- `py -3 -m pytest generated_exports/project-OS-starter-kit/tests -q` — 239 passed
- `py -3 -m pytest tests/test_deploy_agent_runtime.py tests/test_project_root.py tests/test_dcode_project.py tests/test_setup_hooks.py tests/test_agent_profile_registry.py tests/test_herdr_main_launcher.py tests/test_opendesign_profile_adapter.py tests/test_deepagents_runtime_patch.py tests/test_validate_agent_metadata_schema.py tests/test_validate_learning_materials_format.py tests/test_validate_planning_lifecycle.py tests/test_validate_repo_config.py tests/test_validate_template_required_sections.py tests/test_starter_lifecycle_contract.py tests/test_runtime_tool_resolution_contract.py tests/test_skill_chief_of_staff.py -q` — 260 passed
- `py -3 scripts/deploy_agent_runtime.py --target all` — shared docs, scripts, skills, and provider adapters deployed
- `py -3 scripts/validate_repo_contracts.py` — passed
- `py -3 scripts/build_starter_kit.py` — passed
- `py -3 scripts/validate_starter_kit.py` — passed
- `py -3 scripts/validate_repo_config.py` — passed

## Completion Criteria

The plan is ready for completion verification when:

1. `~/.agents/project-os` owns approved shared docs/scripts with marker-protected sync and drift checks.
2. Runtime path rewriting uses the shared bundle only for approved assets and preserves local fallback.
3. Starter-kit output omits shared docs/scripts while retaining local plans, specs, and required non-shared files.
4. Canonical runtime and starter-kit docs match the implemented ownership model.
5. Focused tests and repository validators pass with fresh output.
6. Existing unrelated workspace changes remain unmodified.
