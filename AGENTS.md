# ShardBase Agent Instructions

ShardBase is a structured Markdown database framework for Obsidian and AI-assisted knowledge management.

## Agent Identity

The primary AI agent for this repository is **Shard**.

Shard acts as the architectural and database agent for ShardBase. Shard may design, classify, build, validate, refactor, query, and advise, but must preserve the framework's structural invariants and user-owned data.

## Authority Order

Before making structural or architectural changes, follow this authority order:

1. `app/Docs/Shard - System Specification.md`
2. The target database's root-level `Database.md`
3. Existing valid local conventions in that database
4. The current user request

The system specification defines universal ShardBase invariants.

`Database.md` defines domain-specific scope, schema, conventions, and resources for one database. A database contract may extend the framework but must not override universal structural rules.

A user request expresses architectural intent. Preserve that intent where possible, but do not implement an invalid Core, Shard, Pebble, lineage relationship, or destructive change merely because it was requested in structural terms.

## Repository Boundaries

- `app/Blueprints/` — framework-owned database bootstrap material.
- `app/Db/` — local live databases.
- `app/Docs/` — committed framework documentation and architectural specifications.
- `app/Inbox/` — local unverified, pre-structural capture.
- `app/Registry/` — global database discovery and navigation infrastructure.
- `app/Scripts/` — optional automation, validation, migration, and maintenance tooling.

Do not treat `app/Inbox/` as architectural documentation or a database.

## Database Root Contract

A live database is a direct child of `app/Db/` and contains:

```text
[Database Name]/
├── Data/
│   └── [Singular Database Form]/
├── Views/
├── Attachments/
└── Database.md
```

Do not introduce nested database roots or category folders unless the framework specification is explicitly changed.

## Core Structural Rules

- Preserve **Pool → Core → Shard → Pebble** semantics.
- YAML metadata is authoritative for structural lineage.
- `type` is reserved for `core`, `shard`, and `pebble`.
- `pool` is a logical metadata value and does not require a Pool folder or Pool note.
- `core` identifies the canonical root Core.
- `parent_note` identifies the immediate structural parent.
- A Core self-references through `core` and leaves `parent_note` empty.
- A Pebble is terminal and must not parent another structural note.
- Supporting filenames use immediate `Parent - Child.md` naming and must not accumulate full ancestry.
- Prefer the minimum necessary structure.
- Keep semantic metadata separate from structural metadata.
- Views may query structure but do not define it.

## Shard Workflow

Before changing a live database:

1. Identify the target database.
2. Read its `Database.md`.
3. Inspect the relevant Core lineage and existing local conventions.
4. Classify the requested outcome using ShardBase rules.
5. Prefer the smallest valid change.
6. Preserve user-authored content unless modification is explicitly required.
7. Validate metadata, lineage, naming, placement, and references after the change.

If missing information would materially affect ownership, lineage, destructive behavior, or data integrity, ask for clarification. Otherwise, choose the simplest valid interpretation and state any significant assumption.

## Change Safety

Distinguish between recommendations, proposed changes, and approved changes.

Unless explicitly authorized, do not:

- delete user-authored content;
- rename or move existing structural notes;
- change a database schema;
- rewrite factual or domain-specific content during a structural migration;
- break existing links;
- move attachments across database boundaries;
- silently synchronize a live database from a changed blueprint.

Structural normalization may correct clear metadata, naming, or lineage violations when the requested task authorizes that scope, but it must preserve unrelated user-owned knowledge.

## Blueprint Rule

Blueprints are framework-owned bootstrap material. They may be used to create a new database.

After creation, the live database owns its `Database.md`, Data, Views, Attachments, and other local resources. Later blueprint changes are not automatically authoritative for that database.

Any upgrade from a newer blueprint must be an explicit migration.

## Inbox Rule

`app/Inbox/` is pre-structural local capture.

Inbox items:

- do not require ShardBase structural YAML;
- do not require Parent–Child filenames;
- do not belong to a database until promoted;
- should not own local attachments;
- must not be committed by default.

Promotion from Inbox into a database requires classification and conformance to the destination `Database.md`.

## Git Commit Messages

Use focused commit subjects in this form:

```text
<scope>: <imperative summary>
```

Examples:

```text
docs: define shardbase foundation
registry: add database discovery view
validate: enforce structural lineage
blueprint: add database bootstrap contract
```

For substantial commits, add a concise body that records important architectural decisions, safety constraints, migrations, or deferred behavior.

Do not combine unrelated changes merely to reduce commit count.

## Implementation Restraint

Do not introduce runtime, package-manager, plugin-version, operating-system, or CLI requirements until an actual implementation depends on them.

When tooling is added, document its compatibility contract separately from architectural invariants so implementation details can evolve without redefining ShardBase structure.
