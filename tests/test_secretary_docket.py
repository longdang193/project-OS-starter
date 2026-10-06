from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "docs/operating_system/templates/secretary-docket.yaml"


def test_secretary_docket_template_parses_as_empty_list() -> None:
    assert yaml.safe_load(TEMPLATE.read_text(encoding="utf-8")) == []


def test_secretary_docket_template_example_is_comments_only() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")

    assert "# - id:" in text
    assert "\n- id:" not in text
    assert "docs/superpowers/secretary-docket.yaml" not in text
