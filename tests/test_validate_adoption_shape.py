"""
@meta
type: test
scope: unit
domain: docs
covers:
  - Adoption mode validation for starter, managed, and legacy architecture-doc states
  - Guardrails against method-layer pseudo-features and mixed feature contract shapes
excludes:
  - Full downstream project migration
  - Architecture metadata generation
  - CI workflow wiring

tags:
  - fast
  - ci-safe
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = REPO_ROOT / "scripts" / "validate_adoption_shape.py"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_validator(repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--repo-root", str(repo_root)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def write_adoption_mode(
    root: Path,
    mode: str,
    managed: bool,
    legacy: bool,
    generator: str = "none",
    extra: str = "",
) -> None:
    write_text(
        root / "repo_config" / "adoption-mode.yaml",
        f"""adoption_mode: {mode}
managed_architecture_metadata: {str(managed).lower()}
legacy_feature_contracts: {str(legacy).lower()}
architecture_generator: {generator}
{extra}""",
    )


def test_validator_passes_for_current_starter_repo() -> None:
    result = run_validator(REPO_ROOT)

    assert result.returncode == 0
    assert "adoption shape validation passed" in result.stdout.lower()


def test_validator_rejects_mode_boolean_mismatch(tmp_path: Path) -> None:
    write_adoption_mode(tmp_path, "managed_architecture_metadata", managed=False, legacy=False)

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "booleans do not match" in result.stdout.lower()


def test_validator_rejects_method_layer_pseudo_feature(tmp_path: Path) -> None:
    write_adoption_mode(tmp_path, "legacy_compatibility", managed=False, legacy=True)
    write_text(
        tmp_path / "docs" / "features" / "repo-operating-system.yaml",
        """repo-operating-system:
  depends_on: []
  capabilities: []
""",
    )

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "method-layer pseudo-feature" in result.stdout.lower()
    assert "repo-operating-system" in result.stdout


def test_validator_rejects_flat_feature_yaml_in_managed_mode(tmp_path: Path) -> None:
    write_adoption_mode(
        tmp_path,
        "managed_architecture_metadata",
        managed=True,
        legacy=False,
        generator="scripts/sync_architecture_docs.py",
    )
    write_text(tmp_path / "docs" / "features" / "data-pipeline.yaml", "depends_on: []\n")

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "flat authoritative feature yaml" in result.stdout.lower()


def test_validator_rejects_managed_contract_beside_flat_contract_in_legacy_mode(
    tmp_path: Path,
) -> None:
    write_adoption_mode(
        tmp_path,
        "legacy_compatibility",
        managed=False,
        legacy=True,
        extra="""migration_follow_up:
  required: true
  target: docs/superpowers/plans/migrate.md
""",
    )
    write_text(tmp_path / "docs" / "features" / "data-pipeline.yaml", "depends_on: []\n")
    write_text(
        tmp_path / "docs" / "features" / "data-pipeline" / "data-pipeline.yaml",
        "depends_on: []\n",
    )

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "beside a flat authoritative contract" in result.stdout.lower()


def test_validator_rejects_invalid_capability_ids(tmp_path: Path) -> None:
    write_adoption_mode(tmp_path, "legacy_compatibility", managed=False, legacy=True)
    write_text(
        tmp_path / "docs" / "features" / "data-pipeline.yaml",
        """depends_on: []
capability_ids:
  - "Staging: flatten GA4 events"
""",
    )

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "invalid capability id" in result.stdout.lower()


def test_validator_rejects_missing_required_root_docs(tmp_path: Path) -> None:
    write_adoption_mode(
        tmp_path,
        "managed_architecture_metadata",
        managed=True,
        legacy=False,
        generator="scripts/sync_architecture_docs.py",
    )
    write_text(
        tmp_path / "docs" / "features" / "data-pipeline" / "feature.source.yaml",
        """feature_id: data-pipeline
name: Data Pipeline
status: active
type: workflow
summary: Pipeline summary.
invariants: []
domains: []
depends_on: []
capabilities: []
stage_participation: []
lineage_exceptions: []
""",
    )
    write_text(tmp_path / "docs" / "features" / "data-pipeline" / "history.md", "# History\n")
    write_text(tmp_path / "docs" / "features" / "data-pipeline" / "lineage.generated.yaml", "features: {}\n")
    write_text(tmp_path / "docs" / "features" / "data-pipeline" / "data-pipeline.yaml", "feature_id: data-pipeline\n")

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "missing required root project doc" in result.stdout.lower()
    assert "docs/setup.md" in result.stdout


def test_validator_rejects_bare_capability_ids_in_managed_metadata_template(
    tmp_path: Path,
) -> None:
    write_adoption_mode(
        tmp_path,
        "starter_method_only",
        managed=False,
        legacy=False,
    )
    for relative_path in (
        "docs/setup.md",
        "docs/configuration.md",
        "docs/usage.md",
        "docs/pipeline.md",
        "docs/architecture.md",
    ):
        write_text(tmp_path / relative_path, "# placeholder\n")
    write_text(
        tmp_path / "docs" / "architecture_templates" / "feature.source.yaml",
        """feature_id: billing-insights
name: Billing Insights
status: active
type: workflow
summary: Summarize billing activity for operator reporting.
domains:
  - billing
depends_on: []
invariants:
  - invariant_id: billing-inputs-validated
    name: Billing Inputs Validated
    statement: Billing reports use validated billing records only.
    state: active
capabilities:
  - capability_id: billing-insights.billing-revenue-summary
    name: Billing Revenue Summary
    summary: Summarize billed revenue by account and reporting period.
    state: active
stage_participation:
  - stage_id: analytics
    role: primary
    capability_ids:
      - billing-revenue-summary
lineage_exceptions: []
""",
    )

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "template capability_ids must use feature-qualified ids" in result.stdout.lower()
    assert "docs/architecture_templates/feature.source.yaml" in result.stdout


def test_validator_rejects_bare_capability_ids_in_yaml_architecture_template(
    tmp_path: Path,
) -> None:
    write_adoption_mode(
        tmp_path,
        "starter_method_only",
        managed=False,
        legacy=False,
    )
    for relative_path in (
        "docs/setup.md",
        "docs/configuration.md",
        "docs/usage.md",
        "docs/pipeline.md",
        "docs/architecture.md",
    ):
        write_text(tmp_path / relative_path, "# placeholder\n")
    write_text(
        tmp_path / "docs" / "architecture_templates" / "yaml-architecture.yaml",
        """# @architecture
# owner: billing-insights
# features:
#   - billing-insights
# stages:
#   - analytics
# capabilities:
#   - billing-revenue-summary
# role: config
# canonical: true
""",
    )

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "yaml architecture template capabilities must use feature-qualified ids" in result.stdout.lower()
    assert "docs/architecture_templates/yaml-architecture.yaml" in result.stdout


def test_validator_rejects_bare_capability_ids_in_markdown_frontmatter_template(
    tmp_path: Path,
) -> None:
    write_adoption_mode(
        tmp_path,
        "starter_method_only",
        managed=False,
        legacy=False,
    )
    for relative_path in (
        "docs/setup.md",
        "docs/configuration.md",
        "docs/usage.md",
        "docs/pipeline.md",
        "docs/architecture.md",
    ):
        write_text(tmp_path / relative_path, "# placeholder\n")
    write_text(
        tmp_path / "docs" / "architecture_templates" / "markdown-frontmatter.md",
        """# Markdown Frontmatter Template

```md
---
doc_id: billing-insights-operator-guide
doc_type: guide
explains:
  features:
    - billing-insights
  capabilities:
    - billing-revenue-summary
  stages:
    - analytics
---
```
""",
    )

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "frontmatter template capabilities must use feature-qualified ids" in result.stdout.lower()
    assert "docs/architecture_templates/markdown-frontmatter.md" in result.stdout

