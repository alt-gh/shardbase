# ShardBase Validation Tooling

The validator performs read-only structural checks against version `foundation-1` of the [System Specification](../Docs/Shard%20System%20Specification.md). A successful run means the implemented checks passed; it is not proof of full database-semantic conformance or Foundation completion.

## Setup and Commands

This implementation requires Python 3.10 or newer and the pinned PyYAML dependency in `requirements.txt`. It has been tested with Python 3.14. These are tooling requirements, not universal ShardBase architectural requirements.

Run these commands from the repository root. The example environment is temporary and entirely outside the vault; recreate it if the operating system removes it. A persistent environment may instead live in another user-selected location outside the project and synchronized vault.

```sh
shardbase_runtime="/tmp/shardbase-validator-venv"
python3 -B -m venv "$shardbase_runtime"
"$shardbase_runtime/bin/python" -B -m pip install --no-cache-dir --no-compile -r app/Scripts/requirements.txt
"$shardbase_runtime/bin/python" -B app/Scripts/validate_shardbase.py
"$shardbase_runtime/bin/python" -B -m unittest discover -s app/Scripts -p 'test_*.py' -v
```

To inspect one database, append its root path to the validator command. The path must be a direct child of an `app/Knowledge/Databases/` boundary, including when testing a temporary copy. The sanitized fixture and Games blueprint must be copied into that layout before validating them; the tests do this automatically in temporary storage outside the vault.

Dependency installation downloads software; validation itself performs no network operations. Validation never writes, renames, repairs, or migrates canonical files. `-B` keeps Python bytecode out of the project, and dependency installation disables persistent pip caching and compilation.

## Implemented Checks

- Discover every direct database directory, including incomplete roots missing `Database.md`; report discovery failures rather than treating them as an empty instance.
- Parse UTF-8 YAML frontmatter with [PyYAML's safe loader](https://pyyaml.org/wiki/PyYAMLDocumentation), supporting block and flow collections, comments, quoted escapes, multiline values, and ordinary aliases/merges. Explicit duplicate keys, unsupported tags, malformed YAML, and non-mapping frontmatter produce diagnostics. PyYAML's scalar resolution applies: quote text such as `yes`, `on`, or numeric identifiers when a string is intended.
- Check manifest fields and scalar/list shapes, integer `manifest_version: 1`, an opening H1, required H2 sections and H3 Includes/Excludes beneath Scope, heading depth/spacing, collection declarations, root `Attachments/`, and `Views/`. Unsupported manifest versions stop inspection of that database's contents.
- Reject traversal and absolute collection paths before scanning. Check resolved containment before reading structural files or directories, including symlink targets. Database-root symlinks require ownership review and are not followed by this implementation.
- Discover structural candidates at collection roots and one workspace level. Exclude attachment subtrees and root Agents, Templates, and Views. Check workspace Core identity, naming, lineage membership, and split placement. Nested directories other than `Attachments/` are reported for resource-contract review without recursively scanning them.
- Inspect direct root Markdown files other than `Database.md` for misplaced `type`, `core`, or `parent_note` declarations and report `note-location`. These files never enter structural link resolution. Ordinary root resources without those declarations are not treated as structural notes; malformed frontmatter or unreadable root Markdown receives `root-frontmatter` or `read-error`. This targeted check does not certify arbitrary resource contracts or infer structural intent from prose.
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

Root placement and manifest heading checks correct false acceptance under existing rules. The naming fixes implement the approved normative `foundation-1` specification boundary and can change expected filenames for previously accepted state. `manifest_version` remains `1`; it does not identify the specification version under which a database was authored. The validator checks only the current documented scope, without historical-version inference or migration. See System Specification Section 19.2 for the preservation-oriented transition: review affected files and references, retain a recoverable local copy, resolve collisions, explicitly authorize the bounded rename/reference update, and validate preservation and conformance. Nothing is automatically normalized, renamed, or migrated.

## Blueprint Scaffolding

`app/Blueprints/Games/` includes empty `.gitkeep` files so Git preserves `Data/Game/Attachments/` and `Views/`. These are packaging placeholders, not notes or semantic knowledge. Copying this starter material into a new database preserves the required empty directory structure. Later blueprint changes do not update an existing live database.
