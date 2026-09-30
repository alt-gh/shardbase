"""Universal Inbox capture and safe canonical commit primitives."""

from __future__ import annotations

import os
import secrets
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from validate_shardbase import (
    NOTE_ID,
    FrontmatterError,
    parse_frontmatter,
    portable_component,
)

if TYPE_CHECKING:
    from database_preparation import PreparedNote


class CreationError(ValueError):
    """A reviewable creation failure with no replacement of existing knowledge."""


@dataclass(frozen=True)
class CreatedNote:
    path: Path
    template: Path | None


NOTE_TYPES = {"core", "shard", "pebble"}


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


class DraftDumper(yaml.SafeDumper):
    pass


DraftDumper.add_representer(type(None), lambda dumper, value: dumper.represent_scalar("tag:yaml.org,2002:null", ""))


class CaptureDumper(DraftDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def render_capture(title: str, kind: str, alias: str | None, note_id: str) -> str:
    """Render database-independent metadata for a pre-structural CLI capture."""
    metadata = dict(type=kind, pool=None, core=None, parent_note=None,
                    status="draft", aliases=[alias.strip()] if alias and alias.strip() else None,
                    id=note_id, tags=None)
    body = f"# {title}\n\n"
    return "---\n" + yaml.dump(metadata, Dumper=CaptureDumper, allow_unicode=True, sort_keys=False) + "---\n" + body


def inbox_ids(root: Path) -> set[str]:
    """Reserve valid IDs in parseable Inbox drafts, including nested folders."""
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
                    # Plain or unfinished captures do not participate in ID reservation.
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


def filename_key(name: str) -> str:
    return unicodedata.normalize("NFC", name).casefold()


def refuse_collision(directory: Path, filename: str) -> None:
    if directory.exists() and any(filename_key(path.name) == filename_key(filename) for path in directory.iterdir()):
        raise CreationError(f"A file already uses {filename!r} in {directory}. Choose a meaningfully distinct title.")


def create_note(root: Path, title: str, kind: str = "core",
                alias: str | None = None) -> CreatedNote:
    root = root.resolve(strict=True)
    if not root.is_dir() or not checked_path(root, root / "app").is_dir():
        raise CreationError("--root must select an instance directory containing app/.")
    if kind not in NOTE_TYPES:
        raise CreationError("Note type must be core, shard, or pebble.")
    title = title.strip()
    if not title or any(unicodedata.category(char) in {"Cc", "Zl", "Zp"} for char in title):
        raise CreationError("Provide a non-empty, single-line note title without control characters.")
    stem = portable_component(title)
    if stem is None:
        raise CreationError("The title has no usable portable filename; choose a meaningful title.")
    document = render_capture(title, kind, alias, new_id(inbox_ids(root)))
    filename = stem + ".md"
    directory = checked_path(root, root / "app/Knowledge/Inbox")
    refuse_collision(directory, filename)
    path = checked_path(root, directory / filename)
    directory.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(document)
    return CreatedNote(path, None)


def commit_canonical(root: Path, prepared: PreparedNote) -> CreatedNote:
    """Roll back only owned artifacts; never remove a competing creator's output.

    Like other creation tooling, this assumes a stable filesystem, not hostile
    concurrent mutation. Inode checks additionally preserve replaced artifacts.
    """
    from validate_shardbase import validate_database

    path = checked_path(root, prepared.path)
    directory = path.parent
    workspace_identity = file_identity = None

    def identity(stat):
        return stat.st_dev, stat.st_ino

    try:
        if prepared.new_workspace:
            refuse_collision(directory.parent, directory.name)
            directory.mkdir()  # Never adopt an existing workspace, even if empty.
            workspace_identity = identity(directory.lstat())
        refuse_collision(directory, path.name)
        checked_path(root, path)
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            file_identity = identity(os.fstat(stream.fileno()))
            stream.write(prepared.document)
        issues = validate_database(prepared.database)
        if issues:
            details = "\n".join(issue.render(prepared.database) for issue in issues)
            raise CreationError("Post-write structural validation failed:\n" + details)
    except BaseException:
        if file_identity is not None:
            try:
                if identity(path.lstat()) == file_identity:
                    path.unlink()
            except FileNotFoundError:
                pass
        if workspace_identity is not None:
            try:
                if identity(directory.lstat()) == workspace_identity:
                    directory.rmdir()  # Only succeeds if this command's directory is empty.
            except OSError:
                pass
        raise
    return CreatedNote(path, prepared.template)
