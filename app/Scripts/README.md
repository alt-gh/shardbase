# Shardbase CLI and Validation Tooling

This document describes the **current implementation** in `app/Scripts/`: how to run it, what it does, and what it does not yet do.

It does not define Shardbase architecture. Universal requirements come from [`../Docs/Shard System Specification.md`](../Docs/Shard%20System%20Specification.md); database-specific requirements come from the target database's root `Database.md`.

Current tooling targets System Specification `foundation-6`, retaining foundation-3 naming and `manifest_version: 1` within the implementation scope described below.

## Runtime Setup

The current scripts require Python 3.10 or newer and the pinned PyYAML and cryptography dependencies in `requirements.txt`. These are tooling requirements, not universal Shardbase requirements. Existing installations should rerun the installer after updating to install new dependencies.

### Bootstrap a private instance (macOS/Linux/Windows)

Download and extract the repository ZIP, then open a terminal in its root. Git and existing knowledge are not required:

```sh
python bootstrap.py
```

Use `python3 bootstrap.py` on macOS/Linux if needed, or `py bootstrap.py` on Windows. Python 3.10+ is required, with no fixed upper version limit. Bootstrap checks its own folder for framework files before preparing anything. A root `.git` file or directory is reported as a Git-managed/development instance; bootstrap never runs Git or checks enclosing repositories.

| Platform | External runtime | External launcher |
|---|---|---|
| macOS/Linux | `~/.local/share/shardbase/venv` | `~/.local/bin/shardbase` |
| Windows | `%LOCALAPPDATA%\Shardbase\venv` | `%LOCALAPPDATA%\Shardbase\bin\shardbase.cmd` |
| Windows without `LOCALAPPDATA` | `~/AppData/Local/Shardbase/venv` | `~/AppData/Local/Shardbase/bin/shardbase.cmd` |

Use `--runtime "/external/path/to/venv"` and `--bin-dir "/external/path/to/bin"` for custom locations; `--help` lists these options. Runtime, launcher, and temporary paths must resolve outside this instance, other identifiable Shardbase instances, and Obsidian vaults. Keep custom locations outside vaults without recognizable markers too.

Bootstrap creates or reuses an external venv and verifies its interpreter can run Python 3.10+. An invalid, unsupported, or partially created runtime is preserved and setup fails; review it yourself or choose another `--runtime`. Rerunning a valid runtime reinstalls/repairs pinned dependencies.

Dependency installation may access configured Python package indexes/network resources. Pip runs with `--isolated`, `--no-cache-dir`, `--no-compile`, and `--disable-pip-version-check`; bytecode is disabled. Bootstrap performs no release lookup, telemetry, self-update, framework download, or knowledge synchronization.

Launchers run the selected instance's source by absolute path with `-B`, preserving caller arguments. Reruns leave identical launchers unchanged. A complete recognized generated launcher (version 1, or the exact previous POSIX format) can be retargeted to a fresh ZIP after dependencies install successfully. A marker alone does not establish ownership. Unrelated or edited files, unknown formats, symlinks, and non-regular paths are refused and preserved; choose another `--bin-dir` or review the existing file.

Ownership is checked before installation and immediately before publication. New launchers use no-clobber publication; replacing an existing managed launcher is atomic but assumes no concurrent edits in the final check-to-replace interval. Avoid simultaneous installers or edits of the same launcher. Filesystems must support hard links for first publication; failures leave competing files intact.

Bootstrap invokes the external interpreter directly to check `shardbase.py commands`, independently of PATH. A failed check fails setup. After a successful root bootstrap, a fresh private ZIP-style instance in a fully interactive terminal is handed directly to `shardbase init` with that external interpreter; PATH availability is not required. Git-managed/development instances, noninteractive runs, lower-level installer use, and private instances with existing knowledge do not enter an interactive session and instead print `shardbase init` as the manual next step. Cancelling or failing guided setup preserves the successfully prepared runtime and launcher.

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
| `shardbase init [--root PATH] [--no-color]` | Guided new-instance, encrypted-restore, or setup-only onboarding |
| `shardbase create new` | Create a universal pre-structural note in Inbox; prompt for omitted choices |
| `shardbase create new database` | Select a blueprint and create a new live database scaffold |
| `shardbase create new database --blueprint games` | Create the Games database without a selection prompt |
| `shardbase create` | Show the creation command group |
| `shardbase new` | Compatibility alias for note creation, with identical note options |
| `shardbase validate` | Read-only structural checks on all live databases in the installed instance |
| `shardbase validate "/path/to/database"` | Check one database root |
| `shardbase validate --root "/path/to/instance"` | Check all live databases in another instance |
| `shardbase doctor [--root PATH] [--no-color]` | Read-only instance and local tooling health diagnostics |
| `shardbase backup [archive]` | Choose an output file/folder, then encrypt and verify local knowledge |
| `shardbase restore [archive]` | Authenticate and import a backup; prompt for the file when omitted |
| `shardbase restore archive --dry-run` | Verify a backup and check destination conflicts without writing knowledge |
| `shardbase commands` | List all commands, including the compatibility alias |
| `shardbase help` or `shardbase --help` | Show top-level help |
| `shardbase help create new` or `shardbase create new --help` | Show creation options |
| `shardbase help create new database` | Show database scaffolding options |
| `shardbase help validate` or `shardbase validate --help` | Show validation options |

`shardbase help <command>` and `<command> --help` use the same parser and stay aligned with the implemented options. The standalone validator script remains available for existing workflows; it accepts the same optional database path and `--root` selection.

## Guided Initialization

Run `shardbase init` to choose one of three interactive workflows:

1. **Start a new private instance** — inspect current health and live database identities, offer only supplied blueprints whose `database_id` is not already materialized, delegate creation to the database-creation engine, then structurally validate the created database and summarize doctor health.
2. **Restore an encrypted backup** — use the same backup-path prompt, secure passphrase input, restore engine, and result wording as `shardbase restore`, then structurally validate discovered live databases and summarize doctor health. Existing structural knowledge failures do not universally block this recovery path; remaining failures after restore are reported.
3. **Finish setup without creating knowledge** — summarize doctor health without creating `app/Knowledge/`, Inbox, Databases, Git/editor state, or a setup marker.

Initialization is rerunnable and derives state from the framework, current knowledge boundary, live manifests, and diagnostics. It does not maintain a hidden completion marker. Existing databases are reported and never recreated or overwritten; malformed or ambiguous live state is surfaced rather than ignored. If every supplied blueprint is already materialized, the command exits without attempting a guaranteed collision.

New and restored databases receive explicit read-only structural verification plus a doctor summary. A primary create/restore success is preserved if later verification fails, while the command returns nonzero and directs the user to inspect the result. Passing structural checks does not certify database-semantic validity. Guided new-instance setup stops after database creation and points to `shardbase create new`; it does not create a first note.

Input termination and Ctrl+C print `Cancelled.` and return status 130. For automation, continue to use the lower-level creation, restore, validation, and doctor commands; guided initialization intentionally has no parallel noninteractive path-selection flags.

## Instance Health Diagnostics

Run `shardbase doctor` to inspect the instance bound to the CLI. Use `--root "/path/to/instance"` to diagnose another instance and `--no-color` for plain text; `NO_COLOR` is also respected. `shardbase doctor --help` and `shardbase help doctor` share the actual command parser.

Results appear in four groups with stable check codes:

- **Framework** checks required functional directories/files, safely reads the declared System Specification version, and reuses blueprint discovery. Development checkout assets and Obsidian configuration are not required. Missing root `bootstrap.py` is a warning.
- **Privacy** reports root Git state, enclosing Git boundaries, and tracked knowledge using hardened local Git inspection. Root Git is informational. Parent Git, tracked knowledge, changed tracked knowledge, and unavailable/failed Git inspection are warnings that call for owner review. No remotes are contacted or Git state changed.
- **Runtime** checks the active Python version, external interpreter/prefix boundaries, required imports, and versions against the selected instance's `requirements.txt`. Missing/broken dependencies are blocking; usable dependency pin drift is a warning. Doctor can report dependency failures without those dependencies installed.
- **Knowledge** accepts absent or unused knowledge directories and automatically discovers and structurally validates live databases using the existing validator. Findings retain validator codes and path context. This does not certify database-semantic conformance or infer historical per-database specification versions; see [validator scope](#read-only-validator).

Launcher discovery is limited to PATH and the platform default from bootstrap. No discovered launcher is informational because direct-script use may be intentional. Each discovered launcher must have a supported managed format, target the selected instance, and use a usable external Python 3.10+ interpreter. A launcher targeting another instance fails even when `--root` deliberately selects that instance. Doctor never scans arbitrary folders or retargets launchers.

The four severities are `OK` (passed), `INFO` (context or a check that could not run because a prerequisite failed), `WARN` (review advised), and `FAIL` (blocking issue). Exit status is `0` with no failures, `1` with any failure, `2` for invalid syntax, and `130` for cancellation. **Warnings do not fail the command.** The final summary counts warnings and blocking issues separately.

Doctor is observational: it performs no repair, initialization, installation, migration, backup, network access, or persistent diagnostic writes. Knowledge, launchers, runtimes, PATH, and shell profiles are never changed. Output is human-readable; there is no public JSON contract or repair mode.

## Encrypted Backup and Restore

These are manual offline CLI commands. New backups use format v2 and contain only durable user state: `app/Knowledge/Inbox/**`, every reconstructable live database's `Data/**` and `Views/**`, and the entire `.obsidian/**` tree. Live `Database.md`, supplied Templates and Agents, other managed package resources, framework files, and unrelated local files are excluded. Nothing is uploaded, scheduled, synchronized, or executed.

For a normal backup and restore into another existing Shardbase checkout:

```sh
shardbase backup "$HOME/knowledge.sbbackup"
shardbase restore "$HOME/knowledge.sbbackup" --root "/path/to/new/shardbase"
```

The first command prompts for a hidden passphrase and confirmation. The second prompts for the same passphrase, verifies the entire backup and destination, then imports the knowledge automatically. No decryption, extraction, file rearrangement, or post-import conversion commands are needed. Use a strong passphrase of several random words; creation requires at least 12 UTF-8 bytes. **Shardbase cannot recover a lost passphrase.**

With no output argument, `shardbase backup` prompts for a save location. Enter a new filename or an existing folder; choosing a folder generates a unique `.sbbackup` filename there. Press Enter to accept the suggested unique filename in `~/Shardbase Backups/`; that default folder is created if needed. An explicit output argument also accepts either a filename or an existing folder. For a custom filename, its parent directory must already exist. Output must be outside Shardbase instances and identifiable vaults. An existing backup is never replaced, and the command prints the resulting location.

`shardbase restore` prompts for the backup file to read when omitted. Use `--root "/path/to/instance"` to choose the destination checkout. Format v2 resolves each archived `database_id` against that checkout's installed blueprints, materializes its current package folder, and places archived Data and Views beneath it; the old folder name is not destination truth. Both commands accept `--root`, defaulting to the checkout used for installation.

### User State and Git

The commands never contact GitHub. Format v2 embeds all in-scope user files regardless of Git status; it has no Git-reference optimization. `.obsidian/` remains ignored by the root `.gitignore`, and backup fails closed with an untracking diagnostic if any `.obsidian` content was force-added to the repository.

A small fixed list of generated caches and OS files is excluded; the exact list is in the [format contract](BACKUP_FORMAT.md#path-and-inventory-rules). `.gitignore` is not an inventory selector. Symlinks, nested `.git` paths, and special files are refused instead of followed or silently skipped.

### Restoration and Version Updates

Restore preserves user-state bytes, logical filenames, directory layout, empty directories, and file modification times. It preserves the owner's executable bit while limiting newly restored files to owner access. Existing byte-identical files are skipped; differing files and file/directory conflicts stop the entire preflight before any durable write. Destination-only content is preserved. `.obsidian/` is never merged by overwriting differences, so restore before first opening a fresh checkout in Obsidian when possible.

The intended update workflow is to back up the old instance and restore into a fresh newer checkout. Do not create replacement databases first: restore obtains each managed package from the destination release, then adds archived Data and Views. Every source live database must have exactly one reconstructable installed destination blueprint/package. Custom or missing identities fail visibly rather than producing incomplete databases.

If a destination already has the represented database, restore accepts it only when its managed files exactly match what the current destination release would materialize; Data and Views are ignored in that package comparison and checked separately as user state. A differing package fails rather than being upgraded or overwritten. This explicitly protects pre-foundation-5 live customizations: format v2 does not preserve edits to managed files, and no in-place migration is attempted.

Format v2 supports user-state transfer from `foundation-4`, `foundation-5`, or `foundation-6` into `foundation-6`, while retaining the recorded foundation-4/5 transfers into foundation-5. This is the explicit ownership-boundary upgrade path: it leaves the old instance untouched and does not preserve its managed-file customizations. The reader retains format-v1 full-`app/Knowledge/` semantics and its fixed compatibility vector for `foundation-3` → `foundation-3`/`foundation-4` and `foundation-4` → `foundation-4`; v1 is never reinterpreted or silently crossed into the foundation-5 managed-package ownership boundary.

### Verification, Password Input, and Failures

Backup streams encryption and then uses the actual restore reader to decrypt, authenticate, and hash-check the result before publishing it. Restore authenticates the entire envelope, validates its logical inventory, verifies each file, resolves all database packages, stages them, and preflights every package/user-state conflict before publishing. Encryption uses AES-256-GCM and scrypt; filenames and manifest metadata are also encrypted. Restored plugins and Agents are copied as inert bytes and never executed.

To inspect a restore without changing knowledge:

```sh
shardbase restore "$HOME/knowledge.sbbackup" --root "/path/to/new/shardbase" --dry-run
```

For manually invoked noninteractive use, both commands accept `--password-file "/external/path/passphrase"`. The UTF-8 file must be owner-only on POSIX systems, for example mode `0600`; one terminal LF/CRLF is accepted. Keep it outside knowledge and separate from the backup. No plaintext password command-line option or environment variable is supported. Without a password file, an unavailable secure terminal causes a clean error instead of falling back to an echoed prompt.

Close editors and other writers during backup/restore. Backup checks for changes during inventory/copy and fails if observed, but does not provide a live filesystem snapshot. Restore assumes a stable local filesystem. Each imported file is published complete with exclusive hardlink creation; files are never partially written in knowledge. Ordinary errors and Ctrl+C attempt to roll back only new additions. Abrupt termination can leave some complete additions; rerun the same restore to finish. This is not a globally atomic multi-file transaction, and rollback cannot guarantee cleanup when the filesystem itself fails.

Temporary plaintext is held in owner-private directories outside the vault and cleaned on ordinary completion/error. Abrupt termination may leave an external `shardbase-transfer-*` directory; backup interruptions may also leave an encrypted `.shardbase-backup-*.partial` next to the intended output. There is no secure-deletion guarantee for temporary plaintext, filesystem snapshots, or OS swap. Use an encrypted local filesystem where those at-rest threats matter.

Restore staging must support hardlinks and reside on the same filesystem as its destination. The default is the system temporary directory. For a target on another volume, pass `--staging-dir "/external/directory/on/target-volume"`; this existing directory must be outside every vault. No manual copying or extraction is needed. Backup accepts the same option for verification staging but does not require staging to share the source filesystem. Backups themselves may be stored on another volume, provided that output filesystem supports hardlinks for atomic publication.

Format-v2 and legacy-v1 limits are a 32 GiB uncompressed payload, a 16 MiB manifest, 100,000 inventory entries, and portable paths. Key derivation needs approximately 128 MiB of RAM; file I/O is streamed in 1 MiB blocks. Allow external staging space for approximately twice the uncompressed backup size plus reconstructed packages during restore. No compression or deduplication is performed. ACLs, ownership, xattrs/resource forks, directory timestamps, and hardlink relationships are not preserved.

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

Once created, its Data and Views are user-owned; its manifest, supplied Templates and Agents, and other package resources are managed. Future blueprint changes do not synchronize into the live package in place. Review `Database.md`; new CLI notes still begin in Inbox and are promoted deliberately after ownership and structure are resolved.

## Note Creation

Run `shardbase create new` to choose a title, provisional Core/Shard/Pebble type, and optional alias. Every note is saved to `app/Knowledge/Inbox/<portable title>.md`; body development remains separate. `shardbase new` is the equivalent compatibility alias.

For unattended use, supply the three choices. These examples use synthetic titles:

```sh
shardbase create new --title "Example Game" --type core --alias ""
shardbase create new --title "Example Topic" --type shard --alias "Topic Reference"
shardbase new --title "Example Detail" --type pebble --alias ""
shardbase create new --help
```

Missing choices are prompted; input termination or Ctrl+C cancels. The CLI does not prompt for intent, database, template, Pool, Core, parent, or collection. The former `--intent`, `--database`, `--template`, `--pool`, `--core`, `--parent`, and `--collection` note flags are no longer accepted.

Use `--root "/path/to/instance"` to select another existing instance containing `app/`. The default is the checkout containing the script. `shardbase new` remains an alias with the same options.

### Inbox Metadata

Every CLI capture receives the complete universal key set in a stable order:

```yaml
---
type: shard
pool:
core:
parent_note:
status: draft
aliases:
id: 7k3m9p2x4q
tags:
---
# Example Topic
```

The selected `type` is provisional. Pool, Core lineage, immediate parent, collection, canonical placement, database ownership, and database-specific semantic metadata remain unresolved. A supplied alias becomes a one-item YAML string list. The generated ID uses the canonical 10-character lowercase Crockford Base32 format and must survive promotion unchanged.

Capture is universal and template-independent: it does not inspect canonical databases, Games templates, or blueprint defaults. Valid IDs in parseable Inbox Markdown, including nested user-organized folders, are reserved during generation. Plain or malformed Inbox Markdown does not block capture. Editor-created Inbox notes may remain ordinary Markdown without this scaffold; existing Inbox files are not migrated.

## Manual Promotion

There is no automated promotion command or filesystem watcher. Historical prepared Inbox notes remain available for deliberate review. Before manually moving an Inbox note, establish ownership, collection, Pool, role, complete lineage, semantic metadata, stable ID, canonical filename, and placement against the System Specification and destination `Database.md`. Preserve a valid prepared ID and recheck destination uniqueness/collisions at the time of the move; fail safely rather than silently changing it. Then run the validator; manual moves do not trigger validation.

Knowledgeable users can also create compliant canonical files manually. The retained internal canonical preparation and commit machinery remains tested as the basis for a future promotion command, but it is not exposed as note-creation flags. Promotion and arbitrary semantic validation remain separate work.

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
- canonical draft promotion. Canonical preparation and commit primitives retain these structural checks for future promotion, but no public promotion command exists.

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

Inbox capture reads parseable Inbox frontmatter only to reserve valid IDs; it does not inspect or validate canonical databases. Symlinks in the capture path or nested Inbox scan are rejected. Retained canonical preparation reads declared collection roots and one workspace level for IDs and naming collisions, excluding attachments, and validates existing and resulting structural state. These checks do not prove database-semantic validity or materialization judgment.

The implementation assumes a stable local filesystem during an operation and is not transactional. An interrupted draft write may leave a partial new draft; a rerun will refuse to overwrite it. Canonical creation rolls back its own new file and, if empty, its own new workspace on caught failures, including Ctrl+C. It never removes preexisting or competing content. Abrupt process termination, power loss, or a cleanup I/O error can leave partial output requiring review; this is not a crash-safe transaction.

Backup/restore use separate authenticated staging and publication rules described under [Encrypted Backup and Restore](#encrypted-backup-and-restore).

## Tests and Fixtures

Development tests live in the top-level [`tests/`](../../tests/) tree, with synthetic fixtures in [`tests/fixtures/`](../../tests/fixtures/). The test-only `_support.py` helper resolves shared paths and makes `app/Scripts/` importable during test discovery. Runtime tooling does not depend on the test tree.

Tests use temporary instances outside the vault. Keep `TMPDIR` or its platform equivalent outside the vault when customizing it.

The sanitized fixtures and tests prove the current structural validation behavior, including valid/invalid manifests, YAML shapes, common note metadata, lineage failures, workspace placement, filename normalization/collisions, boundary escapes, and Markdown heading checks.

Inbox-capture tests prove all provisional types, stable ID allocation and nested collision retry, universal metadata, template/database independence, portable filenames, safe aliases, collision refusal, grouped/legacy routes, removed-flag errors, and preservation of existing files. Retained canonical-preparation tests prove live database/template selection, workspace/flat defaults, Core/parent selection and inheritance, ID retries, collision refusal, validation gates, and rollback preservation. These proofs use disposable instances and synthetic examples, never live user knowledge. Command and installer tests also cover dependency-free help, validation routing, external runtime boundaries, and launcher quoting. Database-bootstrap tests cover blueprint discovery, external staging and structural validation, resource/link preservation, existing-database refusal, unsafe source boundaries, and bootstrap-to-Inbox-capture proof. Semantic-schema, attachment-reference, fragmentation/materialization, and complete lifecycle proof fixtures remain future work.

Backup/restore tests use only synthetic external instances. They cover a two-command subprocess round trip, binary attachments, empty directories, metadata, idempotence, Git exclusions, changed tracked data, independent AES-GCM decoding, wrong passphrases, tampering/truncation, authenticated malformed inventories, unsafe paths, collisions, source changes, interrupted publication, rollback, and dependency-free command help.

## Continuous Integration

The [CI workflow](../../.github/workflows/ci.yml) runs on pull requests and pushes to `main`, and supports manual dispatch. Separate jobs run pinned Ruff checks and the complete unittest suite, with a direct `python -B app/Scripts/shardbase.py commands` smoke check on every test environment. Tests cover Python 3.10 and 3.14 on Ubuntu, plus Python 3.14 on Windows. Python 3.10 is the supported minimum; 3.14 is the current stable endpoint selected for this matrix.

Use the local setup, lint, and test commands above to reproduce failures in an external environment. CI keeps caches outside the checkout and disables Python bytecode generation. Required status checks and branch protection remain deferred.

## Compatibility

The preferred spelling is `shardbase create new`; `shardbase new` remains equivalent. Both routes create only in Inbox. Existing Inbox files, blank IDs in historical/editor-created drafts, canonical notes, and flat lineages stay untouched. The specification is now foundation-6; foundation-3 naming and `manifest_version: 1` are retained.

The validator checks the current `foundation-6` canonical structural contract in its documented scope. Inbox captures remain outside canonical database validation. `manifest_version: 1` identifies only the manifest schema and does not identify the System Specification version under which a database was authored.

The validator does not migrate older state. For the recorded `foundation-1` through `foundation-6` compatibility boundaries and preservation-oriented transitions, use the System Specification.

## Blueprint Scaffolding

`app/Blueprints/Games/` includes tracked empty-directory scaffolding for `Data/Game/Attachments/` and `Views/`, plus draft templates and the optional Vera Agent resource. Packaging placeholders are not semantic knowledge.

Copying a blueprint materializes a managed database package plus user-owned Data/Views scaffolding. Later blueprint changes never silently update an existing live database; format-v2 restore reconstructs the current package only in a fresh checkout or verifies an already-equivalent package.
