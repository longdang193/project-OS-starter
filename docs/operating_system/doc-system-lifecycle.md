# Doc System Lifecycle

This document defines the source-of-truth model for project docs.

## Core Principle

Documentation should let a human or agent answer:

- what exists
- what is current
- what changed
- why it changed
- where the real source of truth lives

Docs explain code. They do not replace it.

## Source-Of-Truth Layers

```text
code/                        -> real truth
docs/stages/*.source.yaml    -> human-owned stage source when stage-aware docs are in scope
docs/stages/*.yaml           -> generated stage contracts when stage-aware docs are in scope
docs/features/*/feature.source.yaml -> human-authored feature metadata source when adopted
docs/features/*/*.yaml       -> structured current-state truth, generated for opted-in features
docs/features/*/lineage.generated.yaml -> generated feature-local evidence and timeline facts
docs/features/<feature_id>/  -> feature explanation and human history
docs/*.md                    -> cross-cutting product docs
docs/operating_system/*.md   -> repo rules and workflows
README.md                    -> overview
docs/generated/*             -> generated discovery indexes
```

## Placement Rules

### Code

Use code for:

- runtime behavior
- routes and APIs
- validation logic
- data and schema logic

### `repo_config/`

Use repo/system config for:

- publication boundaries
- adapter generation mappings
- other repo-owned system configuration

### `configs/`

Use runtime/workflow config for:

- training settings
- monitoring settings
- asset manifests
- smoke profiles

### `docs/features/*/*.yaml`

Use feature YAML for:

- current feature contracts
- identity, status, dependencies, capabilities, refs

For active features, `feature.source.yaml` is the human-owned source and the
concrete feature-id contract, for example `model-training-pipeline.yaml`, is
generated from source metadata plus code/test/doc/spec/plan markers.
`<feature_id>` is a placeholder in docs, not a literal filename to create.

Generated feature contracts may include freshness metadata such as
`last_updated_at`, `latest_change_id`, and `revision` when completed-plan
metadata exists. Those values are generated and should not be stored manually in
`feature.source.yaml`.

These files are not replacements for runtime/workflow config under `configs/`.

Formatting rule:

- keep human-authored feature source YAML readable
- do not manually edit generated feature YAML files with the `GENERATED FILE`
  header
- do not use `manual_refs`; generated refs come from metadata on the owning
  code, tests, docs, specs, and plans
- quote strings only when YAML requires it or exact literal preservation depends on it
- avoid unnecessary quotes on ordinary prose entries
- preserve field order unless the schema owner intentionally changes it
- use `.\scripts\format_contract_yaml.py` as the canonical normalization/check path for human-authored feature/stage YAML
- use `tools\docs\generate_architecture_metadata.py` as the canonical refresh/check path for opted-in generated feature contracts and discovery indexes

### `docs/stages/*.source.yaml` And Generated Stage Contracts

Stage source files are human-owned workflow-boundary maps. They may contain
stable intent such as purpose, workflow position, primary features, inputs,
outputs, transition points, and short human notes.

Generated stage contracts at `docs/stages/<stage_id>.yaml` assemble refs from
metadata. Do not manually edit generated fields such as `feature_refs`,
`capability_refs`, `code_refs`, `test_refs`, `doc_refs`, `config_refs`, or
`component_refs`.

Stage refs come from:

- feature source metadata
- canonical code markers
- test proof markers
- docs frontmatter such as `explains.stages`
- YAML `# @architecture` metadata in configs and AML components

Supporting helper awareness belongs in `docs/generated/architecture_dag.yaml`
rather than primary stage refs.

### `docs/features/*/lineage.generated.yaml`

Use feature-local generated lineage for:

- capability and invariant evidence
- code, test, spec, plan, and doc links
- Python file ownership from `@meta`
- setup-script ownership from bounded `@meta` blocks in `setup/*.ps1` and `setup/*.sh`
- canonical function evidence from `@capability`
- test proof evidence from `@proves`
- optional docs explanation evidence from `doc_id` / `explains` frontmatter
- generated timeline facts from completed plan metadata
- evidence gaps for active capabilities

This is the canonical detailed generated evidence surface for an opted-in
feature. Do not duplicate the same machine-readable evidence in `history.md` or
global generated indexes.

For active capabilities, this file also reports lineage completeness:

- `complete` means the capability has the required evidence
- `excepted` means the capability still has a declared temporary gap allowed by
  `feature.source.yaml > lineage_exceptions`
- `incomplete` means the capability has unresolved evidence gaps and the
  validator should fail

Do not edit these values directly in generated files. Update source metadata,
code ownership markers, test proof markers, or the narrow exception block in
`feature.source.yaml`, then regenerate.

Selective reading rule for opted-in feature folders:

- read `feature.source.yaml` first because it is the human-owned source
- read the generated `<feature_id>.yaml` only when the current assembled contract view is needed
- read `lineage.generated.yaml` for ownership, evidence, drift, or traceability work
- read `history.md` or other feature prose only when explanation or chronology is needed
- do not load the entire feature folder by default

### `docs/features/<feature_id>/`

Use feature-specific docs for:

- architecture
- focused flows
- human-authored feature history
- summarized cloud validation evidence for one feature

Feature history should explain meaning, nuance, and operator context. The repo
now treats it as a partial-generated surface:

- the generator owns the block between `<!-- GENERATED HISTORY START -->` and
  `<!-- GENERATED HISTORY END -->`
- humans own the `## Human Notes` section below that block
- manual notes should add context, not restate machine-readable lineage facts

### `docs/*.md`

Use cross-cutting docs for:

- product architecture
- setup
- shared user/operator guidance

Human-authored docs that materially explain features, capabilities, stages,
configs, components, or operator workflows may use lightweight frontmatter such
as `doc_id`, `doc_type`, and `explains.features` / `explains.capabilities` /
`explains.stages` / `explains.configs` / `explains.components`. Do not add
frontmatter to every markdown file by default.

### `docs/operating_system/*.md`

Use operating-system docs for:

- repo governance
- publication workflow
- planning rules
- tooling policy
- instruction layering

They may describe config ownership rules, but they are not the config surfaces
themselves.

### `docs/generated/*`

Use generated discovery for:

- aggregate indexes
- summaries
- lookup surfaces

Generated files must not be edited manually.

Current repo note:

- `docs/generated/architecture_dag.yaml` and
  `docs/generated/capability_lineage.yaml` are adopted generated discovery
  indexes for architecture metadata
- detailed capability evidence lives beside each opted-in feature in
  `docs/features/<feature_id>/lineage.generated.yaml`
- do not invent unrelated generated discovery files just to satisfy the abstract
  doc model
- refresh adopted generated discovery with
  `tools\docs\generate_architecture_metadata.py`
- when publishing public docs, omit or scrub feature-local lineage if it exposes
  private-only spec, plan, operating-system, or agent paths

## Sync Principle

When behavior or structure changes:

- update code
- update the owning feature YAML when a feature contract changes
- update `feature.source.yaml`, not the generated concrete feature-id YAML, when active
  feature meaning changes
- update feature docs or cross-cutting docs as needed
- update operating-system docs when repo rules or workflows change
- refresh generated feature contracts and discovery from source layers when
  feature/source/spec/plan/code/test/doc metadata changes
- keep generated timeline facts in feature-local lineage, not in feature
  history prose blocks
- refresh partial-generated feature histories when completed plan metadata
  changes for an affected feature
- normalize feature/stage YAML with `.\scripts\format_contract_yaml.py` when
  contract-formatting drift is introduced or cleaned up

Canonical architecture sync/check workflow:

```powershell
.\.venv\Scripts\python.exe scripts/sync_architecture_docs.py
.\.venv\Scripts\python.exe scripts/sync_architecture_docs.py --check
```

Lineage exception policy:

- keep exceptions source-owned in `feature.source.yaml`
- keep the allowed gap vocabulary intentionally small
- treat exceptions as temporary rollout bridges, not permanent proof
- prefer adding missing `@meta`, `@capability`, `@proves`, or doc/spec/plan
  metadata when the real owner already exists
- let the validator fail rather than leaving silent active gaps

## Practical Heuristic

Use the deepest layer that owns the fact:

- behavior -> code
- feature state -> feature YAML
- feature explanation -> feature docs
- dated feature validation evidence -> feature history or focused feature ops docs
- generated plan-change timeline facts -> the generated block inside feature history
- downloaded runtime artifacts -> evidence inputs, not source docs
- repo workflow -> operating-system docs
- navigation -> README or generated discovery when that layer exists
