# Mode B Feature Migration Checklist

Use this checklist when migrating one real product feature into managed architecture metadata.

- [ ] Confirm `repo_config/adoption-mode.yaml` uses `managed_architecture_metadata`.
- [ ] Classify the candidate as a real product feature, not operating-system method work.
- [ ] Create `docs/features/<feature_id>/`.
- [ ] Copy `feature.source.yaml` and replace all example IDs and prose.
- [ ] Use feature-qualified capability IDs: `<feature_id>.<capability_slug>`.
- [ ] Copy `history.md` and replace the heading.
- [ ] Create or update `docs/stages/<stage_id>.source.yaml`.
- [ ] Add Python `@meta` ownership metadata where source files own feature behavior.
- [ ] Add one canonical `@capability` marker for each active capability.
- [ ] Add test `@proves` markers for capability proof evidence.
- [ ] Add YAML `# @architecture` metadata only where configs or components materially participate.
- [ ] Add markdown frontmatter only to docs that materially explain the feature, stage, or capability.
- [ ] Run `python scripts/sync_architecture_docs.py`.
- [ ] Run `python scripts/validate_adoption_shape.py`.
- [ ] Run `python scripts/sync_architecture_docs.py --check`.
- [ ] Run the relevant project test suite.
- [ ] Commit only when source metadata, generated outputs, validation, and tests agree.
