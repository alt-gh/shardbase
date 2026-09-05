#!/usr/bin/env python3
"""Read-only validation of ShardBase manifests and structural notes.

See app/Scripts/README.md for setup, supported conventions, and limitations.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:
    raise SystemExit("PyYAML is required. See app/Scripts/README.md for setup outside the vault.")


MANIFEST_FIELDS = ("manifest_version", "database_id", "database_name", "data_collections", "database_status")
STRUCTURAL_FIELDS = ("type", "pool", "core", "parent_note", "status")
VALID_TYPES = {"core", "shard", "pebble"}
VALID_STATUSES = {"active", "draft", "archived"}
REQUIRED_BODY_SECTIONS = ("Purpose", "Scope", "Includes", "Excludes", "Architecture", "Schema", "Conventions", "Resources")
FORBIDDEN = re.compile(r'[\x00-\x1f<>:"/\\|?*]')
DEVICE_STEMS = {"CON", "PRN", "AUX", "NUL"} | {f"{prefix}{i}" for prefix in ("COM", "LPT") for i in range(1, 10)}


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


class FrontmatterError(ValueError):
    pass


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loading with explicit duplicate keys rejected, not overwritten."""

    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            raise FrontmatterError("YAML mapping tag requires a mapping value")
        seen = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self.construct_object(key_node, deep=deep)
            try:
                if key in seen:
                    raise FrontmatterError(f"duplicate YAML key at frontmatter line {key_node.start_mark.line + 1}")
                seen.add(key)
            except TypeError:
                raise FrontmatterError("YAML mapping keys must be scalar values") from None
        return super().construct_mapping(node, deep=deep)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.lstrip("\ufeff").splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise FrontmatterError("document must begin with YAML frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i].rstrip("\r\n") == "---"), None)
    if end is None:
        raise FrontmatterError("YAML frontmatter closing delimiter is missing")
    try:
        metadata = yaml.load("".join(lines[1:end]), Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        location = f" at frontmatter line {mark.line + 1}" if mark else ""
        raise FrontmatterError(f"invalid or unsupported YAML{location}") from None
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError) as error:
        if isinstance(error, FrontmatterError):
            raise
        # Some malformed explicit scalar tags raise built-in exceptions in PyYAML.
        raise FrontmatterError("invalid or excessively nested YAML") from None
    if not isinstance(metadata, dict) or any(not isinstance(key, str) for key in metadata):
        raise FrontmatterError("frontmatter must be a mapping with string field names")
    return metadata, "".join(lines[end + 1:])


def within_boundary(path: Path, root: Path, issues: list[Issue]) -> bool:
    """Check resolved containment before inspecting a file or directory's contents."""
    try:
        if path.resolve().is_relative_to(root):
            return True
    except (OSError, RuntimeError):
        pass
    issues.append(Issue(path, "path-boundary", "path cannot be resolved inside the database/discovery boundary; not inspected"))
    return False


def children(path: Path, issues: list[Issue]) -> list[Path]:
    try:
        return sorted(path.iterdir())
    except OSError:
        issues.append(Issue(path, "read-error", "directory could not be read"))
        return []


def load_note(path: Path, root: Path, issues: list[Issue], kind: str = "structural") -> Note | None:
    if not within_boundary(path, root, issues):
        return None
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        issues.append(Issue(path, "read-error", "file could not be read as UTF-8"))
        return None
    try:
        metadata, body = parse_frontmatter(text)
    except FrontmatterError as error:
        issues.append(Issue(path, f"{kind}-frontmatter", str(error)))
        return None
    return Note(path, metadata, body)


def scalar_choice(value: Any, choices: set[str]) -> bool:
    return isinstance(value, str) and value in choices


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def wikilink_target(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", value.strip())
    return match.group(1).strip() if match else None


def headings(body: str) -> list[tuple[int, int, str]]:
    """Top-level ATX headings, excluding fenced code blocks."""
    result = []
    fence: str | None = None
    for index, line in enumerate(body.splitlines()):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            continue
        if marker:
            fence = marker[1]
            continue
        match = re.match(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?)|[ \t]*)$", line)
        if match:
            title = re.sub(r"[ \t]+#+[ \t]*$", "", match[2] or "").strip()
            result.append((index, len(match[1]), title))
    return result


def primary_title(note: Note) -> str | None:
    found = headings(note.body.lstrip("\r\n"))
    return found[0][2] if found and found[0][0] == 0 and found[0][1] == 1 and found[0][2] else None


def portable_component(name: str) -> str | None:
    component = " ".join(FORBIDDEN.sub(" ", name).split()).rstrip(".").rstrip()
    if component in {"", ".", ".."}:
        return None
    return "_" + component if component.upper() in DEVICE_STEMS else component


def expected_filename(note: Note, core: Note | None, parent: Note | None) -> str | None:
    """Default title convention: opening H1 is the Core/local node name."""
    title = primary_title(note)
    if title is None:
        return None
    names = [title]
    if note.metadata.get("type") != "core":
        if core is None or parent is None:
            return None
        names = [primary_title(core)]
        if parent.path != core.path:
            names.append(primary_title(parent))
        names.append(title)
    if any(name is None for name in names):
        return None
    components = [portable_component(name) for name in names]
    if any(component is None for component in components):
        return None
    return " - ".join(components) + ".md"


def check_markdown(note: Note, issues: list[Issue]) -> None:
    body = note.body.lstrip("\r\n")
    lines = body.splitlines()
    if primary_title(note) is None:
        issues.append(Issue(note.path, "heading", "note body must begin with a non-empty level-one heading"))
    previous_level = 0
    for index, level, _ in headings(body):
        if level > previous_level + 1:
            issues.append(Issue(note.path, "heading-sequence", f"heading skips a level at body line {index + 1}"))
        previous_level = level
        if index + 1 >= len(lines) or lines[index + 1].strip() or (index + 2 < len(lines) and not lines[index + 2].strip()):
            issues.append(Issue(note.path, "heading-blank-line", f"heading needs exactly one following blank line at body line {index + 1}"))


def database_notes(root: Path, collections: list[Path], issues: list[Issue]) -> tuple[list[Note], list[Path]]:
    notes: list[Note] = []
    workspaces: list[Path] = []

    def scan(directory: Path, workspace: bool = False) -> None:
        for path in children(directory, issues):
            if not within_boundary(path, root, issues):
                continue
            if path.name == "Attachments":
                if not path.is_dir():
                    issues.append(Issue(path, "attachments-missing", "Attachments must be a directory"))
                continue
            if path.is_dir():
                if workspace:
                    issues.append(Issue(path, "nested-directory", "nested workspace directories require resource-contract review; not scanned as structural notes"))
                else:
                    workspaces.append(path)
                    scan(path, workspace=True)
            elif path.suffix == ".md":
                note = load_note(path, root, issues)
                if note:
                    notes.append(note)

    for collection in collections:
        scan(collection)
    return notes, workspaces


def validate_database(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    root = root.absolute()
    # Resolve OS aliases (such as /var -> /private/var), but do not redirect
    # an explicitly selected database root into another owned database.
    if root.is_symlink():
        return [Issue(root, "path-boundary", "database-root symlinks require explicit ownership review; not inspected")]
    try:
        root = root.resolve()
    except (OSError, RuntimeError):
        return [Issue(root, "path-boundary", "database root could not be resolved; not inspected")]
    if (root.parent.name, root.parent.parent.name, root.parent.parent.parent.name) != ("Databases", "Knowledge", "app"):
        return [Issue(root, "database-location", "database must be a direct child of app/Knowledge/Databases")]
    manifest_path = root / "Database.md"
    if not within_boundary(manifest_path, root, issues):
        return issues
    if not manifest_path.is_file():
        return [Issue(manifest_path, "manifest-missing", "Database.md is required")]
    manifest = load_note(manifest_path, root, issues, "manifest")
    if manifest is None:
        return issues
    metadata = manifest.metadata
    for field in MANIFEST_FIELDS:
        if field not in metadata:
            issues.append(Issue(manifest_path, "manifest-field", f"missing required field '{field}'"))
    if type(metadata.get("manifest_version")) is not int or metadata["manifest_version"] != 1:
        issues.append(Issue(manifest_path, "manifest-version", "only integer manifest_version 1 is supported; database contents were not inspected"))
        return issues
    for field, code in (("database_id", "manifest-id"), ("database_name", "manifest-name")):
        if not nonempty_string(metadata.get(field)):
            issues.append(Issue(manifest_path, code, f"{field} must be a non-empty string"))
    if "type" in metadata:
        issues.append(Issue(manifest_path, "manifest-type", "Database.md is not a structural note and must not declare type"))
    if not scalar_choice(metadata.get("database_status"), VALID_STATUSES):
        issues.append(Issue(manifest_path, "manifest-status", "database_status must be active, draft, or archived"))
    sections = {title for _, _, title in headings(manifest.body)}
    for section in REQUIRED_BODY_SECTIONS:
        if section not in sections:
            issues.append(Issue(manifest_path, "manifest-section", f"missing required body section '{section}'"))

    collections = metadata.get("data_collections")
    if not isinstance(collections, list) or not collections or any(not nonempty_string(item) for item in collections):
        issues.append(Issue(manifest_path, "manifest-collections", "data_collections must be a non-empty list of names"))
        collections = []
    declared: list[str] = []
    for collection in collections:
        if collection in {".", ".."} or "/" in collection or "\\" in collection or "\x00" in collection:
            issues.append(Issue(manifest_path, "collection-name", "each collection must be a direct-child directory name, not a path"))
        elif collection in declared:
            issues.append(Issue(manifest_path, "manifest-collections", "data_collections must contain unique names"))
        else:
            declared.append(collection)
    views = root / "Views"
    if within_boundary(views, root, issues) and not views.is_dir():
        issues.append(Issue(views, "views-missing", "Views/ is required, but may be empty"))
    data_root = root / "Data"
    if not within_boundary(data_root, root, issues):
        return issues
    collection_paths = []
    for collection in declared:
        path = data_root / collection
        if not within_boundary(path, root, issues):
            continue
        if path.resolve().parent != data_root.resolve():
            issues.append(Issue(path, "collection-location", "collection must resolve directly beneath Data/; not inspected"))
            continue
        if not path.is_dir():
            issues.append(Issue(path, "collection-missing", "declared data collection directory is required"))
            continue
        collection_paths.append(path)
        attachments = path / "Attachments"
        if within_boundary(attachments, root, issues) and not attachments.is_dir():
            issues.append(Issue(attachments, "attachments-missing", "each declared collection must contain Attachments/"))
    if data_root.is_dir():
        for child in children(data_root, issues):
            if not within_boundary(child, root, issues):
                continue
            if child.is_dir() and child.name not in declared:
                issues.append(Issue(child, "collection-undeclared", "direct data collection is not declared in Database.md"))
            elif child.suffix == ".md" and child.is_file():
                issues.append(Issue(child, "note-location", "canonical notes must be inside a declared collection"))

    notes, workspaces = database_notes(root, collection_paths, issues)
    by_stem: dict[str, list[Note]] = defaultdict(list)
    for note in notes:
        by_stem[note.path.stem].append(note)
    for matches in by_stem.values():
        if len(matches) > 1:
            for note in matches:
                issues.append(Issue(note.path, "filename-collision", "filename stem is not unique across the database"))

    def resolve(value: Any) -> Note | None:
        target = wikilink_target(value)
        if target is None:
            return None
        matches = by_stem.get(target, [])
        if not matches:
            # Qualified links select already-discovered local notes; never open a link path.
            matches = [note for note in notes if target in {
                note.path.relative_to(root).as_posix(),
                note.path.relative_to(root).with_suffix("").as_posix(),
                note.path.relative_to(root.parents[3]).as_posix(),
                note.path.relative_to(root.parents[3]).with_suffix("").as_posix(),
                note.path.name,
            }]
        return matches[0] if len(matches) == 1 and len(by_stem[matches[0].path.stem]) == 1 else None

    cores = {note.path: resolve(note.metadata.get("core")) for note in notes}
    parents = {note.path: resolve(note.metadata.get("parent_note")) for note in notes}
    expected_names: dict[str, list[Note]] = defaultdict(list)
    for note in notes:
        metadata = note.metadata
        note_type = metadata.get("type")
        core, parent = cores[note.path], parents[note.path]
        for field in STRUCTURAL_FIELDS:
            if field not in metadata:
                issues.append(Issue(note.path, "structural-field", f"missing required field '{field}'"))
        if not scalar_choice(note_type, VALID_TYPES):
            issues.append(Issue(note.path, "structural-type", "type must be core, shard, or pebble"))
        if not nonempty_string(metadata.get("pool")):
            issues.append(Issue(note.path, "structural-pool", "pool must be a non-empty scalar string"))
        if not scalar_choice(metadata.get("status"), VALID_STATUSES):
            issues.append(Issue(note.path, "structural-status", "status must be active, draft, or archived"))
        if note_type == "core":
            if metadata.get("parent_note") is not None and metadata.get("parent_note") != "":
                issues.append(Issue(note.path, "core-parent", "Core parent_note must be empty"))
            if core is None or core.path != note.path:
                issues.append(Issue(note.path, "core-reference", "Core core field must self-reference"))
        elif scalar_choice(note_type, {"shard", "pebble"}):
            if core is None or core.metadata.get("type") != "core":
                issues.append(Issue(note.path, "core-reference", "core must resolve unambiguously to a canonical Core"))
            elif nonempty_string(metadata.get("pool")) and metadata.get("pool") != core.metadata.get("pool"):
                issues.append(Issue(note.path, "lineage-pool", "supporting note must use its Core's Pool"))
            if parent is None:
                issues.append(Issue(note.path, "parent-reference", "parent_note must resolve unambiguously to a note in this database"))
            elif parent.metadata.get("type") == "pebble":
                issues.append(Issue(note.path, "pebble-parent", "a Pebble cannot be a structural parent"))
            elif not scalar_choice(parent.metadata.get("type"), {"core", "shard"}):
                issues.append(Issue(note.path, "parent-type", "structural parent must be a Core or Shard"))
            if parent and parent.path == note.path:
                issues.append(Issue(note.path, "self-parent", "a note cannot parent itself"))
            if parent and core and cores[parent.path] and cores[parent.path].path != core.path:
                issues.append(Issue(note.path, "lineage-core", "parent and child declare different root Cores"))

        if FORBIDDEN.search(note.path.stem) or note.path.stem.endswith((" ", ".")) or note.path.stem.upper() in DEVICE_STEMS:
            issues.append(Issue(note.path, "filename-portable", "filename violates portable naming rules"))
        title = primary_title(note)
        if title is not None and portable_component(title) is None:
            issues.append(Issue(note.path, "filename-name", "canonical name has no usable portable filename component"))
        expected = expected_filename(note, core, parent)
        if expected:
            expected_names[expected].append(note)
            if note.path.name != expected:
                issues.append(Issue(note.path, "filename", f"expected '{expected}' under the default heading/title convention"))
                # A legitimate local name may itself contain ' - '.
                if scalar_choice(note_type, {"shard", "pebble"}) and len(note.path.stem.split(" - ")) > 3:
                    issues.append(Issue(note.path, "filename-context", "supporting filename accumulates context inconsistent with its canonical names"))
        check_markdown(note, issues)
        if note_type != "core":
            seen = {note.path}
            ancestor = parent
            while ancestor:
                if ancestor.path in seen:
                    issues.append(Issue(note.path, "lineage-cycle", "structural parent lineage contains a cycle"))
                    break
                seen.add(ancestor.path)
                if metadata.get("status") == "active" and ancestor.metadata.get("status") == "archived":
                    issues.append(Issue(note.path, "archived-ancestor", "active note is beneath an archived structural ancestor"))
                if ancestor.metadata.get("type") == "core":
                    if core and ancestor.path != core.path:
                        issues.append(Issue(note.path, "lineage-root", "parent chain reaches a different Core than the core field"))
                    break
                ancestor = parents[ancestor.path]

    for matches in expected_names.values():
        if len(matches) > 1:
            for note in matches:
                issues.append(Issue(note.path, "filename-collision", "canonical names derive the same expected filename"))
    for workspace in workspaces:
        contained = [note for note in notes if note.path.parent == workspace]
        roots = [note for note in contained if note.metadata.get("type") == "core"]
        if len(roots) != 1 or roots[0].path.stem != workspace.name:
            issues.append(Issue(workspace, "workspace-core", "workspace must contain exactly one Core and be named for its filename stem"))
            continue
        workspace_core = roots[0]
        for note in contained:
            core = cores[note.path]
            if core is None or core.path != workspace_core.path:
                issues.append(Issue(note.path, "workspace-lineage", "workspace may contain only its own Core lineage"))
        for note in notes:
            core = cores[note.path]
            if core and core.path == workspace_core.path and note.path.parent != workspace:
                issues.append(Issue(note.path, "workspace-split", "a workspace lineage must not be split across other locations"))
    for note in notes:
        core = cores[note.path]
        if core and note.path.parent in workspaces and core.path.parent != note.path.parent:
            issues.append(Issue(note.path, "workspace-split", "workspace note must be colocated with its Core"))
    return issues


def discover_databases(app_root: Path, issues: list[Issue] | None = None) -> list[Path]:
    issues = issues if issues is not None else []
    try:
        app_root = app_root.resolve()
    except (OSError, RuntimeError):
        issues.append(Issue(app_root, "path-boundary", "discovery root could not be resolved; not inspected"))
        return []
    db_root = app_root / "Knowledge" / "Databases"
    if not within_boundary(db_root, app_root, issues):
        return []
    if not db_root.is_dir():
        if db_root.exists():
            issues.append(Issue(db_root, "database-location", "Databases must be a directory"))
        return []
    roots = []
    for path in children(db_root, issues):
        if path.is_symlink():
            issues.append(Issue(path, "path-boundary", "database-root symlinks require explicit ownership review; not inspected"))
        elif path.is_dir():
            roots.append(path)
        elif path.name != ".gitkeep":
            issues.append(Issue(path, "database-location", "Databases/ may contain only database directories"))
    return roots


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, help="database root; defaults to all database candidates under app/Knowledge/Databases")
    args = parser.parse_args(argv)
    workspace = Path(__file__).resolve().parents[2]
    all_issues: list[Issue] = []
    roots = [args.path] if args.path else discover_databases(workspace / "app", all_issues)
    for issue in all_issues:
        print(issue.render(workspace))
    if not roots and not all_issues:
        print("No databases found under app/Knowledge/Databases.")
    for root in roots:
        issues = validate_database(root)
        all_issues.extend(issues)
        print(f"{root}: {'structural checks passed (see validation scope)' if not issues else f'{len(issues)} issue(s)'}")
        for issue in issues:
            print(f"  {issue.render(root.absolute())}")
    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
