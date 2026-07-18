---
layer: operating_system
artifact_type: plan
status: completed
template_id: implementation-plan
name: build-project-os-starter-kit
parent_workstream: none
targets:
  - scripts/
  - docs/operating_system/
  - .agents/skills/
  - repo_config/planning_artifact_schema.yaml
  - AGENTS.md
  - GEMINI.md
  - CLAUDE.md
  - project-OS-starter-kit/
---

## Goal

Build a generated `project-OS-starter-kit` from `project-OS-starter` so the starter repo remains the single source of truth while the kit becomes a clone-ready, consume-only downstream starter. The kit must ship prebuilt agent entry surfaces and the minimum governance, planning, template, script, and validation surfaces needed for normal starter usage, while excluding adapter-regeneration and runtime-bundle deployment machinery.

## Key Deliverables

### Kit generation contract and ownership boundary

Define a canonical generation contract inside `project-OS-starter` that makes `project-OS-starter-kit` a generated output rather than an independently edited repo. The contract must explicitly preserve these boundaries: `project-OS-starter` alone owns adapter regeneration and kit publication, while the kit consumes final shipped `AGENTS.md`, `GEMINI.md`, and `CLAUDE.md` without any downstream adapter sync path.

### Curated include/exclude surface with script-reference closure

Implement a curated selection model for kit contents that includes clone-ready repo surfaces, `repo_config/planning_artifact_schema.yaml`, required operating-system docs/templates/prompts, kept skills/workflows, and every non-runtime-bundle script directly referenced by those kept skills. The selection model must exclude `.codex/`, adapter mappings and adapter sync/verify machinery, runtime-bundle deployment/validation/test paths, and any source-only factory surfaces not needed by a downstream cloned repo.

### Repeatable build and verification workflow

Add bounded generation and verification workflow so maintainers can rebuild the kit from current source and prove that the generated output matches the least-privilege contract. Verification must confirm shipped prebuilt adapter files exist, forbidden regeneration/deployment surfaces are absent, required script references resolve, and the generated kit remains ready for direct clone-and-use onboarding.

## Task/Wave Breakdown

### task 1: define kit contract, ownership, and allowed surface


### task 2: inventory kept skills and derive required script/doc closure

Review each skill and kept workflow intended for shipment in the kit, then enumerate every directly referenced script, prompt, template, governance doc, planning doc, and validator path required for those shipped instructions to remain truthful. Produce a source-owned manifest or equivalent bounded config inside `project-OS-starter` that drives kit assembly from this closure rather than by broad folder copying. Ensure `repo_config/planning_artifact_schema.yaml` is required. For any skill whose instructions still point at forbidden adapter-regeneration or runtime-bundle machinery, either exclude that skill from the kit or patch its source-owned guidance so the generated kit contains only valid downstream instructions.

### task 3: implement kit generator from source-owned manifest

Add or extend build tooling in `project-OS-starter` to materialize the kit into a generated output directory or publish-ready staging tree. The generator should copy only approved surfaces, preserve final shipped `AGENTS.md`, `GEMINI.md`, and `CLAUDE.md`, create required empty starter folders where needed, and omit all forbidden paths. Keep the implementation source-first: the kit must never become an edited source layer. If publication metadata or README content needs kit-specific synthesis, generate it from starter-owned templates or manifests rather than maintaining a second hand-edited repo contract.

### task 4: add verification for required and forbidden kit contents

Create automated verification that checks generated kit shape against the contract. Required checks should verify presence of clone-ready starter surfaces, required docs structure, kept skills/workflows, `repo_config/planning_artifact_schema.yaml`, and all script references needed by shipped skills. Forbidden checks should fail if `.codex/`, adapter mappings, adapter sync/verify scripts, runtime-bundle deployment/validation/test surfaces, or other banned factory-only paths appear in the generated kit. Also verify that shipped prebuilt adapter entry files exist while no downstream adapter-regeneration path remains.

### task 5: document build, refresh, and publication workflow

Document maintainer workflow for rebuilding and validating the kit from `project-OS-starter`, including exact commands, expected output location, and rule that direct edits to `project-OS-starter-kit` are not allowed. Clarify when maintainers must regenerate kit outputs after changing skills, prompts, governance docs, scripts, or other included starter-owned surfaces. Ensure documentation distinguishes between kit generation, adapter regeneration in the source repo, and any separate private runtime-bundle workflows.

## Verification

- .\.venv\Scripts\python.exe scripts/validate_repo_contracts.py --fast
- .\.venv\Scripts\python.exe -m pytest tests
- py -3 scripts/validate_repo_config.py
- py -3 scripts/build_starter_kit.py
- py -3 scripts/validate_starter_kit.py
- git diff -- generated_exports/project-OS-starter-kit

## Completion Criteria

A plan item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`
4. `project-OS-starter` can generate a clone-ready `project-OS-starter-kit` without manual kit edits
5. generated kit verification proves required consume-only surfaces are present and forbidden adapter-regeneration/runtime-bundle surfaces are absent
