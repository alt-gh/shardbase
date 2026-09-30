"""Synthetic, external-only encryption, preservation, and adversarial transfer proofs."""

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

from _support import FIXTURES, SCRIPTS
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

# isort: split
# The test path bootstrap must run before importing runtime modules.
import backup_restore as transfer
from backup_restore import BackupError, backup, restore

PASSWORD = b"synthetic test passphrase"


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.source = self.make_instance("source")
        self.target = self.make_instance("target")
        self.output = self.base / "snapshot.sbbackup"
        self.note = self.write(self.source, "app/Knowledge/Inbox/Example note.md", b"# Example\n\nPrivate synthetic content.\n")
        self.write(self.source, "app/Knowledge/Databases/Example/Data/Items/Attachments/example.bin", bytes(range(256)) * 9000)
        (self.source / "app/Knowledge/Databases/Example/Views").mkdir()
        (self.source / "app/Knowledge/Databases/Example/Data/Items/Empty").mkdir()
        self.write(self.source, ".obsidian/workspace.json", b"Excluded editor state")
        self.write(self.source, "app/Docs/framework.md", b"Excluded framework")

    def make_instance(self, name):
        root = self.base / name
        self.write(root, transfer.SPEC_PATH, b"Specification version: `foundation-3`\n")
        return root

    def write(self, root, relative, contents):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
        return path

    def tree(self, root):
        return {path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
                for path in root.rglob("*")}

    def create(self):
        return backup(self.source, self.output, PASSWORD)

    def git(self, root, *arguments):
        environment = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        result = subprocess.run(["git", "-C", str(root), *arguments], env=environment, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def init_git(self, root):
        self.git(root, "init", "-q")
        self.git(root, "config", "user.name", "Synthetic Tester")
        self.git(root, "config", "user.email", "test@example.invalid")
        self.git(root, "add", "app/Docs")
        self.git(root, "commit", "-qm", "Synthetic framework")

    def encrypted(self, manifest, contents=b"", *, raw=None):
        raw = json.dumps(manifest, separators=(",", ":")).encode() if raw is None else raw
        plaintext = struct.pack(">Q", len(raw)) + raw + contents
        salt, nonce = bytes(range(16)), bytes(range(12))
        header = transfer.HEADER.pack(transfer.MAGIC, 1, salt, nonce)
        key = Scrypt(salt=salt, length=32, n=2**17, r=8, p=1).derive(PASSWORD)
        self.output.write_bytes(header + AESGCM(key).encrypt(nonce, plaintext, header))

    def manifest(self, entries=None):
        return json.loads(transfer.encode_manifest(entries or [], "foundation-3"))

    def file_entry(self, name, content=b"test"):
        return {"path": name, "kind": "file", "size": len(content), "sha256": hashlib.sha256(content).hexdigest(),
                "mode": 0o600, "mtime_ns": 1_000_000_000}

    def test_round_trip_preserves_every_byte_empty_directory_and_metadata(self):
        self.note.chmod(0o700)
        os.utime(self.note, ns=(1_700_000_000_123456789, 1_700_000_000_123456789))
        before = self.tree(self.source)
        self.create()
        result = restore(self.target, self.output, PASSWORD)
        self.assertEqual(result["files_added"], 2)
        self.assertEqual(self.tree(self.source), before)
        self.assertEqual(self.tree(self.source / transfer.BOUNDARY), self.tree(self.target / transfer.BOUNDARY))
        note = self.target / self.note.relative_to(self.source)
        self.assertEqual(note.stat().st_mtime_ns, self.note.stat().st_mtime_ns)
        if os.name == "posix":
            self.assertEqual(note.stat().st_mode & 0o777, 0o700)
        self.assertFalse((self.target / ".obsidian").exists())
        self.assertFalse((self.target / "app/Docs/framework.md").exists())
        if os.name == "posix":
            self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)

    def test_fixed_independent_v1_compatibility_vector(self):
        vector = json.loads((FIXTURES / "backup-v1.json").read_text())
        self.output.write_bytes(base64.b64decode(vector["envelope_base64"], validate=True))
        result = restore(self.target, self.output, vector["passphrase"].encode())
        self.assertEqual(result["files_added"], 1)
        self.assertEqual((self.target / "app/Knowledge/Inbox/Example.txt").read_bytes(), b"test")

    def test_valid_database_lineage_and_links_survive_transfer(self):
        from validate_shardbase import validate_database
        source = self.make_instance("valid")
        relative = Path("app/Knowledge/Databases/Example Database")
        shutil.copytree(FIXTURES / "valid-database", source / relative)
        self.assertEqual(validate_database(source / relative), [])
        backup(source, self.output, PASSWORD)
        restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.tree(source / relative), self.tree(self.target / relative))
        self.assertEqual(validate_database(self.target / relative), [])

    def test_default_backup_location_and_prompted_restore_need_no_extra_steps(self):
        from shardbase import main
        with patch("pathlib.Path.home", return_value=self.base), redirect_stdout(io.StringIO()):
            with patch("builtins.input", return_value=""), patch("backup_restore.getpass.getpass", return_value=PASSWORD.decode()):
                self.assertEqual(main(["backup", "--root", str(self.source)]), 0)
            archives = list((self.base / "Shardbase Backups").glob("*.sbbackup"))
            self.assertEqual(len(archives), 1)
            with patch("builtins.input", return_value=str(archives[0])), patch("backup_restore.getpass.getpass", return_value=PASSWORD.decode()):
                self.assertEqual(main(["restore", "--root", str(self.target)]), 0)
        self.assertEqual(self.tree(self.source / transfer.BOUNDARY), self.tree(self.target / transfer.BOUNDARY))

    def test_prompted_backup_can_choose_a_custom_file_or_folder(self):
        from shardbase import main
        folder = self.base / "Chosen backup folder"
        folder.mkdir()
        for selection in (folder / "Chosen filename.sbbackup", folder):
            with self.subTest(selection=selection), patch("builtins.input", return_value=str(selection)), \
                    patch("backup_restore.getpass.getpass", return_value=PASSWORD.decode()), redirect_stdout(io.StringIO()):
                self.assertEqual(main(["backup", "--root", str(self.source)]), 0)
        self.assertTrue((folder / "Chosen filename.sbbackup").is_file())
        self.assertEqual(len(list(folder.glob("*.sbbackup"))), 2)

    def test_explicit_backup_folder_generates_a_filename_without_a_path_prompt(self):
        from shardbase import main
        folder = self.base / "Explicit backup folder"
        folder.mkdir()
        with patch("builtins.input", side_effect=AssertionError("Unexpected prompt")), \
                patch("backup_restore.getpass.getpass", return_value=PASSWORD.decode()), redirect_stdout(io.StringIO()):
            self.assertEqual(main(["backup", str(folder), "--root", str(self.source)]), 0)
        self.assertEqual(len(list(folder.glob("*.sbbackup"))), 1)

    def test_backup_path_prompt_cancellation_does_not_create_output(self):
        from shardbase import main
        with patch("pathlib.Path.home", return_value=self.base), patch("builtins.input", side_effect=EOFError), \
                patch("backup_restore.getpass.getpass", side_effect=AssertionError("Unexpected password prompt")), \
                redirect_stdout(io.StringIO()):
            self.assertEqual(main(["backup", "--root", str(self.source)]), 130)
        self.assertFalse((self.base / "Shardbase Backups").exists())

    def test_repeat_restore_is_idempotent_and_preserves_unrelated_data(self):
        self.write(self.target, "app/Knowledge/Inbox/Unrelated.md", b"Keep me")
        self.create()
        restore(self.target, self.output, PASSWORD)
        before = self.tree(self.target)
        result = restore(self.target, self.output, PASSWORD)
        self.assertEqual(result["files_added"], 0)
        self.assertEqual(result["files_unchanged"], 2)
        self.assertEqual(self.tree(self.target), before)

    def test_conflicts_fail_before_any_write(self):
        self.create()
        for relative in ("app/Knowledge/Inbox/Example note.md", "app/Knowledge/Databases/Example/Data"):
            with self.subTest(relative=relative):
                target = self.make_instance(str(len(relative)))
                self.write(target, relative, b"Existing different content")
                before = self.tree(target)
                with self.assertRaises(BackupError):
                    restore(target, self.output, PASSWORD)
                self.assertEqual(self.tree(target), before)

    def test_dry_run_authenticates_and_checks_without_creating_knowledge(self):
        self.create()
        before = self.tree(self.target)
        result = restore(self.target, self.output, PASSWORD, dry_run=True)
        self.assertEqual(result["files_added"], 2)
        self.assertEqual(self.tree(self.target), before)

    def test_wrong_password_and_tampering_never_write_target(self):
        self.create()
        original = self.output.read_bytes()
        before = self.tree(self.target)
        with self.assertRaisesRegex(BackupError, "authentication failed"):
            restore(self.target, self.output, b"wrong password")
        for index in (12, transfer.HEADER.size, len(original) - 1):
            data = bytearray(original)
            data[index] ^= 1
            self.output.write_bytes(data)
            with self.assertRaisesRegex(BackupError, "authentication failed"):
                restore(self.target, self.output, PASSWORD)
        for data in (original[:10], original[:-8], original + b"trailing"):
            self.output.write_bytes(data)
            with self.assertRaises(BackupError):
                restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.tree(self.target), before)

    def test_unknown_format_version_fails_before_kdf(self):
        self.output.write_bytes(transfer.HEADER.pack(transfer.MAGIC, 99, b"s" * 16, b"n" * 12) + b"x" * 16)
        with patch("backup_restore.cipher", side_effect=AssertionError("Must not derive a key")):
            with self.assertRaisesRegex(BackupError, "version 1"):
                restore(self.target, self.output, PASSWORD)

    def test_ciphertext_hides_metadata_and_uses_fresh_randomness(self):
        self.create()
        second = self.base / "second.sbbackup"
        backup(self.source, second, PASSWORD)
        self.assertNotEqual(self.output.read_bytes(), second.read_bytes())
        for secret in (b"Example note", b"Private synthetic", b"foundation-3", b"app/Knowledge"):
            self.assertNotIn(secret, self.output.read_bytes())
        data = self.output.read_bytes()
        _, _, salt, nonce = transfer.HEADER.unpack(data[:transfer.HEADER.size])
        key = Scrypt(salt=salt, length=32, n=2**17, r=8, p=1).derive(PASSWORD)
        plain = AESGCM(key).decrypt(nonce, data[transfer.HEADER.size:], data[:transfer.HEADER.size])
        length = struct.unpack(">Q", plain[:8])[0]
        self.assertEqual(json.loads(plain[8:8 + length])["scope"], "app/Knowledge")

    def test_existing_backup_is_never_overwritten(self):
        self.output.write_bytes(b"Preserve existing output")
        with self.assertRaisesRegex(BackupError, "already exists"):
            self.create()
        self.assertEqual(self.output.read_bytes(), b"Preserve existing output")

    def test_concurrent_backup_publication_preserves_competing_output(self):
        original = os.link
        def compete(source, destination):
            Path(destination).write_bytes(b"Other backup")
            return original(source, destination)
        with patch("backup_restore.os.link", side_effect=compete):
            with self.assertRaises(FileExistsError):
                self.create()
        self.assertEqual(self.output.read_bytes(), b"Other backup")
        self.assertEqual(list(self.base.glob(".shardbase-backup-*")), [])

    def test_backup_output_and_staging_must_be_external(self):
        for output in (self.source / "backup.sbbackup", self.target / "backup.sbbackup"):
            with self.assertRaisesRegex(BackupError, "outside"):
                backup(self.source, output, PASSWORD)
        with self.assertRaisesRegex(BackupError, "outside"):
            backup(self.source, self.output, PASSWORD, self.source)
        self.assertFalse(self.output.exists())

    def test_generated_caches_are_excluded(self):
        self.write(self.source, "app/Knowledge/Inbox/.DS_Store", b"ignored")
        self.write(self.source, "app/Knowledge/Inbox/__pycache__/code.pyc", b"ignored")
        manifest = self.create()
        self.assertFalse(any("ignored" in entry["path"] or "__pycache__" in entry["path"] or ".DS_Store" in entry["path"] for entry in manifest["entries"]))

    def test_git_files_are_excluded_and_required_in_destination(self):
        self.init_git(self.source)
        self.git(self.source, "add", str(self.note.relative_to(self.source)))
        self.git(self.source, "commit", "-qm", "Synthetic tracked knowledge")
        manifest = self.create()
        self.assertEqual([item["path"] for item in manifest["entries"] if item["kind"] == "git"], [self.note.relative_to(self.source).as_posix()])
        before = self.tree(self.target)
        with self.assertRaisesRegex(BackupError, "Git-backed"):
            restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.tree(self.target), before)
        self.write(self.target, self.note.relative_to(self.source), self.note.read_bytes())
        result = restore(self.target, self.output, PASSWORD)
        self.assertEqual(result["files_added"], 1)
        self.assertEqual(result["git_files"], 1)

    def test_local_edits_to_tracked_files_fail_even_when_index_ignores_them(self):
        self.init_git(self.source)
        relative = str(self.note.relative_to(self.source))
        self.git(self.source, "add", relative)
        self.git(self.source, "commit", "-qm", "Synthetic tracked knowledge")
        self.git(self.source, "update-index", "--assume-unchanged", relative)
        self.note.write_bytes(b"Local changes that must not be lost")
        with self.assertRaisesRegex(BackupError, "local changes"):
            self.create()
        self.assertFalse(self.output.exists())

    def test_staged_new_knowledge_is_not_silently_excluded(self):
        self.init_git(self.source)
        self.git(self.source, "add", str(self.note.relative_to(self.source)))
        with self.assertRaisesRegex(BackupError, "local changes"):
            self.create()

    def test_staged_deletion_of_all_tracked_knowledge_blocks_transfer(self):
        self.init_git(self.source)
        relative = str(self.note.relative_to(self.source))
        self.git(self.source, "add", relative)
        self.git(self.source, "commit", "-qm", "Synthetic tracked knowledge")
        self.git(self.source, "rm", relative)
        with self.assertRaisesRegex(BackupError, "local changes"):
            self.create()

    def test_empty_unborn_git_index_still_backs_up_local_knowledge(self):
        self.git(self.source, "init", "-q")
        self.assertEqual(sum(item["kind"] == "file" for item in self.create()["entries"]), 2)

    def test_limits_fail_without_publishing_output(self):
        for setting, value in (("MAX_ENTRIES", 1), ("MAX_MANIFEST", 20), ("MAX_PAYLOAD", 20)):
            with self.subTest(setting=setting), patch.object(transfer, setting, value):
                with self.assertRaises(BackupError):
                    self.create()
                self.assertFalse(self.output.exists())

    def test_missing_parent_and_unlisted_payload_bytes_are_rejected(self):
        self.encrypted(self.manifest(), b"extra")
        with self.assertRaisesRegex(BackupError, "payload size"):
            restore(self.target, self.output, PASSWORD)
        self.encrypted(self.manifest([self.file_entry("app/Knowledge/Inbox/Example.txt")]), b"test")
        with self.assertRaisesRegex(BackupError, "directory parent"):
            restore(self.target, self.output, PASSWORD)

    def test_restore_from_staging_directory_alias(self):
        staging = self.base / "staging"
        staging.mkdir()
        alias = self.base / "staging-alias"
        alias.symlink_to(staging, target_is_directory=True)
        self.create()
        result = restore(self.target, self.output, PASSWORD, alias)
        self.assertEqual(result["files_added"], 2)

    def test_broken_git_metadata_fails_closed(self):
        (self.source / ".git").mkdir()
        with self.assertRaisesRegex(BackupError, "Git tracking"):
            self.create()

    def test_specification_transition_requires_explicit_migration_support(self):
        self.create()
        self.write(self.target, transfer.SPEC_PATH, b"Specification version: `foundation-5`\n")
        before = self.tree(self.target)
        with self.assertRaisesRegex(BackupError, "specification transition"):
            restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.tree(self.target), before)

    def test_foundation_3_to_4_transfer_preserves_knowledge(self):
        self.create()
        self.write(self.target, transfer.SPEC_PATH, b"Specification version: `foundation-4`\n")
        restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.tree(self.source / transfer.BOUNDARY), self.tree(self.target / transfer.BOUNDARY))

    def test_foundation_4_round_trip_and_downgrade_refusal(self):
        self.write(self.source, transfer.SPEC_PATH, b"Specification version: `foundation-4`\n")
        self.create()
        before = self.tree(self.target)
        with self.assertRaisesRegex(BackupError, "specification transition"):
            restore(self.target, self.output, PASSWORD)
        self.assertEqual(before, self.tree(self.target))
        self.write(self.target, transfer.SPEC_PATH, b"Specification version: `foundation-4`\n")
        restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.tree(self.source / transfer.BOUNDARY), self.tree(self.target / transfer.BOUNDARY))

    def test_backup_refuses_a_specification_its_reader_cannot_restore(self):
        self.write(self.source, transfer.SPEC_PATH, b"Specification version: `foundation-2`\n")
        with self.assertRaisesRegex(BackupError, "supports foundation-3"):
            self.create()
        self.assertFalse(self.output.exists())

    def test_unsafe_authenticated_paths_fail_without_writes(self):
        root_entry = {"path": transfer.BOUNDARY, "kind": "directory"}
        for name in ("../outside", "/absolute", "app/Knowledge/../Docs/attack", "app/Scripts/attack.py",
                     "app/Knowledge/C:\\attack", "app/Knowledge/.git/config", "app/Knowledge/NUL", "app/Knowledge/trailing."):
            with self.subTest(name=name):
                self.encrypted(self.manifest([root_entry, self.file_entry(name)]), b"test")
                with self.assertRaises(BackupError):
                    restore(self.target, self.output, PASSWORD)
                self.assertFalse((self.target / transfer.BOUNDARY).exists())

    def test_duplicate_and_case_colliding_archive_names_fail(self):
        for names in (("Example", "Example"), ("Example", "example"), ("Caf\u00e9", "Cafe\u0301")):
            entries = [{"path": transfer.BOUNDARY, "kind": "directory"}]
            entries += [self.file_entry(f"{transfer.BOUNDARY}/{name}") for name in names]
            self.encrypted(self.manifest(entries), b"testtest")
            with self.assertRaisesRegex(BackupError, "equivalent"):
                restore(self.target, self.output, PASSWORD)

    def test_malformed_authenticated_payloads_fail_cleanly(self):
        root_entry = {"path": transfer.BOUNDARY, "kind": "directory"}
        cases = [self.manifest([root_entry, self.file_entry(f"{transfer.BOUNDARY}/file")]),
                 self.manifest([self.file_entry(f"{transfer.BOUNDARY}/missing/file")]),
                 self.manifest([{"kind": [], "path": transfer.BOUNDARY}])]
        for value in cases:
            self.encrypted(value, b"bad!")
            with self.assertRaises(BackupError):
                restore(self.target, self.output, PASSWORD)
        self.encrypted({}, raw=b'{"version":1,"version":1}')
        with self.assertRaisesRegex(BackupError, "Duplicate JSON"):
            restore(self.target, self.output, PASSWORD)
        self.assertFalse((self.target / transfer.BOUNDARY).exists())

    def test_symlinks_are_refused(self):
        link = self.source / "app/Knowledge/Inbox/link"
        link.symlink_to(self.base / "missing")
        with self.assertRaisesRegex(BackupError, "Symlinks"):
            self.create()
        link.unlink()
        self.create()
        (self.target / "app/Knowledge").symlink_to(self.source / "app/Knowledge", target_is_directory=True)
        with self.assertRaisesRegex(BackupError, "Symlinks"):
            restore(self.target, self.output, PASSWORD)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation is unavailable on this platform")
    def test_special_files_are_refused(self):
        os.mkfifo(self.source / "app/Knowledge/Inbox/pipe")
        with self.assertRaisesRegex(BackupError, "special file"):
            self.create()

    def test_nested_git_repository_is_refused(self):
        (self.source / "app/Knowledge/Inbox/.git").mkdir()
        with self.assertRaisesRegex(BackupError, "Nested Git"):
            self.create()

    def test_case_collision_with_existing_target_is_refused(self):
        self.create()
        self.write(self.target, "app/Knowledge/Inbox/example note.md", b"other data")
        before = self.tree(self.target)
        with self.assertRaises(BackupError):
            restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.tree(self.target), before)

    def test_restore_io_failure_rolls_back_only_new_files_and_directories(self):
        self.create()
        self.write(self.target, "app/Knowledge/Inbox/Unrelated.md", b"Keep me")
        before = self.tree(self.target)
        original = os.link
        calls = []
        def failing(source, destination):
            calls.append(destination)
            if len(calls) == 2:
                raise OSError("Synthetic disk failure")
            return original(source, destination)
        with patch("backup_restore.os.link", side_effect=failing):
            with self.assertRaisesRegex(OSError, "Synthetic disk"):
                restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.tree(self.target), before)
        self.assertEqual(restore(self.target, self.output, PASSWORD)["files_added"], 2)

    def test_restore_interrupt_rolls_back_new_state(self):
        self.create()
        before = self.tree(self.target)
        with patch("backup_restore.sync_directory", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                restore(self.target, self.output, PASSWORD)
        self.assertEqual(self.tree(self.target), before)

    def test_backup_verification_failure_does_not_publish(self):
        with patch("backup_restore.unpack", side_effect=BackupError("Synthetic verify failure")):
            with self.assertRaisesRegex(BackupError, "verify failure"):
                self.create()
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.base.glob(".shardbase-backup-*")), [])

    def test_backup_detects_source_changes_and_cleans_partial_output(self):
        original = transfer.inventory
        calls = []
        def changing(root, tracked):
            calls.append(root)
            if len(calls) == 2:
                self.write(self.source, "app/Knowledge/Inbox/Arrived.md", b"Late write")
            return original(root, tracked)
        with patch("backup_restore.inventory", side_effect=changing):
            with self.assertRaisesRegex(BackupError, "changed during backup"):
                self.create()
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.base.glob(".shardbase-backup-*")), [])

    def test_empty_knowledge_is_a_valid_round_trip(self):
        empty = self.make_instance("empty")
        backup(empty, self.output, PASSWORD)
        result = restore(self.target, self.output, PASSWORD)
        self.assertEqual(result["files_added"], 0)

    def test_password_input_is_confirmed(self):
        path = self.write(self.base, "passphrase", PASSWORD + b"\r\n")
        path.chmod(0o600)
        self.assertEqual(transfer.read_password(path, confirm=True), PASSWORD)
        with patch("backup_restore.getpass.getpass", side_effect=["long enough passphrase", "different passphrase"]):
            with self.assertRaisesRegex(BackupError, "do not match"):
                transfer.read_password(None, confirm=True)

    @unittest.skipUnless(os.name == "posix", "Owner-only mode bits require POSIX permissions")
    def test_password_file_must_be_owner_only(self):
        path = self.write(self.base, "passphrase", PASSWORD)
        path.chmod(0o644)
        with self.assertRaisesRegex(BackupError, "owner"):
            transfer.read_password(path, confirm=True)

    def test_two_command_subprocess_workflow_and_clean_errors(self):
        password = self.write(self.base, "password", PASSWORD)
        password.chmod(0o600)
        def cli(*args):
            return subprocess.run([sys.executable, "-B", str(SCRIPTS / "shardbase.py"), *map(str, args)],
                                  input="", capture_output=True, text=True)
        result = cli("backup", self.output, "--root", self.source, "--password-file", password)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Backup verified", result.stdout)
        before = self.tree(self.target)
        result = cli("restore", self.output, "--root", self.target, "--password-file", password, "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No knowledge was written", result.stdout)
        self.assertEqual(self.tree(self.target), before)
        result = cli("restore", self.output, "--root", self.target, "--password-file", password)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Restore complete", result.stdout)
        self.assertEqual(self.tree(self.source / transfer.BOUNDARY), self.tree(self.target / transfer.BOUNDARY))
        password.write_bytes(b"wrong")
        result = cli("restore", self.output, "--root", self.target, "--password-file", password)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        self.assertNotIn(PASSWORD.decode(), result.stdout + result.stderr)
        self.assertEqual(list(self.source.rglob("__pycache__")), [])


if __name__ == "__main__":
    unittest.main()
