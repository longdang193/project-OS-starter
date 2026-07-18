from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('prompt_inventory',ROOT/'scripts/validate_prompt_ladder.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

def test_prompt_inventory_matches_target():
    assert module.validate_prompt_ladder(ROOT)==[]
