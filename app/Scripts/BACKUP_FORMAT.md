# ShardBase Knowledge Backup Format

Format version: `1`

This is the wire contract implemented by `backup_restore.py`, not a change to the System Specification or database schemas. The conventional extension is `.sbbackup`; readers identify the header, not the extension. Backup and restore are offline, manual CLI operations. Usage and operational limits are in [README.md](README.md#encrypted-backup-and-restore).

## Envelope

All integers in the envelope and payload framing are unsigned, big-endian. The complete file is:

```text
40-byte header || ciphertext || 16-byte authentication tag
```

| Offset | Length | Meaning |
|---:|---:|---|
| 0 | 8 | Magic bytes `53 48 41 52 44 42 4b 00` (`SHARDBK` followed by NUL) |
| 8 | 4 | Format version, integer `1` |
| 12 | 16 | Cryptographically random scrypt salt |
| 28 | 12 | Cryptographically random AES-GCM nonce |
| 40 | variable | Encrypted payload, at most 32 GiB |
| EOF − 16 | 16 | Full AES-GCM authentication tag |

Derive a 32-byte key with scrypt: `N=131072`, `r=8`, `p=1`, using the exact UTF-8 passphrase bytes and the header salt. These fixed parameters consume approximately 128 MiB for key derivation; the file cannot request higher costs. No Unicode normalization, whitespace stripping, or passphrase storage is performed. A password file may end in one LF or CRLF, which is removed. Embedded CR/LF is rejected. Creation requires 12–4096 bytes; readers accept 1–4096 bytes. Passphrases remain vulnerable to offline guessing if weak.

Encrypt using AES-256-GCM with the header nonce and **all 40 header bytes as authenticated additional data**. Generate a fresh salt and nonce for every backup using the operating system CSPRNG. Use the full 128-bit tag. The 32 GiB plaintext cap stays below GCM's per-message limit. Changing algorithms, KDF parameters, framing, or field meanings requires a new format version. Unknown versions are refused before key derivation.

The implementation uses the `cryptography` library's [GCM construction](https://cryptography.io/en/50.0.1/hazmat/primitives/symmetric-encryption/#cryptography.hazmat.primitives.ciphers.modes.GCM) and [scrypt KDF](https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#scrypt). Decryption streams to an owner-private external temporary directory, and **no manifest parsing, path interpretation, or destination write occurs before authentication succeeds**. The complete envelope, including truncation and appended data, is authenticated. Metadata and filenames are encrypted; envelope version and total size remain visible.

## Plaintext Payload

```text
8-byte manifest byte length || UTF-8 JSON manifest || file bytes in manifest order
```

There is no compression, archive extraction, ZIP password scheme, pickle, executable deserialization, or external encryption executable. The manifest length must be 1–16 MiB. The manifest contains at most 100,000 entries, including directories and excluded Git references. File bytes are concatenated only for entries whose `kind` is `file`, in entry-array order; their `size` fields give exact boundaries. Zero-length files consume zero bytes. Trailing or missing payload bytes are errors.

Example manifest, with a synthetic four-byte file containing `test`:

```json
{
  "format": "shardbase-knowledge-backup",
  "version": 1,
  "specification": "foundation-3",
  "created_utc": "2026-09-26T12:00:00+00:00",
  "scope": "app/Knowledge",
  "git_policy": "committed-tracked-files-excluded",
  "entries": [
    {"path": "app/Knowledge", "kind": "directory"},
    {"path": "app/Knowledge/Inbox", "kind": "directory"},
    {
      "path": "app/Knowledge/Inbox/Example.txt",
      "kind": "file",
      "size": 4,
      "sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
      "mode": 384,
      "mtime_ns": 1700000000000000000
    }
  ]
}
```

The writer records its source instance's declared System Specification version and currently accepts `foundation-3` only. This is provenance, not proof that individual notes conform to that specification. The reader currently supports unchanged `foundation-3` → `foundation-3` transfer only. A different framework checkout/release with the same specification is compatible. Historical schema conversion and unknown future specifications require explicit migration support; both commands reject them.

Required fields are exact: unknown fields and duplicate JSON keys are rejected. Top-level `version` is integer `1`; `format`, `scope`, and `git_policy` have the exact values above. `specification` has the form `foundation-N` with a positive integer N. `created_utc` is a string written as an ISO 8601 UTC timestamp and is informational.

Entry fields:

| Kind | Fields | Interpretation |
|---|---|---|
| `directory` | `path`, `kind` | Preserve a directory, including an empty one |
| `file` | `path`, `kind`, `size`, `sha256`, `mode`, `mtime_ns` | Restore the next `size` payload bytes and verify their SHA-256 |
| `git` | Same fields as `file` | No payload bytes; require an existing destination file with the recorded size and SHA-256 |

`size` is an integer from 0 through 32 GiB. `sha256` is 64 lowercase hexadecimal characters. `mode` is decimal 384 (`0600`) or 448 (`0700`), preserving only the owner's executable bit; it never grants group/world access or privileged bits. `mtime_ns` is an integer from 0 through `2^63−1`, in nanoseconds since the Unix epoch. Ownership, ACLs, xattrs/resource forks, hardlink relationships, directory timestamps, and other filesystem metadata are not represented. Existing identical files retain their existing metadata. Files restored on less precise filesystems may have rounded timestamps.

## Path and Inventory Rules

Paths are instance-relative POSIX strings, limited to 4096 UTF-8 bytes. Every path is either `app/Knowledge` or a descendant. The knowledge root, when present, must be a directory; every other entry must have a declared directory parent. Entry ordering has no ancestry meaning. An empty list represents an absent knowledge directory.

Reject absolute paths, empty/`.`/`..` components, backslashes, Windows-reserved characters and device names, control characters, trailing dots/spaces, surrogate characters, duplicate paths, and paths equivalent under NFC normalization plus case folding. Nested `.git` components, symlinks, and special files are unsupported. Readers never use manifest paths for external staging filenames; staging uses entry indexes.

The writer includes ordinary files and directories within knowledge, including Inbox drafts, database contracts, attachments, Templates, Views, and Agents. It omits these exact generated directory names: `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.venv`, `node_modules`; and these exact file names: `.DS_Store`, `Thumbs.db`, `Desktop.ini`. A symlink with an otherwise excluded name still causes failure. No other ignore pattern is used to select private files. Framework surfaces, `.obsidian/`, and unrelated local files are outside scope.

Within a Git checkout, unchanged committed tracked knowledge becomes `git` references. The writer checks the index against `HEAD` and raw working-file bytes against their committed Git blob IDs; staged changes and local edits are errors, including edits hidden by index flags. Git filters are not run, so a filter/line-ending-converted tracked file also requires resolution. Ignored private knowledge remains included. Git submodules/nested repositories are not traversed. A copied/downloaded instance with no root `.git` includes all in-scope files, because there is no local tracking information. The CLI does not contact GitHub or prove that local commits have been pushed.

## Reader Safety and Compatibility

Readers authenticate the complete envelope, enforce manifest and payload bounds, validate the complete inventory, hash every included file, check specification compatibility, verify excluded Git dependencies, and preflight **all** destination conflicts before creating knowledge. Restore is additive: it skips byte-identical files and refuses differing files, file/directory conflicts, unsafe paths, and equivalent-name collisions. It neither deletes destination-only files nor overwrites existing ones. It is a recovery/transfer operation, not a schema validator or a destructive snapshot mirror.

Publication uses same-filesystem hardlinks with exclusive destination creation. Each published file is complete. Ordinary failures and Ctrl+C trigger best-effort rollback of only files/directories created by the current restore. Abrupt process termination can leave a subset of complete additions; running the same restore again recognizes them and completes the import. The multi-file operation is not globally atomic. Keep the source and destination idle during transfer; this is not a live filesystem snapshot or protection against hostile concurrent filesystem changes.

Future readers must explicitly retain v1 support or fail visibly. They must not reinterpret these fields, silently normalize knowledge, guess a schema migration, or require a user to extract/decrypt/rearrange backup contents manually.
