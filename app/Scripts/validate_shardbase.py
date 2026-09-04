#!/usr/bin/env python3
"""Validate ShardBase database manifests and structural notes."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MANIFEST_FIELDS = ("manifest_version", "database_id", "database_name", "data_collections", "database_status")
STRUCTURAL_FIELDS = ("type", "pool", "core", "parent_note", "status")
VALID_TYPES = {"core", "shard", "pebble"}
VALID_STATUSES = {"active", "draft", "archived"}
REQUIRED_BODY_SECTIONS = ("Purpose", "Scope", "Includes", "Excludes", "Architecture", "Schema", "Conventions", "Resources")


@dataclass(frozen=True)
class Note:
    path: Path
    metadata: dict[str, Any]
    body: str


@dataclass(frozen=True)
class Issue:
    path: Path
    code: str
    message: str

    def render(self, root: Path) -> str:
        try:
            display_path = self.path.relative_to(root)
        except ValueError:
            display_path = self.path
        return f"{display_path}: {self.code}: {self.message}"


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"null", "~"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return None

    metadata: dict[str, Any] = {}
    current_list: str | None = None
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_list:
            metadata[current_list].append(parse_scalar(line[4:]))
            continue
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            metadata[key] = []
            current_list = key
        else:
            metadata[key] = parse_scalar(value)
            current_list = None
    return metadata, "\n".join(lines[end + 1 :])


def wikilink_target(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", value.strip())
    return match.group(1).strip() if match else None


def canonical_stem(path: Path) -> str:
    return path.stem


def current_node_name(note: Note, notes_by_path: dict[Path, Note]) -> str:
    parent_target = wikilink_target(note.metadata.get("parent_note"))
    if note.metadata.get("type") == "core" or not parent_target:
        return canonical_stem(note.path)
    parent = next((candidate for candidate in notes_by_path.values() if candidate.path.stem == parent_target), None)
    if parent is None:
        return canonical_stem(note.path)
    parent_parts = parent.path.stem.split(" - ")
    return parent_parts[-1]


def expected_filename(note: Note, notes_by_path: dict[Path, Note]) -> str:
    stem = canonical_stem(note.path)
    if note.metadata.get("type") == "core":
        return stem + ".md"
    core_target = wikilink_target(note.metadata.get("core"))
    parent_target = wikilink_target(note.metadata.get("parent_note"))
    core_name = core_target or stem.split(" - ")[0]
    parent_name = parent_target or core_name
    current_name = stem.split(" - ")[-1]
    if parent_name == core_name:
        return f"{core_name} - {current_name}.md"
    parent = notes_by_path.get(parent_name)
    immediate_name = parent.path.stem.split(" - ")[-1] if parent else parent_name
    return f"{core_name} - {immediate_name} - {current_name}.md"


def load_note(path: Path) -> Note:
    parsed = parse_frontmatter(path.read_text(encoding="utf-8"))
    if parsed is None:
        return Note(path, {}, path.read_text(encoding="utf-8"))
    metadata, body = parsed
    return Note(path, metadata, body)


def database_notes(root: Path, collections: list[str]) -> list[Note]:
    notes: list[Note] = []
    for collection in collections:
        collection_root = root / "Data" / collection
        if not collection_root.is_dir():
            continue
        for path in sorted(collection_root.glob("*.md")):
            notes.append(load_note(path))
    return notes


def validate_database(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    root = root.resolve()
    if root.parent.name != "Databases" or root.parent.parent.name != "Knowledge":
        issues.append(Issue(root, "database-location", "database must be a direct child of app/Knowledge/Databases"))
    manifest_path = root / "Database.md"
    if not manifest_path.is_file():
        return issues + [Issue(manifest_path, "manifest-missing", "Database.md is required")]

    parsed = parse_frontmatter(manifest_path.read_text(encoding="utf-8"))
    if parsed is None:
        return issues + [Issue(manifest_path, "manifest-frontmatter", "Database.md must begin with YAML frontmatter")]
    metadata, body = parsed
    for field in MANIFEST_FIELDS:
        if field not in metadata:
            issues.append(Issue(manifest_path, "manifest-field", f"missing required field '{field}'"))
    if metadata.get("manifest_version") != 1:
        issues.append(Issue(manifest_path, "manifest-version", "manifest_version must be 1"))
    if not isinstance(metadata.get("database_id"), str) or not metadata.get("database_id"):
        issues.append(Issue(manifest_path, "manifest-id", "database_id must be a non-empty string"))
    if not isinstance(metadata.get("database_name"), str) or not metadata.get("database_name"):
        issues.append(Issue(manifest_path, "manifest-name", "database_name must be a non-empty string"))
    collections = metadata.get("data_collections")
    if not isinstance(collections, list) or not collections or any(not isinstance(item, str) or not item for item in collections):
        issues.append(Issue(manifest_path, "manifest-collections", "data_collections must be a non-empty list of names"))
        collections = []
    elif len(set(collections)) != len(collections):
        issues.append(Issue(manifest_path, "manifest-collections", "data_collections must contain unique names"))
    if metadata.get("database_status") not in {"active", "draft", "archived"}:
        issues.append(Issue(manifest_path, "manifest-status", "database_status must be active, draft, or archived"))
    if not isinstance(metadata.get("data_collections"), list):
        collections = []
    for collection in collections:
        collection_root = root / "Data" / collection
        if not collection_root.is_dir():
            issues.append(Issue(collection_root, "collection-missing", "declared data collection directory is required"))
        attachments = collection_root / "Attachments"
        if collection_root.is_dir() and not attachments.is_dir():
            issues.append(Issue(attachments, "attachments-missing", "each declared collection must contain Attachments/"))
    data_root = root / "Data"
    if data_root.is_dir():
        declared = set(collections)
        for child in data_root.iterdir():
            if child.is_dir() and child.name not in declared:
                issues.append(Issue(child, "collection-undeclared", "direct data collection is not declared in Database.md"))
    headings = {match.group(2) for match in re.finditer(r"^(#{1,6}) (.+)$", body, re.MULTILINE)}
    for section in REQUIRED_BODY_SECTIONS:
        if section not in headings:
            issues.append(Issue(manifest_path, "manifest-section", f"missing required body section '{section}'"))

    notes = database_notes(root, collections)
    notes_by_stem = {note.path.stem: note for note in notes}
    expected_names: dict[str, list[Note]] = {}
    for note in notes:
        expected_names.setdefault(expected_filename(note, notes_by_stem), []).append(note)
    for expected_name, colliding_notes in expected_names.items():
        if len(colliding_notes) > 1:
            for note in colliding_notes:
                issues.append(Issue(note.path, "filename-collision", f"filename is also required by {expected_name}"))
    for note in notes:
        metadata = note.metadata
        if not metadata:
            issues.append(Issue(note.path, "structural-frontmatter", "structural note must begin with YAML frontmatter"))
        for field in STRUCTURAL_FIELDS:
            if field not in metadata:
                issues.append(Issue(note.path, "structural-field", f"missing required field '{field}'"))
        note_type = metadata.get("type")
        if note_type not in VALID_TYPES:
            issues.append(Issue(note.path, "structural-type", "type must be core, shard, or pebble"))
        if not isinstance(metadata.get("pool"), str) or not metadata.get("pool"):
            issues.append(Issue(note.path, "structural-pool", "pool must be a non-empty scalar string"))
        if metadata.get("status") not in VALID_STATUSES:
            issues.append(Issue(note.path, "structural-status", "status must be active, draft, or archived"))
        core_target = wikilink_target(metadata.get("core"))
        parent_target = wikilink_target(metadata.get("parent_note"))
        if note_type == "core":
            if parent_target is not None:
                issues.append(Issue(note.path, "core-parent", "Core parent_note must be empty"))
            if core_target != note.path.stem:
                issues.append(Issue(note.path, "core-reference", "Core core field must self-reference its filename stem"))
        else:
            if core_target not in notes_by_stem or notes_by_stem.get(core_target, note).metadata.get("type") != "core":
                issues.append(Issue(note.path, "core-reference", "supporting note core must resolve to a canonical Core"))
            if parent_target not in notes_by_stem:
                issues.append(Issue(note.path, "parent-reference", "supporting note parent_note must resolve to an existing note"))
            elif notes_by_stem[parent_target].metadata.get("type") == "pebble":
                issues.append(Issue(note.path, "pebble-parent", "a Pebble cannot be a structural parent"))
            if parent_target == note.path.stem:
                issues.append(Issue(note.path, "self-parent", "a note cannot parent itself"))
        if note_type in {"shard", "pebble"} and len(note.path.stem.split(" - ")) > 3:
            issues.append(Issue(note.path, "filename-context", "supporting filenames may contain at most three components"))
        if note.path.name != expected_filename(note, notes_by_stem):
            issues.append(Issue(note.path, "filename", f"expected '{expected_filename(note, notes_by_stem)}'"))
        if not re.search(r"^# .+\n\n", note.body):
            issues.append(Issue(note.path, "heading", "note body must begin with a level-one heading followed by one blank line"))
        for line_number, line in enumerate(note.body.splitlines(), 1):
            if re.match(r"^#{3,6} ", line):
                previous = note.body.splitlines()[line_number - 2] if line_number > 1 else ""
                if previous and previous.strip():
                    issues.append(Issue(note.path, "heading-sequence", "heading levels must be sequential"))
                    break

    parent_map = {note.path.stem: wikilink_target(note.metadata.get("parent_note")) for note in notes if note.metadata.get("type") != "core"}
    for start in parent_map:
        seen: set[str] = set()
        current: str | None = start
        while current in parent_map:
            if current in seen:
                issues.append(Issue(notes_by_stem[start].path, "lineage-cycle", "structural parent lineage contains a cycle"))
                break
            seen.add(current)
            current = parent_map[current]
    return issues


def discover_databases(app_root: Path) -> list[Path]:
    db_root = app_root / "Knowledge" / "Databases"
    if not db_root.is_dir():
        return []
    return sorted(path for path in db_root.iterdir() if path.is_dir() and (path / "Database.md").is_file())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, help="database root; defaults to all databases under app/Knowledge/Databases")
    args = parser.parse_args(argv)
    workspace = Path(__file__).resolve().parents[2]
    roots = [args.path] if args.path else discover_databases(workspace / "app")
    if not roots:
        print("No databases found under app/Knowledge/Databases.")
        return 0
    all_issues: list[Issue] = []
    for root in roots:
        issues = validate_database(root)
        all_issues.extend(issues)
        print(f"{root}: {'valid' if not issues else f'{len(issues)} issue(s)'}")
        for issue in issues:
            print(f"  {issue.render(root)}")
    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
