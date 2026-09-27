# ShardBase CLI and Validation Tooling

This document describes the **current implementation** in `app/Scripts/`: how to run it, what it does, and what it does not yet do.

It does not define ShardBase architecture. Universal requirements come from [`../Docs/Shard System Specification.md`](../Docs/Shard%20System%20Specification.md); database-specific requirements come from the target database's root `Database.md`.

Current tooling targets System Specification `foundation-3` within the implementation scope described below.

## Runtime Setup

The current scripts require Python 3.10 or newer and the pinned PyYAML and cryptography dependencies in `requirements.txt`. These are tooling requirements, not universal ShardBase requirements. Existing installations should rerun the installer after updating to install new dependencies.

### Install the convenient command (macOS/Linux)

From the repository root:

```sh
python3 -B app/Scripts/install_cli.py
export PATH="$HOME/.local/bin:$PATH"
shardbase commands
```

The installer creates the Python environment at `~/.local/share/shardbase/venv` and the `shardbase` launcher at `~/.local/bin/shardbase`. Both live outside the project. It installs the pinned requirements with pip caching and dependency bytecode generation disabled. The launcher runs the checkout's source directly with `-B`; it does not copy knowledge or install build metadata into the vault.

Add the displayed PATH line to your shell configuration, such as `~/.zshrc`, if you want it available in new terminals. The installer does not edit shell configuration. If the launcher directory is already on PATH, no PATH change is needed.

Use `--runtime "/external/path/to/venv"` and `--bin-dir "/external/path/to/bin"` to choose other locations. The installer rejects paths inside this project, another identifiable ShardBase instance, or an Obsidian vault, including symlink paths that resolve there. Its temporary directory must also be external. Keep all custom runtime/cache locations outside any vault, including vaults without recognizable markers.

Rerunning setup with the same paths is supported. Existing unrelated directories or different launchers are refused instead of overwritten. If you move the checkout, review the old launcher and remove it deliberately or choose a different launcher directory before reinstalling.

The command defaults to the checkout used for installation, even when run from another directory. Use `--root "/path/to/instance"` with creation or validation to select another instance.

### Run without installing a launcher

Use an external environment on platforms without the POSIX launcher, or for development/testing. From the repository root:

```sh
shardbase_runtime="/tmp/shardbase-validator-venv"
python3 -B -m venv "$shardbase_runtime"
"$shardbase_runtime/bin/python" -B -m pip install --no-cache-dir --no-compile -r app/Scripts/requirements.txt
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py commands
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py create new
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py validate
"$shardbase_runtime/bin/python" -B -m unittest discover -s app/Scripts -p 'test_*.py' -v
```

These are POSIX shell examples; on Windows choose an external environment directory and use its `Scripts/python.exe`. Temporary environments can be removed by the operating system; use the installed external runtime for regular use.

Dependency installation may access the network. Creation, help, validation, backup, and restore operate locally and do not call external services. Help and command listing also work before dependencies are installed.

Use `-B` or `PYTHONDONTWRITEBYTECODE=1` for every Python runner that touches the project. Keep environments, dependencies, bytecode, caches, and test instances outside the project/vault. These settings prevent new bytecode but do not remove stale generated files already present.

## Command Reference

Run `shardbase commands` to see every available command in the terminal. Running `shardbase` without arguments shows the same list. This is the complete current command set:

| Command | Purpose |
|---|---|
| `shardbase create new` | Create an Inbox or database-intended note; prompt for omitted choices |
| `shardbase create new database` | Select a blueprint and create a new live database scaffold |
| `shardbase create new database --blueprint games` | Create the Games database without a selection prompt |
| `shardbase create` | Show the creation command group |
| `shardbase new` | Compatibility alias for note creation, with identical note options |
| `shardbase validate` | Read-only structural checks on all live databases in the installed instance |
| `shardbase validate "/path/to/database"` | Check one database root |
| `shardbase validate --root "/path/to/instance"` | Check all live databases in another instance |
| `shardbase backup [archive]` | Choose an output file/folder, then encrypt and verify local knowledge |
| `shardbase restore [archive]` | Authenticate and import a backup; prompt for the file when omitted |
| `shardbase restore archive --dry-run` | Verify a backup and check destination conflicts without writing knowledge |
| `shardbase commands` | List all commands, including the compatibility alias |
| `shardbase help` or `shardbase --help` | Show top-level help |
| `shardbase help create new` or `shardbase create new --help` | Show creation options |
| `shardbase help create new database` | Show database scaffolding options |
| `shardbase help validate` or `shardbase validate --help` | Show validation options |

`shardbase help <command>` and `<command> --help` use the same parser and stay aligned with the implemented options. The standalone validator script remains available for existing workflows; it accepts the same optional database path and `--root` selection.

## Encrypted Backup and Restore

These are manual CLI commands. They operate only on `app/Knowledge/`, including Inbox, database contracts, notes, attachments, and database-owned resources. Obsidian settings, framework files, and unrelated local files are outside scope. Nothing is uploaded, scheduled, or synchronized.

For a normal backup and restore into another existing ShardBase checkout:

```sh
shardbase backup "$HOME/knowledge.sbbackup"
shardbase restore "$HOME/knowledge.sbbackup" --root "/path/to/new/shardbase"
```

The first command prompts for a hidden passphrase and confirmation. The second prompts for the same passphrase, verifies the entire backup and destination, then imports the knowledge automatically. No decryption, extraction, file rearrangement, or post-import conversion commands are needed. Use a strong passphrase of several random words; creation requires at least 12 UTF-8 bytes. **ShardBase cannot recover a lost passphrase.**

With no output argument, `shardbase backup` prompts for a save location. Enter a new filename or an existing folder; choosing a folder generates a unique `.sbbackup` filename there. Press Enter to accept the suggested unique filename in `~/ShardBase Backups/`; that default folder is created if needed. An explicit output argument also accepts either a filename or an existing folder. For a custom filename, its parent directory must already exist. Output must be outside ShardBase instances and identifiable vaults. An existing backup is never replaced, and the command prints the resulting location.

`shardbase restore` prompts for the backup file to read when omitted. Use `--root "/path/to/instance"` to choose which existing ShardBase instance receives the restored knowledge; files retain their layout under that instance's `app/Knowledge/`. Both commands accept `--root`, defaulting to the checkout used for installation. For example, `shardbase backup "/Volumes/Archive/My Backups"` saves into that existing folder, and `shardbase restore "/Volumes/Archive/My Backups/chosen.sbbackup" --root "/path/to/new/shardbase"` imports that selected backup into the selected instance.

### Local Data and Git Exclusion

The commands never contact GitHub. For offline operation, **unchanged committed Git-tracked knowledge is the proxy for data already hosted in Git**. Its bytes are omitted, while encrypted references record the paths, sizes, and SHA-256 digests restore must find in the destination checkout. Local commits are not proof of a push; users who deliberately track knowledge must ensure that committed data is available in the target checkout. The CLI does not claim to verify remote availability.

Staged or modified tracked knowledge blocks the operation so local changes cannot be silently omitted. Index flags such as `assume-unchanged` do not bypass this check. Symlink/submodule entries and nested repositories are refused. Git clean/text filters are not executed; transformed working copies of tracked knowledge also block the check. Git is required for an instance with root `.git`. A downloaded/copied instance without root `.git` includes all ordinary knowledge because it has no local tracking information. Framework data is excluded in either case by the knowledge boundary.

Ignored knowledge is included. A small fixed list of generated caches and OS files is excluded; the exact list is in the [format contract](BACKUP_FORMAT.md#path-and-inventory-rules). Other `.gitignore` patterns do not remove user data from backups. Symlinks and special files are refused instead of followed or silently skipped.

### Restoration and Version Updates

Restore preserves bytes, filenames, directory layout, empty directories, and file modification times. It preserves the owner's executable bit while limiting newly restored files to owner access. It does not rewrite metadata, links, IDs, templates, or database contracts. Existing byte-identical files are skipped; differing files and file/directory conflicts stop the entire preflight before any knowledge is written. Destination-only content is preserved. There is no destructive overwrite, merge-resolution, or snapshot-mirroring mode.

The intended update workflow is to back up the old instance and restore into a fresh newer checkout using the two commands above. Do not create replacement databases in the fresh checkout first; restore brings the existing databases and their contracts with it. The target framework and CLI must already be installed, as for all other CLI operations.

Format v1 supports unchanged `foundation-3` data transfer into another `foundation-3` checkout, including newer releases that keep that specification. Restore refuses an unsupported specification transition before writing. It is a temporary **data transfer** mechanism for version updates; it does not implement historical or future schema migrations. The source's declared specification is recorded, not inferred from individual notes. An older or malformed note can therefore be recovered unchanged; successful restore is not a claim of structural or database-semantic validity. The read-only `shardbase validate` remains available for a separate conformance review, but is not required to complete transfer.

### Verification, Password Input, and Failures

Backup streams encryption and then uses the actual restore reader to decrypt, authenticate, and hash-check the result before publishing it. Restore authenticates the entire envelope, validates its inventory, verifies each file, checks compatibility and excluded Git dependencies, and preflights conflicts before publishing any knowledge. Encryption uses AES-256-GCM and scrypt; filenames and manifest metadata are also encrypted. The [versioned format contract](BACKUP_FORMAT.md) defines the complete interoperable file layout.

To inspect a restore without changing knowledge:

```sh
shardbase restore "$HOME/knowledge.sbbackup" --root "/path/to/new/shardbase" --dry-run
```

For manually invoked noninteractive use, both commands accept `--password-file "/external/path/passphrase"`. The UTF-8 file must be owner-only on POSIX systems, for example mode `0600`; one terminal LF/CRLF is accepted. Keep it outside knowledge and separate from the backup. No plaintext password command-line option or environment variable is supported. Without a password file, an unavailable secure terminal causes a clean error instead of falling back to an echoed prompt.

Close editors and other writers during backup/restore. Backup checks for changes during inventory/copy and fails if observed, but does not provide a live filesystem snapshot. Restore assumes a stable local filesystem. Each imported file is published complete with exclusive hardlink creation; files are never partially written in knowledge. Ordinary errors and Ctrl+C attempt to roll back only new additions. Abrupt termination can leave some complete additions; rerun the same restore to finish. This is not a globally atomic multi-file transaction, and rollback cannot guarantee cleanup when the filesystem itself fails.

Temporary plaintext is held in owner-private directories outside the vault and cleaned on ordinary completion/error. Abrupt termination may leave an external `shardbase-transfer-*` directory; backup interruptions may also leave an encrypted `.shardbase-backup-*.partial` next to the intended output. There is no secure-deletion guarantee for temporary plaintext, filesystem snapshots, or OS swap. Use an encrypted local filesystem where those at-rest threats matter.

Restore staging must support hardlinks and reside on the same filesystem as its destination. The default is the system temporary directory. For a target on another volume, pass `--staging-dir "/external/directory/on/target-volume"`; this existing directory must be outside every vault. No manual copying or extraction is needed. Backup accepts the same option for verification staging but does not require staging to share the source filesystem. Backups themselves may be stored on another volume, provided that output filesystem supports hardlinks for atomic publication.

Format-v1 limits are a 32 GiB uncompressed payload, a 16 MiB manifest, 100,000 inventory entries, and portable paths. Key derivation needs approximately 128 MiB of RAM; file I/O is streamed in 1 MiB blocks. Allow external staging space for approximately twice the uncompressed backup size during verification/restore. No compression or deduplication is performed. ACLs, ownership, xattrs/resource forks, directory timestamps, and hardlink relationships are not preserved. These limits are checked and failures are reported; they are not silently approximated.

## Database Creation

After downloading the repository and installing the external CLI runtime, run:

```sh
shardbase create new database
```

The command offers a blueprint picker even when only one option is available. Currently the repository supplies **Games**. It discovers direct subfolders of `app/Blueprints/` with a root `Database.md`, displaying `database_name` and using `database_id` for selection. Adding another blueprint package makes it available without changing the CLI. Duplicate blueprint identities and malformed manifests require review; directories without a manifest are not offered.

For unattended use or a different existing instance:

```sh
shardbase create new database --blueprint games
shardbase create new database --blueprint games --root "/path/to/instance"
shardbase create new database --help
```

`--root` selects both the instance's blueprint source and its knowledge destination. The instance must already contain `app/`; this command bootstraps a downloaded/copied instance rather than cloning the repository or installing dependencies. `--blueprint` is the manifest's ID, not an arbitrary path. Note-creation flags do not apply to this subcommand.

The selected blueprint folder is copied to `app/Knowledge/Databases/<blueprint folder>/`. For Games this is `app/Knowledge/Databases/Games/`. The operation preserves the manifest identity and supplied resources, including declared collections, attachment folders, Views, optional Templates and Agents, packaged `.gitkeep` files, and empty directories. It creates `app/Knowledge/Inbox/` if missing. It does not invent notes beyond the selected package, execute copied scripts/agents, or modify editor settings.

Relative inline Markdown links from the blueprint to framework `app/Docs/`, `app/Scripts/`, and `app/Registry/` resources are adjusted in the new copy to account for the deeper destination. Local database links, web URLs, wikilinks, and fenced/inline code remain unchanged. Blueprint authors should use URL-encoded inline Markdown links for framework references; reference-style and other custom link conventions are not automatically relocated.

Before any live database write, the command checks the source package, copies it into an external temporary instance, adjusts supported links, and runs the existing structural validator. Invalid scaffolding is reported before creating the live destination. Only active/draft blueprints are accepted. Symlinks, special files, and recognized runtime/build artifacts in the package are refused. The temporary directory must be outside the project and identifiable knowledge vaults.

An existing destination, including an empty folder or a case/Unicode-equivalent name, is refused. A live database with the same `database_id` under a different folder is also refused. Existing incomplete or unreadable database manifests block the identity check rather than being guessed through. There is no overwrite, merge, automatic upgrade, or cleanup mode.

The final copy uses exclusive creation. If an I/O error or interruption occurs during that copy, an incomplete new folder can remain; inspect it before retrying. The command reports copy errors and does not delete or overwrite the partial state. As with other creation operations, the filesystem is assumed stable during the operation; the copy is not a transaction.

Once created, the database is user-owned. Future blueprint changes do not synchronize into it. Review its `Database.md`, then run `shardbase create new` to prepare a note for that database. Structural validation is not a proof of arbitrary database-semantic rules or complete Foundation compliance.

## Note Creation

ShardBase recommends the CLI for new notes intended for permanent database use. Temporary notes can be created directly in a Markdown editor (preferably Obsidian) or filesystem, with `app/Knowledge/Inbox/` configured as the editor's default new-note location. Editor captures need no structural metadata.

Run:

```sh
shardbase create new
```

The command asks for a title, Core/Shard/Pebble type, optional alias, and **note intent**:

| Intent | Preparation | Save location |
|---|---|---|
| Inbox | Existing Games draft scaffold; metadata remains provisional and `id` may be blank | `app/Knowledge/Inbox/<portable title>.md` |
| Database-intended | Selected database/template, fresh ID, canonical filename, and optional parent-derived lineage | `app/Knowledge/Inbox/<canonical filename>.md` |

Both choices create YAML and one title H1. Neither creates canonical database state, moves files, or creates a `Staged/` folder. Review the note and move it manually through your editor or filesystem when ready.

For unattended use, supply the choices needed by your target. These examples use synthetic titles and aliases:

```sh
shardbase create new --title "Example Game" --type core --alias "" --intent database --database games
shardbase create new --title "Example Topic" --type shard --alias "Topic Reference" --intent database --database games --parent "Example Game"
shardbase create new --title "Example Detail" --type pebble --alias "" --intent database --database games --parent ""
shardbase create new --title "Temporary idea" --type core --alias "" --intent inbox
shardbase create new --help
```

The second example assumes the Core has already been moved into the live Games database. The third deliberately defers lineage; it requires completion before promotion. Missing choices are prompted. Use `--parent ""` to explicitly defer parent selection, `--template "Filename.md"` when several templates match, `--collection "Name"` when several collections exist, and `--pool "Value"` when neither a template nor a parent supplies the Pool.

The default instance is the checkout containing the script. Use `shardbase create new --root "/path/to/instance"` to target another existing ShardBase instance containing `app/`.

### Database and Template Selection

Database-intended creation discovers direct children of `app/Knowledge/Databases/` and `app/Blueprints/` through their root `Database.md`. Select by the manifest's `database_id`, not the folder name. Live contracts take precedence over blueprints with the same ID. Duplicate identities within either group and malformed manifests are reported; directories without manifests are not selectable. Only active/draft version-1 manifests with declared, existing collections are accepted for preparation.

The CLI selects Markdown templates directly inside the chosen source's `Templates/` by their YAML `type`. One matching template is automatic; multiple matches require a choice. No matching template means a universal scaffold with an explicit Pool or selected parent. A live database never falls back to a blueprint's templates. Note preparation never creates or synchronizes a live database; use the separate database creation command deliberately to bootstrap one.

Template YAML supplies semantic defaults, aliases, and tags. Template bodies are ignored and no template code is executed. New note identity and lineage are generated from the user's selections, so template IDs, self-links, parent links, and lifecycle status are not copied. New database-intended notes start as `status: draft`; skipping the alias preserves the template's alias default. Optional facts absent from the template are not invented.

The CLI does not interpret semantic schemas or Pool vocabularies from prose. Review template defaults and any manually entered Pool against the selected `Database.md`. Additional databases work without hard-coded Games field names, but custom display-title conventions and more complex template systems need their own tooling support.

### Prepared Filenames and Metadata

Core filenames remain title-based, for example `Example Game.md`. Shard and Pebble filenames use the local title and generated ID, for example `Example Topic - 2gmcy7r7dr.md`. Every database-intended note, including a Core, receives a fresh foundation-3 ID. The opening H1 retains the human-facing title. Titles whose trailing Markdown heading markers would change their parsed H1 are rejected for database preparation.

For example, after selecting an existing Core as parent:

```markdown
---
type: shard
pool: Games
core: '[[Example Game]]'
parent_note: '[[Example Game]]'
status: draft
aliases:
- Topic Reference
id: 2gmcy7r7dr
tags:
---
# Example Topic

```

The ID above is illustrative; actual IDs are random. IDs are checked against the selected source's discovered notes and parseable YAML in existing Inbox Markdown files, including user-organized subfolders. A collision generates another token. Plain or unfinished Inbox YAML is allowed and does not participate in ID checking. Canonical filename collisions in the selected source and output filename collisions in Inbox are reported without overwrite or automatic numbering.

For Shards and Pebbles, select an existing live Core or Shard through the picker or `--parent`. The CLI resolves its YAML lineage, inherits the root Core's Pool, and fills `core` and `parent_note`. Parent use requires the selected database to pass the existing structural validator. Pebbles cannot be parents. Collection and workspace placement follow the selected lineage, and conflicting explicit Pool/collection choices are refused.

If no parent exists yet, or you choose **Decide later**, `core` and `parent_note` remain blank. A filename and ID alone do not make such a draft ready for promotion. Move a prepared Core into its live database before selecting it as another note's parent. Inbox notes and blueprint sample notes are not parent candidates.

For live targets, the CLI prints the suggested manual move path. Blueprint selection prints a reminder to materialize a live database first. Intent/target selection is not added as an undocumented semantic YAML field; selecting a target does not create database membership while the file is in Inbox.

### Inbox Capture Compatibility

`--intent inbox` retains the previous Games draft behavior: select the Core, Shard, or Pebble template from the single live `database_id: games` owner, or from the Games blueprint when no live owner exists. A missing live template is reported without blueprint fallback. Universal draft defaults fill missing fields; other template metadata remains provisional and may be invalid. Core placeholders become a provisional self-link; unresolved supporting placeholders become blank. No IDs are generated and existing canonical notes are not inspected for this capture path.

This legacy scaffold does not limit plain editor-created Inbox notes to Games or require any Inbox note to have structural metadata. Use database intent to prepare notes for other selected databases.

## Manual Promotion

There is currently **no automatic note promotion command, direct canonical note creation command, or filesystem watcher**. Database scaffolding is a separate blueprint-copy operation.

Before moving a note, review ownership, collection, Pool, structural role, lineage, semantic metadata, and placement against the System Specification and destination `Database.md`. Database-intended creation has already prepared the filename and ID; preserve that ID. An ordinary Inbox capture may still need both. Complete unresolved lineage before moving supporting notes.

Move the file into the appropriate declared collection or existing Core workspace using your editor or filesystem, then run the validator. A manual move does not trigger validation. Recheck ID uniqueness and collisions because the database or other pending notes may have changed since preparation. If you edit a title, update its filename and dependent links while retaining the ID.

The current validator checks its implemented structural scope; database semantics still need separate review. Preparation does not claim to validate all manifest/body requirements or arbitrary semantic defaults. Fully validated canonical creation/promotion remains future work.

## Read-Only Validator

Run all live databases:

```sh
shardbase validate
```

To inspect one database, append its root path. Use `--root "/path/to/instance"` to discover all databases in another instance; a missing instance root is an error, while a valid empty instance succeeds. The path must be a direct child of an `app/Knowledge/Databases/` boundary, including for temporary test copies.

The validator is read-only. It does not write, rename, repair, migrate, or normalize canonical files.

### Implemented Scope

The validator currently checks:

- discovery of direct database roots, including incomplete roots missing `Database.md`;
- UTF-8 YAML frontmatter using a safe PyYAML loader, including duplicate-key/malformed/unsupported-tag diagnostics;
- manifest field/value/shape requirements and required manifest body headings;
- declared data collections, root `Attachments/`, and `Views/`;
- traversal, absolute-path, containment, and relevant symlink boundaries before scanning;
- structural discovery at collection roots and one Core-workspace level;
- exclusion of attachment subtrees and root `Agents/`, `Templates/`, and `Views/` from structural discovery;
- misplaced root Markdown files that declare structural metadata;
- required structural fields and common fields `aliases`, `id`, and `tags`, including foundation-3 note-ID format and database-wide uniqueness;
- same-database Core/parent resolution, Core self-reference, permitted parent types, Pool consistency, cycles, self-parenting, parent-chain root consistency, and active descendants beneath archived ancestors;
- Core-workspace naming/membership and split-lineage placement;
- portable Core filenames, supporting local-title + opaque-ID filenames, actual duplicate stems, expected-filename collisions, and duplicate note IDs;
- opening H1, incremental top-level ATX heading depth, and exactly one blank line after headings outside fenced code blocks.

Structural wikilinks resolve only against discovered notes in the selected database. Supported target forms include unique stems, `.md` filenames, database-relative paths, and repository/vault-root-relative paths beginning with `app/Knowledge/Databases/`; supported path forms may omit `.md`. Aliases and heading fragments do not change the selected structural note. Cross-database structural targets and arbitrary traversal are not followed.

### Naming Assumption

The current filename checker assumes:

- a Core's opening H1 is its canonical entity name and derives `Portable Core Name.md`;
- a Shard or Pebble's opening H1 is its canonical local title and derives `Portable Local Title - Opaque ID.md`;
- canonical IDs match the foundation-3 10-character lowercase Crockford Base32 format and are unique within the database.

The validator derives structural lineage only from YAML references. It does not parse ancestry from filenames and does not resolve structural wikilinks through aliases or note IDs. A local title may itself contain the literal delimiter ` - `; the required final ID suffix remains unambiguous because the expected filename is derived from metadata rather than inferred by splitting an existing filename.

A database that intentionally uses another documented display-title convention requires a database-aware naming adapter before the validator's filename findings can be treated as complete conformance findings.

For the normative portable normalization, ID contract, and filename algorithm, use the System Specification rather than this implementation guide.

### Not Yet Implemented Generically

The validator does **not** currently determine or enforce:

- database semantic schema fields, shapes, bounded values, or applicability from `Database.md`;
- database Pool vocabulary from prose;
- whether a note genuinely earns materialization versus remaining a heading;
- duplicate/overlapping semantic content beyond deterministic structural collisions;
- attachment references, missing attachments, or attachment-orphan audits;
- arbitrary database-local resource contracts;
- complete Markdown linting;
- historical System Specification version detection;
- migrations;
- canonical draft promotion or canonical note creation.

A successful run therefore means the implemented structural checks passed. It is not proof of complete database-semantic validity or Foundation completion.

## Results

Exit status:

- `0` — command succeeded, or validation found no issues in its implemented scope, including an empty instance with no database candidates;
- `1` — validation/discovery issues or an operation error, depending on command;
- `2` — invalid CLI command syntax for `shardbase.py`;
- `130` — command cancelled or ended by input termination; recovery behavior depends on the operation as described in its section.

Validator diagnostics include a path, stable issue code, and message. Consumers should use issue codes rather than parse human-readable messages or rely on issue counts.

YAML errors report location without echoing source content.

## File Safety

Note creation uses a non-empty single-line title, portable output filename, output-boundary/symlink checks, and exclusive creation. It never overwrites an existing output path or silently numbers collisions.

Inbox capture retains its permissive draft behavior. Database preparation additionally reads declared collection roots and one workspace level for IDs and naming collisions, excluding attachments; it validates existing structural state when a parent is selected. Symlinks in inspected creation paths are rejected, and malformed canonical YAML blocks preparation rather than hiding unknown identities. These checks do not prove database-semantic validity or materialization judgment.

The implementation assumes a stable local filesystem during an operation and is not transactional. An interrupted draft write may leave a partial new draft; a rerun will refuse to overwrite it. Error recovery never deletes existing user knowledge.

Backup/restore use separate authenticated staging and publication rules described under [Encrypted Backup and Restore](#encrypted-backup-and-restore).

## Tests and Fixtures

Tests use temporary instances outside the vault. Keep `TMPDIR` or its platform equivalent outside the vault when customizing it.

The sanitized fixtures and tests prove the current structural validation behavior, including valid/invalid manifests, YAML shapes, common note metadata, lineage failures, workspace placement, filename normalization/collisions, boundary escapes, and Markdown heading checks.

Database-preparation tests also prove database/template selection, ID generation and collision retries, parent-derived lineage, workspace placement, preservation, cancellation, and a subprocess-driven Core → Shard → Pebble workflow whose files pass the validator after manual movement without metadata or filename edits. These proofs use disposable instances and synthetic examples, never live user knowledge. Command and installer tests also cover grouped/legacy creation, dependency-free help, validation routing, external runtime boundaries, launcher quoting, and preservation of existing files. Database-bootstrap tests cover blueprint discovery, external staging and structural validation, resource/link preservation, existing-database refusal, unsafe source boundaries, and bootstrap-to-note-creation proof. Semantic-schema, attachment-reference, fragmentation/materialization, and complete lifecycle proof fixtures remain future work.

Backup/restore tests use only synthetic external instances. They cover a two-command subprocess round trip, binary attachments, empty directories, metadata, idempotence, Git exclusions, changed tracked data, independent AES-GCM decoding, wrong passphrases, tampering/truncation, authenticated malformed inventories, unsafe paths, collisions, source changes, interrupted publication, rollback, and dependency-free command help.

## Compatibility

The preferred spelling for notes is `shardbase create new`; `shardbase new` remains an equivalent note-creation alias. Both prompt for intent. Existing unattended commands should add `--intent inbox` to retain their prior capture behavior, or use `--intent database --database <database_id>` for preparation. `--destination` remains unsupported because intent does not change the save location. Both paths save directly to Inbox. Existing files, including `Inbox/Staged/` captures and blank IDs in older drafts, remain untouched; no knowledge migration is performed. Canonical validity and the foundation-3 schema are unchanged.

The validator checks the current `foundation-3` contract in its documented scope. `manifest_version: 1` identifies only the manifest schema and does not identify the System Specification version under which a database was authored.

The validator does not migrate older state. For the recorded `foundation-1`, `foundation-2`, and `foundation-3` compatibility boundaries and preservation-oriented transitions, use the System Specification.

## Blueprint Scaffolding

`app/Blueprints/Games/` includes tracked empty-directory scaffolding for `Data/Game/Attachments/` and `Views/`, plus draft templates and the optional Vera Agent resource. Packaging placeholders are not semantic knowledge.

Copying a blueprint materializes a starting database package. Later blueprint changes never silently update a live database.
