---
name: brainstorming
description: "You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation. Before writing the spec doc, invokes doc-system-lifecycle for the 5-layer doc system and planning-dispatch for the triage block."
---

# Brainstorming Ideas Into Designs

Help turn ideas into validated designs through structured dialogue.

<HARD-GATE>
Do NOT write code or implement anything before:
1. design is presented
2. user explicitly approves
</HARD-GATE>

---

## Core Principle

> Design → validate → then plan.  
> Do not skip classification or doc placement.

This skill produces **design only**.  
It does NOT produce implementation.

---

## Doc-System Alignment

Before writing any spec or doc, align with the 5-layer system:

```text
code/                                → real truth
docs/stages/*.source.yaml            → human-owned stage source when stage-aware docs are in scope
docs/stages/*.yaml                   → generated stage contracts when stage-aware docs are in scope
docs/features/*/feature.source.yaml  → human-owned feature source
docs/features/*/<feature_id>.yaml    → generated feature contract (current state)
docs/features/*/lineage.generated.yaml → generated feature-local evidence
docs/features/<feature_id>/          → feature-specific explanation + partial-generated history
docs/*.md                            → cross-cutting explanation
docs/generated/                      → discovery (auto)
README.md                            → overview
```

Rules:

- Specs live under `docs/superpowers/specs/`
- `feature.source.yaml` must exist before spec when a managed feature is changing; cross-cutting operating-system work may use `feature_source: none`
- The spec must link back to the affected `docs/features/<feature_id>/feature.source.yaml` and generated `docs/features/<feature_id>/<feature_id>.yaml` when they exist
- `<feature_id>` is placeholder notation; use the concrete feature-id filename in real docs, for example `docs/features/model-training-pipeline/model-training-pipeline.yaml`
- Use stage classification when the work is pipeline-heavy, architecture-heavy, or boundary-heavy
- Feature-specific explanation/history belongs under `docs/features/<feature_id>/`
- Cross-cutting explanation belongs under `docs/*.md`
- Stage-aware work should name both `docs/stages/<stage_id>.source.yaml` and
  `docs/stages/<stage_id>.yaml`
- When one feature folder is in scope, read minimally:
  - `feature.source.yaml` first
  - generated `<feature_id>.yaml` only when the assembled contract view is needed
  - `lineage.generated.yaml` only for ownership, evidence, or drift work
  - `history.md` only for narrative context
  - do not load the entire feature folder by default

---

## Checklist (Execution Order)

```text
1. **Explore context**

 - read code + `docs/features/*/feature.source.yaml` + generated `docs/features/*/<feature_id>.yaml`
 - when stage-aware work is central, read `docs/stages/<stage_id>.source.yaml`
   and the generated stage contract instead of only the generated stage path
- when one feature folder is in scope, prefer the smallest truthful reading set instead of loading every file in that folder
- check if feature already exists
- recent commits
- other docs
- when the task touches repo-operating behavior, known repeated issues, or unsettled harness areas, consult `docs/operating_system/agent_memory/*`

2. **Ask clarifying questions (one at a time)**

3. **Propose 2–3 approaches**

- include tradeoffs
- give recommendation

4. **Present design (incremental)**

- architecture
- components
- data flow
- constraints / invariants
- confirm with user

5. **Feature and Stage Alignment**

- identify `feature_id`
- identify affected stages when relevant
- decide the primary lens: stage | feature | mixed | cross-cutting
- classify: add / modify / replace
- name doc targets:
- feature source → `docs/features/<feature_id>/feature.source.yaml`
- feature contract → generated `docs/features/<feature_id>/<feature_id>.yaml`
- feature lineage → `docs/features/<feature_id>/lineage.generated.yaml` or `none`
- feature history → `docs/features/<feature_id>/history.md` or `none`
- stage source → `docs/stages/<stage_id>.source.yaml` or `none`
- stage contract → `docs/stages/<stage_id>.yaml` or `none`
- feature-specific docs → `docs/features/<feature_id>/<doc>.md` or `none`
- cross-cutting docs → `docs/<doc>.md` or `docs/operating_system/<doc>.md` or `none`
- README → `README.md` or `none`
- generated discovery → `docs/generated/<file>` or `none`
- confirm:
- new feature → create `feature.source.yaml`
- existing → update `feature.source.yaml`
- cross-cutting operating-system or method change → `feature_source: none` is allowed

6. **Invoke planning-dispatch**

- produce triage block
- confirm routing → writing-plans

7. **Write spec**

- save to `docs/superpowers/specs/YYYY-MM-DD-HH-MM-<topic>-spec.md`
- follow frontmatter rules
- link the spec to the affected `docs/features/<feature_id>/feature.source.yaml` and generated contract

8. **Spec review loop**

- review → fix → repeat (max 3)

9. **User approval**

10. **Handoff**

- invoke writing-plans
```

---

## Process Flow (Updated)

```text
Explore context
  ↓
Ask questions
  ↓
Propose approaches
  ↓
Present design
  ↓
User approval
  ↓
Feature and stage alignment
  ↓
planning-dispatch (triage)
  ↓
Write spec
  ↓
Review loop
  ↓
User approval
  ↓
writing-plans
```

---

## Design Rules

- prefer small, well-bounded components
- avoid over-engineering (YAGNI)
- follow existing patterns in repo
- improve locally if needed (not global refactor)

Each unit must answer:

- what it does
- how to use it
- what it depends on

---

## Spec Writing Rules

- spec belongs in `docs/superpowers/specs/`
- `feature.source.yaml` = human-owned meaning; generated feature YAML = current state
- spec = explanation + design
- spec must name the affected `docs/features/<feature_id>/feature.source.yaml` and generated `docs/features/<feature_id>/<feature_id>.yaml` when one exists
- stage-heavy specs should also name affected stages, the primary lens, and the
  `stage_source` / `stage_contract` targets
- spec should name any feature-specific docs or cross-cutting docs it expects to be updated

### Required frontmatter

```yaml
---
feature_type: add | modify | replace
feature_name: <feature_id>
status: draft | building
summary: "<1-line goal>"
---
```

Optional:

```yaml
invariants:
  - constraint
```

---

## Anti-Patterns

- writing spec before feature classification
- writing spec without classifying affected stages when the work is clearly boundary-heavy
- writing spec without linking the affected feature source when one exists
- assuming `FEATURES.md`
- mixing design + implementation
- skipping YAML alignment
- generating global design docs

