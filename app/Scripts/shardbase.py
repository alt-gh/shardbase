#!/usr/bin/env python3
"""ShardBase command-line entry point. See README.md for external runtime setup."""

from __future__ import annotations

import argparse
import os
import sys
import unicodedata
from pathlib import Path

# Suppress bytecode before importing any project modules, even without -B.
sys.dont_write_bytecode = True

from note_creation import CreationError, create_note


class Terminal:
    """Small text UI with optional ANSI styling and a readable plain-text mode."""

    def __init__(self, no_color: bool = False):
        self.color = sys.stdout.isatty() and not no_color and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"

    def style(self, text: str, code: str = "1;36") -> str:
        # Display local titles/paths as text, never as terminal control sequences.
        text = "".join(char if unicodedata.category(char) not in {"Cc", "Cf", "Zl", "Zp"} else " " for char in text)
        return f"\033[{code}m{text}\033[0m" if self.color else text

    def section(self, title: str) -> None:
        print(f"\n  {self.style(title)}")

    def choose(self, title: str, choices: list[tuple[str, str, str]]) -> str:
        self.section(title)
        for number, (_, label, description) in enumerate(choices, 1):
            print(f"    {self.style(str(number), '36')}  {self.style(label, '1')}")
            print(f"       {self.style(description, '2')}")
        while True:
            answer = input(f"\n  Choose [1-{len(choices)}]: ").strip()
            for number, (value, _, _) in enumerate(choices, 1):
                if answer == str(number) or answer == value:
                    return value
            print(f"  Choose 1-{len(choices)}, or enter an option's exact name.")


def new_note(args: argparse.Namespace) -> int:
    ui = Terminal(args.no_color)
    ui.section("SHARDBASE  /  New note")
    print("  A blank page, with its structure ready.")
    print(ui.style("  Games  ·  YAML + title only  ·  Ctrl+C to cancel", "2"))
    if args.title is None:
        ui.section("Title")
        print("  Enter the local title, such as a game name, Zombies, or Terminus.")
        title = input("\n  Title: ")
    else:
        title = args.title
    kind = args.kind or ui.choose("Note type", [
        ("core", "Core", "A game: the root of its own knowledge lineage."),
        ("shard", "Shard", "A subject within a game; can have child notes."),
        ("pebble", "Pebble", "A terminal detail within a game; has no child notes."),
    ])
    if args.alias is None:
        ui.section("Alias (optional)")
        print("  Add an alternative name, or press Enter to skip.")
        alias = input("\n  Alias: ")
    else:
        alias = args.alias
    destination = args.destination or ui.choose("Destination", [
        ("inbox", "Inbox", "Capture now in Knowledge/Inbox/."),
        ("databases", "Databases", "Review first in Knowledge/Inbox/Staged/."),
    ])
    result = create_note(args.root, title, destination, kind, alias)
    ui.section("Note created")
    print(f"  {ui.style(title.strip(), '1')}  ·  {kind.title()}  ·  Draft")
    print(f"  {ui.style(str(result.path.relative_to(args.root.resolve())), '32')}")
    print(f"  {ui.style('Instance: ' + str(args.root.resolve()), '2')}")
    if alias.strip():
        print(f"  Alias: {ui.style(alias.strip(), '0')}")
    if destination == "databases":
        print("\n  Staged for review. Open the file in your Markdown editor.")
    else:
        print("\n  Ready for your Markdown editor. Metadata remains provisional.")
    print("  Complete and validate metadata when promoting to a live database.")
    print()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shardbase", description="ShardBase — local notes, structured simply.")
    commands = parser.add_subparsers(dest="command", required=True)
    new = commands.add_parser("new", help="Create a Core, Shard, or Pebble draft", description="Create YAML and a title H1 for Inbox review. Omitted choices are prompted.", epilog='Example: shardbase new --title "Terminus" --type shard --alias "" --destination databases')
    new.add_argument("--title", help="Note title; prompted when omitted")
    new.add_argument("--destination", choices=("inbox", "databases"), help="Databases writes to Inbox/Staged; prompted when omitted")
    new.add_argument("--type", dest="kind", choices=("core", "shard", "pebble"), help="Structural note type; prompted when omitted")
    new.add_argument("--alias", help='Optional alternative name; prompted when omitted (use --alias "" to skip)')
    new.add_argument("--no-color", action="store_true", help="Disable terminal colors (also respects NO_COLOR)")
    new.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="Instance root containing app/ (default: this checkout)")
    new.set_defaults(handler=new_note)
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.", file=sys.stderr)
        return 130
    except (CreationError, OSError, UnicodeError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
