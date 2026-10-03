import contextlib
import hashlib
import io
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from _support import FIXTURES, GAMES_BLUEPRINT, SCRIPTS
from validate_shardbase import (
    Note,
    _parse_frontmatter_details,
    discover_databases,
    main,
    parse_frontmatter,
    validate_database,
)

VALID_DATABASE = FIXTURES / "valid-database"


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name).resolve() / "app" / "Knowledge" / "Databases" / "Example Database"
        self.database.parent.mkdir(parents=True)
        shutil.copytree(VALID_DATABASE, self.database)

    def tearDown(self):
        self.temp_dir.cleanup()

    @property
    def collection(self):
        return self.database / "Data" / "Game"

    def codes(self):
        return {issue.code for issue in validate_database(self.database)}

    def replace(self, path, old, new):
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding="utf-8")

    def set_field(self, path, field, value):
        _, frontmatter, body = path.read_text(encoding="utf-8").split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        metadata[field] = value
        path.write_text("---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False) + "---" + body, encoding="utf-8")

    def create_note(self, filename, title, kind="core", core=None, parent=None, directory=None, note_id=None):
        path = (directory or self.collection) / filename
        if note_id is None:
            match = re.search(r" - ([0-9a-hjkmnp-tv-z]{10})\.md$", filename)
            note_id = match.group(1) if match else hashlib.sha1(filename.encode("utf-8")).hexdigest()[:10]
        metadata = dict(type=kind, pool="Examples", core=f"[[{core or path.stem}]]", parent_note=f"[[{parent}]]" if parent else None, status="active", aliases=None, id=note_id, tags=None)
        path.write_text("---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False) + f"---\n# {title}\n\nExample content.\n", encoding="utf-8")
        return path

    def bundle(self):
        workspace = self.collection / "Example"
        workspace.mkdir()
        for note in self.collection.glob("*.md"):
            note.rename(workspace / note.name)
        return workspace

    def test_valid_database_passes(self):
        self.assertEqual(validate_database(self.database), [])

    def contract(self, schema):
        self.set_field(self.database / "Database.md", "semantic_schema", schema)

    def field_contract(self, declaration, name="example_field"):
        self.contract({"fields": {name: declaration}})

    def test_semantic_schema_positive_envelopes(self):
        for schema in ({"fields": {}}, {"fields": {}, "allow_undeclared_fields": True},
                       {"fields": {}, "allow_undeclared_fields": False}):
            with self.subTest(schema=schema):
                self.contract(schema)
                self.assertEqual(validate_database(self.database), [])

    def test_pool_vocabulary_declarations(self):
        manifest = self.database / "Database.md"
        for value in (None, {}, "Examples", [], [""], [" \t"], [1], [False], [["Examples"]], ["Examples", "Examples"]):
            with self.subTest(value=value):
                self.set_field(manifest, "pool_vocabulary", value)
                self.assertIn("manifest-pool-vocabulary", self.codes())
        for value in (["Examples"], ["Example", "example", " Example "]):
            self.set_field(manifest, "pool_vocabulary", value)
            before = manifest.read_bytes()
            self.assertEqual(validate_database(self.database), [])
            self.assertEqual(manifest.read_bytes(), before)

    def test_invalid_semantic_schema_envelopes(self):
        for schema in (None, [], "schema", {}, {"fields": []}, {"fields": None},
                       {"fields": {}, "unknown": True}, {"fields": {}, 1: True}):
            with self.subTest(schema=schema):
                self.contract(schema)
                self.assertIn("semantic-schema", self.codes())
        for value in (None, "true", "false", 0, 1, [], {}, 1.5):
            with self.subTest(value=value):
                self.contract({"fields": {}, "allow_undeclared_fields": value})
                self.assertIn("semantic-schema", self.codes())

    def test_invalid_semantic_field_names(self):
        for name in (1, None, "", " \t", "type", "pool", "core", "parent_note", "status", "aliases", "id", "tags"):
            with self.subTest(name=name):
                self.field_contract({"shape": "string"}, name)
                self.assertIn("semantic-field", self.codes())

    def test_invalid_semantic_field_declarations(self):
        for declaration in (None, [], "string", {}, {"shape": "object"}, {"shape": []},
                            {"shape": None}, {"shape": "string", "extension": True}, {"shape": "string", 1: True}):
            with self.subTest(declaration=declaration):
                self.field_contract(declaration)
                self.assertIn("semantic-field", self.codes())

    def test_valid_semantic_shapes_selectors_and_constraints(self):
        for shape, values in (("string", ["One", "one", " One "]),
                              ("string_list", ["One", "one"]), ("boolean", [True, False]),
                              ("integer", [-1, 0, 1]), ("date", ["0001-01-01", "2024-02-29", "9999-12-31"])):
            for required in (True, False):
                with self.subTest(shape=shape, required=required):
                    self.field_contract(dict(shape=shape, allowed_values=values, collections=["Game"],
                                             types=["core", "shard", "pebble"], required=required))
                    self.assertEqual(validate_database(self.database), [])
        for minimum in (0, 1):
            for unique in (True, False):
                self.field_contract(dict(shape="string_list", item_pattern=r"^[a-z]+$", min_items=minimum, unique=unique))
                self.assertEqual(validate_database(self.database), [])
        # A whitespace regex is valid; non-emptiness does not trim patterns.
        self.field_contract(dict(shape="string_list", item_pattern=" "))
        self.assertEqual(validate_database(self.database), [])

    def test_invalid_semantic_selectors(self):
        for selector, invalid in (
            ("collections", (None, "Game", [], [1], [False], [{}], ["Game", "Game"], ["Other"], [""])),
            ("types", (None, "core", [], [1], [False], [{}], ["core", "core"], ["pool"], ["Core"])),
        ):
            for value in invalid:
                with self.subTest(selector=selector, value=value):
                    self.field_contract({"shape": "string", selector: value})
                    self.assertIn("semantic-field", self.codes())

    def test_collections_selectors_use_manifest_not_filesystem(self):
        (self.database / "Data/Other").mkdir()
        self.field_contract(dict(shape="string", collections=["Other"]))
        self.assertIn("semantic-field", self.codes())
        self.set_field(self.database / "Database.md", "data_collections", ["Game", "Other"])
        self.assertNotIn("semantic-field", self.codes())
        self.set_field(self.database / "Database.md", "data_collections", [None])
        self.assertTrue({"manifest-collections", "semantic-field"} <= self.codes())

    def test_required_is_strict_boolean(self):
        for value in ("true", "false", 0, 1, None, [], {}, 1.5):
            with self.subTest(value=value):
                self.field_contract(dict(shape="string", required=value))
                self.assertIn("semantic-field", self.codes())

    def test_list_constraints_reject_other_shapes(self):
        for shape in ("string", "boolean", "integer", "date"):
            for constraint, value in (("item_pattern", "x"), ("min_items", 0), ("unique", False)):
                with self.subTest(shape=shape, constraint=constraint):
                    self.field_contract({"shape": shape, constraint: value})
                    self.assertIn("semantic-constraint", self.codes())

    def test_invalid_list_constraint_values(self):
        for constraint, invalid in (
            ("item_pattern", (None, 1, False, [], {}, "", "[", r"(?z)x", "x{999999999999999999999999999999}")),
            ("min_items", (-1, True, False, 1.0, "1", None, [], {})),
            ("unique", (0, 1, "true", "false", None, [], {}, 1.0)),
        ):
            for value in invalid:
                with self.subTest(constraint=constraint, value=value):
                    self.field_contract({"shape": "string_list", constraint: value})
                    self.assertIn("semantic-constraint", self.codes())

    def test_invalid_allowed_values(self):
        for shape, invalid in (
            ("string", ([1], [False], [None], [[]], [{}], [""], [" \t"], ["x", "x"])),
            ("string_list", ([1], [False], [None], [["x"]], [{}], [""], [" "], ["x", "x"])),
            ("boolean", ([0], [1], ["true"], [None], [[]], [{}], [True, True])),
            ("integer", ([True], [False], [1.0], ["1"], [None], [[]], [{}], [1, 1])),
            ("date", ([1], [False], [None], [[]], [{}], ["2026-10-03", "2026-10-03"])),
        ):
            for values in (None, "x", {}, [], *invalid):
                with self.subTest(shape=shape, values=values):
                    self.field_contract(dict(shape=shape, allowed_values=values))
                    self.assertIn("semantic-constraint", self.codes())
        for shape in ("boolean", "integer"):
            self.field_contract(dict(shape=shape, allowed_values=[True, 1]))
            issues = validate_database(self.database)
            self.assertTrue(any("must match shape" in issue.message for issue in issues))
            self.assertFalse(any("distinct" in issue.message for issue in issues))

    def date_contract_source(self, values):
        manifest = self.database / "Database.md"
        original = manifest.read_text()
        # Keep raw scalar spelling rather than round-tripping through safe_dump.
        manifest.write_text(original.replace("---\n", "---\nsemantic_schema:\n  fields:\n    event_date:\n      shape: date\n      allowed_values: [" + values + "]\n", 1))
        return manifest, original

    def test_date_allowed_values_exact_source(self):
        for scalar in ('"2026-10-03"', "2026-10-03", "'0001-01-01'", "0001-01-01", "9999-12-31", "2024-02-29"):
            with self.subTest(scalar=scalar):
                manifest, original = self.date_contract_source(scalar)
                try:
                    self.assertEqual(validate_database(self.database), [])
                finally:
                    manifest.write_text(original)
        for scalar in ("2026-1-03", "2026-10-3", "2026-10", "2026-10-03T12:00:00", "2026-02-30",
                       "0000-01-01", "10000-01-01", "2026-1-3", "2026-10-03 12:00:00Z"):
            for quoted in (False, True):
                with self.subTest(scalar=scalar, quoted=quoted):
                    manifest, original = self.date_contract_source(f'"{scalar}"' if quoted else scalar)
                    try:
                        # Impossible unquoted timestamps fail safe YAML construction.
                        self.assertTrue({"manifest-frontmatter", "semantic-constraint"} & self.codes())
                    finally:
                        manifest.write_text(original)
        for values in ('2026-10-03, "2026-10-03"', '!!str 2026-10-03, 2026-10-03'):
            manifest, original = self.date_contract_source(values)
            try:
                self.assertIn("semantic-constraint", self.codes())
            finally:
                manifest.write_text(original)

    def test_frontmatter_details_preserve_source_and_public_api(self):
        source = '---\nexact: 2026-10-03\nquoted: "2026-10-03"\ntimestamp: 2026-1-3T12:00:00\n---\n# Example\n'
        details = _parse_frontmatter_details(source)
        self.assertEqual(parse_frontmatter(source), (details.metadata, details.body))
        nodes = {key.value: value for key, value in details.root_node.value}
        self.assertEqual(nodes["exact"].value, "2026-10-03")
        self.assertEqual(nodes["quoted"].value, "2026-10-03")
        self.assertEqual(nodes["timestamp"].value, "2026-1-3T12:00:00")
        self.assertEqual(details.metadata["exact"].isoformat(), "2026-10-03")
        self.assertEqual(details.metadata["timestamp"].isoformat(), "2026-01-03T12:00:00")

    def test_semantic_contract_does_not_enforce_note_values(self):
        self.set_field(self.database / "Database.md", "pool_vocabulary", ["Other"])
        self.contract({"allow_undeclared_fields": False, "fields": {
            "required_field": dict(shape="integer", required=True),
            "optional_field": dict(shape="string_list", collections=["Game"], types=["pebble"],
                                   allowed_values=["one"], item_pattern="one", min_items=2, unique=True),
        }})
        self.set_field(self.collection / "Example.md", "optional_field", [1, 1])
        self.set_field(self.collection / "Example.md", "undeclared_field", {})
        self.assertEqual(validate_database(self.database), [])

    def test_unsupported_manifest_gates_semantic_contract_validation(self):
        self.set_field(self.database / "Database.md", "manifest_version", 2)
        self.contract(None)
        with patch("validate_shardbase.validate_semantic_contract", side_effect=AssertionError("unsupported manifest")):
            self.assertIn("manifest-version", self.codes())

    def test_common_fields_required_on_every_structural_type_without_rewriting(self):
        for path in sorted(self.collection.glob("*.md")):
            original = path.read_text(encoding="utf-8")
            for field in ("aliases", "id", "tags"):
                with self.subTest(note=path.name, field=field):
                    path.write_text(re.sub(rf"(?m)^{re.escape(field)}:.*\n", "", original, count=1), encoding="utf-8")
                    before = path.read_bytes()
                    issues = validate_database(self.database)
                    self.assertTrue(any(issue.path == path and issue.code == "note-field" and f"'{field}'" in issue.message for issue in issues))
                    self.assertEqual(path.read_bytes(), before)
            path.write_text(original, encoding="utf-8")

    def test_common_field_valid_shapes(self):
        path = self.collection / "Example.md"
        for field, values in (
            ("aliases", (None, [], ["Another name", "Exemple"])),
            ("tags", (None, [], ["games", "games/reference"])),
            ("id", ("0a1b2c3d4e", "1234567890", "zzzzzzzzzz")),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    self.set_field(path, field, value)
                    self.assertEqual(validate_database(self.database), [])

    def test_common_field_invalid_shapes(self):
        path = self.collection / "Example.md"
        original = path.read_text(encoding="utf-8")
        for field, values in (
            ("aliases", ("", "Name", True, 1, {}, [None], [1], [False], [""], [" "], [["Name"]], [{}])),
            ("tags", ("", "games", True, 1, {}, [None], [1], [False], [""], [" "], [["games"]], [{}])),
            ("id", (None, "", "note-001", "ABCDEF0123", "iiiiiiiiii", "oooooooooo", "llllllllll", "uuuuuuuuuu", "short", "12345678901", True, 1, 1.5, [], ["abcdef0123"], {}, {"value": "abcdef0123"})),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    path.write_text(original, encoding="utf-8")
                    self.set_field(path, field, value)
                    self.assertIn(f"note-{field}", self.codes())


    def test_note_ids_must_be_unique(self):
        shard = self.collection / "Weapons - 5f6g7h8j9k.md"
        self.set_field(shard, "id", "0a1b2c3d4e")
        self.assertIn("note-id-duplicate", self.codes())

    def test_common_fields_do_not_change_structural_resolution(self):
        core = self.collection / "Example.md"
        self.set_field(core, "aliases", ["Alternate"])
        self.set_field(core, "id", "abcde12345")
        self.set_field(core, "tags", ["Another Pool"])
        self.assertEqual(validate_database(self.database), [])
        shard = self.collection / "Weapons - 5f6g7h8j9k.md"
        for target in ("Alternate", "abcde12345"):
            with self.subTest(target=target):
                self.set_field(shard, "parent_note", f"[[{target}]]")
                self.assertIn("parent-reference", self.codes())

    def test_root_structural_notes_are_reported_without_resolving_them(self):
        path = self.create_note("Misplaced.md", "Misplaced", directory=self.database)
        self.set_field(self.collection / "Weapons - 5f6g7h8j9k.md", "parent_note", "[[Misplaced]]")
        issues = validate_database(self.database)
        self.assertTrue(any(issue.path == path and issue.code == "note-location" for issue in issues))
        self.assertIn("parent-reference", {issue.code for issue in issues})

    def test_root_resources_are_not_structural_notes(self):
        (self.database / "README.md").write_text("Resource documentation without frontmatter.\n")
        (self.database / "Resource.md").write_text("---\ndescription: Local resource\n---\nResource content.\n")
        self.assertEqual(validate_database(self.database), [])

    def test_root_malformed_and_unreadable_files_are_reported(self):
        (self.database / "Broken.md").write_text("---\ntype: [core\n---\n")
        (self.database / "Unreadable.md").write_bytes(b"\xff")
        self.assertTrue({"root-frontmatter", "read-error"} <= self.codes())

    def test_manifest_heading_contract(self):
        manifest = self.database / "Database.md"
        original = manifest.read_text()
        for old, new, code in (
            ("# Example Database", "Example Database", "heading"),
            ("### Includes", "###### Includes", "manifest-section"),
            ("### Excludes", "## Excludes", "manifest-section"),
            ("### Includes", "## Other\n\n### Includes", "manifest-section"),
            ("## Schema", "### Schema", "manifest-section"),
            ("## Purpose\n\n", "## Purpose\n", "heading-blank-line"),
        ):
            with self.subTest(new=new):
                manifest.write_text(original.replace(old, new))
                self.assertIn(code, self.codes())
        manifest.write_text(original + "\n```markdown\n###### Example only\n```\n")
        self.assertEqual(validate_database(self.database), [])

    def test_missing_manifest_field_is_reported(self):
        manifest = self.database / "Database.md"
        manifest.write_text(manifest.read_text().replace("database_status: active\n", ""), encoding="utf-8")
        codes = {issue.code for issue in validate_database(self.database)}
        self.assertIn("manifest-field", codes)

    def test_note_without_frontmatter_is_reported(self):
        note = self.database / "Data" / "Game" / "Unstructured.md"
        note.write_text("# Unstructured\n\nThis must not be silently ignored.\n", encoding="utf-8")
        codes = {issue.code for issue in validate_database(self.database)}
        self.assertIn("structural-frontmatter", codes)

    def test_pebble_cannot_parent_a_note(self):
        shard = self.database / "Data" / "Game" / "Weapons - 5f6g7h8j9k.md"
        shard.write_text(shard.read_text(encoding="utf-8").replace("parent_note: \"[[Example]]\"", "parent_note: \"[[Blade - mnpqrstvwz]]\""), encoding="utf-8")
        codes = {issue.code for issue in validate_database(self.database)}
        self.assertIn("pebble-parent", codes)

    def test_lineage_cycle_is_reported(self):
        first = self.database / "Data" / "Game" / "Weapons - 5f6g7h8j9k.md"
        first.write_text(first.read_text(encoding="utf-8").replace("parent_note: \"[[Example]]\"", "parent_note: \"[[Blade - mnpqrstvwz]]\""), encoding="utf-8")
        codes = {issue.code for issue in validate_database(self.database)}
        self.assertIn("lineage-cycle", codes)

    def test_supporting_filename_with_ancestry_is_reported(self):
        source = self.database / "Data" / "Game" / "Blade - mnpqrstvwz.md"
        target = source.with_name("Example - Weapons - Blade - mnpqrstvwz.md")
        source.rename(target)
        self.assertIn("filename", self.codes())

    def test_reparenting_does_not_change_supporting_filename(self):
        self.create_note("Armor - 6666666666.md", "Armor", "shard", "Example", "Example")
        blade = self.collection / "Blade - mnpqrstvwz.md"
        self.set_field(blade, "parent_note", "[[Armor - 6666666666]]")
        self.assertEqual(validate_database(self.database), [])

    def test_same_local_title_is_valid_with_distinct_ids(self):
        self.create_note("Topic - 7777777777.md", "Topic", "shard", "Example", "Example")
        self.create_note("Topic - 8888888888.md", "Topic", "shard", "Example", "Example")
        self.assertEqual(validate_database(self.database), [])

    def test_valid_yaml_forms(self):
        manifest = self.database / "Database.md"
        self.replace(manifest, "data_collections:\n  - Game", "data_collections: [Game] # inline list")
        core = self.collection / "Example.md"
        self.replace(core, "status: active", "status: active # current")
        self.replace(core, "pool: Examples", 'pool: "Exa\\u006dples"')
        self.replace(core, "entity_kind: example", "entity_kind: example\nextra: &value\n  text: |\n    First line.\n    ---\n    Second line.\ncopy: *value\nmerged:\n  <<: *value\n  text: override")
        self.assertEqual(validate_database(self.database), [])

    def test_malformed_yaml_is_a_diagnostic(self):
        path = self.collection / "Example.md"
        original = path.read_text()
        for frontmatter in ("type: [core", "[core, shard]", "null", "1: value", "type: core\ntype: shard", "extra: !!python/object:unknown {}", "extra: 2026-99-99", "? [a, b]\n: value", "!!map [x]", "!!bool maybe", "!!timestamp nope"):
            with self.subTest(frontmatter=frontmatter):
                path.write_text(f"---\n{frontmatter}\n---\n# Example\n\nContent.\n")
                self.assertIn("structural-frontmatter", self.codes())
        path.write_text(original)

    def test_missing_closing_delimiter(self):
        path = self.collection / "Example.md"
        path.write_text("---\ntype: core\n")
        self.assertIn("structural-frontmatter", self.codes())

    def test_structural_field_shapes_do_not_crash(self):
        path = self.collection / "Example.md"
        original = path.read_text()
        for field, code in (("type", "structural-type"), ("status", "structural-status"), ("pool", "structural-pool"), ("core", "core-reference")):
            for value in ([], ["core"], {}, {"value": "core"}, True, 1, None):
                with self.subTest(field=field, value=value):
                    path.write_text(original)
                    self.set_field(path, field, value)
                    self.assertIn(code, self.codes())

    def test_manifest_shapes_and_versions_do_not_crash(self):
        path = self.database / "Database.md"
        original = path.read_text()
        for field, code in (("database_status", "manifest-status"), ("database_name", "manifest-name"), ("database_id", "manifest-id"), ("data_collections", "manifest-collections"), ("manifest_version", "manifest-version")):
            for value in ([], [1], {}, {"value": 1}, True, None):
                with self.subTest(field=field, value=value):
                    path.write_text(original)
                    self.set_field(path, field, value)
                    self.assertIn(code, self.codes())

    def test_duplicate_manifest_keys_are_reported(self):
        path = self.database / "Database.md"
        self.replace(path, "manifest_version: 1", "manifest_version: 2\nmanifest_version: 1")
        self.assertIn("manifest-frontmatter", self.codes())

    def test_unsupported_version_does_not_read_notes(self):
        self.set_field(self.database / "Database.md", "manifest_version", 2)
        with patch("validate_shardbase.database_notes", side_effect=AssertionError("must not scan unsupported state")):
            self.assertIn("manifest-version", self.codes())

    def test_collection_paths_are_rejected_before_reading(self):
        manifest = self.database / "Database.md"
        outside = self.database.parent / "Outside"
        outside.mkdir()
        (outside / "Attachments").mkdir()
        (outside / "Secret.md").write_text("This must not be read")
        original_read = Path.read_text
        reads = []

        def read(path, *args, **kwargs):
            reads.append(path.resolve())
            return original_read(path, *args, **kwargs)

        for name in ("../../Outside", str(outside), ".", "..", "Nested/Game", "..\\..\\Outside"):
            with self.subTest(name=name):
                self.set_field(manifest, "data_collections", [name])
                with patch.object(Path, "read_text", read):
                    self.assertIn("collection-name", self.codes())
        self.assertTrue(all(path.is_relative_to(self.database) for path in reads))

    def test_external_symlinks_are_not_read(self):
        outside = self.database.parent / "Outside"
        outside.mkdir()
        secret = outside / "Secret.md"
        secret.write_text("This must not be read")
        original_read = Path.read_text

        def read(path, *args, **kwargs):
            self.assertTrue(path.resolve().is_relative_to(self.database))
            return original_read(path, *args, **kwargs)

        for location in ("Database.md", "Escaped.md", "Data", "Data/Game", "Data/Game/Example.md", "Data/Game/Attachments", "Data/Game/EscapedWorkspace"):
            with self.subTest(location=location):
                path = self.database / location
                backup = path.with_name(path.name + ".backup")
                existed = path.exists()
                if existed:
                    path.rename(backup)
                path.symlink_to(secret if path.suffix == ".md" else outside, target_is_directory=path.suffix != ".md")
                with patch.object(Path, "read_text", read):
                    self.assertIn("path-boundary", self.codes())
                path.unlink()
                if existed:
                    backup.rename(path)

    def test_valid_workspace_and_attachment_exclusions(self):
        workspace = self.bundle()
        (workspace / "Attachments").mkdir()
        for folder in (self.collection / "Attachments", workspace / "Attachments", self.database / "Agents", self.database / "Templates", self.database / "Views"):
            folder.mkdir(exist_ok=True)
            (folder / "Resource.md").write_bytes(b"\xff")
        self.assertEqual(validate_database(self.database), [])

    def test_invalid_workspace_note_is_checked(self):
        workspace = self.bundle()
        self.set_field(workspace / "Weapons - 5f6g7h8j9k.md", "type", "invalid")
        self.assertIn("structural-type", self.codes())

    def test_split_workspace_is_reported(self):
        workspace = self.bundle()
        note = workspace / "Blade - mnpqrstvwz.md"
        note.rename(self.collection / note.name)
        self.assertIn("workspace-split", self.codes())

    def test_workspace_with_flat_core_is_reported(self):
        workspace = self.collection / "Example"
        workspace.mkdir()
        note = self.collection / "Weapons - 5f6g7h8j9k.md"
        note.rename(workspace / note.name)
        self.assertIn("workspace-core", self.codes())
        self.assertIn("workspace-split", self.codes())

    def test_wrong_workspace_name_is_reported(self):
        self.bundle().rename(self.collection / "Wrong")
        self.assertIn("workspace-core", self.codes())

    def test_workspace_rejects_foreign_lineage(self):
        workspace = self.bundle()
        self.create_note("Other.md", "Other")
        self.create_note("Topic - abcdef0123.md", "Topic", "shard", "Other", "Other", workspace)
        self.assertIn("workspace-lineage", self.codes())

    def test_nested_structural_directories_are_not_scanned(self):
        nested = self.bundle() / "Weapons"
        nested.mkdir()
        (nested / "Broken.md").write_bytes(b"\xff")
        self.assertIn("nested-directory", self.codes())
        self.assertNotIn("read-error", self.codes())

    def test_required_directories_and_undeclared_collections(self):
        (self.database / "Views" / ".gitkeep").unlink()
        (self.database / "Views").rmdir()
        (self.collection / "Attachments" / ".gitkeep").unlink()
        (self.collection / "Attachments").rmdir()
        (self.database / "Data/Other").mkdir()
        self.assertTrue({"views-missing", "attachments-missing", "collection-undeclared"} <= self.codes())

    def test_collection_declarations_are_unique(self):
        self.set_field(self.database / "Database.md", "data_collections", ["Game", "Game"])
        self.assertIn("manifest-collections", self.codes())

    def test_pool_mismatch_is_reported(self):
        self.set_field(self.collection / "Weapons - 5f6g7h8j9k.md", "pool", "Other")
        self.assertIn("lineage-pool", self.codes())

    def test_core_parent_must_be_empty(self):
        core = self.collection / "Example.md"
        for value in ("garbage", " ", [], {}, False, "[[Example]]"):
            with self.subTest(value=value):
                self.set_field(core, "parent_note", value)
                self.assertIn("core-parent", self.codes())
        for value in (None, ""):
            self.set_field(core, "parent_note", value)
            self.assertEqual(validate_database(self.database), [])

    def test_parent_chain_must_reach_declared_core(self):
        self.create_note("Other.md", "Other")
        self.set_field(self.collection / "Weapons - 5f6g7h8j9k.md", "parent_note", "[[Other]]")
        self.assertTrue({"lineage-core", "lineage-root"} <= self.codes())

    def test_archived_ancestors_are_reported(self):
        self.set_field(self.collection / "Example.md", "status", "archived")
        self.set_field(self.collection / "Weapons - 5f6g7h8j9k.md", "status", "draft")
        issues = validate_database(self.database)
        self.assertTrue(any(issue.path.name == "Blade - mnpqrstvwz.md" and issue.code == "archived-ancestor" for issue in issues))
        self.set_field(self.collection / "Blade - mnpqrstvwz.md", "status", "archived")
        self.assertNotIn("archived-ancestor", self.codes())

    def test_archived_database_does_not_require_archived_notes(self):
        self.set_field(self.database / "Database.md", "database_status", "archived")
        self.assertEqual(validate_database(self.database), [])

    def test_missing_parent_and_core_are_reported(self):
        path = self.collection / "Weapons - 5f6g7h8j9k.md"
        self.set_field(path, "core", "[[Missing]]")
        self.set_field(path, "parent_note", "[[Missing]]")
        self.assertTrue({"core-reference", "parent-reference"} <= self.codes())

    def test_links_only_resolve_inside_discovered_database(self):
        path = self.collection / "Weapons - 5f6g7h8j9k.md"
        for target in ("[[Example|Display]]", "[[Example.md]]", "[[Data/Game/Example]]", "[[app/Knowledge/Databases/Example Database/Data/Game/Example]]"):
            self.set_field(path, "parent_note", target)
            self.assertEqual(validate_database(self.database), [])
        self.set_field(path, "parent_note", "[[../Other/Data/Game/Example]]")
        self.assertIn("parent-reference", self.codes())

    def test_ghost_links_do_not_create_orphans(self):
        core = self.collection / "Example.md"
        core.write_text(core.read_text() + "\n[[Example - Future Topic]]\n")
        self.assertEqual(validate_database(self.database), [])

    def test_portable_names_and_recursive_lineage(self):
        self.create_note("Example Game Chapter 2.md", "Example Game: Chapter 2")
        self.create_note("_CON.md", "CON")
        self.create_note("Étoile.md", "Étoile")
        self.set_field(self.collection / "Blade - mnpqrstvwz.md", "type", "shard")
        self.create_note("Detail - a1b2c3d4e5.md", "Detail", "pebble", "Example", "Blade - mnpqrstvwz")
        self.assertEqual(validate_database(self.database), [])

    def test_wikilink_delimiters_normalize_in_every_name_component(self):
        self.create_note("Game 1.md", "Game #1")
        self.create_note("Weapons primary - 1111111111.md", "Weapons [primary]", "shard", "Game 1", "Game 1")
        self.create_note("Blade 2 - 2222222222.md", "Blade #2", "pebble", "Game 1", "Weapons primary - 1111111111")
        workspace = self.collection / "Game 1"
        workspace.mkdir()
        for path in [p for p in self.collection.glob("*.md") if p.stem in {"Game 1", "Weapons primary - 1111111111", "Blade 2 - 2222222222"}]:
            path.rename(workspace / path.name)
        self.set_field(workspace / "Weapons primary - 1111111111.md", "parent_note", "[[Game 1#Overview|Game #1]]")
        self.assertEqual(validate_database(self.database), [])

    def test_wikilink_normalization_collisions_and_legacy_names(self):
        self.create_note("Game #1.md", "Game #1")
        self.create_note("Game 1.md", "Game 1")
        self.assertTrue({"filename", "filename-portable", "filename-collision"} <= self.codes())

    def test_alternating_trailing_spaces_and_periods(self):
        self.create_note("Game.md", "Game. .")
        self.create_note("Topic - 3333333333.md", "Topic. . .", "shard", "Game", "Game")
        self.create_note("_CON.md", "CON. .")
        self.assertEqual(validate_database(self.database), [])
        self.create_note("Unusable.md", ". . .")
        self.assertIn("filename-name", self.codes())

    def test_delimiter_inside_canonical_name_is_not_extra_ancestry(self):
        core = "Alpha - Beta"
        self.create_note(core + ".md", core)
        self.create_note("Weapons - 4444444444.md", "Weapons", "shard", core, core)
        self.create_note("Blade - Silver - 5555555555.md", "Blade - Silver", "pebble", core, "Weapons - 4444444444")
        self.assertEqual(validate_database(self.database), [])

    def test_unsafe_and_mismatched_core_filenames(self):
        for filename, title in (("Bad:Name.md", "Bad:Name"), ("CON.md", "CON"), ("Trailing..md", "Trailing."), ("Wrong.md", "Different")):
            with self.subTest(filename=filename):
                # Windows treats colons as alternate streams and CON as a device.
                # Inject discovered notes to check every name without creating it.
                path = self.collection / filename
                note = Note(path, dict(type="core", pool="Examples", core=f"[[{path.stem}]]",
                                       parent_note=None, status="active", aliases=None, id="0123456789", tags=None),
                            f"# {title}\n\nExample content.\n")
                with patch("validate_shardbase.database_notes", return_value=([note], {})):
                    self.assertIn("filename", self.codes())

    def test_empty_normalized_name_is_reported(self):
        self.create_note("Wrong.md", "???")
        self.assertIn("filename-name", self.codes())

    def test_normalized_filename_collisions_are_reported(self):
        self.create_note("First.md", "A:B")
        self.create_note("Second.md", "A?B")
        self.assertIn("filename-collision", self.codes())

    def test_duplicate_stems_are_not_resolved_by_collection_path(self):
        other = self.database / "Data/Other"
        other.mkdir()
        (other / "Attachments").mkdir()
        self.set_field(self.database / "Database.md", "data_collections", ["Game", "Other"])
        self.create_note("Example.md", "Example", directory=other)
        self.set_field(self.collection / "Weapons - 5f6g7h8j9k.md", "core", "[[Data/Game/Example]]")
        self.assertTrue({"filename-collision", "core-reference"} <= self.codes())

    def test_heading_spacing_and_depth(self):
        core = self.collection / "Example.md"
        self.replace(core, "## Overview", "### Overview")
        self.assertIn("heading-sequence", self.codes())
        self.replace(core, "### Overview\n\n", "## Overview\n")
        self.assertIn("heading-blank-line", self.codes())

    def test_fenced_code_and_frontmatter_blank_lines(self):
        core = self.collection / "Example.md"
        self.replace(core, "---\n# Example", "---\n\n# Example")
        core.write_text(core.read_text() + "\n```markdown\n###### This is code\nNo heading spacing required\n```\n")
        self.assertEqual(validate_database(self.database), [])

    def test_unreadable_note_is_a_diagnostic(self):
        (self.collection / "Broken.md").write_bytes(b"\xff")
        self.assertIn("read-error", self.codes())

    def test_discovery_includes_manifestless_database(self):
        missing = self.database.parent / "Missing"
        missing.mkdir()
        roots = discover_databases(self.database.parents[2])
        self.assertIn(missing, roots)
        self.assertEqual([issue.code for issue in validate_database(missing)], ["manifest-missing"])
        with patch("validate_shardbase.discover_databases", return_value=roots), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main([]), 1)
        self.assertIn("manifest-missing", output.getvalue())

    def test_cli_exit_status(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "validate_shardbase.py"), str(self.database)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.set_field(self.collection / "Example.md", "type", ["core"])
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "validate_shardbase.py"), str(self.database)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("structural-type", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_discovery_failure_is_not_an_empty_success(self):
        app = Path(self.temp_dir.name) / "other-app"
        (app / "Knowledge").mkdir(parents=True)
        (app / "Knowledge/Databases").write_text("wrong shape")
        issues = []
        self.assertEqual(discover_databases(app, issues), [])
        self.assertEqual([issue.code for issue in issues], ["database-location"])

    def test_discovery_rejects_database_symlinks(self):
        path = self.database.parent / "Alias"
        path.symlink_to(self.database, target_is_directory=True)
        issues = []
        roots = discover_databases(self.database.parents[2], issues)
        self.assertNotIn(path, roots)
        self.assertTrue(any(issue.code == "path-boundary" for issue in issues))
        self.assertEqual([issue.code for issue in validate_database(path)], ["path-boundary"])

    def test_empty_instance_is_successful(self):
        with patch("validate_shardbase.discover_databases", return_value=[]), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main([]), 0)
        self.assertIn("No databases found", output.getvalue())

    def test_missing_dependency_explains_setup(self):
        result = subprocess.run([sys.executable, "-B", "-S", str(SCRIPTS / "validate_shardbase.py")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("app/Scripts/README.md", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_blueprint_scaffolding_survives_file_only_copy(self):
        blueprint = GAMES_BLUEPRINT
        target = self.database.parent / "Games"
        # Copy files only, as Git does: empty directories alone cannot satisfy this test.
        for source in blueprint.rglob("*"):
            if source.is_file():
                destination = target / source.relative_to(blueprint)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
        self.assertEqual(validate_database(target), [])
        self.assertTrue((target / "Views").is_dir())

    def test_validation_does_not_modify_database(self):
        before = {path.relative_to(self.database): path.read_bytes() for path in self.database.rglob("*") if path.is_file()}
        validate_database(self.database)
        after = {path.relative_to(self.database): path.read_bytes() for path in self.database.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

if __name__ == "__main__":
    unittest.main()
