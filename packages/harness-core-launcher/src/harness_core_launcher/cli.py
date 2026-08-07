from __future__ import annotations

import argparse
import json

from .loader import load_core


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load harness-core safely.")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args(argv)
    result = load_core()
    if isinstance(result, dict):
        print(json.dumps(result, sort_keys=True))
        return 1
    if args.probe:
        print(json.dumps({"ok": True, "package": "harness-core"}, sort_keys=True))
    return 0
