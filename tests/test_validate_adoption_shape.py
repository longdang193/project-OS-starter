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

