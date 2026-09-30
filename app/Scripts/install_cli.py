#!/usr/bin/env python3
"""Compatibility entry point for external ShardBase runtime installation."""

import sys
from pathlib import Path

sys.dont_write_bytecode = True


def main(argv=None):
    from bootstrap_support import setup_main

    return setup_main(Path(__file__).resolve().parents[2], argv)


if __name__ == "__main__":
    sys.exit(main())
