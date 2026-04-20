# Mode B Example Migration

Use this example when a project has one legacy product feature contract and wants to migrate it into managed architecture metadata.

This is an example only. Replace `billing-insights` with the real product feature ID and keep operating-system adoption work out of `docs/features/`.

## Starting Point

The project has selected Mode B:

```yaml
adoption_mode: managed_architecture_metadata
managed_architecture_metadata: true
legacy_feature_contracts: false
architecture_generator: scripts/sync_architecture_docs.py
```

The legacy feature currently lives as a flat YAML file:

```text
docs/features/billing-insights.yaml
docs/stages/analytics.source.yaml
src/billing/reporting.py
tests/test_billing_reporting.py
```

## Target Shape

The feature should move to a managed folder:

```text
docs/features/billing-insights/
  feature.source.yaml
  billing-insights.yaml
  lineage.generated.yaml
  history.md
docs/stages/analytics.source.yaml
src/billing/reporting.py
tests/test_billing_reporting.py
```

Ownership:

- `feature.source.yaml` holds the human-owned feature meaning.
- `billing-insights.yaml` is generated or normalized current-state output.
- `lineage.generated.yaml` is generated evidence.
- `history.md` holds feature-local notes outside generated blocks.

## Example Sequence

1. Confirm `repo_config/adoption-mode.yaml` is set to `managed_architecture_metadata`.
2. Classify `billing-insights` as a real product feature, not starter adoption or repo-method work.
3. Create `docs/features/billing-insights/`.
4. Move semantic content from `docs/features/billing-insights.yaml` into `docs/features/billing-insights/feature.source.yaml`.
5. Normalize capabilities to feature-qualified stable IDs:

```yaml
capabilities:
  - capability_id: billing-insights.billing-revenue-summary
    name: Billing Revenue Summary
    summary: Summarize billed revenue by account and reporting period.
```

6. Update `docs/stages/analytics.source.yaml` so stage ownership references the feature:

```yaml
primary_features:
  - billing-insights
```

7. Update code and tests that feed lineage to reference canonical feature IDs and feature-qualified capability IDs:

```python
# @feature billing-insights
# @capability billing-insights.billing-revenue-summary
```

```python
# @proves billing-insights.billing-revenue-summary
```

8. Run the project architecture generator or sync workflow so generated feature contracts, lineage, and discovery come from source.
9. Remove the flat `docs/features/billing-insights.yaml` after the generated folder contract exists.
10. Validate:

```powershell
python scripts/validate_adoption_shape.py
git diff --check
```

11. Run the project test suite for the changed feature.
12. Commit only after source metadata, generated outputs, validation, and tests agree.

## What Not To Do

Do not leave both of these as authoritative current truth:

```text
docs/features/billing-insights.yaml
docs/features/billing-insights/feature.source.yaml
```

Do not create this feature for starter adoption, adapter work, publication setup, or agent rules. Those are operating-system concerns and belong in `docs/operating_system/` or operating-system specs/plans with explicit `targets`.
