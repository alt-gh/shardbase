"""Local draft creation, independent of CLI prompts; never promotes or overwrites.

Inbox captures may have unresolved or invalid metadata. Database preparation
adds IDs, canonical filenames, and selected lineage with bounded checks; full
structural and semantic review still belongs to manual promotion.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from validate_shardbase import FrontmatterError, parse_frontmatter, portable_component

import yaml


class CreationError(ValueError):
    """A reviewable creation failure with no replacement of existing knowledge."""


@dataclass(frozen=True)
class CreatedNote:
    path: Path
    template: Path | None
    suggested_path: Path | None = None


TEMPLATES = {"core": "Game.md", "shard": "Game Shard.md", "pebble": "Game Pebble.md"}


def checked_path(root: Path, path: Path) -> Path:
    """Reject symlinks beneath the explicitly selected instance boundary."""
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise CreationError(f"Symlink paths require ownership review: {current}")
    if not path.resolve().is_relative_to(root):
        raise CreationError(f"Path leaves the instance boundary: {path}")
    return path


def read_document(root: Path, path: Path) -> tuple[dict[str, Any], str]:
    checked_path(root, path)
    try:
        return parse_frontmatter(path.read_text(encoding="utf-8"))
    except FrontmatterError as error:
        raise CreationError(f"{path}: {error}") from None


def game_source(root: Path, kind: str = "core") -> Path:
    databases = checked_path(root, root / "app/Knowledge/Databases")
    matches = []
    if databases.exists():
        for candidate in sorted(databases.iterdir()):
            checked_path(root, candidate)
            if not candidate.is_dir():
                continue
            manifest = checked_path(root, candidate / "Database.md")
            if not manifest.is_file():
                continue
            try:
                metadata, _ = read_document(root, manifest)
            except CreationError:
                # A malformed manifest cannot identify a template owner.
                continue
            if metadata.get("database_id") == "games":
                matches.append(candidate)
    if len(matches) > 1:
        raise CreationError("Multiple databases declare database_id: games; resolve the ambiguity first.")
    source = matches[0] if matches else root / "app/Blueprints/Games"
    template = checked_path(root, source / "Templates" / TEMPLATES[kind])
    if not template.is_file():
        raise CreationError(f"Missing {template}. Add a contract-compatible Game template deliberately; live databases are never updated from blueprints automatically.")
    return template


class DraftDumper(yaml.SafeDumper):
    pass


DraftDumper.add_representer(type(None), lambda dumper, value: dumper.represent_scalar("tag:yaml.org,2002:null", ""))


def render_game(template_metadata: dict[str, Any], title: str, stem: str,
                kind: str = "core", alias: str | None = None) -> str:
    # Supply a complete editing scaffold, without asserting canonical validity.
    metadata = dict(type=kind, pool="Games", core=None, parent_note=None,
                    status="draft", aliases=None, id=None, tags=None)
    metadata.update(template_metadata)
    metadata["type"] = kind
    if kind == "core" and metadata["core"] in (None, "[[{{stem}}]]"):
        metadata["core"] = f"[[{stem}]]"
    elif metadata["core"] in ("[[{{stem}}]]", "[[{{core}}]]"):
        metadata["core"] = None
    if metadata["parent_note"] == "[[{{parent}}]]":
        metadata["parent_note"] = None
    if alias is not None and alias.strip():
        # Dump as data, so punctuation and YAML-looking aliases remain strings.
        metadata["aliases"] = [alias.strip()]
    body = f"# {title}\n\n"
    return "---\n" + yaml.dump(metadata, Dumper=DraftDumper, allow_unicode=True, sort_keys=False) + "---\n" + body


def filename_key(name: str) -> str:
    return unicodedata.normalize("NFC", name).casefold()


def refuse_collision(directory: Path, filename: str) -> None:
    if directory.exists() and any(filename_key(path.name) == filename_key(filename) for path in directory.iterdir()):
        raise CreationError(f"A file already uses {filename!r} in {directory}. Choose a meaningfully distinct title.")


def create_note(root: Path, title: str, kind: str = "core",
                alias: str | None = None, *, intent: str = "inbox",
                database: str | None = None, template: str | None = None,
                pool: str | None = None, parent: str | None = None,
                collection: str | None = None) -> CreatedNote:
    root = root.resolve(strict=True)
    if not root.is_dir() or not checked_path(root, root / "app").is_dir():
        raise CreationError("--root must select an instance directory containing app/.")
    if kind not in TEMPLATES:
        raise CreationError("Note type must be core, shard, or pebble.")
    if intent not in {"inbox", "database"}:
        raise CreationError("Intent must be inbox or database.")
    if intent == "inbox" and any(value is not None for value in (database, template, pool, parent, collection)):
        raise CreationError("Database options require --intent database.")
    title = title.strip()
    if not title or any(unicodedata.category(char) in {"Cc", "Zl", "Zp"} for char in title):
        raise CreationError("Provide a non-empty, single-line note title without control characters.")
    stem = portable_component(title)
    if stem is None:
        raise CreationError("The title has no usable portable filename; choose a meaningful title.")
    directory = checked_path(root, root / "app/Knowledge/Inbox")
    suggested_path = None
    if intent == "database":
        from database_preparation import prepare_note
        document, filename, selected_template, suggested_path = prepare_note(
            root, title, kind, alias, database, template, pool, parent, collection)
    else:
        selected_template = game_source(root, kind)
        metadata, _ = read_document(root, selected_template)
        document = render_game(metadata, title, stem, kind, alias)
        filename = stem + ".md"
    refuse_collision(directory, filename)
    path = checked_path(root, directory / filename)
    # Parse the template and prepare output before touching the destination.
    directory.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also protects against a competing creator of this path.
    # Never truncate an existing file, including a dangling destination symlink.
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(document)
    return CreatedNote(path, selected_template, suggested_path)
