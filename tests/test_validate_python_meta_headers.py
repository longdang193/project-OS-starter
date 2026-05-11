from pathlib import Path

from scripts.validate_python_meta_headers import validate_python_meta_headers


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_capability_linkage_passes_with_known_feature_capability(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "features" / "fitcv" / "feature.source.yaml",
        """
capabilities:
  - capability_id: fitcv.valid-capability
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "src" / "pkg" / "module.py",
        '"""@meta\nname: module\ntype: module\ndomain: runtime\nownership: feature\nresponsibility:\n  - do thing\ninputs:\n  - in\noutputs:\n  - out\ncapabilities:\n  - fitcv.valid-capability\nlifecycle:\n  status: active\n"""\n',
    )

    issues = validate_python_meta_headers(
        tmp_path,
        ["src"],
        enforce_capability_linkage=True,
        require_ownership=True,
        require_feature_capabilities=True,
    )

    assert issues == []


def test_capability_linkage_fails_with_unknown_capability(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "features" / "fitcv" / "feature.source.yaml",
        """
capabilities:
  - capability_id: fitcv.valid-capability
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "src" / "pkg" / "module.py",
        '"""@meta\nname: module\ntype: module\ndomain: runtime\nownership: feature\nresponsibility:\n  - do thing\ninputs:\n  - in\noutputs:\n  - out\ncapabilities:\n  - fitcv.unknown-capability\nlifecycle:\n  status: active\n"""\n',
    )

    issues = validate_python_meta_headers(
        tmp_path,
        ["src"],
        enforce_capability_linkage=True,
        require_ownership=True,
        require_feature_capabilities=True,
    )

    assert any("unknown @meta capability `fitcv.unknown-capability`" in issue for issue in issues)


def test_lifecycle_requires_status_entry(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "pkg" / "module.py",
        '"""@meta\nname: module\ntype: module\ndomain: runtime\nownership: infrastructure\nresponsibility:\n  - do thing\ninputs:\n  - in\noutputs:\n  - out\nlifecycle:\n  - active\n"""\n',
    )

    issues = validate_python_meta_headers(tmp_path, ["src"], require_ownership=True)

    assert any("`lifecycle` must include `status`" in issue for issue in issues)


def test_feature_ownership_requires_capabilities(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "pkg" / "module.py",
        '"""@meta\nname: module\ntype: module\ndomain: runtime\nownership: feature\nresponsibility:\n  - do thing\ninputs:\n  - in\noutputs:\n  - out\nlifecycle:\n  status: active\n"""\n',
    )

    issues = validate_python_meta_headers(
        tmp_path,
        ["src"],
        require_ownership=True,
        require_feature_capabilities=True,
    )

    assert any("`ownership: feature` requires non-empty `capabilities`" in issue for issue in issues)


def test_missing_ownership_fails_when_required(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "pkg" / "module.py",
        '"""@meta\nname: module\ntype: module\ndomain: runtime\nresponsibility:\n  - do thing\ninputs:\n  - in\noutputs:\n  - out\nlifecycle:\n  status: active\n"""\n',
    )

    issues = validate_python_meta_headers(tmp_path, ["src"], require_ownership=True)

    assert any("`ownership` must be `feature` or `infrastructure`" in issue for issue in issues)


def test_infrastructure_allows_missing_capabilities(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "pkg" / "module.py",
        '"""@meta\nname: module\ntype: module\ndomain: validation\nownership: infrastructure\nresponsibility:\n  - validate thing\ninputs:\n  - in\noutputs:\n  - out\nlifecycle:\n  status: active\n"""\n',
    )

    issues = validate_python_meta_headers(
        tmp_path,
        ["src"],
        require_ownership=True,
        require_feature_capabilities=True,
    )

    assert issues == []

