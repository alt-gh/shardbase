"""Synthetic format-v2, legacy-v1, preservation, and adversarial proofs."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from _support import FIXTURES, ROOT, SCRIPTS
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

# isort: split
# Test path bootstrap must run before runtime imports.
import backup_restore as transfer
from backup_restore import BackupError, backup, restore
from database_creation import create_database

PASSWORD = b"synthetic test passphrase"
BLUEPRINT = ROOT / "app/Blueprints/Games"


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.source = self.make_instance("source", "Old Package")
        self.target = self.make_instance("target", "Game Library")
        self.output = self.base / "snapshot.sbbackup"
        self.live = self.source / "app/Knowledge/Databases/Legacy Games"
        shutil.copytree(self.source / "app/Blueprints/Old Package", self.live)
        self.write(self.live, "Agents/Vera.md", self.read(self.live, "Agents/Vera.md") + b"\nSource-only managed edit.\n")
        self.write(self.live, "Database.md", self.read(self.live, "Database.md") + b"\nSource-only contract edit.\n")
        self.write(self.live, "Templates/Game.md", self.read(self.live, "Templates/Game.md") + b"\nSource-only template edit.\n")
        self.write(self.target, "app/Blueprints/Game Library/Agents/Vera.md",
                   self.read(self.target, "app/Blueprints/Game Library/Agents/Vera.md") + b"\nDestination release marker.\n")
        self.write(self.target, "app/Blueprints/Game Library/Database.md",
                   self.read(self.target, "app/Blueprints/Game Library/Database.md") + b"\nDestination contract marker.\n")
        self.write(self.target, "app/Blueprints/Game Library/Templates/Game.md",
                   self.read(self.target, "app/Blueprints/Game Library/Templates/Game.md") + b"\nDestination template marker.\n")
        self.note = self.write(self.source, "app/Knowledge/Inbox/Example note.md", b"# Example\n\nSynthetic inbox.\n")
        self.data = self.write(self.live, "Data/Game/Example.md", b"# Example game\n\nSynthetic data.\n")
        self.view = self.write(self.live, "Views/My View.md", b"# Synthetic view\n")
        (self.live / "Data/Game/Empty").mkdir()
        self.obsidian = self.write(self.source, ".obsidian/plugins/example/data.json", b'{"enabled":true}\n')
        for relative in ("app.json", "appearance.json", "hotkeys.json", "workspace.json",
                         "themes/Example/theme.css", "plugins/example/manifest.json"):
            self.write(self.source, f".obsidian/{relative}", f"synthetic {relative}\n".encode())
        self.write(self.source, ".obsidian/snippets/custom.css", b"body { color: red; }\n")
        self.write(self.source, "app/Docs/framework.md", b"Excluded framework")
        self.write(self.source, "root-local.txt", b"Excluded root file")

    def make_instance(self, name: str, blueprint_name: str | None = None, spec: str = "foundation-6") -> Path:
        root = self.base / name
        self.write(root, transfer.SPEC_PATH, f"Specification version: `{spec}`\n".encode())
        if blueprint_name:
            shutil.copytree(BLUEPRINT, root / "app/Blueprints" / blueprint_name)
        return root

    def write(self, root: Path, relative: str, contents: bytes) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
        return path

    def read(self, root: Path, relative: str) -> bytes:
        return (root / relative).read_bytes()

    def tree(self, root: Path) -> dict[str, bytes | None]:
        if not root.exists():
            return {}
        return {path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
                for path in root.rglob("*")}

    def create(self):
        return backup(self.source, self.output, PASSWORD)

    def git(self, root: Path, *arguments: str) -> bytes:
        environment = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        result = subprocess.run(["git", "-C", str(root), *arguments], env=environment, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def init_git(self, root: Path) -> None:
        self.git(root, "init", "-q")
        self.git(root, "config", "user.name", "Synthetic Tester")
        self.git(root, "config", "user.email", "test@example.invalid")
        self.write(root, ".gitignore", b".obsidian/\n")
        self.git(root, "add", ".gitignore", "app/Docs", "app/Blueprints")
        self.git(root, "commit", "-qm", "Synthetic framework")

    def encrypted(self, manifest: dict, contents: bytes = b"", version: int = 2, *, raw: bytes | None = None) -> None:
        raw = json.dumps(manifest, separators=(",", ":")).encode() if raw is None else raw
        plaintext = struct.pack(">Q", len(raw)) + raw + contents
        salt, nonce = bytes(range(16)), bytes(range(12))
        header = transfer.HEADER.pack(transfer.MAGIC, version, salt, nonce)
        key = Scrypt(salt=salt, length=32, n=2**17, r=8, p=1).derive(PASSWORD)
        self.output.write_bytes(header + AESGCM(key).encrypt(nonce, plaintext, header))

    def manifest(self, entries=None, databases=None) -> dict:
        return json.loads(transfer.encode_manifest_v2(entries or [], "foundation-6", databases or []))

    def file_entry(self, root: str, name: str, content: bytes = b"test", database_id: str | None = None) -> dict:
        entry = {"root": root, "path": name, "kind": "file", "size": len(content),
                 "sha256": hashlib.sha256(content).hexdigest(), "mode": 0o600, "mtime_ns": 1_000_000_000}
        if database_id:
            entry["database_id"] = database_id
        return entry

    def test_v2_inventory_contains_only_approved_user_state(self):
        manifest = self.create()
        self.assertEqual(manifest["version"], 2)
        self.assertEqual(manifest["databases"], [{"database_id": "games"}])
        entries = {(item["root"], item.get("database_id"), item["path"]) for item in manifest["entries"]}
        self.assertIn(("inbox", None, "Example note.md"), entries)
        self.assertIn(("database", "games", "Data/Game/Example.md"), entries)
        self.assertIn(("database", "games", "Views/My View.md"), entries)
        self.assertIn(("obsidian", None, "plugins/example/data.json"), entries)
        serialized = json.dumps(manifest)
        for excluded in ("Database.md", "Agents/Vera.md", "Templates/Game.md", "framework.md", "root-local.txt"):
            self.assertNotIn(excluded, serialized)
        self.assertFalse(any(item["kind"] == "git" for item in manifest["entries"]))
        self.assertEqual(struct.unpack(">I", self.output.read_bytes()[8:12])[0], 2)

    def test_round_trip_reconstructs_destination_package_by_identity_and_folder(self):
        self.note.chmod(0o700)
        os.utime(self.note, ns=(1_700_000_000_123456789, 1_700_000_000_123456789))
        self.create()
        result = restore(self.target, self.output, PASSWORD)
        destination = self.target / "app/Knowledge/Databases/Game Library"
        self.assertEqual(result["databases_materialized"], 1)
        self.assertEqual((destination / "Data/Game/Example.md").read_bytes(), self.data.read_bytes())
        self.assertEqual((destination / "Views/My View.md").read_bytes(), self.view.read_bytes())
        self.assertEqual((self.target / ".obsidian/plugins/example/data.json").read_bytes(), self.obsidian.read_bytes())
        self.assertIn(b"Destination release marker", (destination / "Agents/Vera.md").read_bytes())
        self.assertIn(b"Destination contract marker", (destination / "Database.md").read_bytes())
        self.assertIn(b"Destination template marker", (destination / "Templates/Game.md").read_bytes())
        self.assertNotIn(b"Source-only managed edit", (destination / "Agents/Vera.md").read_bytes())
        self.assertNotIn(b"Source-only contract edit", (destination / "Database.md").read_bytes())
        self.assertNotIn(b"Source-only template edit", (destination / "Templates/Game.md").read_bytes())
        self.assertFalse((self.target / "app/Knowledge/Databases/Legacy Games").exists())
        restored_note = self.target / "app/Knowledge/Inbox/Example note.md"
        self.assertEqual(restored_note.stat().st_mtime_ns, self.note.stat().st_mtime_ns)
        if os.name == "posix":
            self.assertEqual(restored_note.stat().st_mode & 0o777, 0o700)

    def test_foundation_4_user_state_upgrades_into_foundation_6(self):
        self.write(self.source, transfer.SPEC_PATH, b"Specification version: `foundation-4`\n")
        manifest = self.create()
        self.assertEqual(manifest["specification"], "foundation-4")
        result = restore(self.target, self.output, PASSWORD)
        self.assertEqual(result["format_version"], 2)
        self.assertEqual(
            self.read(self.target, "app/Knowledge/Databases/Game Library/Data/Game/Example.md"),
            self.data.read_bytes(),
        )

    def test_v2_writer_rejects_unrecorded_source_specification(self):
        self.write(self.source, transfer.SPEC_PATH, b"Specification version: `foundation-3`\n")
        with self.assertRaisesRegex(BackupError, "supports foundation-4"):
            self.create()
        self.assertFalse(self.output.exists())

    def test_repeat_restore_and_exact_existing_package_are_idempotent(self):
        create_database(self.target, "games")
        self.write(self.target, "app/Knowledge/Inbox/Destination only.md", b"Keep me")
        self.create()
        first = restore(self.target, self.output, PASSWORD)
        before = self.tree(self.target)
        second = restore(self.target, self.output, PASSWORD)
        self.assertEqual(first["databases_materialized"], 0)
        self.assertEqual(second["files_added"], 0)
        self.assertGreater(second["files_unchanged"], 0)
        self.assertEqual(self.tree(self.target), before)

    def test_existing_managed_package_difference_fails_before_writes(self):
        create_database(self.target, "games")
        managed = self.target / "app/Knowledge/Databases/Game Library/Database.md"
        managed.write_bytes(managed.read_bytes() + b"\nLocal managed edit.\n")
        self.create()
        before = self.tree(self.target)
        with self.assertRaisesRegex(BackupError, "managed package"):
            restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.tree(self.target), before)

    def test_user_and_obsidian_conflicts_fail_complete_preflight(self):
        self.create()
        cases = {
            "app/Knowledge/Inbox/Example note.md": b"different inbox",
            "app/Knowledge/Databases/Game Library/Data/Game/Example.md": b"different data",
            "app/Knowledge/Databases/Game Library/Views/My View.md": b"different view",
            ".obsidian/plugins/example/data.json": b"different settings",
        }
        for number, (relative, content) in enumerate(cases.items()):
            with self.subTest(relative=relative):
                target = self.make_instance(f"conflict-{number}", "Game Library")
                if relative.startswith("app/Knowledge/Databases/"):
                    create_database(target, "games")
                self.write(target, relative, content)
                before = self.tree(target)
                with self.assertRaisesRegex(BackupError, "will not be replaced"):
                    restore(target, self.output, PASSWORD)
                self.assertEqual(self.tree(target), before)

    def test_destination_only_user_state_is_preserved(self):
        self.write(self.target, ".obsidian/destination-only.json", b"keep")
        self.write(self.target, "app/Knowledge/Inbox/Destination.md", b"keep")
        self.create()
        restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.read(self.target, ".obsidian/destination-only.json"), b"keep")
        self.assertEqual(self.read(self.target, "app/Knowledge/Inbox/Destination.md"), b"keep")

    def test_dry_run_authenticates_and_fully_preflights_without_writes(self):
        self.create()
        before = self.tree(self.target)
        result = restore(self.target, self.output, PASSWORD, dry_run=True)
        self.assertGreater(result["files_added"], 0)
        self.assertEqual(result["databases_materialized"], 1)
        self.assertEqual(self.tree(self.target), before)

    def test_unreconstructable_database_fails_backup(self):
        shutil.move(self.source / "app/Blueprints/Old Package", self.source / "app/Blueprints/Unavailable")
        (self.source / "app/Blueprints/Unavailable/Database.md").unlink()
        with self.assertRaisesRegex(BackupError, "cannot be reconstructed"):
            self.create()
        self.assertFalse(self.output.exists())

    def test_missing_destination_package_fails_restore_without_writes(self):
        self.create()
        shutil.rmtree(self.target / "app/Blueprints/Game Library")
        before = self.tree(self.target)
        with self.assertRaisesRegex(BackupError, "cannot be reconstructed"):
            restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.tree(self.target), before)

    def test_force_tracked_obsidian_blocks_backup(self):
        self.init_git(self.source)
        self.git(self.source, "add", "-f", ".obsidian/plugins/example/data.json")
        self.git(self.source, "commit", "-qm", "Force tracked editor state")
        with self.assertRaisesRegex(BackupError, "Untrack"):
            self.create()

    def test_tracked_user_data_is_still_embedded(self):
        self.init_git(self.source)
        relative = self.note.relative_to(self.source).as_posix()
        self.git(self.source, "add", "-f", relative)
        self.git(self.source, "commit", "-qm", "Tracked synthetic user state")
        self.note.write_bytes(b"Tracked but locally modified user state\n")
        manifest = self.create()
        entry = next(item for item in manifest["entries"] if item.get("path") == "Example note.md")
        self.assertEqual(entry["kind"], "file")
        self.assertEqual(entry["sha256"], hashlib.sha256(self.note.read_bytes()).hexdigest())

    def test_obsidian_and_user_state_symlinks_are_refused(self):
        for parent in (self.source / ".obsidian", self.live / "Data"):
            link = parent / "unsafe-link"
            link.symlink_to(self.base / "missing")
            with self.subTest(parent=parent), self.assertRaisesRegex(BackupError, "Symlinks"):
                self.create()
            link.unlink()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation unavailable")
    def test_special_files_are_refused(self):
        os.mkfifo(self.source / ".obsidian/pipe")
        with self.assertRaisesRegex(BackupError, "special file"):
            self.create()

    def test_empty_user_state_and_no_databases_round_trip(self):
        empty_source = self.make_instance("empty-source")
        empty_target = self.make_instance("empty-target")
        backup(empty_source, self.output, PASSWORD)
        manifest = restore(empty_target, self.output, PASSWORD)
        self.assertEqual(manifest["files_added"], 0)
        self.assertFalse((empty_target / "app/Knowledge").exists())

    def test_empty_inbox_and_obsidian_directories_are_preserved(self):
        empty_source = self.make_instance("empty-roots-source")
        empty_target = self.make_instance("empty-roots-target")
        (empty_source / "app/Knowledge/Inbox").mkdir(parents=True)
        (empty_source / ".obsidian").mkdir()
        backup(empty_source, self.output, PASSWORD)
        restore(empty_target, self.output, PASSWORD)
        self.assertTrue((empty_target / "app/Knowledge/Inbox").is_dir())
        self.assertTrue((empty_target / ".obsidian").is_dir())

    def test_fixed_independent_v1_compatibility_vector(self):
        vector = json.loads((FIXTURES / "backup-v1.json").read_text())
        self.output.write_bytes(base64.b64decode(vector["envelope_base64"], validate=True))
        legacy = self.make_instance("legacy-target", spec="foundation-3")
        result = restore(legacy, self.output, vector["passphrase"].encode())
        self.assertEqual(result["format_version"], 1)
        self.assertEqual(self.read(legacy, "app/Knowledge/Inbox/Example.txt"), b"test")

    def test_v1_is_not_reinterpreted_across_foundation_5_boundary(self):
        vector = json.loads((FIXTURES / "backup-v1.json").read_text())
        self.output.write_bytes(base64.b64decode(vector["envelope_base64"], validate=True))
        before = self.tree(self.target)
        with self.assertRaisesRegex(BackupError, "cannot cross the foundation-5"):
            restore(self.target, self.output, vector["passphrase"].encode())
        self.assertEqual(self.tree(self.target), before)

    def test_fixed_independent_v2_compatibility_vector(self):
        vector = json.loads((FIXTURES / "backup-v2.json").read_text())
        self.output.write_bytes(base64.b64decode(vector["envelope_base64"], validate=True))
        result = restore(self.target, self.output, vector["passphrase"].encode())
        database = self.target / "app/Knowledge/Databases/Game Library"
        self.assertEqual(result["format_version"], 2)
        self.assertEqual(self.read(self.target, "app/Knowledge/Inbox/Vector.txt"), b"inbox")
        self.assertEqual((database / "Data/Game/Vector.md").read_bytes(), b"data")
        self.assertEqual((database / "Views/Vector.md").read_bytes(), b"view")
        self.assertEqual(self.read(self.target, ".obsidian/app.json"), b"obsidian")

    def test_unknown_format_version_fails_before_kdf(self):
        self.output.write_bytes(transfer.HEADER.pack(transfer.MAGIC, 99, b"s" * 16, b"n" * 12) + b"x" * 16)
        with patch("backup_restore.cipher", side_effect=AssertionError("Must not derive key")):
            with self.assertRaisesRegex(BackupError, "versions are 1 and 2"):
                restore(self.target, self.output, PASSWORD)

    def test_wrong_password_tampering_truncation_and_append_never_write(self):
        self.create()
        original = self.output.read_bytes()
        before = self.tree(self.target)
        with self.assertRaisesRegex(BackupError, "authentication failed"):
            restore(self.target, self.output, b"wrong")
        for data in (original[:10], original[:-8], original + b"trailing"):
            self.output.write_bytes(data)
            with self.assertRaises(BackupError):
                restore(self.target, self.output, PASSWORD)
        data = bytearray(original)
        data[transfer.HEADER.size + 3] ^= 1
        self.output.write_bytes(data)
        with self.assertRaisesRegex(BackupError, "authentication failed"):
            restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.tree(self.target), before)

    def test_unsafe_authenticated_v2_paths_fail_without_writes(self):
        directory = {"root": "inbox", "path": "", "kind": "directory"}
        for name in ("../outside", "/absolute", "C:\\attack", ".git/config", "NUL", "trailing."):
            with self.subTest(name=name):
                self.encrypted(self.manifest([directory, self.file_entry("inbox", name)]), b"test")
                with self.assertRaises(BackupError):
                    restore(self.target, self.output, PASSWORD)
                self.assertFalse((self.target / "app/Knowledge").exists())

    def test_duplicate_missing_parent_and_payload_mismatch_are_rejected(self):
        directory = {"root": "inbox", "path": "", "kind": "directory"}
        cases = [
            (self.manifest([directory, self.file_entry("inbox", "Example"), self.file_entry("inbox", "example")]), b"testtest"),
            (self.manifest([self.file_entry("inbox", "missing/file")]), b"test"),
            (self.manifest(), b"extra"),
        ]
        for manifest, payload in cases:
            self.encrypted(manifest, payload)
            with self.assertRaises(BackupError):
                restore(self.target, self.output, PASSWORD)

    def test_backup_detects_source_mutation_and_cleans_partial_output(self):
        original = transfer.inventory_v2
        calls = []

        def changing(root):
            calls.append(root)
            if len(calls) == 2:
                self.write(self.source, "app/Knowledge/Inbox/Arrived.md", b"late")
            return original(root)

        with patch("backup_restore.inventory_v2", side_effect=changing):
            with self.assertRaisesRegex(BackupError, "changed during backup"):
                self.create()
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.base.glob(".shardbase-backup-*")), [])

    def test_restore_io_failure_rolls_back_package_and_user_state(self):
        self.create()
        before = self.tree(self.target)
        original = os.link
        calls = []

        def failing(source, destination):
            calls.append(destination)
            if len(calls) == 3:
                raise OSError("Synthetic disk failure")
            return original(source, destination)

        with patch("backup_restore.os.link", side_effect=failing):
            with self.assertRaisesRegex(OSError, "Synthetic disk"):
                restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.tree(self.target), before)
        self.assertGreater(restore(self.target, self.output, PASSWORD)["files_added"], 0)

    def test_limits_and_existing_output_fail_without_publication(self):
        for setting, value in (("MAX_ENTRIES", 1), ("MAX_MANIFEST", 20), ("MAX_PAYLOAD", 20)):
            with self.subTest(setting=setting), patch.object(transfer, setting, value):
                with self.assertRaises(BackupError):
                    self.create()
                self.assertFalse(self.output.exists())
        self.output.write_bytes(b"preserve")
        with self.assertRaisesRegex(BackupError, "already exists"):
            self.create()
        self.assertEqual(self.output.read_bytes(), b"preserve")

    def test_cli_reports_user_state_package_and_dry_run_semantics(self):
        password = self.write(self.base, "password", PASSWORD)
        password.chmod(0o600)

        def cli(*args):
            return subprocess.run([sys.executable, "-B", str(SCRIPTS / "shardbase.py"), *map(str, args)],
                                  input="", capture_output=True, text=True)

        result = cli("backup", self.output, "--root", self.source, "--password-file", password)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("user files", result.stdout)
        before = self.tree(self.target)
        result = cli("restore", self.output, "--root", self.target, "--password-file", password, "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No user state or package files were written", result.stdout)
        self.assertEqual(self.tree(self.target), before)

    def test_prompted_cli_backup_and_restore(self):
        from shardbase import main

        with patch("pathlib.Path.home", return_value=self.base), redirect_stdout(io.StringIO()):
            with patch("builtins.input", return_value=""), patch("backup_restore.getpass.getpass", return_value=PASSWORD.decode()):
                self.assertEqual(main(["backup", "--root", str(self.source)]), 0)
            archive = next((self.base / "Shardbase Backups").glob("*.sbbackup"))
            with patch("builtins.input", return_value=str(archive)), patch("backup_restore.getpass.getpass", return_value=PASSWORD.decode()):
                self.assertEqual(main(["restore", "--root", str(self.target)]), 0)
        self.assertEqual(self.read(self.target, ".obsidian/plugins/example/data.json"), self.obsidian.read_bytes())


if __name__ == "__main__":
    unittest.main()
