#!/usr/bin/env python3
"""Read-only wrapper for persistent-team-bootstrap validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bootstrap_team import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo.absolute()
    config = args.config if args.config.is_absolute() else repo / args.config
    code, result = run(repo, config, "validate", False)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
