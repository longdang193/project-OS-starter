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
    starter_sync: str = "",
    extra: str = "",
) -> None:
    write_text(
        root / "repo_config" / "adoption-mode.yaml",
        f"""adoption_mode: {mode}
managed_architecture_metadata: {str(managed).lower()}
legacy_feature_contracts: {str(legacy).lower()}
architecture_generator: {generator}
{starter_sync}\
{extra}""",
    )


def managed_starter_sync_block(extra: str = "") -> str:
    return """starter_sync:
  starter_baseline_ref: starter@2026-04-21
  last_shared_surface_review_at: "2026-04-21"
  reviewed_surface_classes:
    - repo_config
    - operating_system_docs
    - skills
    - adapters
    - generated_instruction_surfaces
    - validation_and_sync_scripts
""" + extra


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
        starter_sync=managed_starter_sync_block(),
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
        starter_sync=managed_starter_sync_block(),
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


def test_validator_rejects_missing_required_project_folder(tmp_path: Path) -> None:
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
        "docs/intent/README.md",
    ):
        write_text(tmp_path / relative_path, "# placeholder\n")
    (tmp_path / "docs" / "operating_system").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "superpowers" / "specs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "repo_config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    # Intentionally omit tests/ to exercise the required-folder rule.

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "missing required project folder" in result.stdout.lower()
    assert "tests/" in result.stdout


def test_validator_rejects_intent_folder_without_markdown_files(tmp_path: Path) -> None:
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
    (tmp_path / "docs" / "intent").mkdir(parents=True, exist_ok=True)
    write_text(tmp_path / "docs" / "intent" / "notes.txt", "placeholder\n")
    (tmp_path / "docs" / "operating_system").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "superpowers" / "specs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "superpowers" / "plans").mkdir(parents=True, exist_ok=True)
    (tmp_path / "repo_config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests").mkdir(parents=True, exist_ok=True)

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "intent layer must contain at least one markdown file" in result.stdout.lower()
    assert "docs/intent/" in result.stdout


def seed_required_folder_surface(root: Path) -> None:
    for relative_path in (
        "docs/intent/README.md",
        "docs/operating_system/repo-governance.md",
        "docs/operating_system/doc-system-lifecycle.md",
        "docs/superpowers/specs/README.md",
        "docs/superpowers/plans/README.md",
        "repo_config/adoption-mode.yaml",
        "scripts/README.md",
        "tests/README.md",
    ):
        if relative_path == "repo_config/adoption-mode.yaml":
            write_adoption_mode(
                root,
                "starter_method_only",
                managed=False,
                legacy=False,
            )
        else:
            write_text(root / relative_path, "# placeholder\n")


def test_validator_rejects_heading_only_required_doc(tmp_path: Path) -> None:
    seed_required_folder_surface(tmp_path)
    write_text(tmp_path / "docs" / "setup.md", "# Setup\n")
    write_text(
        tmp_path / "docs" / "configuration.md",
        "# Configuration\nConfiguration covers environment variables and profiles.\n",
    )
    write_text(
        tmp_path / "docs" / "usage.md",
        "# Usage\nUse the main command entrypoints in the normal run flow.\n",
    )
    write_text(
        tmp_path / "docs" / "pipeline.md",
        "# Pipeline\nThe workflow stages describe the end-to-end processing flow.\n",
    )
    write_text(
        tmp_path / "docs" / "architecture.md",
        "# Architecture\nMajor components and information flow define the system boundaries.\n",
    )

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "required doc must contain more than a heading" in result.stdout.lower()
    assert "docs/setup.md" in result.stdout


def test_validator_rejects_placeholder_only_required_doc(tmp_path: Path) -> None:
    seed_required_folder_surface(tmp_path)
    write_text(
        tmp_path / "docs" / "setup.md",
        "# Setup\nTODO placeholder. Fill this in later.\n",
    )
    write_text(
        tmp_path / "docs" / "configuration.md",
        "# Configuration\nConfiguration covers environment variables and profiles.\n",
    )
    write_text(
        tmp_path / "docs" / "usage.md",
        "# Usage\nUse the main command entrypoints in the normal run flow.\n",
    )
    write_text(
        tmp_path / "docs" / "pipeline.md",
        "# Pipeline\nThe workflow stages describe the end-to-end processing flow.\n",
    )
    write_text(
        tmp_path / "docs" / "architecture.md",
        "# Architecture\nMajor components and information flow define the system boundaries.\n",
    )

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "required doc is still placeholder-only" in result.stdout.lower()
    assert "docs/setup.md" in result.stdout


def test_validator_rejects_required_doc_without_semantic_coverage(tmp_path: Path) -> None:
    seed_required_folder_surface(tmp_path)
    write_text(
        tmp_path / "docs" / "setup.md",
        "# Setup\nDependencies and provisioning steps define the bootstrap order.\n",
    )
    write_text(
        tmp_path / "docs" / "configuration.md",
        "# Configuration\nConfiguration covers environment variables and profiles.\n",
    )
    write_text(
        tmp_path / "docs" / "usage.md",
        "# Usage\nThis document talks in general terms about collaboration habits and project background without explaining how to operate the system after setup.\n",
    )
    write_text(
        tmp_path / "docs" / "pipeline.md",
        "# Pipeline\nThe workflow stages describe the end-to-end processing flow.\n",
    )
    write_text(
        tmp_path / "docs" / "architecture.md",
        "# Architecture\nMajor components and information flow define the system boundaries.\n",
    )

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "required doc is missing expected semantic coverage" in result.stdout.lower()
    assert "docs/usage.md" in result.stdout


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


def test_validator_rejects_missing_starter_sync_record_in_managed_mode(tmp_path: Path) -> None:
    write_adoption_mode(
        tmp_path,
        "managed_architecture_metadata",
        managed=True,
        legacy=False,
        generator="scripts/sync_architecture_docs.py",
    )
    write_text(
        tmp_path / "docs" / "setup.md",
        "# Setup\nDependencies and install prerequisites define the bootstrap path.\n",
    )
    write_text(
        tmp_path / "docs" / "configuration.md",
        "# Configuration\nConfiguration covers environment variables, config files, defaults, and override ownership.\n",
    )
    write_text(
        tmp_path / "docs" / "usage.md",
        "# Usage\nUse the documented commands and entrypoints in the normal developer workflow.\n",
    )
    write_text(
        tmp_path / "docs" / "pipeline.md",
        "# Pipeline\nThe workflow stages and handoff sequence describe the processing flow.\n",
    )
    write_text(
        tmp_path / "docs" / "architecture.md",
        "# Architecture\nMajor components, boundaries, and information flow define the system integration shape.\n",
    )
    (tmp_path / "docs" / "intent").mkdir(parents=True, exist_ok=True)
    write_text(tmp_path / "docs" / "intent" / "README.md", "# Intent\nPurpose and outcomes.\n")
    (tmp_path / "docs" / "operating_system").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "superpowers" / "specs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "superpowers" / "plans").mkdir(parents=True, exist_ok=True)
    (tmp_path / "repo_config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests").mkdir(parents=True, exist_ok=True)

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "requires a starter_sync record" in result.stdout.lower()


def test_validator_rejects_incomplete_starter_sync_record_in_managed_mode(tmp_path: Path) -> None:
    write_adoption_mode(
        tmp_path,
        "managed_architecture_metadata",
        managed=True,
        legacy=False,
        generator="scripts/sync_architecture_docs.py",
        starter_sync="""starter_sync:
  starter_baseline_ref: ""
  last_shared_surface_review_at: not-a-date
  reviewed_surface_classes:
    - repo_config
  divergences:
    - path: ""
      class: not_a_real_class
      status: custom
      rationale: ""
""",
    )
    write_text(
        tmp_path / "docs" / "setup.md",
        "# Setup\nDependencies and install prerequisites define the bootstrap path.\n",
    )
    write_text(
        tmp_path / "docs" / "configuration.md",
        "# Configuration\nConfiguration covers environment variables, config files, defaults, and override ownership.\n",
    )
    write_text(
        tmp_path / "docs" / "usage.md",
        "# Usage\nUse the documented commands and entrypoints in the normal developer workflow.\n",
    )
    write_text(
        tmp_path / "docs" / "pipeline.md",
        "# Pipeline\nThe workflow stages and handoff sequence describe the processing flow.\n",
    )
    write_text(
        tmp_path / "docs" / "architecture.md",
        "# Architecture\nMajor components, boundaries, and information flow define the system integration shape.\n",
    )
    (tmp_path / "docs" / "intent").mkdir(parents=True, exist_ok=True)
    write_text(tmp_path / "docs" / "intent" / "README.md", "# Intent\nPurpose and outcomes.\n")
    (tmp_path / "docs" / "operating_system").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "superpowers" / "specs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "superpowers" / "plans").mkdir(parents=True, exist_ok=True)
    (tmp_path / "repo_config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests").mkdir(parents=True, exist_ok=True)

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "starter_sync.starter_baseline_ref must be a non-empty string" in result.stdout
    assert "starter_sync.last_shared_surface_review_at must be an iso-8601 date or timestamp" in result.stdout.lower()
    assert "starter_sync.reviewed_surface_classes is missing required mode b surface classes" in result.stdout.lower()
    assert "starter_sync.divergences[0].class must be one of the reviewed surface classes" in result.stdout.lower()

