---
layer: operating_system
artifact_type: spec
status: proposed
template_id: detailed-specification
name: publication-doc-boundary-refactor-spec
parent_workstream: none
targets:
  - docs/operating_system/publication/public-repo-publication-policy.md
  - docs/operating_system/publication/public-repo-publishing.md
  - docs/operating_system/publication/public-safe-doc-rewrite-guide.md
  - docs/operating_system/procedures/publication-procedure.md
  - .agents/skills/skill-private-public-repo-governance/SKILL.md
related_features: []
related_stages: []
---

# Detailed Specification: Publication Documentation Boundary Refactor

## Goal

Eliminate overlap across publication governance docs by assigning single-purpose ownership to each document, then update all referencing surfaces so publication policy is authoritative, publishing steps are procedural, and rewrite guidance is sanitization-specific.

## Key Deliverables

### Deliverable 1: Clear ownership contract for publication docs

Define and enforce unique scope for:

- `public-repo-publication-policy.md` (normative rules)
- `public-repo-publishing.md` (execution runbook)
- `public-safe-doc-rewrite-guide.md` (sanitization playbook)

### Deliverable 2: Cross-reference realignment across repo surfaces

Update files that mention these docs so links and wording route readers to correct owner doc without duplicating policy/process content.

### Deliverable 3: Governance skill binding

Ensure `skill-private-public-repo-governance` explicitly references publication docs and states precedence expectations for boundary rules.

## Design Analysis

### Current state

- three publication documents contain overlapping policy, runbook, and rewrite guidance
- downstream references can preserve ambiguity when ownership is not explicit

### Constraints

- each content type needs one canonical owner
- summaries may link to canonical detail but must not restate it
- active references and governance skill wording must follow the surviving boundaries

### Alternatives

- keep overlapping documents: rejected because drift remains
- consolidate all publication content into one document: rejected because policy, runbook, and rewrite methods have distinct owners
- preserve three focused documents with explicit boundaries: selected

## Design Decisions

### Decision: policy doc is sole normative authority

- context: policy statements currently repeated in runbook and rewrite guide
- choice: keep all mandatory boundary rules only in `public-repo-publication-policy.md`
- alternatives considered:
  - split policy rules across all three docs
  - keep policy duplicated for convenience
- impact:
  - removes rule drift risk
  - requires strong cross-linking for discoverability

### Decision: publishing doc is procedure-only

- context: procedural and normative content currently mixed
- choice: `public-repo-publishing.md` owns sequence, commands, and operator gates only
- alternatives considered:
  - hybrid policy+procedure document
- impact:
  - execution clarity improves
  - policy updates no longer require runbook edits unless workflow changes

### Decision: rewrite guide owns sanitization patterns only

- context: rewrite examples and publication rules are entangled
- choice: `public-safe-doc-rewrite-guide.md` owns keep/sanitize/omit patterns, examples, and anti-pattern rewrites
- alternatives considered:
  - fold rewrite guidance into publishing doc
- impact:
  - keeps tactical rewrite logic decoupled from publication governance

### Decision: governance skill must mention publication docs explicitly

- context: users route via skill; missing doc mentions causes indirect drift
- choice: add canonical publication-doc references in `skill-private-public-repo-governance/SKILL.md` plus precedence note
- alternatives considered:
  - rely on implicit links in other docs
- impact:
  - improves routing reliability and policy adherence during agent use

## Invariants

- each publication concern has one canonical document owner.
- policy rules are not duplicated as normative text in runbook or rewrite guide.
- runbook references policy for boundary authority.
- rewrite guide references policy (why) and runbook (when) without redefining either.
- governance skill explicitly lists publication documents.
- reference surfaces link to canonical owner docs.

## Acceptance Criteria

- ownership table for three publication docs is documented and applied.
- no section-level normative duplication remains across three docs.
- all files referencing these docs point to correct canonical owner for intent.
- governance skill includes publication doc mention block and precedence note.
- future reader can answer “rule vs process vs rewrite” from doc placement alone.

## Non-Goals

- changing publication runtime behavior or script logic.
- introducing new publication validation engines.
- rewriting unrelated operating-system procedures.

## Risks and Mitigations

- risk: over-trimming useful context from one doc
  - mitigation: allow short summary + canonical link, prohibit full duplication

- risk: stale references in plans/specs
  - mitigation: repository-wide mention scan and targeted link update checklist

- risk: skill wording conflicts with policy docs
  - mitigation: add explicit precedence statement: policy doc wins for boundary rules

## Validation Plan

- proof target: overlap removed across three publication docs
  - method: section-by-section inspection against ownership table
  - evidence: review checklist showing each section mapped to single owner

- proof target: references updated in all mention files
  - method: repository text search for three filenames and manual link classification
  - evidence: reference inventory with “correct owner” status per file

- proof target: governance skill mentions publication docs
  - method: inspect `skill-private-public-repo-governance/SKILL.md`
  - evidence: explicit publication-doc list and precedence statement present

- proof target: no policy/process confusion remains
  - method: reviewer scenario test (ask where rule/procedure/rewrite belongs)
  - evidence: unambiguous answers using doc boundaries only

## Completion Criteria

1. publication doc boundary contract approved and documented.
2. mention inventory captured for all three docs.
3. governance skill publication-doc reference requirement specified.
4. spec accepted as handoff input for implementation planning.

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `docs/operating_system/templates/detailed-specification-template.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
