# ShardBase CLI and Validation Tooling

The initial CLI creates a Game note containing required YAML and one H1. It supports Inbox capture and database-intended staging for editor review. Creation and validation run locally and do not access external services.

The validator performs read-only structural checks against version `foundation-2` of the [System Specification](../Docs/Shard%20System%20Specification.md). A successful run means the implemented checks passed; it is not proof of full database-semantic conformance or Foundation completion.

## Setup and Commands

This implementation requires Python 3.10 or newer and the pinned PyYAML dependency in `requirements.txt`. It has been tested with Python 3.14. These are tooling requirements, not universal ShardBase architectural requirements.

Run these commands from the repository root. The example environment is temporary and entirely outside the vault; recreate it if the operating system removes it. A persistent environment may instead live in another user-selected location outside the project and synchronized vault.

```sh
shardbase_runtime="/tmp/shardbase-validator-venv"
python3 -B -m venv "$shardbase_runtime"
"$shardbase_runtime/bin/python" -B -m pip install --no-cache-dir --no-compile -r app/Scripts/requirements.txt
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py new
"$shardbase_runtime/bin/python" -B app/Scripts/validate_shardbase.py
"$shardbase_runtime/bin/python" -B -m unittest discover -s app/Scripts -p 'test_*.py' -v
```

To inspect one database, append its root path to the validator command. The path must be a direct child of an `app/Knowledge/Databases/` boundary, including when testing a temporary copy. The sanitized fixture and Games blueprint must be copied into that layout before validating them; the tests do this automatically in temporary storage outside the vault.

Dependency installation downloads software; validation itself performs no network operations. Validation never writes, renames, repairs, or migrates canonical files. `-B` keeps Python bytecode out of the project, and dependency installation disables persistent pip caching and compilation.

The repository runtime policy requires these artifacts to remain physically outside the project and vault; `.gitignore` only prevents tracking. Apply bytecode suppression to every Python entry point, including test discovery, custom import commands, and IDE runners: use `-B` or set `PYTHONDONTWRITEBYTECODE=1` in that runner's environment before starting Python. Keep virtual environments, dependencies, caches, and build output outside the vault as well. These settings prevent new bytecode files but do not remove an existing `__pycache__/` directory; inspect and remove stale generated files separately, preserving source files and user-owned knowledge.

## Create a Note

Run `shardbase.py new` using the external Python environment above. The flow asks for a title, a type (Core, Shard, or Pebble), an optional alias immediately after type selection, and a destination:

| Choice | File location beneath the selected instance |
|---|---|
| `1` / Inbox | `app/Knowledge/Inbox/<portable title>.md` |
| `2` / Databases | `app/Knowledge/Inbox/Staged/<portable title>.md` |

Both destinations are Inbox capture. Any type can be created without an existing Core, parent, or live database. There is no parent picker or `--parent` option. Creation does not validate structural lineage, semantic metadata, database conformance, or canonical filenames. These drafts are for editing and review; selecting Databases does not make the file canonical.

Supply all answers explicitly for unattended use:

```sh
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py new --title "Example Game" --type core --alias "" --destination databases
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py new --title "Zombies" --type shard --alias "Survival" --destination databases
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py new --title "Terminus" --type pebble --alias "" --destination inbox
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py new --help
```

The default instance is the checkout containing the script, regardless of the shell's working directory. Use `new --root "/path/to/instance"` to select another existing instance root containing `app/`. Runtime environments and test instances must remain outside the vault.

### Draft Metadata and Alias

The shipped templates create all eight note fields plus a single H1. A Shard named `Terminus` with alias `Island` contains:

```markdown
---
type: shard
pool: Games
core:
parent_note:
status: draft
aliases:
- Island
id:
tags:
---
# Terminus

```

Shard and Pebble templates leave `core` and `parent_note` blank for later review. A Core template uses a provisional self-link and an empty parent. All types use the entered title for the H1 and derive the output filename from that title alone. The CLI does not infer ancestry from a title containing ` - ` or require bounded canonical filenames in Inbox. There is exactly one blank line after the H1 and no additional body content.

Press Enter at the alias prompt to skip it, or pass `--alias ""`. With the shipped templates this leaves `aliases:` blank. An entered alias becomes a one-item YAML string list; punctuation, numeric-looking strings, and commas are retained as part of that one alias. Skipping preserves an existing template alias default. Supplying an alias replaces that default in the new draft only. IDs and timestamps are never generated.

### Template Sources

System Specification §5.3 establishes the optional database-root `Templates/` directory as the canonical database-owned template location. The framework ships `Game.md`, `Game Shard.md`, and `Game Pebble.md` in [Games/Templates/](../Blueprints/Games/Templates/), selected by the requested structural type.

The CLI reads database manifests only to locate a template owner by `database_id: games`; it does not validate their versions, required fields, lifecycle status, declared collections, or canonical notes. Missing or malformed manifests cannot identify a template owner and are skipped during this lookup. If no Games owner is identified, the selected instance's Games blueprint supplies the template. Multiple matching owners remain a template-selection ambiguity that must be resolved explicitly. A selected live database's missing template is reported rather than silently copied or replaced from a blueprint. No database is created or synchronized as a side effect.

A template must be readable YAML frontmatter with string field names so its values can be loaded safely. Malformed YAML, duplicate keys, or unsupported YAML tags still produce parse errors; this is input decoding rather than database conformance validation. The CLI supplies missing note fields with editing defaults, applies the selected `type`, and preserves other template metadata for review without checking its schema or meaning. The Core template's `[[{{stem}}]]` becomes the provisional self-link. Legacy unresolved `[[{{core}}]]` and `[[{{parent}}]]` placeholders become blank values; no parent lookup occurs. Literal template links remain unverified. Template bodies are ignored, and no template code is executed.

These are Inbox starter resources, not immediately valid canonical Shards or Pebbles. The Games contract and System Specification still determine what is valid when a note is promoted. Unknown semantic fields, unresolved links, or invalid values in a draft must be reviewed at that boundary.

### Review and Canonical Validation

Edit the file freely in your Markdown editor. When promoting it into a live database, classify ownership and placement, complete `core` and `parent_note` as applicable, conform the filename to canonical rules, and review metadata under the destination `Database.md`. Canonical creation/promotion must result in conformant knowledge; this change does not relax live-database rules.

The existing read-only validator inspects live database notes and excludes Inbox, including Staged. Run it against the destination database as part of manual promotion, and review database semantics separately. This MVP has no automatic promotion command or folder watcher; manually moving a file does not automatically run validation. Automatic promotion, direct canonical creation, database creation commands, domain-template selection, and body generation remain deferred.

### Terminal Presentation and File Safety

The interactive flow uses spaced menus, short descriptions, and a compact result summary. Color is enabled only for terminal output; redirected output stays plain. Use `--no-color`, `NO_COLOR`, or `TERM=dumb` to disable it. Ctrl+C or end-of-input cancels without implicitly selecting an option.

Creation retains basic file safety: a non-empty single-line title, a usable portable filename, output-boundary and symlink checks, and exclusive creation. Existing output filenames, including case and Unicode normalization collisions, are never overwritten or silently numbered. No existing note contents are read to establish eligibility or check canonical collisions. These protections prevent accidental file damage; they do not certify structural validity.

`shardbase.py` owns prompts and arguments; `note_creation.py` owns template loading, draft rendering, and exclusive file creation. YAML parsing and portable filename normalization reuse helpers in `validate_shardbase.py`; its conformance checks are not invoked by `new`. No new dependencies are required.

The implementation assumes a stable local directory tree and is not a transaction system. An interrupted write can leave a partial new draft for review, which a rerun will refuse to overwrite. It does not protect against concurrent directory/symlink replacement or differently cased concurrent writes on a case-sensitive filesystem. Existing knowledge is never deleted as error recovery.

Exit codes are `0` for creation, `1` for an operation error, `2` for invalid command syntax, and `130` for cancellation or end-of-input. The entry point suppresses project bytecode; retain `-B` for tests and other Python runners. Tests use temporary instances outside the vault; keep `TMPDIR` (or its platform equivalent) outside the vault when customizing it.

## Implemented Checks

- Discover every direct database directory, including incomplete roots missing `Database.md`; report discovery failures rather than treating them as an empty instance.
- Parse UTF-8 YAML frontmatter with [PyYAML's safe loader](https://pyyaml.org/wiki/PyYAMLDocumentation), supporting block and flow collections, comments, quoted escapes, multiline values, and ordinary aliases/merges. Explicit duplicate keys, unsupported tags, malformed YAML, and non-mapping frontmatter produce diagnostics. PyYAML's scalar resolution applies: quote text such as `yes`, `on`, or numeric identifiers when a string is intended.
- Check manifest fields and scalar/list shapes, integer `manifest_version: 1`, an opening H1, required H2 sections and H3 Includes/Excludes beneath Scope, heading depth/spacing, collection declarations, root `Attachments/`, and `Views/`. Unsupported manifest versions stop inspection of that database's contents.
- Reject traversal and absolute collection paths before scanning. Check resolved containment before reading structural files or directories, including symlink targets. Database-root symlinks require ownership review and are not followed by this implementation.
- Discover structural candidates at collection roots and one workspace level. Exclude attachment subtrees and root Agents, Templates, and Views. Check workspace Core identity, naming, lineage membership, and split placement. Nested directories other than `Attachments/` are reported for resource-contract review without recursively scanning them.
- Inspect direct root Markdown files other than `Database.md` for misplaced `type`, `core`, or `parent_note` declarations and report `note-location`. These files never enter structural link resolution. Ordinary root resources without those declarations are not treated as structural notes; malformed frontmatter or unreadable root Markdown receives `root-frontmatter` or `read-error`. This targeted check does not certify arbitrary resource contracts or infer structural intent from prose.
- Require `aliases`, `id`, and `tags` on every discovered Core, Shard, and Pebble. Blank YAML values are valid defaults; aliases/tags also accept empty lists or lists of non-empty strings, and IDs accept strings. Report missing keys as `note-field` and invalid shapes as `note-aliases`, `note-id`, or `note-tags`. Common fields do not participate in structural reference resolution; no IDs are generated or checked for uniqueness.
- Check required structural fields, unambiguous local Core/parent resolution, empty Core parent fields, permitted parent types, Pool consistency, cycles, self-parenting, parent-chain root consistency, and active descendants beneath archived ancestors. Archiving a database does not require rewriting every contained note's status.
- Derive portable filenames from canonical title components under the supported convention below. Check bounded context, portable characters and reserved stems, actual duplicate stems, and collisions in expected filenames across all scanned collections/workspaces. Never resolve collisions by choosing one duplicate or by using directory placement.
- Check opening headings, incremental top-level ATX heading depth, and exactly one following blank line, excluding fenced code blocks. Blank lines between frontmatter and the first heading are accepted.

Structural wikilinks resolve only against the discovered notes in the selected database. Supported targets are unique stems, filenames with `.md`, database-relative paths, and repository/vault-root-relative paths beginning with `app/Knowledge/Databases/`; path forms may omit `.md`. Aliases and heading fragments do not change the selected structural note. Arbitrary relative traversal, absolute paths, and cross-database targets are not followed. Ordinary body links and Ghost Shards do not establish structural parentage.

## Naming Convention and Remaining Scope

The filename checker currently supports the convention that a Core's opening H1 is its canonical entity name and a supporting note's opening H1 is its canonical local node name. It derives Core and immediate-parent context through YAML references, not by splitting ancestor filenames. A local name containing ` - ` is still one name component.

Portable normalization replaces wikilink delimiters `#`, `[` and `]` with spaces, as well as the other forbidden characters, and removes the entire trailing sequence of spaces and periods. `Game #1` derives `Game 1.md` with `core: "[[Game 1]]"`; `Game. .` derives `Game.md`. Display titles remain intact. Aliases and fragments still work after the normalized target. Names that normalize to the same filename produce collision diagnostics.

The sanitized fixtures use this convention; Games explicitly uses it for Core titles. The universal specification permits other documented display-title conventions. A database with another convention needs a database-aware naming adapter before this tool's filename findings can be treated as conformance findings. This implementation does not infer alternate title meanings from prose or invent a new semantic title field.

Database-semantic schemas and Pool vocabularies are not automatically interpreted from `Database.md` prose. Semantic field validation, materialization/fragmentation judgment, attachment reference and orphan audits, arbitrary database-local resources, full Markdown parsing, and specification-version migration remain separate work. Additional resource directories reported as `nested-directory` require review against their database contract; the diagnostic is not a new universal prohibition on permitted resources.

The filesystem checks assume a stable local tree during a run; they do not provide a transaction or protection against concurrent replacement of files. Avoid using the validator as a write/migration gate until the operation's full structural and database-semantic requirements are covered.

## Results and Compatibility

Exit status `0` means no issues in the implemented scope (or no database candidates in an empty instance). Exit status `1` means validation or discovery found issues. Diagnostics contain a path, an issue code, and a message; consumers should use issue codes rather than parse message text or rely on issue counts. One problem can generate several dependent diagnostics. YAML errors report location without echoing source content.

Root placement and manifest heading checks correct false acceptance under existing rules. The naming fixes implement the approved normative `foundation-1` specification boundary and can change expected filenames for previously accepted state. `manifest_version` remains `1`; it does not identify the specification version under which a database was authored. The validator checks only the current documented scope, without historical-version inference or migration. See System Specification Section 19.2 for the preservation-oriented transition: review affected files and references, retain a recoverable local copy, resolve collisions, explicitly authorize the bounded rename/reference update, and validate preservation and conformance. The `foundation-2` boundary additionally requires `aliases`, `id`, and `tags`. This is breaking for notes missing these keys or using incompatible values. Its bounded transition reviews existing uses, preserves a recoverable local copy, adds only missing blank keys under authorization, resolves incompatible existing values deliberately, and validates conformance and content preservation. Existing valid values are never cleared. Nothing is automatically normalized, renamed, or migrated.

## Blueprint Scaffolding

`app/Blueprints/Games/` includes empty `.gitkeep` files so Git preserves `Data/Game/Attachments/` and `Views/`. These are packaging placeholders, not notes or semantic knowledge. Copying this starter material into a new database preserves the required empty directory structure. Later blueprint changes do not update an existing live database.
