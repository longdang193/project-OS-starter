from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('agent_schema',ROOT/'scripts/validate_agent_metadata_schema.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

def test_agent_metadata_matches_lean_schema():
    assert module.validate(ROOT)==[]


def test_agent_metadata_allows_no_workflow_directory(tmp_path):
    skills = tmp_path / ".agents" / "skills" / "sample"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text(
        "---\nname: sample\ndescription: Sample skill.\nrequired_reads: []\n---\n",
        encoding="utf-8",
    )
    assert module.validate(tmp_path) == []
