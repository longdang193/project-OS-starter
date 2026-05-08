---
thread_id: starter-adoption-experience.starter-kit-least-privilege-generation
status: completed
completed_at: 2026-05-08T23:06:00Z
---

# Starter-Kit Least-Privilege Generation

## Goal

Make `project-OS-starter-kit` a generated, consume-only starter built from
`project-OS-starter` with explicit least-privilege assembly and validation.

## Why Now

The starter must stop shipping stale source-only adapter/runtime machinery and
must prove that downstream clones receive only truthful, clone-ready surfaces.

## Dependencies

- source-owned governance must define starter-kit ownership and forbidden
  surfaces
- generated output must be reproducible from source without manual kit edits
- verification must fail on content-level source-only leakage

## Shared Surfaces

- `repo_config/starter-kit-manifest.json`
- `repo_config/starter-kit-closure.json`
- `scripts/build_starter_kit.py`
- `scripts/validate_starter_kit.py`
- `tests/test_starter_kit_generation.py`
- `docs/operating_system/governance/repo-governance.md`
- `docs/operating_system/procedures/starter-kit-workflow.md`

## Notes

- `generated_exports/project-OS-starter-kit/` is disposable generated build
  output and is ignored from lane commits
- downstream kit clones consume shipped root instruction docs but must not
  regain source-only regeneration machinery
