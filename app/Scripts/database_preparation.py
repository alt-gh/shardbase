"""Resolve and render canonical database notes before any destination mutation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from note_creation import (
    CreationError,
    DraftDumper,
    checked_path,
    filename_key,
    inbox_ids,
    new_id,
    read_document,
    refuse_collision,
)
from validate_shardbase import (
    Note,
    core_creation_placement,
    expected_filename,
    nonempty_string,
    primary_title,
    validate_database,
    wikilink_target,
)


@dataclass(frozen=True)
class DatabaseSource:
    path: Path
    metadata: dict[str, Any]
    live: bool


def database_sources(root: Path, *, live_only: bool = False) -> list[DatabaseSource]:
    """Discover identities, preferring live contracts over matching blueprints."""
    sources: dict[str, DatabaseSource] = {}
    for relative, live in (("app/Knowledge/Databases", True), ("app/Blueprints", False)):
        if live_only and not live:
            continue
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
                if live:
                    raise CreationError(f"Missing live database manifest: {manifest}")
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
    sources = database_sources(root, live_only=True)
    matches = [source for source in sources if source.metadata["database_id"] == identity]
    if not matches:
        if any(item.metadata["database_id"] == identity for item in database_sources(root)):
            raise CreationError(f"Database {identity} exists only as a blueprint; create/materialize the live database first.")
        raise CreationError(f"No live database declares database_id: {identity}.")
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


def validated_notes(root: Path, source: DatabaseSource) -> list[Note]:
    """Reject unsafe scan paths and invalid existing canonical state before mutation."""
    notes = source_notes(root, source)
    issues = validate_database(source.path)
    if issues:
        details = "\n".join(issue.render(source.path) for issue in issues)
        raise CreationError("Resolve the selected database's structural validation issues before creation:\n" + details)
    return notes


def select_core(source: DatabaseSource, notes: list[Note], value: str) -> Note:
    core = resolve_note(source, notes, value)
    if core.metadata["type"] != "core":
        raise CreationError("--core must select a root Core.")
    return core


def eligible_parents(source: DatabaseSource, notes: list[Note], core: Note) -> list[Note]:
    return [note for note in notes if note.metadata["type"] in ("core", "shard")
            and resolve_note(source, notes, note.metadata["core"]).path == core.path]


@dataclass(frozen=True)
class PreparedNote:
    document: str
    path: Path
    template: Path | None
    database: Path
    new_workspace: bool


def prepare_note(root: Path, title: str, kind: str, alias: str | None,
                 database: str | None, template: str | None, pool: str | None,
                 parent: str | None, collection: str | None, core: str | None = None) -> PreparedNote:
    source = select_database(root, database)
    try:
        placement = core_creation_placement(source.metadata)
    except ValueError as error:
        raise CreationError(str(error)) from None
    notes = validated_notes(root, source)
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
    directory = None
    if kind == "core":
        if parent is not None or core is not None:
            raise CreationError("A new Core cannot have a parent or select an existing Core.")
    else:
        if not parent:
            raise CreationError("Canonical supporting notes require --parent; select a Core lineage and an immediate Core/Shard parent.")
        parent_note = resolve_note(source, notes, parent)
        if parent_note.metadata["type"] not in ("core", "shard"):
            raise CreationError("A Pebble cannot be a parent.")
        root_core = select_core(source, notes, core if core is not None else parent_note.metadata["core"])
        if parent_note not in eligible_parents(source, notes, root_core):
            raise CreationError("The selected parent must belong to the selected Core lineage.")
        if pool is not None and metadata["pool"] != root_core.metadata["pool"]:
            raise CreationError("The selected Pool must match the root Core.")
        metadata.update(pool=root_core.metadata["pool"], core=f"[[{root_core.path.stem}]]",
                        parent_note=f"[[{parent_note.path.stem}]]")
        # YAML resolved the Core; its already-validated placement determines locality.
        directory = root_core.path.parent
        core_collection = root_core.path.relative_to(source.path / "Data").parts[0]
        if collection is not None and collection != core_collection:
            raise CreationError("The collection must match the selected Core's lineage.")
        collection = core_collection
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
    new_workspace = kind == "core" and placement == "workspace"
    if directory is None:
        directory = source.path / "Data" / collection
        if new_workspace:
            refuse_collision(directory, filename[:-3])
            directory = directory / filename[:-3]
    refuse_collision(directory, filename)
    destination = checked_path(root, directory / filename)
    document = "---\n" + yaml.dump(metadata, Dumper=DraftDumper, allow_unicode=True, sort_keys=False) + "---\n" + body
    return PreparedNote(document, destination, selected_template, source.path, new_workspace)
