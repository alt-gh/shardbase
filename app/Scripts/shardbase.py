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
    from note_creation import CreationError, create_note, read_document
    from database_preparation import database_sources, select_database, source_notes, templates_for

    ui = Terminal(args.no_color)
    ui.section("SHARDBASE  /  New note")
    print("  A blank page, with its structure ready.")
    print(ui.style("  YAML + title only  ·  Saved to Inbox  ·  Ctrl+C to cancel", "2"))
    if args.title is None:
        ui.section("Title")
        print("  Enter the note's human-readable local title.")
        title = input("\n  Title: ")
    else:
        title = args.title
    kind = args.kind or ui.choose("Note type", [
        ("core", "Core", "An independent subject: the root of its own knowledge lineage."),
        ("shard", "Shard", "A subject within a Core; can have child notes."),
        ("pebble", "Pebble", "A terminal detail within a Core; has no child notes."),
    ])
    if args.alias is None:
        ui.section("Alias (optional)")
        print("  Add an alternative name, or press Enter to skip.")
        alias = input("\n  Alias: ")
    else:
        alias = args.alias
    intent = args.intent or ui.choose("Note intent", [
        ("inbox", "Inbox", "Temporary capture with editable Games draft metadata."),
        ("database", "Database-intended", "Prepare a filename, ID, and metadata for a selected database."),
    ])
    database, template, pool = args.database, args.template, args.pool
    parent, collection = args.parent, args.collection
    source = None
    if intent == "database":
        root = args.root.resolve(strict=True)
        if database is None:
            sources = database_sources(root)
            if not sources:
                raise CreationError("No database contracts found. Add a live database or blueprint with Database.md.")
            database = ui.choose("Intended database", [
                (item.metadata["database_id"], str(item.metadata.get("database_name", item.metadata["database_id"])),
                 f"{item.metadata['database_id']} · {'Live database' if item.live else 'Blueprint; create a live copy before moving'}")
                for item in sources
            ])
        source = select_database(root, database)
        templates = templates_for(root, source, kind)
        if template is None and len(templates) > 1:
            template = ui.choose("Template", [(path.name, path.stem, "Use this database's metadata defaults.") for path in templates])
        if kind != "core" and parent is None:
            parents = [note for note in source_notes(root, source)
                       if note.metadata.get("type") in ("core", "shard")] if source.live else []
            if parents:
                parent = ui.choose("Parent note", [
                    (note.path.relative_to(source.path).as_posix(), note.path.stem, note.metadata["type"].title())
                    for note in parents
                ] + [("", "Decide later", "Leave Core and parent blank for manual review before moving.")])
            else:
                parent = ""
                print("  No live parent available; Core and parent will remain blank for review.")
        if pool is None and not parent:
            selected = next((path for path in templates if path.name == template), None) if template else (templates[0] if len(templates) == 1 else None)
            defaults = read_document(root, selected)[0] if selected else {}
            if not isinstance(defaults.get("pool"), str) or not defaults["pool"].strip():
                ui.section("Pool")
                print(f"  Use the vocabulary in {ui.style(str(source.path / 'Database.md'))}.")
                pool = input("\n  Pool: ")
        if collection is None and not parent and len(source.metadata["data_collections"]) > 1:
            collection = ui.choose("Collection", [(name, name, "Declared in the selected Database.md.") for name in source.metadata["data_collections"]])
    result = create_note(args.root, title, kind, alias, intent=intent, database=database,
                         template=template, pool=pool, parent=parent, collection=collection)
    ui.section("Note created")
    print(f"  {ui.style(title.strip(), '1')}  ·  {kind.title()}  ·  Draft")
    print(f"  {ui.style(str(result.path.relative_to(args.root.resolve())), '32')}")
    print(f"  {ui.style('Instance: ' + str(args.root.resolve()), '2')}")
    if alias.strip():
        print(f"  Alias: {ui.style(alias.strip(), '0')}")
    print("\n  Saved to Inbox. Open the file in your Markdown editor and move it when ready.")
    if source:
        print(f"  Intended database: {ui.style(source.metadata['database_name'])}")
        if result.suggested_path:
            print(f"  Manual move target: {ui.style(str(result.suggested_path.relative_to(args.root.resolve())))}")
        else:
            print("  Blueprint selected: create a live database copy before moving this note.")
        print("  Filename and ID prepared. Preserve the ID when moving or editing the note.")
        if kind != "core" and not parent:
            print("  Core and parent are unresolved: complete lineage before moving.")
        print("  Review the database contract and validate after your manual move.")
    else:
        print("  Metadata remains provisional. Complete it before any database promotion.")
    print()
    return 0


def run_validation(args: argparse.Namespace) -> int:
    from validate_shardbase import main as validate

    arguments = ["--root", str(args.root)]
    if args.path is not None:
        arguments.append(str(args.path))
    return validate(arguments)


def new_database(args: argparse.Namespace) -> int:
    from database_creation import available_blueprints, create_database
    from note_creation import CreationError

    if any(getattr(args, name, None) is not None for name in
           ("title", "kind", "alias", "intent", "database", "template", "pool", "parent", "collection")):
        raise CreationError("Note options do not apply to database scaffolding; use --blueprint and --root.")
    ui = Terminal(args.no_color)
    ui.section("SHARDBASE  /  New database")
    identity = args.blueprint
    if identity is None:
        blueprints = available_blueprints(args.root)
        if not blueprints:
            raise CreationError("No blueprints found in this instance's app/Blueprints/. Each blueprint needs a root Database.md.")
        identity = ui.choose("Blueprint", [
            (item.database_id, item.database_name, f"Create app/Knowledge/Databases/{item.path.name}/ from this blueprint.")
            for item in blueprints
        ])
    destination = create_database(args.root, identity)
    ui.section("Database created")
    print(f"  {ui.style(str(destination.relative_to(args.root.resolve())), '32')}")
    print("  The blueprint's scaffolding and resources are now your local database copy.")
    print("  Structural checks passed. Review Database.md for its domain conventions.")
    print("\n  Next: shardbase create new")
    print("  Choose database intent, prepare a note in Inbox, and move it manually when ready.\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="shardbase", description="ShardBase — local notes, structured simply.")
    commands = parser.add_subparsers(dest="command")
    pages = {(): parser}
    catalog: list[tuple[str, str]] = []

    def register(parent, name, route, summary, **kwargs):
        page = parent.add_parser(name, help=summary, **kwargs)
        pages[route] = page
        catalog.append((" ".join(route), summary))
        return page

    def add_new_command(parent, route, summary):
        new = register(
            parent, "new", route, summary,
            description="Create YAML and a title H1 in app/Knowledge/Inbox/. Choose Inbox capture or prepare a database-intended note for a manual move. Omitted choices are prompted.",
            epilog='Example: shardbase create new --title "Example Game" --type core --alias "" --intent database --database games',
        )
        new.add_argument("--title", help="Note title; prompted when omitted")
        new.add_argument("--type", dest="kind", choices=("core", "shard", "pebble"), help="Structural note type; prompted when omitted")
        new.add_argument("--alias", help='Optional alternative name; prompted when omitted (use --alias "" to skip)')
        new.add_argument("--intent", choices=("inbox", "database"), help="Inbox capture or database preparation; both save to Inbox; prompted when omitted")
        new.add_argument("--database", help="Target database_id from Database.md; requires --intent database")
        new.add_argument("--template", help="Matching-type filename inside the selected Templates/; prompted if ambiguous")
        new.add_argument("--pool", help="Pool from Database.md; otherwise supplied by the template or selected parent")
        new.add_argument("--parent", help='Existing Core/Shard stem or database-relative path; use --parent "" to decide later')
        new.add_argument("--collection", help="Declared data collection; inferred from a parent or a single collection")
        new.add_argument("--no-color", action="store_true", help="Disable terminal colors (also respects NO_COLOR)")
        new.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="Instance root containing app/ (default: this checkout)")
        new.set_defaults(handler=new_note)
        return new

    create = register(commands, "create", ("create",), "Show creation commands")
    create.set_defaults(handler=lambda args: create.print_help() or 0)
    create_commands = create.add_subparsers(dest="create_command")
    new = add_new_command(create_commands, ("create", "new"), "Create a note, or choose the database subcommand")
    subjects = new.add_subparsers(dest="new_subject")
    database = register(subjects, "database", ("create", "new", "database"), "Create a new database from an available blueprint",
                        description="Copy a selected app/Blueprints/ package into a new app/Knowledge/Databases/ folder. Existing databases are never merged or overwritten.")
    database.add_argument("--blueprint", help="Blueprint database_id from Database.md; prompted when omitted")
    database.add_argument("--root", type=Path, default=argparse.SUPPRESS, help="Instance containing app/Blueprints/ (default: this checkout)")
    database.add_argument("--no-color", action="store_true", default=argparse.SUPPRESS, help="Disable terminal colors")
    database.set_defaults(handler=new_database)
    add_new_command(commands, ("new",), "Alias for create new")

    validate = register(commands, "validate", ("validate",), "Check database structure without modifying files")
    validate.add_argument("path", nargs="?", type=Path, help="Database root; omit to check all live databases in the instance")
    validate.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="Instance root containing app/ (default: this checkout)")
    validate.set_defaults(handler=run_validation)

    def show_commands(args):
        print("ShardBase commands\n")
        for route, summary in catalog:
            print(f"  {'shardbase ' + route:<32} {summary}")
        print("\nUse shardbase help <command> or append --help for options.")
        print("Command reference: app/Scripts/README.md#command-reference")
        return 0

    listing = register(commands, "commands", ("commands",), "List every available command")
    listing.set_defaults(handler=show_commands)
    help_page = register(commands, "help", ("help",), "Show help, e.g. shardbase help create new")
    help_page.add_argument("topic", nargs="*", help="Command or command group")

    def show_help(args):
        page = pages.get(tuple(args.topic))
        if page is None:
            help_page.error("unknown command; use shardbase commands to see available commands")
        page.print_help()
        return 0

    help_page.set_defaults(handler=show_help)
    parser.set_defaults(handler=show_commands)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.", file=sys.stderr)
        return 130
    except (ValueError, OSError, UnicodeError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
