# ShardBase CLI and Validation Tooling

This document describes the **current implementation** in `app/Scripts/`: how to run it, what it does, and what it does not yet do.

It does not define ShardBase architecture. Universal requirements come from [`../Docs/Shard System Specification.md`](../Docs/Shard%20System%20Specification.md); database-specific requirements come from the target database's root `Database.md`.

Current tooling targets System Specification `foundation-4`, retaining foundation-3 naming within the implementation scope described below.

## Runtime Setup

The current scripts require Python 3.10 or newer and the pinned PyYAML and cryptography dependencies in `requirements.txt`. These are tooling requirements, not universal ShardBase requirements. Existing installations should rerun the installer after updating to install new dependencies.

### Bootstrap a private instance (macOS/Linux/Windows)

Download and extract the repository ZIP, then open a terminal in its root. Git and existing knowledge are not required:

```sh
python bootstrap.py
```

Use `python3 bootstrap.py` on macOS/Linux if needed, or `py bootstrap.py` on Windows. Python 3.10+ is required, with no fixed upper version limit. Bootstrap checks its own folder for framework files before preparing anything. A root `.git` file or directory is reported as a Git-managed/development instance; bootstrap never runs Git or checks enclosing repositories.

| Platform | External runtime | External launcher |
|---|---|---|
| macOS/Linux | `~/.local/share/shardbase/venv` | `~/.local/bin/shardbase` |
| Windows | `%LOCALAPPDATA%\ShardBase\venv` | `%LOCALAPPDATA%\ShardBase\bin\shardbase.cmd` |
| Windows without `LOCALAPPDATA` | `~/AppData/Local/ShardBase/venv` | `~/AppData/Local/ShardBase/bin/shardbase.cmd` |

Use `--runtime "/external/path/to/venv"` and `--bin-dir "/external/path/to/bin"` for custom locations; `--help` lists these options. Runtime, launcher, and temporary paths must resolve outside this instance, other identifiable ShardBase instances, and Obsidian vaults. Keep custom locations outside vaults without recognizable markers too.

Bootstrap creates or reuses an external venv and verifies its interpreter can run Python 3.10+. An invalid, unsupported, or partially created runtime is preserved and setup fails; review it yourself or choose another `--runtime`. Rerunning a valid runtime reinstalls/repairs pinned dependencies.

Dependency installation may access configured Python package indexes/network resources. Pip runs with `--isolated`, `--no-cache-dir`, `--no-compile`, and `--disable-pip-version-check`; bytecode is disabled. Bootstrap performs no release lookup, telemetry, self-update, framework download, or knowledge synchronization.

Launchers run the selected instance's source by absolute path with `-B`, preserving caller arguments. Reruns leave identical launchers unchanged. A complete recognized generated launcher (version 1, or the exact previous POSIX format) can be retargeted to a fresh ZIP after dependencies install successfully. A marker alone does not establish ownership. Unrelated or edited files, unknown formats, symlinks, and non-regular paths are refused and preserved; choose another `--bin-dir` or review the existing file.

Ownership is checked before installation and immediately before publication. New launchers use no-clobber publication; replacing an existing managed launcher is atomic but assumes no concurrent edits in the final check-to-replace interval. Avoid simultaneous installers or edits of the same launcher. Filesystems must support hard links for first publication; failures leave competing files intact.

Bootstrap invokes the external interpreter directly to check `shardbase.py commands`, independently of PATH. A failed check fails setup. No database, Inbox, or note is created or inspected. After success, run `shardbase commands`, then `shardbase create new database` when ready. `shardbase init` and `shardbase doctor` remain deferred.

PATH is never changed automatically. If needed, bootstrap prints the exact launcher directory and a current-session POSIX shell or PowerShell command. Persistent PATH/profile configuration remains your choice. The launcher selects the instance used for installation even from another working directory; creation/validation commands also support `--root "/path/to/instance"`.

The lower-level compatibility entry point remains available with the same overrides and shared installation behavior:

```sh
python -B app/Scripts/install_cli.py --runtime "/external/path/to/venv" --bin-dir "/external/path/to/bin"
```

### Run without installing a launcher

For development/testing, you can prepare an external environment directly. From the repository root:

```sh
shardbase_runtime="/tmp/shardbase-validator-venv"
python3 -B -m venv "$shardbase_runtime"
"$shardbase_runtime/bin/python" -B -m pip install --no-cache-dir --no-compile -r app/Scripts/requirements.txt
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py commands
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py create new
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py validate
"$shardbase_runtime/bin/python" -B -m unittest discover -s tests -p 'test_*.py' -v
```

These are POSIX shell examples; on Windows choose an external environment directory and use its `Scripts/python.exe`. Temporary environments can be removed by the operating system; use the installed external runtime for regular use.

Dependency installation may access the network. Creation, help, validation, backup, and restore operate locally and do not call external services. Help and command listing also work before dependencies are installed.

Use `-B` or `PYTHONDONTWRITEBYTECODE=1` for every Python runner that touches the project. Keep environments, dependencies, bytecode, caches, and test instances outside the project/vault. These settings prevent new bytecode but do not remove stale generated files already present.

## Repository Development Lint

Repository development requires Python 3.10 or newer, recorded in the root `pyproject.toml`. Use an activated external virtual environment, such as the one created above. From the repository root:

```sh
export PYTHONDONTWRITEBYTECODE=1
export PIP_NO_CACHE_DIR=1
export PIP_NO_COMPILE=1
export RUFF_CACHE_DIR="${TMPDIR:-/tmp}/shardbase-ruff-cache"
python -m pip install -r requirements-dev.txt
python -m ruff check .
```

Keep any custom cache path outside the project/vault. The root `requirements-dev.txt` pins development-only Ruff; runtime dependencies remain in `app/Scripts/requirements.txt` and are installed separately as described above.

Ruff targets Python 3.10 and checks `E4`, `E7`, `E9`, `F`, and `I` (fundamental errors, Pyflakes checks, and import ordering). Repository-owned Python is linted, with private `app/Knowledge/` and synthetic `tests/fixtures/` excluded from traversal. This is a lint-only workflow; no formatter or Python packaging/build system is configured.

## Command Reference

Run `shardbase commands` to see every available command in the terminal. Running `shardbase` without arguments shows the same list. This is the complete current command set:

| Command | Purpose |
|---|---|
| `shardbase create new` | Create an Inbox capture or canonical database note; prompt for omitted choices |
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

Format v1 supports unchanged `foundation-3` → `foundation-3`/`foundation-4` and `foundation-4` → `foundation-4` transfer. The archive format is unchanged; downgrades are refused. Restore refuses an unsupported specification transition before writing. It is a temporary **data transfer** mechanism for version updates; it does not implement historical or future schema migrations. The source's declared specification is recorded, not inferred from individual notes. An older or malformed note can therefore be recovered unchanged; successful restore is not a claim of structural or database-semantic validity. The read-only `shardbase validate` remains available for a separate conformance review, but is not required to complete transfer.

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

Once created, the database is user-owned. Future blueprint changes do not synchronize into it. Review its `Database.md`, then run `shardbase create new` to create a canonical note directly in that database. Structural validation is not a proof of arbitrary database-semantic rules or complete Foundation compliance.

## Note Creation

Run `shardbase create new` to choose a title, Core/Shard/Pebble type, optional alias, and intent. Both intents create YAML and a title H1; body development remains separate.

| Intent | Behavior | Save location |
|---|---|---|
| Inbox | Pre-structural Games draft scaffold; metadata remains provisional | `app/Knowledge/Inbox/<portable title>.md` |
| Database | Canonical creation after live database selection and structural validation | Selected live database collection/Core workspace |

For unattended use, supply the required choices. These examples use synthetic titles:

```sh
shardbase create new --title "Example Game" --type core --alias "" --intent database --database games
shardbase create new --title "Example Topic" --type shard --alias "Topic Reference" --intent database --database games --core "Example Game" --parent "Example Game"
shardbase create new --title "Example Detail" --type pebble --alias "" --intent database --database games --core "Example Game" --parent "Example Topic - <generated-id>"
shardbase create new --title "Temporary idea" --type core --alias "" --intent inbox
shardbase create new --help
```

Replace `<generated-id>` with the ID in the preceding command's actual filename. Success prints the actual created path. New canonical notes start with `status: draft` and receive a fresh stable ID, including Cores whose filenames omit the ID. The H1 preserves the display title. Trailing Markdown heading markers that would change the parsed title are rejected for database creation.

Missing choices are prompted; input termination or Ctrl+C cancels. Unattended supporting creation must supply a resolved `--parent`; `--parent ""` is rejected. Supplying only `--core` prompts for a parent. `--parent` alone may resolve the Core for script compatibility; if both are supplied, they must agree. Selectors accept unique stems, filenames, or supported database-relative and instance-relative paths, optionally wrapped as wikilinks. Aliases and IDs alone do not resolve lineage.

Use `--root "/path/to/instance"` to select another existing instance containing `app/`. The default is the checkout containing the script. `shardbase new` remains an alias with the same options.

### Database and Template Selection

Database creation discovers live databases through their root `Database.md` and selects by `database_id`, independent of folder name. The picker offers live databases only. A blueprint-only ID produces a message to create/materialize the live database first with `shardbase create new database`. Duplicate identities, missing live manifests, malformed identities, invalid selected manifests, and existing structural failures block creation. Only active/draft version-1 databases are writable targets.

The CLI selects Markdown templates directly inside the selected live database's `Templates/` by YAML `type`. One matching template is automatic; multiple matches require `--template "Filename.md"` or an interactive choice. No matching template uses universal defaults with a Pool supplied explicitly for a Core or inherited for a supporting note. Live canonical creation never falls back to blueprint templates.

Template YAML supplies semantic defaults, aliases, and tags. Template bodies are ignored and no code is executed. Template IDs, Core links, parent links, and status are replaced with the new note's resolved identity and lineage. Skipping the alias preserves a template alias default. Optional facts are not invented.

The CLI does not interpret semantic schemas or Pool vocabularies from prose. Review template defaults and manually entered Pool values against the selected `Database.md`. These checks do not prove semantic validity or that a separate note earns materialization.

### Core and Parent Selection

For a new Core, select `--collection "Name"` when multiple collections are declared; a single collection is automatic. The Pool comes from a matching template or `--pool "Value"`/interactive input. New Cores default to workspaces:

```text
Data/Game/Example Game/
└── Example Game.md
```

The optional manifest preference is defined in [System Specification §4.1](../Docs/Shard%20System%20Specification.md#41-database-manifest). `creation_defaults.core_placement: flat` instead creates the Core directly at the collection root. Older manifests without the preference remain valid and use workspace creation by default. Workspace names use the same portable stem as the Core filename.

For Shards and Pebbles, choose a Core lineage, then an immediate Core/Shard parent. The parent picker shows only eligible members of that lineage; Pebbles cannot be parents. The selected Core determines Pool, collection, and physical location. Conflicting explicit `--pool` or `--collection` values fail. YAML records both root Core and immediate parent; a deeper Shard remains a filesystem sibling in the same workspace.

Existing flat lineages stay flat when supporting notes are added, regardless of the new-Core preference. Existing workspaces stay bundled. There is no automatic migration, nesting of structural directories, or split across collections or locations. Folder placement follows resolved YAML lineage.

### Validation and Failure Behavior

Canonical creation validates the selected manifest and existing database before writing. It checks IDs against canonical notes and parseable pending Inbox drafts, rejects normalized filename/workspace collisions, and uses exclusive file creation. It validates the resulting database and rolls back this operation's new file on validation/I/O failure or interruption. A newly created workspace is removed only if still empty; preexisting directories and competing content are preserved. Structural diagnostics explain failures. Full semantic validation remains future work.

The stable-filesystem assumption and recovery limits are described under [File Safety](#file-safety). No existing note, historical Inbox draft, or live contract is moved, rewritten, or synchronized from a blueprint.

### Inbox Capture Compatibility

`--intent inbox` retains the existing Games scaffold: use the single live `database_id: games` owner's template or the Games blueprint when no live owner exists. A missing live template fails without blueprint fallback. Template metadata stays provisional and may be incomplete or invalid. Core placeholders become a provisional self-link; supporting lineage can stay blank. No IDs are generated or canonical notes validated. Database-only flags, including `--core`, are rejected.

This scaffold does not limit editor-created Inbox notes to Games or require structural metadata. Temporary captures can remain ordinary Markdown. Configure the editor's default new-note location as `app/Knowledge/Inbox/` if desired; the CLI does not change editor settings.

## Manual Promotion

There is no automated promotion command or filesystem watcher. Historical prepared Inbox notes remain available for deliberate review. Before manually moving an Inbox note, establish ownership, collection, Pool, role, complete lineage, semantic metadata, stable ID, canonical filename, and placement against the System Specification and destination `Database.md`. Preserve valid prepared IDs and recheck uniqueness/collisions at the time of the move. Then run the validator; manual moves do not trigger validation.

Knowledgeable users can also create compliant canonical files manually. Direct CLI creation provides the automated path for new database-owned notes; promotion of existing drafts and arbitrary semantic validation remain separate work.

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
- manifest field/value/shape requirements, optional creation preferences, and required manifest body headings;
- declared data collections, root `Attachments/`, and `Views/`;
- traversal, absolute-path, containment, and relevant symlink boundaries before scanning;
- structural discovery at collection roots and one Core-workspace level;
- exclusion of attachment subtrees and root `Agents/`, `Templates/`, and `Views/` from structural discovery;
- misplaced root Markdown files that declare structural metadata;
- required structural fields and common fields `aliases`, `id`, and `tags`, including foundation-3 note-ID format and database-wide uniqueness;
- same-database Core/parent resolution, Core self-reference, permitted parent types, Pool consistency, cycles, self-parenting, parent-chain root consistency, and active descendants beneath archived ancestors;
- Core-workspace naming/membership, same-collection lineage, and split-lineage placement;
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
- canonical draft promotion. Direct canonical creation is implemented separately by the creation command with these structural checks.

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

Inbox capture retains its permissive draft behavior. Canonical creation reads declared collection roots and one workspace level for IDs and naming collisions, excluding attachments, and always validates existing and resulting structural state. Symlinks in inspected creation paths are rejected, and malformed canonical YAML blocks canonical creation rather than hiding unknown identities. These checks do not prove database-semantic validity or materialization judgment.

The implementation assumes a stable local filesystem during an operation and is not transactional. An interrupted draft write may leave a partial new draft; a rerun will refuse to overwrite it. Canonical creation rolls back its own new file and, if empty, its own new workspace on caught failures, including Ctrl+C. It never removes preexisting or competing content. Abrupt process termination, power loss, or a cleanup I/O error can leave partial output requiring review; this is not a crash-safe transaction.

Backup/restore use separate authenticated staging and publication rules described under [Encrypted Backup and Restore](#encrypted-backup-and-restore).

## Tests and Fixtures

Development tests live in the top-level [`tests/`](../../tests/) tree, with synthetic fixtures in [`tests/fixtures/`](../../tests/fixtures/). The test-only `_support.py` helper resolves shared paths and makes `app/Scripts/` importable during test discovery. Runtime tooling does not depend on the test tree.

Tests use temporary instances outside the vault. Keep `TMPDIR` or its platform equivalent outside the vault when customizing it.

The sanitized fixtures and tests prove the current structural validation behavior, including valid/invalid manifests, YAML shapes, common note metadata, lineage failures, workspace placement, filename normalization/collisions, boundary escapes, and Markdown heading checks.

Canonical creation tests prove live database/template selection, workspace/flat defaults, Core/parent selection and inheritance, ID retries, collision refusal, validation gates, rollback preservation, cancellation, and a subprocess-driven Core → Shard → deeper Shard → Pebble workflow with direct placement and correct YAML lineage. These proofs use disposable instances and synthetic examples, never live user knowledge. Command and installer tests also cover grouped/legacy creation, dependency-free help, validation routing, external runtime boundaries, launcher quoting, and preservation of existing files. Database-bootstrap tests cover blueprint discovery, external staging and structural validation, resource/link preservation, existing-database refusal, unsafe source boundaries, and bootstrap-to-note-creation proof. Semantic-schema, attachment-reference, fragmentation/materialization, and complete lifecycle proof fixtures remain future work.

Backup/restore tests use only synthetic external instances. They cover a two-command subprocess round trip, binary attachments, empty directories, metadata, idempotence, Git exclusions, changed tracked data, independent AES-GCM decoding, wrong passphrases, tampering/truncation, authenticated malformed inventories, unsafe paths, collisions, source changes, interrupted publication, rollback, and dependency-free command help.

## Continuous Integration

The [CI workflow](../../.github/workflows/ci.yml) runs on pull requests and pushes to `main`, and supports manual dispatch. Separate jobs run pinned Ruff checks and the complete unittest suite, with a direct `python -B app/Scripts/shardbase.py commands` smoke check on every test environment. Tests cover Python 3.10 and 3.14 on Ubuntu, plus Python 3.14 on Windows. Python 3.10 is the supported minimum; 3.14 is the current stable endpoint selected for this matrix.

Use the local setup, lint, and test commands above to reproduce failures in an external environment. CI keeps caches outside the checkout and disables Python bytecode generation. Required status checks and branch protection remain deferred.

## Compatibility

The preferred spelling is `shardbase create new`; `shardbase new` remains equivalent. Use `--intent inbox` to retain capture behavior. `--intent database --database <database_id>` now writes directly to a live canonical path and requires complete supporting lineage. `--core` selects a supporting note's lineage; parent-only scripts remain supported. Blueprint-only targets and `--parent ""` are no longer accepted for database intent. `--destination` remains unsupported. Existing Inbox files, blank IDs in drafts, and flat lineages stay untouched. The specification is now foundation-4; foundation-3 naming and `manifest_version: 1` are retained.

The validator checks the current `foundation-4` contract in its documented scope. `manifest_version: 1` identifies only the manifest schema and does not identify the System Specification version under which a database was authored.

The validator does not migrate older state. For the recorded `foundation-1` through `foundation-4` compatibility boundaries and preservation-oriented transitions, use the System Specification.

## Blueprint Scaffolding

`app/Blueprints/Games/` includes tracked empty-directory scaffolding for `Data/Game/Attachments/` and `Views/`, plus draft templates and the optional Vera Agent resource. Packaging placeholders are not semantic knowledge.

Copying a blueprint materializes a starting database package. Later blueprint changes never silently update a live database.
