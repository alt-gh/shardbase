# ShardBase CLI and Validation Tooling

This document describes the **current implementation** in `app/Scripts/`: how to run it, what it does, and what it does not yet do.

It does not define ShardBase architecture. Universal requirements come from [`../Docs/Shard System Specification.md`](../Docs/Shard%20System%20Specification.md); database-specific requirements come from the target database's root `Database.md`.

Current tooling targets System Specification `foundation-3` within the implementation scope described below.

## Runtime Setup

The current scripts require Python 3.10 or newer and the pinned PyYAML dependency in `requirements.txt`. These are tooling requirements, not universal ShardBase requirements.

Keep the Python environment, dependencies, bytecode, caches, and test instances outside the project/vault. Run from the repository root:

```sh
shardbase_runtime="/tmp/shardbase-validator-venv"
python3 -B -m venv "$shardbase_runtime"
"$shardbase_runtime/bin/python" -B -m pip install --no-cache-dir --no-compile -r app/Scripts/requirements.txt
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py new
"$shardbase_runtime/bin/python" -B app/Scripts/validate_shardbase.py
"$shardbase_runtime/bin/python" -B -m unittest discover -s app/Scripts -p 'test_*.py' -v
```

Dependency installation may access the network. Draft creation and validation operate locally and do not call external services.

Use `-B` or `PYTHONDONTWRITEBYTECODE=1` for every Python runner that touches the project. These settings prevent new bytecode but do not remove stale generated files already present.

## Draft Creation

Run:

```sh
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py new
```

The current `new` command creates an **Inbox draft**, not canonical database state. It asks for a title, Core/Shard/Pebble draft type, and optional alias, then automatically saves to `app/Knowledge/Inbox/<portable title>.md`. There is no destination prompt or option.

Users can edit and move drafts manually when ready. Moving a draft into a live database requires the review described under **Promotion Status** below.

Any draft type may be created without an existing Core, parent, or live database. The command has no parent picker and no `--parent` option. Supporting drafts may leave `core` and `parent_note` blank for later review.

For unattended use:

```sh
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py new --title "Example Game" --type core --alias ""
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py new --title "Zombies" --type shard --alias "Survival"
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py new --title "Terminus" --type pebble --alias ""
"$shardbase_runtime/bin/python" -B app/Scripts/shardbase.py new --help
```

The default instance is the checkout containing the script. Use `new --root "/path/to/instance"` to target another existing ShardBase instance containing `app/`.

### Draft Contents

The shipped Games templates create all eight universal note fields and a single H1. For example:

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

This is a draft representation. It is not proof that the note is a valid canonical Shard.

The title is used for the H1 and draft filename. The command does not infer ancestry from the title, assign the canonical stable opaque ID, construct the foundation-3 supporting filename, or validate the database semantic contract.

The optional alias becomes a one-item YAML string list. Skipping it preserves the template default. Canonical note IDs and timestamps are not generated. A blank `id` is acceptable in these pre-structural Inbox drafts but is invalid after canonical materialization under foundation-3.

### Template Resolution

The Games blueprint supplies:

- `Templates/Game.md`
- `Templates/Game Shard.md`
- `Templates/Game Pebble.md`

The requested structural draft type chooses the corresponding template.

The CLI looks for a live database whose manifest identifies `database_id: games`. If exactly one owner is identified, its matching template is used. If no live Games owner is identified, the instance's Games blueprint is used. Multiple matching owners are an ambiguity and must be resolved explicitly.

A missing selected live template is reported rather than silently copied from the blueprint. The CLI never creates or synchronizes a live database as a side effect.

Template YAML must be safely parseable. The creator supplies missing universal draft fields, applies the selected draft `type`, and preserves other template metadata without claiming semantic conformance. Template bodies are ignored and no template code is executed.

The Core template's `[[{{stem}}]]` becomes a provisional self-link. Legacy unresolved Core/parent placeholders are rendered blank rather than resolved through a parent search.

## Promotion Status

There is currently **no automatic promotion command, direct canonical creation command, or filesystem watcher**.

To promote a draft manually, the user must determine database ownership, collection, Pool, Core, parent, structural role, semantic metadata, assign a valid database-unique stable opaque `id`, derive the canonical filename, and choose valid placement under the System Specification and destination `Database.md`. The current validator can then check its implemented structural scope, but database semantics still require separate review.

Moving a file manually does not automatically run validation.

Canonical creation/promotion should eventually validate both universal and database-semantic constraints before a write. That capability is not implemented yet.

## Read-Only Validator

Run all live databases:

```sh
"$shardbase_runtime/bin/python" -B app/Scripts/validate_shardbase.py
```

To inspect one database, append its root path. The path must be a direct child of an `app/Knowledge/Databases/` boundary, including for temporary test copies.

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

- `0` — no issues in implemented scope, including an empty instance with no database candidates;
- `1` — validation/discovery issues or an operation error, depending on command;
- `2` — invalid CLI command syntax for `shardbase.py`;
- `130` — draft creation cancelled or ended by input termination.

Validator diagnostics include a path, stable issue code, and message. Consumers should use issue codes rather than parse human-readable messages or rely on issue counts.

YAML errors report location without echoing source content.

## File Safety

Draft creation uses a non-empty single-line title, portable output filename, output-boundary/symlink checks, and exclusive creation. It never overwrites an existing output path or silently numbers collisions.

These are file-safety protections, not structural validation. Draft creation does not inspect existing canonical notes to establish eligibility or resolve canonical naming collisions.

The implementation assumes a stable local filesystem during an operation and is not transactional. An interrupted draft write may leave a partial new draft; a rerun will refuse to overwrite it. Error recovery never deletes existing user knowledge.

## Tests and Fixtures

Tests use temporary instances outside the vault. Keep `TMPDIR` or its platform equivalent outside the vault when customizing it.

The sanitized fixtures and tests prove the current structural validation behavior, including valid/invalid manifests, YAML shapes, common note metadata, lineage failures, workspace placement, filename normalization/collisions, boundary escapes, and Markdown heading checks.

Semantic-schema, attachment-reference, fragmentation/materialization, and full Inbox-to-canonical proof fixtures remain future work.

## Compatibility

The `new` command no longer accepts `--destination`; existing command lines must omit that flag and its value. New drafts always go directly to Inbox. Existing `Inbox/Staged/` files remain untouched and can be organized manually. This CLI interface change does not change the universal contract or require a knowledge migration.

The validator checks the current `foundation-3` contract in its documented scope. `manifest_version: 1` identifies only the manifest schema and does not identify the System Specification version under which a database was authored.

The validator does not migrate older state. For the recorded `foundation-1`, `foundation-2`, and `foundation-3` compatibility boundaries and preservation-oriented transitions, use the System Specification.

## Blueprint Scaffolding

`app/Blueprints/Games/` includes tracked empty-directory scaffolding for `Data/Game/Attachments/` and `Views/`, plus draft templates and the optional Vera Agent resource. Packaging placeholders are not semantic knowledge.

Copying a blueprint materializes a starting database package. Later blueprint changes never silently update a live database.
