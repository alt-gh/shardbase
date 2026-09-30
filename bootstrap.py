#!/usr/bin/env python3
"""Prepare external ShardBase tooling for this instance (Python 3.10+)."""

# Keep this preflight parseable on older Python, before importing shared code.
import sys
from pathlib import Path


def main(argv=None):
    if sys.version_info < (3, 10):
        print("ShardBase bootstrap requires Python 3.10 or newer.\n"
              "Detected: Python {}.{}.{}\n"
              "Rerun bootstrap.py with Python 3.10+.".format(*sys.version_info[:3]),
              file=sys.stderr)
        return 1
    sys.dont_write_bytecode = True
    root = Path(__file__).resolve().parent
    support = root / "app/Scripts/bootstrap_support.py"
    if not support.is_file():
        print("Setup failed: expected a ShardBase instance containing "
              "app/Scripts/bootstrap_support.py.", file=sys.stderr)
        return 1
    sys.path.insert(0, str(support.parent))
    from bootstrap_support import setup_main

    return setup_main(root, argv, bootstrap=True)


if __name__ == "__main__":
    sys.exit(main())
