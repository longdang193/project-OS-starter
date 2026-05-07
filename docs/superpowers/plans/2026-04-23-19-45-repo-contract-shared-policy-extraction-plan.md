---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - scripts/validator_policy.py
  - scripts/validate_repo_contracts.py
  - scripts/validate_adoption_shape.py
  - tests/test_validate_repo_contracts.py
  - tests/test_validate_adoption_shape.py
  - docs/operating_system/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
related_features: []
related_stages: []
---

# Repo Contract Shared Policy Extraction Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-23-repo-contract-shared-policy-extraction-spec.md`  
**Type:** modify  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Extract the small shared repo-contract policy already duplicated across validators so `history.md` boundary markers and required metadata-marker strings come from one source of truth.

**Architecture:** Extend `scripts/validator_policy.py` with a narrow repo-contract policy section for shared marker strings. Refactor `scripts/validate_repo_contracts.py` and `scripts/validate_adoption_shape.py` to import those shared constants while keeping parsing, file walking, subprocess orchestration, and reporting logic local to each validator.

**Key Invariants:**
- `validate_repo_contracts.py` stays primarily an orchestration and flow script.
- Shared boundary and marker strings live in one internal policy module.
- The meaning of `history.md` boundaries and required metadata markers does not change in this pass.
- Existing validator behavior remains stable aside from internal import cleanup.

**Rollout / Revert:**  
- rollback_trigger: Shared-policy extraction changes validator behavior, introduces import coupling problems, or broadens scope beyond the duplicated marker rules.  
- rollback_method: Inline the moved constants back into the validator scripts, keep the spec/plan for a narrower retry, and revisit the shared-policy boundary.

---

## Doc Update Matrix

- Feature source: none
- Feature contract: none
- Feature lineage: none
- Stage source: none
- Stage contracts: none
- Feature history: none
- Feature-specific docs: none
- Cross-cutting docs: none
- Operating-system docs:
  - `docs/operating_system/repo-governance.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/superpowers/specs/2026-04-23-repo-contract-shared-policy-extraction-spec.md`
- README: none
- Generated discovery: none

## Files To Modify

```text
scripts/validator_policy.py
scripts/validate_repo_contracts.py
scripts/validate_adoption_shape.py
tests/test_validate_repo_contracts.py
tests/test_validate_adoption_shape.py
docs/operating_system/repo-governance.md
docs/operating_system/skill-doc-system-lifecycle.md
docs/superpowers/specs/2026-04-23-repo-contract-shared-policy-extraction-spec.md
```

## Scope Boundary

Implement only the narrow shared-policy extraction:

1. add shared repo-contract marker constants to `scripts/validator_policy.py`
2. import them into `validate_repo_contracts.py`
3. align `validate_adoption_shape.py` with the same shared `history.md` boundary constants where applicable
4. add focused regression coverage so both validator paths stay aligned
5. lightly document the ownership split

Do not:

- move subprocess orchestration into shared policy
- redesign `validate_repo_contracts.py` reporting or `--fast` behavior
- make validator policy repo-editable
- use this pass to refactor unrelated validator helpers

## Task 1: Extend Shared Validator Policy

**Files:**
- Modify: `scripts/validator_policy.py`
- Docs: none

- [x] Step 1: Add a dedicated repo-contract policy section to `scripts/validator_policy.py`.
- [x] Step 2: Move the exact `history.md` boundary strings into that section:
  - generated start marker
  - generated end marker
  - required `## Human Notes` heading
- [x] Step 3: Move the required metadata-marker strings into that section:
  - `# @architecture`
  - `@meta`
- [x] Step 4: Keep names explicit and readable so validators can import them without wrapper indirection.

## Task 2: Refactor `validate_repo_contracts.py` To Use Shared Policy

**Files:**
- Modify: `scripts/validate_repo_contracts.py`
- Test: `tests/test_validate_repo_contracts.py`
- Docs: none

- [x] Step 1: Replace local duplicated marker constants with imports from `scripts/validator_policy.py`.
- [x] Step 2: Keep `_starts_with_architecture_block()` and `_has_setup_meta()` local unless extraction is clearly simpler and still policy-scoped.
- [x] Step 3: Leave `build_subprocess_steps()`, `run_step()`, and reporting logic untouched.
- [x] Step 4: Run the repo-contract validator tests and confirm the behavior is unchanged.

Suggested verification command:

```powershell
$env:PYTHONPATH=(Resolve-Path '.tmp-tests\pytest-deps').Path; python -m pytest tests/test_validate_repo_contracts.py -q
```

## Task 3: Align `validate_adoption_shape.py` With Shared Boundary Policy

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Test: `tests/test_validate_adoption_shape.py`
- Docs: none

- [x] Step 1: Find the `history.md` boundary validation path in `validate_adoption_shape.py`.
- [x] Step 2: Replace any local copies of the same boundary strings with imports from `scripts/validator_policy.py`.
- [x] Step 3: Keep adoption-shape validation flow local; only the shared boundary contract moves.
- [x] Step 4: Run the adoption-shape validator tests and confirm there is no behavior regression.

Suggested verification command:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_validate_adoption_shape.py -q
```

## Task 4: Add Focused Regression Coverage

**Files:**
- Modify: `tests/test_validate_repo_contracts.py`
- Modify: `tests/test_validate_adoption_shape.py`
- Modify: `scripts/validator_policy.py` if exports need to be exercised directly

- [x] Step 1: Add or adjust a narrow regression test proving malformed `history.md` boundaries are still rejected through the repo-contract validator path.
- [x] Step 2: Add or adjust a narrow regression test proving the shared boundary contract still holds on the adoption-shape path if current coverage is indirect.
- [x] Step 3: Avoid duplicating large fixtures; prefer one concise case per validator path.
- [x] Step 4: Only add direct policy-module assertions if they guard against accidental omission of the shared constants.

## Task 5: Light Documentation Pass

**Files:**
- Modify: `docs/operating_system/repo-governance.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`
- Modify: `docs/superpowers/specs/2026-04-23-repo-contract-shared-policy-extraction-spec.md`

- [x] Step 1: Note that shared validator contract strings for repo-contract and adoption-shape validation now live in `scripts/validator_policy.py`.
- [x] Step 2: Keep the docs clear that `validate_repo_contracts.py` remains the canonical repo-contract orchestration entrypoint.
- [x] Step 3: Keep the wording maintenance-oriented rather than presenting this as a new end-user workflow.

## Task 6: Full Verification

**Files:**
- Test: `tests/test_validate_repo_contracts.py`
- Test: `tests/test_validate_adoption_shape.py`
- Verify: `scripts/validate_repo_contracts.py`
- Verify: `scripts/validate_adoption_shape.py`

- [x] Step 1: Run the repo-contract validator tests:

```powershell
$env:PYTHONPATH=(Resolve-Path '.tmp-tests\pytest-deps').Path; python -m pytest tests/test_validate_repo_contracts.py -q
```

- [x] Step 2: Run the adoption-shape validator tests:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_validate_adoption_shape.py -q
```

- [x] Step 3: Run the repo-contract validator fast path:

```powershell
$env:UV_CACHE_DIR=(Resolve-Path '.tmp-tests').Path; uv run python scripts\validate_repo_contracts.py --fast
```

- [x] Step 4: Run the adoption-shape validator:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python scripts/validate_adoption_shape.py
```

- [x] Step 5: Run generated metadata check:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python tools/docs/generate_architecture_metadata.py --check
```

- [x] Step 6: Run whitespace validation:

```powershell
git diff --check
```

- [x] Step 7: Review the final diff and confirm this stayed a narrow shared-policy extraction rather than a broader validator rewrite.
