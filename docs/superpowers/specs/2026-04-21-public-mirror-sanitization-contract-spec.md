---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/operating_system/public-safe-doc-rewrite-guide.md
  - docs/operating_system/procedures/publication-workflow.md
  - .agents/skills/skill-private-public-repo-governance/SKILL.md
  - repo_config/publication-config.json
related_features: []
related_stages: []
---

# Public Mirror Sanitization Contract Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Revise publication guidance so the public mirror preserves reproducible structure and sanitizes private payloads instead of over-deleting files.
Reasoning: The current public-safe rewrite guidance over-indexes on removing private material. That protects confidentiality, but it can also remove structural evidence that the public mirror needs for reproducibility, traceability, and credible downstream use.
Invariants:

- The private repo remains the development source of truth.
- The public repo remains a curated downstream mirror.
- Private payloads must not leak into the public mirror.
- Public publication rules must preserve enough visible structure for reproducibility and navigation.
- Canonical truth should flow downward; downstream public views should derive from upstream private sources instead of re-entering private details manually.

Dependencies:

- `docs/operating_system/public-safe-doc-rewrite-guide.md`
- `docs/operating_system/procedures/publication-workflow.md`
- `.agents/skills/skill-private-public-repo-governance/SKILL.md`
- `repo_config/publication-config.json`

Affected stages:

- none

Affected features:

- none

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: none
- feature_lineage: none
- feature_history: none
- stage_source: none
- stage_contract: none
- feature_docs: none
- cross_cutting_docs:
  - `docs/operating_system/public-safe-doc-rewrite-guide.md`
  - `docs/operating_system/procedures/publication-workflow.md`
  - `.agents/skills/skill-private-public-repo-governance/SKILL.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The current public-safe rewrite guidance is directionally correct about keeping
private material out of the public mirror, but it is too biased toward
removing files or stripping them down until little useful structure remains.

That creates a real failure mode:

- the public mirror becomes hard to navigate
- reproducibility weakens because artifact classes disappear
- downstream readers cannot tell which records, manifests, or doc surfaces
  exist upstream
- publication guidance becomes "delete until safe" instead of "preserve what
  can be shown safely"

This is especially risky for files whose presence matters even when some of
their contents are private:

- metadata-bearing docs
- inventories
- manifests
- index-like files
- structured records whose keys or sections support traceability

If the public mirror removes those too aggressively, it stops being a reliable
representation of the project's real shape.

## Goal

Define a publication and rewrite contract that preserves the public mirror's
structural fidelity while still protecting private information.

The contract should teach contributors to choose among three treatments:

1. keep as-is
2. keep and sanitize
3. omit entirely

It should also explain when preserving file shape, headings, schema keys, or
empty metadata fields is the right public-safe choice.

## Non-Goals

This spec does not make all private artifacts publishable.

This spec does not require `docs/superpowers/` artifacts to be published by
default.

This spec does not require a new automated exporter in this step.

This spec does not define the full public schema for every file type in the
repo.

This spec does not force placeholder public files for every omitted private
artifact.

## Proposed Policy Shift

Revise the public-safe rewrite guidance from an implicit binary model:

- publish
- do not publish

to a three-mode model:

### 1. Keep As-Is

Use when a file is already public-safe and needs no redaction.

Examples:

- public-facing setup and usage docs after rewrite
- product-facing README
- public examples

### 2. Keep And Sanitize

Use when the file's existence, schema, headings, metadata keys, or navigation
role matter for reproducibility or discoverability, but some values are private.

Examples:

- metadata-bearing docs whose private references can be blanked
- manifests where sensitive fields can become empty arrays or redacted values
- inventories whose categories can remain while sensitive entries are removed
- index-like files that should still show public-safe shape

### 3. Omit Entirely

Use when the file itself is private-sensitive, or when even its existence would
reveal internal-only operating details that should not appear in the public
mirror.

Examples:

- agent memory
- private publication workflows
- private runbooks
- internal prompts
- internal operating notes whose existence is itself sensitive

## Core Principle

The public mirror should preserve reproducible shape whenever possible.

That means:

- preserve file paths when the path is part of the public contract
- preserve headings and sections when they support navigation
- preserve metadata keys when the schema matters
- preserve link roles or artifact slots when they support traceability
- sanitize private values instead of deleting the whole artifact when the
  structure itself is safe to reveal

Short form:

- redact payload, not evidence

## Sanitization Guidance

The updated guide should explicitly endorse patterns like:

- `specs: []`
- `plans: []`
- `related_docs: []`
- `private_notes: redacted in public mirror`
- section kept with a short public-safe summary instead of internal detail

Sanitization should preserve parseability and the semantic role of the file.

It should avoid:

- broken schemas
- headings with no explanation of why content is missing
- links to files that no longer exist without explanation
- deleting whole files when a thin but truthful public-safe version would work

## Reproducibility Contract

The revised guidance should introduce a lightweight public-mirror
reproducibility contract:

- required public artifacts should remain visible when they are part of the
  project's public-facing structure
- sanitized files should remain syntactically valid
- sanitized files should explain intentional redaction briefly when needed
- omission should be intentional, not a side effect of broad trimming

The contract should make it easier for a downstream reader to answer:

- what classes of artifacts exist
- which ones are public-facing
- which ones were intentionally redacted
- where private upstream detail has been withheld

## Guide Changes

Update `docs/operating_system/public-safe-doc-rewrite-guide.md` to:

- add the three-mode model: keep, sanitize, omit
- replace purely subtractive language with reproducibility-aware guidance
- add a section on preserving structural shape
- add concrete examples of sanitization patterns
- explain that private references inside a file do not automatically require
  deleting the file

The guide should also distinguish:

- file-level sensitivity
- field-level sensitivity
- section-level sensitivity

This is the key decision boundary for whether to omit or sanitize.

## Governance Skill Changes

Update `.agents/skills/skill-private-public-repo-governance/SKILL.md` so the skill
teaches the same three-mode classification.

It should stop implying that "private in part" means "omit in full."

It should teach agents and maintainers to prefer sanitization when:

- the file contributes to public reproducibility
- the schema or headings are safe to reveal
- sensitive values can be removed without misrepresenting the project

## Publication Workflow Changes

Update `docs/operating_system/procedures/publication-workflow.md` so publication review
asks:

- should this file be kept as-is?
- should it be kept and sanitized?
- should it be omitted entirely?

The workflow should explicitly warn against over-trimming files whose presence
helps the public mirror remain reproducible and trustworthy.

## Optional Config Follow-Up

Consider a later config or validation layer that distinguishes:

- forbidden paths
- sanitizable paths
- public-preserved paths

This follow-up is not required in the first implementation, but the spec should
leave room for it.

## Acceptance Criteria

The implementation is complete when:

- the rewrite guide teaches keep / sanitize / omit instead of only remove /
  omit instincts
- the guide includes explicit examples of preserving schema or headings while
  blanking private values
- the private/public governance skill reflects the same policy
- the publication workflow reflects the same decision model
- the resulting guidance explicitly protects reproducibility and structural
  fidelity in the public mirror

## Open Questions

- Which file classes in this repo most need explicit sanitization examples:
  manifests, metadata docs, indexes, or generated discovery?
- Should public-safe sanitization use a standard placeholder vocabulary such as
  `[]`, `redacted`, or `omitted from public mirror`?
- Should a later validation rule check that sanitized files remain syntactically
  valid and structurally faithful?
