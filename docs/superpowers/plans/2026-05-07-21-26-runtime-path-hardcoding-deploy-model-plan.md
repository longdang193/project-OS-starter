---
layer: operating_system
artifact_type: plan
status: proposed
template_id: implementation-plan
name: runtime-path-hardcoding-deploy-model
parent_workstream: none
related_features: []
related_stages: []
targets:
  - repo_config/
  - scripts/
  - docs/operating_system/
  - .agents/skills/
  - generated_agents/
---

# Runtime Path Hardcoding Deploy Model Plan

## Goal

Introduce a deploy-time runtime rendering model where canonical repository sources keep repo-relative or logical paths, while generated runtime surfaces rewrite all executable and file-reference paths into machine-specific absolute paths.

## Key Deliverables

- A documented path-resolution model that separates canonical source paths from runtime absolute paths.
- A runtime configuration contract that defines repo-root and runtime-root base paths.
- Generator/deploy logic that rewrites canonical paths into absolute runtime paths in generated surfaces.
- Validation coverage that checks canonical-source integrity and generated-runtime correctness separately.
- Updated governance and runtime documentation that explains the absolute-path deployment model and cross-PC regeneration workflow.

## Task Breakdown

- task 1: define the canonical vs runtime path model
  - Document path classes and allowed transforms.
  - Define which fields remain repo-relative in canonical source.
  - Define which generated/runtime fields must become absolute.
  - Explicitly distinguish repo-root-resolved paths from global-runtime-resolved paths.
  - Record non-goals, especially that canonical repo source must not be rewritten to machine-specific paths.

- task 2: define runtime configuration inputs
  - Add or update config that captures the deploy-time base paths.
  - Define at least two path bases:
    - repo root absolute path for repo-owned files such as `docs/`, `scripts/`, `.agents/`, `repo_config/`, and `tests/`
    - runtime root absolute path for deployed global execution surfaces such as global skill executables
  - Define precedence rules for those values, including explicit deploy input versus derived defaults.
  - Document how config changes on a new PC trigger regeneration instead of source edits.

- task 3: inventory canonical path-bearing fields and command surfaces
  - Audit generated skill/runtime surfaces for fields such as:
    - `required_reads`
    - `required_outputs` where runtime expansion is intended
    - hook commands
    - generated provenance or source-reference fields when runtime-first rendering is desired
  - Audit generator inputs that currently emit relative paths.
  - Classify each field as one of:
    - repo-relative canonical only
    - runtime absolute path required
    - runtime command rewrite required
    - preserve canonical provenance even in generated output
  - Produce an explicit mapping table for each supported field type.

- task 4: implement deploy-time path rendering rules
  - Update the relevant sync/deploy generator logic to rewrite supported fields during runtime generation.
  - Implement repo-owned path expansion from the resolved repo root.
  - Implement runtime executable path expansion from the resolved runtime root.
  - Rewrite hook commands from canonical local forms such as `python scripts/run_central_config_checks.py` into concrete runtime executable commands when configured.
  - Preserve canonical source files unchanged in the repo.
  - Ensure rendering is deterministic and repeatable across runs.

- task 5: define source-to-runtime mapping contracts
  - Create a mapping contract for canonical hook forms to runtime executable paths.
  - Define examples such as:
    - `python scripts/run_central_config_checks.py`
    - to `py "<runtime_root>\skills\central-config-layer\run_checks.py"`
  - Define examples for `required_reads` expansion such as:
    - `docs/operating_system/governance/repo-governance.md`
    - to `"<repo_root>\docs\operating_system\governance\repo-governance.md"`
  - Specify how quoting and Windows path escaping are rendered.

- task 6: update validators and tests
  - Add tests for canonical-source preservation so repo-authored files stay relative/logical.
  - Add tests for generated/runtime surfaces so deployed outputs contain absolute paths where required.
  - Add tests for repo-root-based expansion versus runtime-root-based expansion.
  - Add tests for missing-config and missing-runtime-surface failure modes.
  - Decide whether fast validator scope should check only canonical surfaces, or also verify generated runtime path rendering when deploy outputs are present.

- task 7: update docs and governance
  - Update repo governance docs to explain:
    - canonical source path policy
    - generated runtime hardcoded path policy
    - cross-PC redeploy expectations
  - Update relevant skill/governance docs that mention generated/runtime outputs.
  - Document that changing PCs requires updating base config and redeploying runtime, not manually editing canonical sources.
  - If needed, document whether generated runtime `Source:` metadata is canonical provenance, runtime location, or both.

- task 8: roll out incrementally
  - Start with one small slice, such as one skill family or one generated adapter surface.
  - Verify generated diffs are correct and readable.
  - Expand the renderer to all supported generated surfaces after the first slice is stable.
  - Re-run generator sync and validator flows after each expansion.
  - Avoid a broad one-shot rewrite until field classification and tests are stable.

- task 9: define migration and fallback behavior
  - Specify how existing generated outputs transition from relative paths to absolute runtime paths.
  - Decide whether deploy can run in a compatibility mode before full absolute-path enforcement.
  - Define clear failure messages when a canonical hook cannot be mapped to a runtime executable.
  - Define fallback behavior for repos or environments that do not install the global runtime surface.

## Verification

- `py scripts/hooks/run_validator.py --fast`
- `py scripts/sync_agent_adapters.py`
- `py scripts/sync_agent_adapters.py --check`
- targeted test command for the updated generator and path-rendering logic
- targeted test command for updated governance and metadata validation surfaces

## Completion Criteria

A plan item is considered complete when:

1. canonical repo files continue to store repo-relative or logical path forms only
2. generated runtime surfaces render supported path fields as absolute machine-specific paths
3. repo-root path fields and runtime-root executable fields are expanded by the correct resolver
4. generator behavior is documented, deterministic, and covered by tests
5. runtime regeneration on a second machine requires only base-config changes plus redeploy
6. validators pass after sync, and generated outputs are up to date
