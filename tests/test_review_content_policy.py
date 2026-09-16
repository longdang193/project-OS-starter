from __future__ import annotations

from scripts import review_content_policy as policy


def test_protected_patterns_match_root_and_nested_paths() -> None:
    protected = [
        ".env",
        "config/.env.production",
        "service/app.private.json",
        "nested/cache.local.db",
    ]
    ordinary = [".envexample.txt", "private/config.json", "src/app.py", "local.txt"]

    assert all(policy.is_protected_path(path) for path in protected)
    assert all(not policy.is_protected_path(path) for path in ordinary)
    assert policy.PROTECTED_PATTERNS == (".env", ".env.*", "*.private.*", "*.local.*")


def test_inventory_policy_protects_both_sides_of_rename_and_copy() -> None:
    inventory = [
        {"status": "R", "old_path": "old/.env", "new_path": "new/config.py"},
        {"status": "C", "old_path": "source.local.txt", "new_path": "copy.txt"},
        {"status": "M", "new_path": "src/app.py"},
    ]

    result = policy.classify_inventory(inventory)

    assert result["protected_paths"] == ("old/.env", "new/config.py", "source.local.txt", "copy.txt")
    assert result["ordinary_paths"] == ("src/app.py",)
    assert result["protected_entries"][0]["old_path"] == "old/.env"
    assert result["protected_entries"][0]["new_path"] == "new/config.py"


def test_invalid_policy_path_rejected() -> None:
    try:
        policy.is_protected_path("../secret.env")
    except ValueError as exc:
        assert "unsafe path" in str(exc)
    else:
        raise AssertionError("unsafe path accepted")
