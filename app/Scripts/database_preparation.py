"""Prepare database-intended Inbox notes without modifying a database.

Templates supply semantic defaults; their contents are not a schema. Only the
documented universal checks below are automated. Promotion remains user-owned.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from note_creation import CreationError, DraftDumper, checked_path, filename_key, read_document
from validate_shardbase import (
    NOTE_ID, Note, expected_filename, nonempty_string, parse_frontmatter,
    FrontmatterError, primary_title, validate_database, wikilink_target,
)


@dataclass(frozen=True)
class DatabaseSource:
    path: Path
    metadata: dict[str, Any]
    live: bool


def database_sources(root: Path) -> list[DatabaseSource]:
    """Discover identities, preferring live contracts over matching blueprints."""
    sources: dict[str, DatabaseSource] = {}
    for relative, live in (("app/Knowledge/Databases", True), ("app/Blueprints", False)):
        directory = checked_path(root, root / relative)
        if not directory.exists():
            continue
        group: dict[str, DatabaseSource] = {}
        for candidate in sorted(directory.iterdir()):
            checked_path(root, candidate)
            if not candidate.is_dir():
                continue
            manifest = checked_path(root, candidate / "Database.md")
            if not manifest.is_file():
                continue
            metadata, _ = read_document(root, manifest)
            identity = metadata.get("database_id")
            if not nonempty_string(identity):
                raise CreationError(f"{manifest}: database_id must be a non-empty string.")
            if identity in group:
                raise CreationError(f"Multiple {'live databases' if live else 'blueprints'} declare database_id: {identity}.")
            group[identity] = DatabaseSource(candidate, metadata, live)
        for identity, source in group.items():
            sources.setdefault(identity, source)
    return list(sources.values())


def select_database(root: Path, identity: str | None) -> DatabaseSource:
    if not identity:
        raise CreationError("Select a target with --database <database_id>.")
    sources = database_sources(root)
    matches = [source for source in sources if source.metadata["database_id"] == identity]
    if len(matches) != 1:
        raise CreationError(f"No database or blueprint declares database_id: {identity}.")
    source = matches[0]
    metadata = source.metadata
    if type(metadata.get("manifest_version")) is not int or metadata["manifest_version"] != 1:
        raise CreationError("Only integer manifest_version 1 is supported.")
    if not nonempty_string(metadata.get("database_name")):
        raise CreationError("The selected manifest needs a database_name.")
    if metadata.get("database_status") not in ("active", "draft"):
        raise CreationError("Select an active or draft database contract.")
    collections = metadata.get("data_collections")
    if not isinstance(collections, list) or not collections or any(
        not nonempty_string(name) or name in {".", ".."} or any(char in name for char in "/\\\x00")
        for name in collections
    ) or len(set(collections)) != len(collections):
        raise CreationError("data_collections must contain unique direct-child directory names.")
    for name in collections:
        path = checked_path(root, source.path / "Data" / name)
        if not path.is_dir():
            raise CreationError(f"Missing declared collection: {path}")
    return source


def templates_for(root: Path, source: DatabaseSource, kind: str) -> list[Path]:
    directory = checked_path(root, source.path / "Templates")
    if not directory.exists():
        return []
    matches = []
    for path in sorted(directory.iterdir()):
        checked_path(root, path)
        if path.is_file() and path.suffix == ".md":
            metadata, _ = read_document(root, path)
            if metadata.get("type") == kind:
                matches.append(path)
    return matches


def source_notes(root: Path, source: DatabaseSource) -> list[Note]:
    """Read only declared collection roots and one workspace level."""
    notes = []

    def scan(directory: Path, workspace: bool = False) -> None:
        for path in sorted(directory.iterdir()):
            # Attachments are never structural, including Markdown attachments.
            if path.name == "Attachments":
                continue
            checked_path(root, path)
            if path.is_dir():
                if workspace:
                    raise CreationError(f"Nested workspace requires placement review: {path}")
                scan(path, True)
            elif path.suffix == ".md":
                metadata, body = read_document(root, path)
                notes.append(Note(path, metadata, body))

    for name in source.metadata["data_collections"]:
        scan(checked_path(root, source.path / "Data" / name))
    return notes


def inbox_ids(root: Path) -> set[str]:
    """Reserve IDs in parseable Inbox drafts, including user-organized folders."""
    result: set[str] = set()

    def scan(directory: Path) -> None:
        if not directory.exists():
            return
        for path in sorted(directory.iterdir()):
            checked_path(root, path)
            if path.is_dir():
                scan(path)
            elif path.suffix == ".md":
                try:
                    metadata, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
                except FrontmatterError:
                    # Plain or unfinished Inbox captures need not have valid YAML.
                    continue
                token = metadata.get("id")
                if isinstance(token, str) and NOTE_ID.fullmatch(token):
                    result.add(token)

    scan(checked_path(root, root / "app/Knowledge/Inbox"))
    return result


def new_id(used: set[str]) -> str:
    for _ in range(100):
        token = "".join(secrets.choice("0123456789abcdefghjkmnpqrstvwxyz") for _ in range(10))
        if token not in used:
            return token
    raise CreationError("Could not allocate an unused note ID; retry creation.")


def resolve_note(source: DatabaseSource, notes: list[Note], value: str) -> Note:
    target = wikilink_target(value) or value
    matches = [note for note in notes if target in {
        note.path.stem, note.path.name,
        note.path.relative_to(source.path).as_posix(),
        note.path.relative_to(source.path).with_suffix("").as_posix(),
        note.path.relative_to(source.path.parents[3]).as_posix() if source.live else "",
        note.path.relative_to(source.path.parents[3]).with_suffix("").as_posix() if source.live else "",
    }]
    if len(matches) != 1:
        raise CreationError("Parent/Core must resolve unambiguously inside the selected database.")
    return matches[0]


def prepare_note(root: Path, title: str, kind: str, alias: str | None,
                 database: str | None, template: str | None, pool: str | None,
                 parent: str | None, collection: str | None) -> tuple[str, str, Path | None, Path | None]:
    source = select_database(root, database)
    templates = templates_for(root, source, kind)
    if template is not None:
        matches = [path for path in templates if path.name == template]
        if len(matches) != 1:
            raise CreationError("--template must name a matching-type file directly inside the selected Templates/.")
        selected_template = matches[0]
    elif len(templates) > 1:
        raise CreationError("Multiple templates match this type; select one with --template <filename>.")
    else:
        selected_template = templates[0] if templates else None
    metadata = dict(type=kind, pool=None, core=None, parent_note=None,
                    status="draft", aliases=None, id=None, tags=None)
    if selected_template:
        defaults, _ = read_document(root, selected_template)
        metadata.update(defaults)
    # Identity/lineage belong to the new note, never to a copied template.
    metadata.update(type=kind, core=None, parent_note=None, status="draft")
    if pool is not None:
        metadata["pool"] = pool.strip()
    notes = source_notes(root, source)
    directory = None
    if parent:
        if kind == "core":
            raise CreationError("A Core cannot have a parent.")
        if not source.live:
            raise CreationError("Move the parent into a live database before selecting it.")
        issues = validate_database(source.path)
        if issues:
            raise CreationError("Resolve the selected database's structural validation issues before using a parent.")
        parent_note = resolve_note(source, notes, parent)
        if parent_note.metadata["type"] not in ("core", "shard"):
            raise CreationError("A Pebble cannot be a parent.")
        core = resolve_note(source, notes, parent_note.metadata["core"])
        if pool is not None and metadata["pool"] != core.metadata["pool"]:
            raise CreationError("The selected Pool must match the parent's root Core.")
        metadata.update(pool=core.metadata["pool"], core=f"[[{core.path.stem}]]",
                        parent_note=f"[[{parent_note.path.stem}]]")
        directory = parent_note.path.parent
        parent_collection = parent_note.path.relative_to(source.path / "Data").parts[0]
        if collection is not None and collection != parent_collection:
            raise CreationError("The collection must match the selected parent's lineage.")
        collection = parent_collection
    if not nonempty_string(metadata["pool"]):
        raise CreationError("Provide --pool using the selected Database.md vocabulary, or use a template/parent with a Pool.")
    for field in ("aliases", "tags"):
        if field == "aliases" and alias is not None and alias.strip():
            metadata[field] = [alias.strip()]
        value = metadata[field]
        if value is not None and not (isinstance(value, list) and all(nonempty_string(item) for item in value)):
            raise CreationError(f"Template {field} must be blank or a list of non-empty strings.")
    collections = source.metadata["data_collections"]
    if collection is None:
        if len(collections) != 1:
            raise CreationError("Select a declared collection with --collection <name>.")
        collection = collections[0]
    if collection not in collections:
        raise CreationError("The selected collection is not declared in Database.md.")
    used = inbox_ids(root)
    used.update(note.metadata["id"] for note in notes if isinstance(note.metadata.get("id"), str))
    if isinstance(metadata.get("id"), str):
        used.add(metadata["id"])
    metadata["id"] = new_id(used)
    body = f"# {title}\n\n"
    draft = Note(root / "draft.md", metadata, body)
    # Reject ATX closing hashes that would silently change the canonical H1 title.
    if primary_title(draft) != title:
        raise CreationError("Use a title without trailing Markdown heading markers.")
    filename = expected_filename(draft)
    if filename is None:
        raise CreationError("Cannot derive a canonical filename from this title.")
    for note in notes:
        expected = expected_filename(note)
        if filename_key(note.path.name) == filename_key(filename) or (
            expected is not None and filename_key(expected) == filename_key(filename)
        ):
            raise CreationError("A note already uses this canonical filename in the selected database; choose a distinct title.")
    if kind == "core":
        metadata["core"] = f"[[{filename[:-3]}]]"
    suggested = (directory or source.path / "Data" / collection) / filename if source.live else None
    document = "---\n" + yaml.dump(metadata, Dumper=DraftDumper, allow_unicode=True, sort_keys=False) + "---\n" + body
    return document, filename, selected_template, suggested
