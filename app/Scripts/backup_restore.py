"""Offline, preservation-oriented user-state transfer. See BACKUP_FORMAT.md."""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import re
import stat
import struct
import subprocess
import tempfile
import unicodedata
import warnings
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

MAGIC = b"SHARDBK\x00"
VERSION = 2
LEGACY_VERSION = 1
HEADER = struct.Struct(">8sI16s12s")
CHUNK = 1024 * 1024
MAX_PAYLOAD = 32 * 1024**3
MAX_MANIFEST = 16 * 1024**2
MAX_ENTRIES = 100_000
BOUNDARY = "app/Knowledge"  # Legacy v1 boundary.
SPEC_PATH = "app/Docs/Shard System Specification.md"
OMIT_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "node_modules"}
OMIT_FILES = {".DS_Store", "Thumbs.db", "Desktop.ini"}


class BackupError(ValueError):
    """An actionable, non-secret diagnostic suitable for the CLI."""


def crypto():
    try:
        from cryptography.exceptions import InvalidTag
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    except ImportError as error:
        raise BackupError("Backup/restore requires cryptography. Rerun the CLI installer to install requirements.txt.") from error
    return Cipher, algorithms, modes, Scrypt, InvalidTag


def cipher(password: bytes, salt: bytes, nonce: bytes, tag: bytes | None = None):
    Cipher, algorithms, modes, Scrypt, _ = crypto()
    key = Scrypt(salt=salt, length=32, n=2**17, r=8, p=1).derive(password)
    return Cipher(algorithms.AES(key), modes.GCM(nonce, tag))


def read_password(path: Path | None, *, confirm: bool) -> bytes:
    if path is not None:
        path = path.expanduser().absolute()
        path = path.parent.resolve(strict=True) / path.name
        safe_path(path)
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > 4098:
            raise BackupError("The password file must be an ordinary file of at most 4098 bytes.")
        if os.name == "posix" and info.st_mode & 0o077:
            raise BackupError("The password file must be accessible only to its owner (chmod 600).")
        password = path.read_bytes()
        if password.endswith(b"\r\n"):
            password = password[:-2]
        elif password.endswith(b"\n"):
            password = password[:-1]
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            try:
                password = getpass.getpass("Passphrase: ").encode("utf-8")
                if confirm and password != getpass.getpass("Confirm passphrase: ").encode("utf-8"):
                    raise BackupError("Passphrases do not match; no backup was created.")
            except getpass.GetPassWarning as error:
                raise BackupError("A secure terminal is required for the passphrase; alternatively use --password-file.") from error
    if not password or len(password) > 4096 or b"\n" in password or b"\r" in password:
        raise BackupError("Use a non-empty, single-line passphrase of at most 4096 UTF-8 bytes.")
    try:
        password.decode("utf-8")
    except UnicodeError as error:
        raise BackupError("The passphrase must be UTF-8.") from error
    if confirm and len(password) < 12:
        raise BackupError("Use a strong passphrase of at least 12 UTF-8 bytes; several random words are recommended.")
    return password


def safe_path(path: Path) -> Path:
    """Refuse symlinks in every existing component, including dangling links."""
    for part in reversed((path, *path.parents)):
        if part.is_symlink():
            raise BackupError(f"Symlinks are not supported: {part}")
    return path


def instance(root: Path) -> Path:
    root = root.expanduser().resolve(strict=True)
    if not safe_path(root / "app").is_dir():
        raise BackupError("--root must select a Shardbase instance containing app/.")
    safe_path(root / BOUNDARY)
    safe_path(root / ".obsidian")
    return root


def specification(root: Path) -> str:
    path = safe_path(root / SPEC_PATH)
    if not path.is_file():
        raise BackupError("The instance is missing its System Specification; compatibility cannot be established.")
    match = re.search(r"^Specification version: `(foundation-[1-9][0-9]*)`", path.read_text(encoding="utf-8"), re.M)
    if not match:
        raise BackupError("Cannot determine the instance's System Specification version.")
    return match[1]


def external(path: Path, root: Path, label: str) -> Path:
    path = path.expanduser().absolute()
    path = path.parent.resolve(strict=True) / path.name
    safe_path(path)
    path = path.resolve()
    project = Path(__file__).resolve().parents[2]
    if any(path.is_relative_to(base) for base in (root, project)) or any(
        (parent / SPEC_PATH).is_file() or (parent / ".obsidian").is_dir()
        for parent in (path, *path.parents)
    ):
        raise BackupError(f"{label} must be outside Shardbase instances and knowledge vaults.")
    return path


@contextmanager
def scratch(root: Path, staging_dir: Path | None):
    selected = (staging_dir or Path(tempfile.gettempdir())).expanduser().resolve(strict=True)
    base = external(selected, root, "Staging directory")
    if not base.is_dir():
        raise BackupError("The staging directory must already exist.")
    with tempfile.TemporaryDirectory(prefix="shardbase-transfer-", dir=base) as name:
        yield Path(name)


def _git(root: Path, *args: str, allow_missing: bool = False) -> bytes:
    git_environment = {"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0", "GIT_NO_LAZY_FETCH": "1", "GIT_NO_REPLACE_OBJECTS": "1"}
    environment = dict(os.environ, **git_environment)
    for key in list(environment):
        if key.startswith("GIT_") and key not in git_environment:
            environment.pop(key)
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
            env=environment, capture_output=True, check=False,
        )
    except OSError as error:
        raise BackupError("Git is required to inspect this checkout safely.") from error
    if allow_missing and result.returncode == 1:
        return b""
    if result.returncode:
        raise BackupError("Git tracking could not be inspected safely; backup/restore stopped.")
    return result.stdout


def _git_checkout(root: Path) -> bool:
    if not (root / ".git").exists() and not (root / ".git").is_symlink():
        return False
    if Path(os.fsdecode(_git(root, "rev-parse", "--show-toplevel")).strip()).resolve() != root:
        raise BackupError("The selected instance must be the Git checkout root.")
    return True


def check_obsidian_untracked(root: Path) -> None:
    if not _git_checkout(root):
        return
    if any(_git(root, "ls-files", "--stage", "-z", "--", ".obsidian").split(b"\x00")):
        raise BackupError(
            ".obsidian contains Git-tracked content. Untrack it (for example, git rm --cached) before backup; "
            ".obsidian must remain private and ignored."
        )


def git_tracked_v1(root: Path) -> set[str]:
    """Legacy v1 committed-reference policy, retained without reinterpretation."""
    if not _git_checkout(root):
        return set()
    records = _git(root, "ls-files", "--stage", "-z", "--", BOUNDARY).split(b"\x00")
    tracked, indexed = set(), {}
    for record in filter(None, records):
        prefix, name = record.split(b"\t", 1)
        mode, object_id, stage = prefix.split()
        if stage != b"0" or mode not in {b"100644", b"100755"}:
            raise BackupError("Resolve conflicted, symlink, or submodule knowledge entries before legacy restore.")
        tracked.add(os.fsdecode(name))
        indexed[name] = (mode, object_id)
    committed = {}
    if _git(root, "rev-parse", "--verify", "--quiet", "HEAD", allow_missing=True):
        for record in filter(None, _git(root, "ls-tree", "-r", "-z", "HEAD", "--", BOUNDARY).split(b"\x00")):
            prefix, name = record.split(b"\t", 1)
            mode, kind, object_id = prefix.split()
            if kind != b"blob":
                raise BackupError("Nested Git repositories in knowledge are unsupported.")
            committed[name] = (mode, object_id)
    if indexed != committed:
        raise BackupError("Git-tracked knowledge has local changes; legacy restore stopped.")
    for name, (mode, object_id) in indexed.items():
        path = safe_path(root / os.fsdecode(name))
        if not path.is_file():
            raise BackupError("Git-tracked knowledge has local changes; legacy restore stopped.")
        before = signature(path)
        digest = hashlib.sha1() if len(object_id) == 40 else hashlib.sha256()
        digest.update(b"blob " + str(before[3]).encode("ascii") + b"\x00")
        with path.open("rb") as stream:
            while block := stream.read(CHUNK):
                digest.update(block)
        if digest.hexdigest().encode() != object_id or signature(path) != before or (
            os.name == "posix" and bool(before[2] & 0o100) != (mode == b"100755")
        ):
            raise BackupError("Git-tracked knowledge has local changes; legacy restore stopped.")
    return tracked


# Read-only diagnostics still report historical tracked Knowledge paths. Format
# v2 backup itself intentionally does not use this set to omit user bytes.
git_tracked = git_tracked_v1


def portable_key(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold()


def validate_component_path(value: str, *, empty: bool = False) -> None:
    if not isinstance(value, str) or len(value.encode("utf-8")) > 4096 or (not value and not empty):
        raise BackupError("Invalid or oversized backup path.")
    if not value and empty:
        return
    for part in value.split("/"):
        if (not part or part in {".", ".."} or part.endswith((" ", "."))
                or any(char in '<>:"\\|?*' or unicodedata.category(char) in {"Cc", "Cs"} for char in part)
                or re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part)):
            raise BackupError("Backup contains a non-portable or unsafe path.")
        if part.casefold() == ".git":
            raise BackupError("Nested Git repositories are unsupported; no partial transfer was performed.")


def validate_v1_name(value: str) -> None:
    if not isinstance(value, str) or (value != BOUNDARY and not value.startswith(BOUNDARY + "/")):
        raise BackupError("Backup entries must stay inside app/Knowledge/.")
    validate_component_path(value)


def signature(path: Path) -> tuple:
    info = safe_path(path).lstat()
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def digest_file(path: Path) -> tuple[int, str]:
    before = signature(path)
    if not stat.S_ISREG(before[2]):
        raise BackupError(f"Expected an ordinary file: {path}")
    digest, size = hashlib.sha256(), 0
    with path.open("rb") as stream:
        while block := stream.read(CHUNK):
            digest.update(block)
            size += len(block)
    if signature(path) != before or size != before[3]:
        raise BackupError("A user-state file changed while being read. Close editors and retry.")
    return size, digest.hexdigest()


def _file_metadata(path: Path, mode: int) -> dict:
    size, digest = digest_file(path)
    return {"size": size, "sha256": digest, "mode": 0o600 | (mode & 0o100), "mtime_ns": path.stat().st_mtime_ns}


def _excluded(child: Path, mode: int) -> bool:
    return ((child.name in OMIT_FILES and stat.S_ISREG(mode))
            or (child.name in OMIT_DIRS and stat.S_ISDIR(mode)))


def inventory_v2(root: Path) -> tuple[list[dict], dict[int, tuple[Path, tuple]], list[str]]:
    try:
        from database_creation import resolve_blueprint
        from database_preparation import database_sources
        from note_creation import CreationError
    except ImportError as error:
        raise BackupError("Backup requires the installed Shardbase database tooling.") from error
    try:
        live = sorted(database_sources(root, live_only=True), key=lambda item: item.metadata["database_id"])
        for source in live:
            resolve_blueprint(root, source.metadata["database_id"])
    except CreationError as error:
        raise BackupError(str(error)) from error
    entries: list[dict] = []
    snapshots: dict[int, tuple[Path, tuple]] = {}
    names: set[tuple[str, str, str]] = set()
    total = 0

    def visit(path: Path, logical_root: str, relative: str, database_id: str = "") -> None:
        nonlocal total
        validate_component_path(relative, empty=True)
        namespace = (logical_root, database_id, portable_key(relative))
        if namespace in names:
            raise BackupError("User state contains case/Unicode-equivalent paths; resolve the collision before transfer.")
        names.add(namespace)
        before = signature(path)
        mode = before[2]
        entry = {"root": logical_root, "path": relative}
        if database_id:
            entry["database_id"] = database_id
        if stat.S_ISDIR(mode):
            entry["kind"] = "directory"
        elif stat.S_ISREG(mode):
            entry.update(kind="file", **_file_metadata(path, mode))
            total += entry["size"]
            if total > MAX_PAYLOAD - MAX_MANIFEST - 8:
                raise BackupError("User state exceeds the format-v2 32 GiB payload limit.")
        else:
            raise BackupError(f"User state contains a special file; only ordinary files/directories are supported: {path}")
        index = len(entries)
        entries.append(entry)
        snapshots[index] = (path, before)
        if len(entries) > MAX_ENTRIES:
            raise BackupError("User state exceeds the format-v2 100,000-entry limit.")
        if entry["kind"] == "directory":
            for child in sorted(path.iterdir()):
                safe_path(child)
                child_mode = child.lstat().st_mode
                if _excluded(child, child_mode):
                    continue
                child_relative = child.name if not relative else f"{relative}/{child.name}"
                visit(child, logical_root, child_relative, database_id)

    inbox = root / "app/Knowledge/Inbox"
    if inbox.exists():
        if not inbox.is_dir():
            raise BackupError("app/Knowledge/Inbox must be a directory.")
        visit(inbox, "inbox", "")
    for source in live:
        identity = source.metadata["database_id"]
        for name in ("Data", "Views"):
            path = source.path / name
            if path.exists():
                if not path.is_dir():
                    raise BackupError(f"{path} must be a directory.")
                visit(path, "database", name, identity)
    obsidian = root / ".obsidian"
    if obsidian.exists():
        if not obsidian.is_dir():
            raise BackupError(".obsidian must be a directory.")
        visit(obsidian, "obsidian", "")
    return entries, snapshots, [item.metadata["database_id"] for item in live]


def encode_manifest_v2(entries: list[dict], spec: str, databases: list[str]) -> bytes:
    manifest = {
        "format": "shardbase-user-state-backup", "version": VERSION,
        "specification": spec, "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_policy": "all-user-state-embedded",
        "databases": [{"database_id": identity} for identity in databases],
        "entries": entries,
    }
    raw = json.dumps(manifest, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_MANIFEST:
        raise BackupError("The backup manifest exceeds the format-v2 16 MiB limit.")
    return raw


def validate_reconstructable_packages(root: Path, databases: list[str], staging_dir: Path | None) -> None:
    """Prove that every represented identity has a buildable current package."""
    try:
        from database_creation import prepare_database_package, resolve_blueprint
        from note_creation import CreationError
    except ImportError as error:
        raise BackupError("Backup requires the installed Shardbase database tooling.") from error
    with scratch(root, staging_dir) as stage:
        for number, identity in enumerate(databases):
            try:
                blueprint = resolve_blueprint(root, identity)
                package_stage = stage / f"package-{number}"
                package_stage.mkdir()
                destination = root / "app/Knowledge/Databases" / blueprint.path.name
                prepare_database_package(root, blueprint, package_stage, destination)
            except CreationError as error:
                raise BackupError(str(error)) from error


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BackupError("Duplicate JSON keys in the backup manifest.")
        result[key] = value
    return result


def _json(raw: bytes) -> dict:
    try:
        return json.loads(raw, object_pairs_hook=no_duplicate_keys)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise BackupError("The backup manifest is malformed.") from error


def _validate_file_entry(entry: dict, expected: set[str]) -> None:
    if (set(entry) != expected or type(entry.get("size")) is not int or not 0 <= entry["size"] <= MAX_PAYLOAD
            or not isinstance(entry.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
            or type(entry.get("mode")) is not int or entry["mode"] not in {0o600, 0o700}
            or type(entry.get("mtime_ns")) is not int or not 0 <= entry["mtime_ns"] <= 2**63 - 1):
        raise BackupError("Invalid file metadata in the backup.")


def decode_manifest_v1(raw: bytes) -> dict:
    value = _json(raw)
    if (not isinstance(value, dict) or set(value) != {"format", "version", "specification", "created_utc", "scope", "git_policy", "entries"}
            or value["format"] != "shardbase-knowledge-backup"
            or type(value["version"]) is not int or value["version"] != LEGACY_VERSION
            or value["scope"] != BOUNDARY or value["git_policy"] != "committed-tracked-files-excluded"
            or not isinstance(value["created_utc"], str) or not isinstance(value["specification"], str)
            or not re.fullmatch(r"foundation-[1-9][0-9]*", value["specification"])
            or not isinstance(value["entries"], list) or len(value["entries"]) > MAX_ENTRIES):
        raise BackupError("Unsupported legacy backup manifest or version.")
    kinds, keys = {}, set()
    for entry in value["entries"]:
        if not isinstance(entry, dict) or entry.get("kind") not in {"directory", "file", "git"}:
            raise BackupError("Invalid legacy backup entry.")
        name = entry.get("path")
        validate_v1_name(name)
        key = portable_key(name)
        if key in keys:
            raise BackupError("Duplicate or case/Unicode-equivalent backup paths.")
        keys.add(key)
        kinds[name] = entry["kind"]
        expected = {"kind", "path"}
        if entry["kind"] != "directory":
            expected |= {"size", "sha256", "mode", "mtime_ns"}
            _validate_file_entry(entry, expected)
        elif set(entry) != expected:
            raise BackupError("Unsupported fields in a legacy backup entry.")
        if name == BOUNDARY and entry["kind"] != "directory":
            raise BackupError("The knowledge root must be a directory.")
    for name in kinds:
        if name != BOUNDARY and kinds.get(str(PurePosixPath(name).parent)) != "directory":
            raise BackupError("Every backup entry must have a declared directory parent.")
    return value


def decode_manifest_v2(raw: bytes) -> dict:
    value = _json(raw)
    fields = {"format", "version", "specification", "created_utc", "git_policy", "databases", "entries"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["format"] != "shardbase-user-state-backup" or type(value["version"]) is not int or value["version"] != VERSION
            or value["git_policy"] != "all-user-state-embedded"
            or not isinstance(value["created_utc"], str) or not isinstance(value["specification"], str)
            or not re.fullmatch(r"foundation-[1-9][0-9]*", value["specification"])
            or not isinstance(value["databases"], list) or len(value["databases"]) > MAX_ENTRIES
            or not isinstance(value["entries"], list)
            or len(value["entries"]) > MAX_ENTRIES):
        raise BackupError("Unsupported backup manifest or version.")
    database_ids: list[str] = []
    for item in value["databases"]:
        if not isinstance(item, dict) or set(item) != {"database_id"} or not isinstance(item["database_id"], str) or not item["database_id"].strip():
            raise BackupError("Invalid database identity in backup.")
        database_ids.append(item["database_id"])
    if len(database_ids) != len(set(database_ids)):
        raise BackupError("Duplicate database identity in backup.")
    declared = set(database_ids)
    kinds: dict[tuple[str, str, str], str] = {}
    keys = set()
    for entry in value["entries"]:
        if not isinstance(entry, dict) or entry.get("kind") not in {"directory", "file"} or entry.get("root") not in {"inbox", "database", "obsidian"}:
            raise BackupError("Invalid backup entry.")
        database_id = entry.get("database_id", "")
        if entry["root"] == "database":
            if database_id not in declared:
                raise BackupError("Backup entry refers to an undeclared database identity.")
        elif "database_id" in entry:
            raise BackupError("Only database entries may declare database_id.")
        name = entry.get("path")
        validate_component_path(name, empty=True)
        if entry["root"] == "database" and (not name or name.split("/", 1)[0] not in {"Data", "Views"}):
            raise BackupError("Database user-state entries must stay beneath Data/ or Views/.")
        if entry["root"] == "database" and "/" not in name and entry["kind"] != "directory":
            raise BackupError("Database Data and Views roots must be directories.")
        key = (entry["root"], database_id, portable_key(name))
        if key in keys:
            raise BackupError("Duplicate or case/Unicode-equivalent backup paths.")
        keys.add(key)
        kinds[(entry["root"], database_id, name)] = entry["kind"]
        expected = {"root", "path", "kind"} | ({"database_id"} if entry["root"] == "database" else set())
        if entry["kind"] == "file":
            expected |= {"size", "sha256", "mode", "mtime_ns"}
            _validate_file_entry(entry, expected)
        elif set(entry) != expected:
            raise BackupError("Unsupported fields in a backup entry.")
    for (logical_root, database_id, name), kind in kinds.items():
        if kind == "file" and name == "":
            raise BackupError("A logical user-state root must be a directory.")
        parent = str(PurePosixPath(name).parent)
        if logical_root == "database":
            if "/" not in name:
                continue
        elif name == "":
            continue
        if parent == ".":
            parent = ""
        if kinds.get((logical_root, database_id, parent)) != "directory":
            raise BackupError("Every backup entry must have a declared directory parent.")
    return value


def decrypt(source: Path, output: Path, password: bytes) -> int:
    _, _, _, _, InvalidTag = crypto()
    safe_path(source)
    info = source.stat()
    if not stat.S_ISREG(info.st_mode) or not HEADER.size + 16 <= info.st_size <= HEADER.size + MAX_PAYLOAD + 16:
        raise BackupError("Invalid backup size (supported formats allow at most 32 GiB of encrypted payload).")
    with source.open("rb") as reader, output.open("xb") as writer:
        os.chmod(output, 0o600)
        header = reader.read(HEADER.size)
        if len(header) != HEADER.size:
            raise BackupError("The backup was truncated while reading its header.")
        magic, version, salt, nonce = HEADER.unpack(header)
        if magic != MAGIC or version not in {LEGACY_VERSION, VERSION}:
            raise BackupError("Not a supported Shardbase backup; supported format versions are 1 and 2.")
        reader.seek(-16, os.SEEK_END)
        tag = reader.read(16)
        reader.seek(HEADER.size)
        decryptor = cipher(password, salt, nonce, tag).decryptor()
        decryptor.authenticate_additional_data(header)
        remaining = info.st_size - HEADER.size - 16
        while remaining:
            block = reader.read(min(CHUNK, remaining))
            if not block:
                raise BackupError("The backup was truncated while reading.")
            remaining -= len(block)
            writer.write(decryptor.update(block))
        try:
            writer.write(decryptor.finalize())
        except InvalidTag as error:
            raise BackupError("Backup authentication failed: incorrect passphrase or damaged/modified backup. Nothing was restored.") from error
        if reader.read(16) != tag or reader.read(1):
            raise BackupError("The backup changed while reading.")
    return version


def unpack(payload: Path, directory: Path, version: int) -> dict:
    with payload.open("rb") as stream:
        prefix = stream.read(8)
        if len(prefix) != 8:
            raise BackupError("Missing backup manifest length.")
        length = struct.unpack(">Q", prefix)[0]
        if not 0 < length <= MAX_MANIFEST:
            raise BackupError("Invalid backup manifest length.")
        raw = stream.read(length)
        if len(raw) != length:
            raise BackupError("Truncated backup manifest.")
        manifest = decode_manifest_v1(raw) if version == LEGACY_VERSION else decode_manifest_v2(raw)
        expected = 8 + length + sum(item.get("size", 0) for item in manifest["entries"] if item["kind"] == "file")
        if expected != payload.stat().st_size:
            raise BackupError("Backup payload size does not match its manifest.")
        for index, entry in enumerate(manifest["entries"]):
            if entry["kind"] != "file":
                continue
            path = directory / str(index)
            digest, remaining = hashlib.sha256(), entry["size"]
            with path.open("xb") as writer:
                os.chmod(path, entry["mode"])
                while remaining:
                    block = stream.read(min(CHUNK, remaining))
                    if not block:
                        raise BackupError("Truncated file in backup.")
                    remaining -= len(block)
                    digest.update(block)
                    writer.write(block)
                writer.flush()
                os.fsync(writer.fileno())
            if digest.hexdigest() != entry["sha256"]:
                raise BackupError("A backup file does not match its SHA-256 digest.")
            os.utime(path, ns=(entry["mtime_ns"], entry["mtime_ns"]))
    return manifest


def backup(root: Path, output: Path, password: bytes, staging_dir: Path | None = None) -> dict:
    root = instance(root)
    output = external(output, root, "Backup output")
    if output.exists():
        raise BackupError("The backup output already exists; choose a new filename.")
    if not output.parent.is_dir():
        raise BackupError("The backup output's parent directory must exist.")
    spec = specification(root)
    if spec not in {"foundation-4", "foundation-5"}:
        raise BackupError("Backup format v2 supports foundation-4 and foundation-5 sources; this specification needs explicit compatibility support.")
    check_obsidian_untracked(root)
    entries, snapshots, databases = inventory_v2(root)
    validate_reconstructable_packages(root, databases, staging_dir)
    raw = encode_manifest_v2(entries, spec, databases)
    decode_manifest_v2(raw)
    header = HEADER.pack(MAGIC, VERSION, os.urandom(16), os.urandom(12))
    _, _, salt, nonce = HEADER.unpack(header)
    encryptor = cipher(password, salt, nonce).encryptor()
    encryptor.authenticate_additional_data(header)
    fd, temporary_name = tempfile.mkstemp(prefix=".shardbase-backup-", suffix=".partial", dir=output.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as writer:
            writer.write(header)
            writer.write(encryptor.update(struct.pack(">Q", len(raw)) + raw))
            for index, entry in enumerate(entries):
                if entry["kind"] != "file":
                    continue
                path, before = snapshots[index]
                if signature(path) != before:
                    raise BackupError("User state changed during backup. Close editors and retry.")
                digest, size = hashlib.sha256(), 0
                with path.open("rb") as reader:
                    while block := reader.read(CHUNK):
                        digest.update(block)
                        size += len(block)
                        if size > entry["size"]:
                            raise BackupError("User state grew during backup. Close editors and retry.")
                        writer.write(encryptor.update(block))
                if size != entry["size"] or digest.hexdigest() != entry["sha256"]:
                    raise BackupError("User state changed during backup. Close editors and retry.")
            writer.write(encryptor.finalize())
            writer.write(encryptor.tag)
            writer.flush()
            os.fsync(writer.fileno())
        check_obsidian_untracked(root)
        entries_after, snapshots_after, databases_after = inventory_v2(root)
        if entries_after != entries or snapshots_after != snapshots or databases_after != databases or specification(root) != spec:
            raise BackupError("User state or database identity changed during backup. Close editors and retry.")
        validate_reconstructable_packages(root, databases, staging_dir)
        with scratch(root, staging_dir) as stage:
            version = decrypt(temporary, stage / "payload", password)
            manifest = unpack(stage / "payload", stage, version)
        os.link(temporary, output)
        sync_directory(output.parent)
        return manifest
    finally:
        temporary.unlink(missing_ok=True)


def sync_directory(path: Path) -> None:
    if os.name == "posix":
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _check_equivalent_name(path: Path) -> None:
    if not path.parent.exists():
        return
    if not path.parent.is_dir():
        raise BackupError("A restore directory conflicts with an existing file.")
    equivalents = {child.name for child in path.parent.iterdir() if portable_key(child.name) == portable_key(path.name)}
    if equivalents and equivalents != {path.name}:
        if len(equivalents) != 1 or not path.exists() or not path.samefile(path.parent / next(iter(equivalents))):
            raise BackupError("Restore would collide with a case/Unicode-equivalent existing path.")
        if unicodedata.normalize("NFC", next(iter(equivalents))) != unicodedata.normalize("NFC", path.name):
            raise BackupError("Restore would collide with an existing path's letter case.")


def check_target_v1(root: Path, entries: list[dict], tracked: set[str]) -> list[tuple[int, dict]]:
    pending = []
    for index, entry in enumerate(entries):
        path = safe_path(root / entry["path"])
        _check_equivalent_name(path)
        kind = entry["kind"]
        if kind == "directory":
            if path.exists() and not path.is_dir():
                raise BackupError("A restore directory conflicts with an existing file.")
        elif kind == "git":
            if not path.is_file() or digest_file(path) != (entry["size"], entry["sha256"]):
                raise BackupError("The target is missing or differs from a Git-backed knowledge file excluded from this legacy backup.")
        elif path.exists():
            if not path.is_file() or digest_file(path) != (entry["size"], entry["sha256"]):
                raise BackupError(f"Restore conflict; existing content will not be replaced: {path}")
        elif entry["path"] in tracked:
            raise BackupError("Legacy restore would write a tracked path missing from the target checkout.")
        else:
            pending.append((index, entry))
    return pending


def _restore_v1(root: Path, manifest: dict, stage: Path, target_spec: str, dry_run: bool) -> dict:
    if (manifest["specification"], target_spec) not in {
        ("foundation-3", "foundation-3"), ("foundation-3", "foundation-4"), ("foundation-4", "foundation-4")
    }:
        raise BackupError(
            "Unsupported legacy specification transition. Format v1 retains foundation-3 → foundation-3/4 and "
            "foundation-4 → foundation-4 full-Knowledge semantics; it cannot cross the foundation-5 ownership boundary."
        )
    tracked = git_tracked_v1(root)
    pending = check_target_v1(root, manifest["entries"], tracked)
    result = {
        "format_version": 1, "files_added": len(pending),
        "files_unchanged": sum(item["kind"] == "file" for item in manifest["entries"]) - len(pending),
        "git_files": sum(item["kind"] == "git" for item in manifest["entries"]),
        "databases_materialized": 0, "obsidian_files": 0, "dry_run": dry_run,
    }
    if dry_run:
        return result
    if git_tracked_v1(root) != tracked:
        raise BackupError("Target Git tracking changed during restore; retry with the checkout idle.")
    check_target_v1(root, manifest["entries"], tracked)
    directories = [(root / item["path"]) for item in manifest["entries"] if item["kind"] == "directory"]
    files = [(stage / str(index), root / entry["path"]) for index, entry in pending]
    _publish(stage, directories, files)
    return result


def _tree(package: Path, *, managed: bool) -> dict[str, tuple]:
    result = {}
    for path in sorted(package.rglob("*")):
        relative = path.relative_to(package)
        if relative.parts and relative.parts[0] in {"Data", "Views"}:
            if managed:
                continue
            if path.is_file():
                continue
        safe_path(path)
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            result[relative.as_posix()] = ("directory",)
        elif stat.S_ISREG(mode):
            size, digest = digest_file(path)
            result[relative.as_posix()] = ("file", size, digest, bool(mode & 0o100))
        else:
            raise BackupError(f"Database package contains an unsupported special file: {path}")
    return result


def _managed_equivalent(expected: Path, existing: Path) -> bool:
    return _tree(expected, managed=True) == _tree(existing, managed=True)


@dataclass(frozen=True)
class PlanItem:
    kind: str
    destination: Path
    source: Path | None = None
    user_file: bool = False


def _logical_destination(root: Path, entry: dict, destinations: dict[str, Path]) -> Path:
    if entry["root"] == "inbox":
        base = root / "app/Knowledge/Inbox"
    elif entry["root"] == "obsidian":
        base = root / ".obsidian"
    else:
        base = destinations[entry["database_id"]]
    return base if not entry["path"] else base.joinpath(*entry["path"].split("/"))


def _plan_v2(root: Path, manifest: dict, stage: Path) -> tuple[list[PlanItem], int]:
    try:
        from database_creation import prepare_database_package, resolve_blueprint
        from database_preparation import database_sources
        from note_creation import CreationError
    except ImportError as error:
        raise BackupError("Restore requires the installed Shardbase database tooling.") from error
    try:
        live = database_sources(root, live_only=True)
    except CreationError as error:
        raise BackupError(str(error)) from error
    live_by_id = {item.metadata["database_id"]: item.path for item in live}
    destinations: dict[str, Path] = {}
    staged_packages: dict[str, Path] = {}
    materialized = 0
    for number, record in enumerate(manifest["databases"]):
        identity = record["database_id"]
        try:
            blueprint = resolve_blueprint(root, identity)
        except CreationError as error:
            raise BackupError(str(error)) from error
        destination = root / "app/Knowledge/Databases" / blueprint.path.name
        destinations[identity] = destination
        stage_root = stage / f"package-{number}"
        stage_root.mkdir()
        try:
            expected = prepare_database_package(root, blueprint, stage_root, destination)
        except CreationError as error:
            raise BackupError(str(error)) from error
        staged_packages[identity] = expected
        existing = live_by_id.get(identity)
        if existing is not None and existing != destination:
            raise BackupError(
                f"Existing database {identity} is at {existing.name}, but the current destination package is "
                f"{destination.name}; no folder-name migration was guessed."
            )
        if destination.exists():
            if existing != destination or not destination.is_dir():
                raise BackupError(f"Current database package destination is occupied: {destination}")
            if not _managed_equivalent(expected, destination):
                raise BackupError(
                    f"Existing managed package for database {identity} differs from the current destination release; "
                    "restore will not merge, upgrade, or overwrite it."
                )
        else:
            materialized += 1
    archived = set(destinations)
    for identity, path in live_by_id.items():
        if identity in archived and path != destinations[identity]:
            raise BackupError(f"Duplicate or relocated live database identity requires review: {identity}")

    items: list[PlanItem] = []
    for identity, expected in staged_packages.items():
        destination = destinations[identity]
        new_package = not destination.exists()
        for relative, descriptor in _tree(expected, managed=False).items():
            source = expected / relative
            top = Path(relative).parts[0]
            if top in {"Data", "Views"}:
                if descriptor[0] == "directory":
                    items.append(PlanItem("directory", destination / relative))
            elif new_package:
                items.append(PlanItem(descriptor[0], destination / relative, source if descriptor[0] == "file" else None))
        if new_package:
            items.append(PlanItem("directory", destination))
    for index, entry in enumerate(manifest["entries"]):
        destination = _logical_destination(root, entry, destinations)
        items.append(PlanItem(entry["kind"], destination, stage / str(index) if entry["kind"] == "file" else None, entry["kind"] == "file"))
    return items, materialized


def _preflight_items(items: list[PlanItem]) -> tuple[list[Path], list[PlanItem], int]:
    planned: dict[str, str] = {}
    directories: dict[str, Path] = {}
    pending: list[PlanItem] = []
    unchanged = 0
    for item in sorted(items, key=lambda value: (len(value.destination.parts), str(value.destination))):
        safe_path(item.destination)
        key = portable_key(str(item.destination))
        previous = planned.get(key)
        if previous is not None and (previous != item.kind or item.kind == "file"):
            raise BackupError("Restore plan contains colliding package or user-state paths.")
        planned[key] = item.kind
        _check_equivalent_name(item.destination)
        if item.kind == "directory":
            directories[key] = item.destination
            if item.destination.exists() and not item.destination.is_dir():
                raise BackupError(f"Restore directory conflicts with an existing file: {item.destination}")
        elif item.destination.exists():
            if not item.destination.is_file() or digest_file(item.destination) != digest_file(item.source):
                raise BackupError(f"Restore conflict; existing content will not be replaced: {item.destination}")
            if item.user_file:
                unchanged += 1
        else:
            pending.append(item)
    return list(directories.values()), pending, unchanged


def _publish(stage: Path, directories: list[Path], files: list[tuple[Path, Path]]) -> None:
    if files:
        for _, destination in files:
            parent = destination.parent
            while not parent.exists():
                parent = parent.parent
            if parent.stat().st_dev != stage.stat().st_dev:
                raise BackupError("Restore staging must be on the target filesystem. Use --staging-dir with an external directory on that filesystem.")
    created_files: list[tuple[Path, int]] = []
    created_dirs: list[Path] = []
    try:
        all_directories = set(directories)
        for directory in list(all_directories):
            parent = directory.parent
            while not parent.exists():
                all_directories.add(parent)
                parent = parent.parent
        for _, destination in files:
            parent = destination.parent
            while not parent.exists():
                all_directories.add(parent)
                parent = parent.parent
        for path in sorted(all_directories, key=lambda value: (len(value.parts), str(value))):
            safe_path(path)
            if not path.exists():
                path.mkdir(mode=0o700)
                created_dirs.append(path)
        for source, destination in files:
            os.link(source, destination)
            created_files.append((destination, source.stat().st_ino))
        for directory in {path.parent for path, _ in created_files} | set(created_dirs):
            sync_directory(directory)
    except BaseException:
        for path, inode in reversed(created_files):
            try:
                if not path.is_symlink() and path.stat().st_ino == inode:
                    path.unlink()
            except OSError:
                pass
        for path in reversed(created_dirs):
            try:
                path.rmdir()
            except OSError:
                pass
        raise


def _restore_v2(root: Path, manifest: dict, stage: Path, target_spec: str, dry_run: bool) -> dict:
    if (manifest["specification"], target_spec) not in {
        ("foundation-4", "foundation-5"), ("foundation-5", "foundation-5")
    }:
        raise BackupError(
            "Unsupported specification transition. Format v2 supports foundation-4/5 user state into foundation-5; "
            "it does not downgrade or infer other migrations."
        )
    check_obsidian_untracked(root)
    items, materialized = _plan_v2(root, manifest, stage)
    directories, pending, unchanged = _preflight_items(items)
    user_pending = sum(item.user_file for item in pending)
    result = {
        "format_version": 2, "files_added": user_pending, "files_unchanged": unchanged,
        "git_files": 0, "databases_materialized": materialized,
        "obsidian_files": sum(entry["kind"] == "file" and entry["root"] == "obsidian" for entry in manifest["entries"]),
        "dry_run": dry_run,
    }
    if dry_run:
        return result
    check_obsidian_untracked(root)
    # Recheck destination state without rebuilding package staging directories.
    directories, pending_again, unchanged_again = _preflight_items(items)
    if len(pending_again) != len(pending) or unchanged_again != unchanged:
        raise BackupError("Restore destination changed during preflight; retry with the instance idle.")
    _publish(stage, directories, [(item.source, item.destination) for item in pending_again])
    return result


def restore(root: Path, source: Path, password: bytes, staging_dir: Path | None = None, *, dry_run: bool = False) -> dict:
    root = instance(root)
    source = source.expanduser().absolute()
    source = safe_path(source.parent.resolve(strict=True) / source.name)
    target_spec = specification(root)
    with scratch(root, staging_dir) as stage:
        version = decrypt(source, stage / "payload", password)
        manifest = unpack(stage / "payload", stage, version)
        if version == LEGACY_VERSION:
            return _restore_v1(root, manifest, stage, target_spec, dry_run)
        return _restore_v2(root, manifest, stage, target_spec, dry_run)
