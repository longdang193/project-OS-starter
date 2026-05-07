---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - scripts/validate_repo_contracts.py
  - scripts/validate_repo_config.py
  - tests/test_validate_repo_contracts.py
  - tests/test_validate_repo_config.py
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/superpowers/specs/2026-04-24-repo-contract-adoption-shape-ownership-spec.md
related_features: []
related_stages: []
---

# Repo Contract And Adoption-Shape Ownership Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-24-repo-contract-adoption-shape-ownership-spec.md`  
**Type:** modify  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Remove duplicated root-doc validation from `validate_repo_config.py`, restore `validate_adoption_shape.py` as the single owner of that contract, and make `validate_repo_contracts.py` call the owning validator directly.

**Architecture:** Keep repo/system config validation in `scripts/validate_repo_config.py`. Keep adoption-shape root-doc rules in `scripts/validate_adoption_shape.py`. Update `scripts/validate_repo_contracts.py` so the canonical gate runs adoption-shape explicitly instead of relying on duplicated logic.

**Key Invariants:**
- Required root-doc validation remains enforced.
- Managed required root-doc metadata remains enforced.
- Repo-config validation remains about repo/system config and runtime config shape.
- The canonical repo-contract gate invokes the true owner for adoption-shape drift.

**Rollout / Revert:**  
- rollback_trigger: The cleanup removes needed coverage from the canonical repo-contract gate or changes unrelated validator behavior.  
- rollback_method: Reintroduce the removed orchestration step or restore the prior validator wiring, but do not keep long-term duplicated root-doc policy in both validators.

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
  - `docs/operating_system/governance/repo-governance.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/superpowers/specs/2026-04-24-repo-contract-adoption-shape-ownership-spec.md`
- README: none
- Generated discovery: none

## Files To Modify

```text
scripts/validate_repo_contracts.py
scripts/validate_repo_config.py
tests/test_validate_repo_contracts.py
tests/test_validate_repo_config.py
docs/operating_system/governance/repo-governance.md
docs/operating_system/skill-doc-system-lifecycle.md
docs/superpowers/specs/2026-04-24-repo-contract-adoption-shape-ownership-spec.md
```

## Scope Boundary

Implement only the ownership cleanup:

1. remove duplicated root-doc validation from `validate_repo_config.py`
2. run `validate_adoption_shape.py` from the canonical repo-contract gate
3. align tests with the single-owner model
4. lightly update operating-system docs

Do not:

- redesign required root-doc rules
- weaken adoption-shape validation
- merge validators together
- broaden this into a larger validator architecture refactor

## Task 1: Restore Repo-Config Scope

**Files:**
- Modify: `scripts/validate_repo_config.py`
- Modify: `tests/test_validate_repo_config.py`

- [x] Step 1: Remove root-doc parsing and managed metadata validation from `validate_repo_config.py`.
- [x] Step 2: Keep publication config, adapter mappings, and runtime config validation intact.
- [x] Step 3: Remove repo-config tests that now belong to adoption-shape coverage instead.

## Task 2: Wire Adoption-Shape Into The Canonical Gate

**Files:**
- Modify: `scripts/validate_repo_contracts.py`
- Modify: `tests/test_validate_repo_contracts.py`

- [x] Step 1: Add `scripts/validate_adoption_shape.py` to the canonical subprocess steps.
- [x] Step 2: Keep fast mode running the same canonical validators, with pytest still optional.
- [x] Step 3: Add focused orchestration coverage showing the adoption-shape step is present.

## Task 3: Align Operating-System Guidance

**Files:**
- Modify: `docs/operating_system/governance/repo-governance.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`

- [x] Step 1: State that required root-doc validation is adoption-shape policy.
- [x] Step 2: State that the canonical repo-contract gate runs the adoption-shape validator directly.

## Verification

Suggested commands:

```powershell
$env:UV_CACHE_DIR='.tmp-tests/uv-cache'
uv run python -m pytest tests/test_validate_repo_config.py -q
uv run python -m pytest tests/test_validate_repo_contracts.py -q
uv run python scripts/validate_repo_contracts.py --fast
git diff --check
```
