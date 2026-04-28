---
thread_id: starter-adoption-experience.prompt-template-metadata-and-validation
status: proposed
---

# Prompt Template Metadata And Validation

## Goal

Define a lightweight metadata shape for prompt-template files and decide what
should stay guidance-only versus what should become validator-backed.

## Why Now

The prompt pack has grown enough that classification, discoverability, and
future validation will benefit from a small structured shape instead of purely
free-form docs.

## Dependencies

- confirm the prompt-pack categories are stable enough to describe in metadata
- avoid colliding with existing spec/plan metadata expectations

## Shared Surfaces

- `docs/operating_system/prompt_templates/`
- `docs/operating_system/prompt_templates/README.md`
- `docs/operating_system/repo-governance.md`
- `scripts/validate_adoption_shape.py` if validation is added later

## Linked Spec

- none yet

## Linked Plan

- none yet

## Notes

- this is a good candidate for a spec before implementation
- validator enforcement should come only after the metadata shape settles
