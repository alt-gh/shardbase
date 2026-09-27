"""Offline, preservation-oriented knowledge transfer. Wire contract: BACKUP_FORMAT.md."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import subprocess
import tempfile
import unicodedata
import warnings


MAGIC = b"SHARDBK\x00"
VERSION = 1
HEADER = struct.Struct(">8sI16s12s")
CHUNK = 1024 * 1024
MAX_PAYLOAD = 32 * 1024**3  # Deliberately below the per-message AES-GCM limit.
MAX_MANIFEST = 16 * 1024**2
MAX_ENTRIES = 100_000
BOUNDARY = "app/Knowledge"
OMIT_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "node_modules"}
OMIT_FILES = {".DS_Store", "Thumbs.db", "Desktop.ini"}
SPEC_PATH = "app/Docs/Shard System Specification.md"


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
        # getpass normally falls back to echoed input; refusing that is intentional.
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
    # Resolve the user's root alias, but never any in-instance symlink.
    root = root.expanduser().resolve(strict=True)
    if not safe_path(root / "app").is_dir():
        raise BackupError("--root must select a ShardBase instance containing app/.")
    safe_path(root / BOUNDARY)
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
    # macOS exposes /tmp and /var through system symlinks. Resolve explicitly
    # selected external parent aliases while still refusing a symlink leaf.
    path = path.parent.resolve(strict=True) / path.name
    safe_path(path)
    path = path.resolve()
    project = Path(__file__).resolve().parents[2]
    if any(path.is_relative_to(base) for base in (root, project)) or any(
        (parent / SPEC_PATH).is_file() or (parent / ".obsidian").is_dir()
        for parent in (path, *path.parents)
    ):
        raise BackupError(f"{label} must be outside ShardBase instances and knowledge vaults.")
    return path


@contextmanager
def scratch(root: Path, staging_dir: Path | None):
    selected = (staging_dir or Path(tempfile.gettempdir())).expanduser().resolve(strict=True)
    base = external(selected, root, "Staging directory")
    if not base.is_dir():
        raise BackupError("The staging directory must already exist.")
    with tempfile.TemporaryDirectory(prefix="shardbase-transfer-", dir=base) as name:
        yield Path(name)


def git_tracked(root: Path) -> set[str]:
    """Use this checkout's committed index only. Never fetch or inspect a parent repo."""
    if not (root / ".git").exists() and not (root / ".git").is_symlink():
        return set()
    git_environment = {"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0", "GIT_NO_LAZY_FETCH": "1", "GIT_NO_REPLACE_OBJECTS": "1"}
    environment = dict(os.environ, **git_environment)
    # Ignore ambient Git redirection, which could select a different user's index.
    for key in list(environment):
        if key.startswith("GIT_") and key not in git_environment:
            environment.pop(key)

    def run(*args, allow_missing=False):
        try:
            result = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
                                    env=environment, capture_output=True, check=False)
        except OSError as error:
            raise BackupError("Git is required to determine this checkout's tracked knowledge files.") from error
        if allow_missing and result.returncode == 1:
            return b""
        if result.returncode:
            raise BackupError("Git tracking could not be inspected safely; backup/restore stopped.")
        return result.stdout

    if Path(os.fsdecode(run("rev-parse", "--show-toplevel")).strip()).resolve() != root:
        raise BackupError("The selected instance must be the Git checkout root.")
    records = run("ls-files", "--stage", "-z", "--", BOUNDARY).split(b"\x00")
    tracked, indexed = set(), {}
    for record in filter(None, records):
        prefix, name = record.split(b"\t", 1)
        mode, object_id, stage = prefix.split()
        if stage != b"0" or mode not in {b"100644", b"100755"}:
            raise BackupError("Resolve conflicted, symlink, or submodule knowledge entries before backup/restore.")
        tracked.add(os.fsdecode(name))
        indexed[name] = (mode, object_id)
    committed = {}
    if run("rev-parse", "--verify", "--quiet", "HEAD", allow_missing=True):
        for record in filter(None, run("ls-tree", "-r", "-z", "HEAD", "--", BOUNDARY).split(b"\x00")):
            prefix, name = record.split(b"\t", 1)
            mode, kind, object_id = prefix.split()
            if kind != b"blob":
                raise BackupError("Nested Git repositories in knowledge are unsupported.")
            committed[name] = (mode, object_id)
    if tracked or committed:
        changed = indexed != committed
        # Hash bytes directly: index assume-unchanged/skip-worktree flags and
        # clean filters must never conceal local edits or invoke external code.
        for name, (mode, object_id) in indexed.items():
            path = safe_path(root / os.fsdecode(name))
            if not path.is_file():
                changed = True
                continue
            before = signature(path)
            digest = hashlib.sha1() if len(object_id) == 40 else hashlib.sha256()
            digest.update(b"blob " + str(before[3]).encode("ascii") + b"\x00")
            with path.open("rb") as stream:
                while block := stream.read(CHUNK):
                    digest.update(block)
            if (digest.hexdigest().encode("ascii") != object_id or signature(path) != before
                    or (os.name == "posix" and bool(before[2] & 0o100) != (mode == b"100755"))):
                changed = True
        if changed:
            raise BackupError("Git-tracked knowledge has local changes. Preserve or resolve them before backup/restore; they will not be silently omitted.")
    return tracked


def portable_key(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold()


def validate_name(value: str) -> None:
    if not isinstance(value, str) or len(value.encode("utf-8")) > 4096:
        raise BackupError("Invalid or oversized backup path.")
    parts = value.split("/")
    if value != BOUNDARY and not value.startswith(BOUNDARY + "/"):
        raise BackupError("Backup entries must stay inside app/Knowledge/.")
    for part in parts:
        if (not part or part in {".", ".."} or part.endswith((" ", "."))
                or any(char in '<>:"\\|?*' or unicodedata.category(char) in {"Cc", "Cs"} for char in part)
                or re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part)):
            raise BackupError("Backup contains a non-portable or unsafe path.")
        if part.casefold() == ".git":
            raise BackupError("Nested Git repositories in knowledge are unsupported; no partial backup was created.")


def signature(path: Path) -> tuple:
    info = safe_path(path).lstat()
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def digest_file(path: Path) -> tuple[int, str]:
    before = signature(path)
    if not stat.S_ISREG(before[2]):
        raise BackupError(f"Expected an ordinary file: {path}")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while block := stream.read(CHUNK):
            digest.update(block)
            size += len(block)
    if signature(path) != before or size != before[3]:
        raise BackupError("A knowledge file changed while being read. Close editors and retry.")
    return size, digest.hexdigest()


def inventory(root: Path, tracked: set[str]) -> tuple[list[dict], dict[str, tuple]]:
    entries, snapshots, names = [], {}, set()
    total = 0

    def visit(path: Path):
        nonlocal total
        name = path.relative_to(root).as_posix()
        validate_name(name)
        key = portable_key(name)
        if key in names:
            raise BackupError("Knowledge contains case/Unicode-equivalent paths; resolve the collision before transfer.")
        names.add(key)
        before = signature(path)
        mode = before[2]
        entry = {"path": name}
        if stat.S_ISDIR(mode):
            entry["kind"] = "directory"
        elif stat.S_ISREG(mode):
            size, digest = digest_file(path)
            entry.update(kind="git" if name in tracked else "file", size=size, sha256=digest,
                         mode=0o600 | (mode & 0o100), mtime_ns=before[4])
            if entry["kind"] == "file":
                total += size
                if total > MAX_PAYLOAD - MAX_MANIFEST - 8:
                    raise BackupError("Knowledge exceeds the format-v1 32 GiB payload limit.")
        else:
            raise BackupError(f"Knowledge contains a special file; only ordinary files/directories are supported: {path}")
        entries.append(entry)
        snapshots[name] = before
        if len(entries) > MAX_ENTRIES:
            raise BackupError("Knowledge exceeds the format-v1 100,000-entry limit.")
        if entry["kind"] == "directory":
            for child in sorted(path.iterdir()):
                # Check links before exclusions, so a ignored-looking link cannot hide a boundary issue.
                safe_path(child)
                child_mode = child.lstat().st_mode
                if ((child.name in OMIT_FILES and stat.S_ISREG(child_mode))
                        or (child.name in OMIT_DIRS and stat.S_ISDIR(child_mode))):
                    continue
                visit(child)

    knowledge = root / BOUNDARY
    if knowledge.exists():
        if not knowledge.is_dir():
            raise BackupError("app/Knowledge must be a directory.")
        visit(knowledge)
    if tracked - {entry["path"] for entry in entries}:
        raise BackupError("Tracked knowledge is missing or excluded as generated state; resolve it before transfer.")
    return entries, snapshots


def encode_manifest(entries: list[dict], spec: str) -> bytes:
    manifest = {"format": "shardbase-knowledge-backup", "version": VERSION,
                "specification": spec, "created_utc": datetime.now(timezone.utc).isoformat(),
                "scope": BOUNDARY, "git_policy": "committed-tracked-files-excluded", "entries": entries}
    raw = json.dumps(manifest, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_MANIFEST:
        raise BackupError("The backup manifest exceeds the format-v1 16 MiB limit.")
    return raw


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BackupError("Duplicate JSON keys in the backup manifest.")
        result[key] = value
    return result


def decode_manifest(raw: bytes) -> dict:
    try:
        value = json.loads(raw, object_pairs_hook=no_duplicate_keys)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise BackupError("The backup manifest is malformed.") from error
    if (not isinstance(value, dict) or set(value) != {"format", "version", "specification", "created_utc", "scope", "git_policy", "entries"}
            or value["format"] != "shardbase-knowledge-backup" or type(value["version"]) is not int or value["version"] != VERSION
            or value["scope"] != BOUNDARY or value["git_policy"] != "committed-tracked-files-excluded"
            or not isinstance(value["created_utc"], str) or not isinstance(value["specification"], str)
            or not re.fullmatch(r"foundation-[1-9][0-9]*", value["specification"])
            or not isinstance(value["entries"], list) or len(value["entries"]) > MAX_ENTRIES):
        raise BackupError("Unsupported backup manifest or version.")
    kinds, keys = {}, set()
    for entry in value["entries"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("kind"), str) or entry["kind"] not in {"directory", "file", "git"}:
            raise BackupError("Invalid backup entry.")
        name = entry.get("path")
        validate_name(name)
        key = portable_key(name)
        if key in keys:
            raise BackupError("Duplicate or case/Unicode-equivalent backup paths.")
        keys.add(key)
        kinds[name] = entry["kind"]
        expected = {"kind", "path"}
        if entry["kind"] != "directory":
            expected |= {"size", "sha256", "mode", "mtime_ns"}
            if (type(entry.get("size")) is not int or not 0 <= entry["size"] <= MAX_PAYLOAD
                    or not isinstance(entry.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
                    or type(entry.get("mode")) is not int or entry["mode"] not in {0o600, 0o700}
                    or type(entry.get("mtime_ns")) is not int or not 0 <= entry["mtime_ns"] <= 2**63 - 1):
                raise BackupError("Invalid file metadata in the backup.")
        if set(entry) != expected:
            raise BackupError("Unsupported fields in a backup entry.")
        if name == BOUNDARY and entry["kind"] != "directory":
            raise BackupError("The knowledge root must be a directory.")
    for name in kinds:
        if name != BOUNDARY and kinds.get(str(PurePosixPath(name).parent)) != "directory":
            raise BackupError("Every backup entry must have a declared directory parent.")
    return value


def decrypt(source: Path, output: Path, password: bytes) -> None:
    _, _, _, _, InvalidTag = crypto()
    safe_path(source)
    info = source.stat()
    if not stat.S_ISREG(info.st_mode) or not HEADER.size + 16 <= info.st_size <= HEADER.size + MAX_PAYLOAD + 16:
        raise BackupError("Invalid backup size (format v1 allows at most 32 GiB of encrypted payload).")
    with source.open("rb") as reader, output.open("xb") as writer:
        os.chmod(output, 0o600)
        header = reader.read(HEADER.size)
        if len(header) != HEADER.size:
            raise BackupError("The backup was truncated while reading its header.")
        magic, version, salt, nonce = HEADER.unpack(header)
        if magic != MAGIC or version != VERSION:
            raise BackupError("Not a supported ShardBase backup; expected format version 1.")
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


def unpack(payload: Path, directory: Path) -> dict:
    """Only called after authentication. Never interpret archive paths as output paths."""
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
        manifest = decode_manifest(raw)
        expected = 8 + length + sum(item.get("size", 0) for item in manifest["entries"] if item["kind"] == "file")
        if expected != payload.stat().st_size:
            raise BackupError("Backup payload size does not match its manifest.")
        for index, entry in enumerate(manifest["entries"]):
            if entry["kind"] != "file":
                continue
            path = directory / str(index)
            digest = hashlib.sha256()
            remaining = entry["size"]
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
    if spec != "foundation-3":
        raise BackupError("Backup v1 supports foundation-3 instances; this specification needs explicit compatibility support.")
    tracked = git_tracked(root)
    entries, snapshots = inventory(root, tracked)
    raw = encode_manifest(entries, spec)
    # Reject paths/metadata that this same format reader cannot restore.
    decode_manifest(raw)
    header = HEADER.pack(MAGIC, VERSION, os.urandom(16), os.urandom(12))
    _, _, salt, nonce = HEADER.unpack(header)
    encryptor = cipher(password, salt, nonce).encryptor()
    encryptor.authenticate_additional_data(header)
    fd, temporary = tempfile.mkstemp(prefix=".shardbase-backup-", suffix=".partial", dir=output.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as writer:
            writer.write(header)
            writer.write(encryptor.update(struct.pack(">Q", len(raw)) + raw))
            for entry in entries:
                if entry["kind"] != "file":
                    continue
                digest, size = hashlib.sha256(), 0
                path = safe_path(root / entry["path"])
                if signature(path) != snapshots[entry["path"]]:
                    raise BackupError("Knowledge changed during backup. Close editors and retry.")
                with path.open("rb") as reader:
                    while block := reader.read(CHUNK):
                        digest.update(block)
                        size += len(block)
                        if size > entry["size"]:
                            raise BackupError("Knowledge grew during backup. Close editors and retry.")
                        writer.write(encryptor.update(block))
                if size != entry["size"] or digest.hexdigest() != entry["sha256"]:
                    raise BackupError("Knowledge changed during backup. Close editors and retry.")
            writer.write(encryptor.finalize())
            writer.write(encryptor.tag)
            writer.flush()
            os.fsync(writer.fileno())
        if git_tracked(root) != tracked or inventory(root, tracked)[1] != snapshots or specification(root) != spec:
            raise BackupError("Knowledge or tracking changed during backup. Close editors and retry.")
        # Exercise the actual restore reader before publishing any successful backup.
        with scratch(root, staging_dir) as stage:
            decrypt(temporary, stage / "payload", password)
            manifest = unpack(stage / "payload", stage)
        # Atomic, exclusive publication; an existing backup can never be replaced.
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


def check_target(root: Path, entries: list[dict], tracked: set[str]) -> list[tuple[int, dict]]:
    pending = []
    # Include existing names when checking case/Unicode collisions, on every OS.
    children = {}
    for index, entry in enumerate(entries):
        path = safe_path(root / entry["path"])
        if path.parent.exists():
            if not path.parent.is_dir():
                raise BackupError("A restore directory conflicts with an existing file.")
            if path.parent not in children:
                children[path.parent] = {}
                for child in path.parent.iterdir():
                    children[path.parent].setdefault(portable_key(child.name), set()).add(child.name)
            equivalents = children[path.parent].get(portable_key(path.name), set())
            # macOS normalizes Unicode names; permit the one equivalent spelling
            # only if it identifies the actual requested filesystem entry.
            if equivalents and equivalents != {path.name}:
                if len(equivalents) != 1 or not path.exists() or not path.samefile(path.parent / next(iter(equivalents))):
                    raise BackupError("Restore would collide with a case/Unicode-equivalent existing path.")
                if unicodedata.normalize("NFC", next(iter(equivalents))) != unicodedata.normalize("NFC", path.name):
                    raise BackupError("Restore would collide with an existing path's letter case.")
        kind = entry["kind"]
        if kind == "directory":
            if path.exists() and not path.is_dir():
                raise BackupError("A restore directory conflicts with an existing file.")
        elif kind == "git":
            if not path.is_file() or digest_file(path) != (entry["size"], entry["sha256"]):
                raise BackupError("The target is missing or differs from a Git-backed knowledge file excluded from this backup. Use a checkout containing that committed data.")
        elif path.exists():
            if not path.is_file() or digest_file(path) != (entry["size"], entry["sha256"]):
                raise BackupError(f"Restore conflict; existing content will not be replaced: {path}")
        elif entry["path"] in tracked:
            raise BackupError("Restore would write a tracked path missing from the target checkout.")
        else:
            pending.append((index, entry))
    return pending


def restore(root: Path, source: Path, password: bytes, staging_dir: Path | None = None,
            *, dry_run: bool = False) -> dict:
    root = instance(root)
    source = source.expanduser().absolute()
    source = safe_path(source.parent.resolve(strict=True) / source.name)
    target_spec = specification(root)
    tracked = git_tracked(root)
    with scratch(root, staging_dir) as stage:
        decrypt(source, stage / "payload", password)
        manifest = unpack(stage / "payload", stage)
        if manifest["specification"] != target_spec or target_spec != "foundation-3":
            raise BackupError("Unsupported specification transition. Restore v1 transfers foundation-3 data unchanged into a foundation-3 checkout; it does not migrate schemas.")
        pending = check_target(root, manifest["entries"], tracked)
        result = {"files_added": len(pending), "files_unchanged": sum(item["kind"] == "file" for item in manifest["entries"]) - len(pending),
                  "git_files": sum(item["kind"] == "git" for item in manifest["entries"]), "dry_run": dry_run}
        if dry_run:
            return result
        # Same-filesystem hardlinks publish complete files atomically, without a
        # plaintext temporary file in the durable vault and without overwriting.
        if pending:
            for _, entry in pending:
                parent = (root / entry["path"]).parent
                while not parent.exists():
                    parent = parent.parent
                if parent.stat().st_dev != stage.stat().st_dev:
                    raise BackupError("Restore staging must be on the target filesystem. Use --staging-dir with an external directory on that filesystem.")
        if git_tracked(root) != tracked:
            raise BackupError("Target Git tracking changed during restore; retry with the checkout idle.")
        check_target(root, manifest["entries"], tracked)
        created_files, created_dirs = [], []
        try:
            directories = sorted((item for item in manifest["entries"] if item["kind"] == "directory"),
                                 key=lambda item: (item["path"].count("/"), item["path"]))
            for entry in directories:
                path = safe_path(root / entry["path"])
                if not path.exists():
                    path.mkdir(mode=0o700)
                    created_dirs.append(path)
            for index, entry in pending:
                path = safe_path(root / entry["path"])
                os.link(stage / str(index), path)
                created_files.append((path, (stage / str(index)).stat().st_ino))
            for directory in {path.parent for path, _ in created_files} | set(created_dirs) | {root / "app"}:
                sync_directory(directory)
        except BaseException:
            # Delete only this operation's new inodes, never pre-existing knowledge.
            # Hard termination can leave complete additions; rerun the same restore.
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
    return result
