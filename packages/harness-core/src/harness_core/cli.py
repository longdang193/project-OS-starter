from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .compatibility import (
    CURRENT_PACKET_API,
    SUPPORTED_HOST_APIS,
    SUPPORTED_PACKET_READ_APIS,
    SUPPORTED_REQUEST_APIS,
    package_release,
)
from .config_validation import validate as validate_config
from .managed import main as managed_main


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments == ["--identity"]:
        print(json.dumps({
            "package": "harness-core",
            "package_release": package_release(),
            "supported_request_apis": sorted(SUPPORTED_REQUEST_APIS),
            "supported_packet_read_apis": sorted(SUPPORTED_PACKET_READ_APIS),
            "current_packet_api": CURRENT_PACKET_API,
            "supported_host_apis": sorted(SUPPORTED_HOST_APIS),
        }, sort_keys=True))
        return 0
    if arguments and arguments[0] == "validate":
        parser = argparse.ArgumentParser(description="Validate harness consumer policy.")
        parser.add_argument("validate")
        parser.add_argument("--repo-root", required=True)
        args = parser.parse_args(arguments)
        errors = validate_config(Path(args.repo_root).resolve())
        print(json.dumps({"status": "valid" if not errors else "blocked", "errors": errors}, sort_keys=True))
        return 0 if not errors else 2
    return managed_main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
