# Shardbase User-State Backup Format

Current write format: `2`

This is the interoperable wire contract implemented by `backup_restore.py`. The conventional extension is `.sbbackup`; readers identify the authenticated header version, not the filename. Format v2 is an offline user-state transfer format for Foundation-4/5 sources into a `foundation-5` destination and Foundation-4/5/6 sources into a `foundation-6` destination. The reader also retains the historical format-v1 contract described below.

## Encryption Envelope

All integers are unsigned and big-endian:

```text
40-byte header || ciphertext || 16-byte authentication tag
```

| Offset | Length | Meaning |
|---:|---:|---|
| 0 | 8 | Magic bytes `53 48 41 52 44 42 4b 00` |
| 8 | 4 | Format version (`2` for new backups; legacy reader also accepts `1`) |
| 12 | 16 | Random scrypt salt |
| 28 | 12 | Random AES-GCM nonce |
| 40 | variable | Encrypted payload, at most 32 GiB |
| EOF − 16 | 16 | Full AES-GCM authentication tag |

Derive a 32-byte key from the exact UTF-8 passphrase bytes with scrypt `N=131072`, `r=8`, `p=1`. Encrypt with AES-256-GCM, authenticating all 40 header bytes as additional data. Every backup uses a fresh operating-system-generated salt and nonce. The format fixes the KDF cost; files cannot request more. Readers reject unknown versions before key derivation.

The passphrase is 1–4096 bytes for reading and 12–4096 bytes for creation. One terminal LF or CRLF in a password file is removed; embedded line endings are invalid. There is no normalization or stored verifier. Weak passphrases remain vulnerable to offline guessing.

Decryption completes into an owner-private external staging directory before any JSON parsing, path interpretation, package resolution, or durable write. Truncation, appended bytes, metadata, filenames, and payload bytes are authenticated. Only the version and total encrypted size are visible.

## Plaintext Framing

```text
8-byte manifest length || UTF-8 JSON manifest || file bytes in entry order
```

The manifest is 1–16 MiB and contains at most 100,000 entries. Only entries with `kind: "file"` consume payload bytes; each `size` determines its exact boundary. Zero-length files consume none. Missing or trailing plaintext bytes are errors. JSON duplicate keys, unknown fields, and unsupported values are rejected. There is no compression, deduplication, executable deserialization, or archive extraction.

## Version 2 Manifest

A representative manifest is:

```json
{
  "format": "shardbase-user-state-backup",
  "version": 2,
  "specification": "foundation-6",
  "created_utc": "2026-09-30T20:00:00+00:00",
  "git_policy": "all-user-state-embedded",
  "databases": [
    {"database_id": "example"}
  ],
  "entries": [
    {"root": "inbox", "path": "", "kind": "directory"},
    {"root": "inbox", "path": "Draft.md", "kind": "file", "size": 4, "sha256": "9f86d081884c7d659a2feaa0c55ad0153bf4f1b2b0b822cd15d6c15b0f00a08", "mode": 384, "mtime_ns": 1700000000000000000},
    {"root": "database", "database_id": "example", "path": "Data/Items", "kind": "directory"},
    {"root": "database", "database_id": "example", "path": "Views", "kind": "directory"},
    {"root": "obsidian", "path": "", "kind": "directory"}
  ]
}
```

Top-level fields are exact. `specification` records the source and matches `foundation-N`; the v2 writer accepts `foundation-4`, `foundation-5`, and `foundation-6`. Restore supports `foundation-4`/`foundation-5` → `foundation-5` and `foundation-4`/`foundation-5`/`foundation-6` → `foundation-6`; downgrade transitions remain unsupported. `created_utc` is an informational ISO 8601 string. `databases` contains unique objects with one non-empty stable `database_id`. Source and destination folder names are intentionally absent.

Entry roots are:

| `root` | Optional identity | Logical `path` | Destination |
|---|---|---|---|
| `inbox` | none | relative to Inbox; `""` denotes the root | `app/Knowledge/Inbox/` |
| `database` | required `database_id` | `Data` or `Views` and descendants | current destination package resolved by identity |
| `obsidian` | none | relative to `.obsidian`; `""` denotes the root | `.obsidian/` |

Directory entries contain exactly `root`, optional `database_id`, `path`, and `kind`. File entries additionally contain `size`, `sha256`, `mode`, and `mtime_ns`. `size` is 0–32 GiB; `sha256` is 64 lowercase hexadecimal characters; `mode` is decimal 384 (`0600`) or 448 (`0700`), preserving only owner execute; `mtime_ns` is 0 through `2^63−1`. Existing identical files retain their existing metadata. Ownership, ACLs, xattrs/resource forks, directory timestamps, and hardlink relationships are not represented.

## Path and Inventory Rules

Logical paths are POSIX strings of at most 4096 UTF-8 bytes. Reject absolute paths, `.`/`..` or empty interior components, backslashes, Windows-reserved characters/device names, controls, surrogates, trailing dots/spaces, nested `.git` components, and duplicates or collisions under NFC normalization plus case folding. Every non-root entry has a declared directory parent; database `Data` and `Views` entries are logical roots and need no database-root entry.

The writer inventories exactly:

- `app/Knowledge/Inbox/**`;
- each reconstructable live database's complete `Data/**` and `Views/**` trees;
- `.obsidian/**`.

It does not inventory live `Database.md`, `Agents/**`, `Templates/**`, other managed package resources, framework surfaces, or unrelated root files. Each live database must resolve by `database_id` to exactly one installed blueprint/package or backup fails. Data and Views are traversed as preservation roots rather than filtered by declared collections or semantic validity.

The entire `.obsidian/` tree is included as encrypted inert content. In a Git checkout, any force-tracked `.obsidian` entry aborts backup; `.obsidian/` remains ignored. All v2 user-file bytes are embedded regardless of their Git status, and `kind: "git"` is invalid.

The writer omits exact generated directory names `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.venv`, and `node_modules`, and exact file names `.DS_Store`, `Thumbs.db`, and `Desktop.ini`. A symlink with an excluded-looking name still fails. Other ignore patterns do not select inventory. Symlinks and special files are always rejected.

## Version 2 Restore

After complete authentication and manifest/file verification, restore resolves every archived identity against the destination release. Exactly one installed package must exist. The blueprint folder name determines the current live folder; the source folder name is unknown and irrelevant. Restore stages and validates that current package, then maps logical Data and Views beneath it.

If a represented live database already exists, its non-Data/non-Views managed tree must be byte/structure/executable-bit equivalent to the currently materialized destination package. Otherwise restore fails before writes. Data and Views are conflict-checked as user state. New packages receive managed files and Data/Views directory scaffolding; archived user files supply their contents.

All existing byte-identical user files are skipped. Differing files, file/directory conflicts, unsafe paths, case/Unicode collisions, tracked Obsidian state, missing packages, and managed-package differences fail complete preflight. Destination-only files remain. Dry-run performs authentication, verification, package construction, identity resolution, and conflict preflight without durable writes. Restored Obsidian plugins, Agents, and other files are never executed.

Publication uses same-filesystem hardlinks and exclusive destination creation. Ordinary errors and Ctrl+C roll back only new files/directories from that invocation. Abrupt termination can leave complete additions; rerunning the same restore is idempotent. The operation is not a live filesystem snapshot or a globally atomic filesystem transaction.

## Legacy Version 1

Version 1 keeps its original meaning: `format: "shardbase-knowledge-backup"`, `scope: "app/Knowledge"`, `git_policy: "committed-tracked-files-excluded"`, and instance-relative `path` entries of kind `directory`, `file`, or `git`. It transfers the full historical Knowledge tree, including database contracts, Templates, Views, and Agents. Unchanged committed knowledge may be represented by payload-free Git references that must exist identically at the destination.

The reader supports the historical `foundation-3` → `foundation-3`/`foundation-4` and `foundation-4` → `foundation-4` transitions. It does not discard managed-looking v1 entries, reinterpret them as v2 roots, or cross the foundation-5 ownership boundary. The independent fixed v1 vector remains part of compatibility testing.

Future readers must explicitly retain each version or fail visibly. They must not silently normalize user state, guess package identity, merge differences, or infer schema migrations.
