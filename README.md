# ShardBase

ShardBase is a structured Markdown database framework designed for Obsidian and AI-assisted knowledge management.

Its goal is simple: let a knowledge base grow without losing lineage, portability, readability, or control.

ShardBase organizes structural knowledge through four concepts:

**Pool → Core → Shard → Pebble**

- **Pool** — a logical grouping inside a database.
- **Core** — the root entity of a knowledge lineage.
- **Shard** — a meaningful, reusable subdivision of a Core or another Shard.
- **Pebble** — a terminal structural note that must not have structural children.

## Shard

**Shard** is the AI agent for ShardBase.

Shard is responsible for understanding database contracts, classifying information, preserving lineage, proposing or creating valid structure, auditing databases, and helping the framework evolve safely.

Shard does not infer architecture from filenames alone. Structural YAML is authoritative for lineage, while filenames and folders remain human-readable context.

When operating on a database, Shard follows this authority order:

1. `app/Docs/Shard - System Specification.md` — universal ShardBase rules.
2. The target database's `Database.md` — database-local purpose, scope, schema, and conventions.
3. Existing valid database content — continuity and established local practice.
4. The current user request — desired outcome, subject to structural validity and change-safety rules.

## Repository Structure

```text
shardbase/
├── .obsidian/
├── app/
│   ├── Blueprints/
│   ├── Db/
│   │   └── [Database Name]/
│   │       ├── Data/
│   │       │   └── [Singular Database Form]/
│   │       │       ├── Core.md
│   │       │       └── Core - Shard.md
│   │       ├── Views/
│   │       ├── Attachments/
│   │       └── Database.md
│   ├── Docs/
│   │   └── Shard - System Specification.md
│   ├── Inbox/
│   ├── Registry/
│   │   └── Registry.md
│   └── Scripts/
├── .gitignore
├── AGENTS.md
└── README.md
```

## Database Anatomy

Each live database is a direct child of `app/Db/` and is self-contained.

### `Database.md`

The database manifest and local contract. It defines database identity, scope, data folder, semantic schema, conventions, and resources.

### `Data/[Singular Database Form]/`

Contains all structural notes for the database.

Pools are **logical metadata values**, not required filesystem folders. This keeps the database filesystem shallow while preserving flexible grouping through YAML and queries.

### `Views/`

Contains database-local views and queries. Views consume metadata; they do not define structural truth.

### `Attachments/`

Contains local files owned by the database. Cross-database attachment references should be avoided so a database remains portable.

## Structural Metadata

Every Core, Shard, and Pebble uses the universal structural fields:

```yaml
---
type: core | shard | pebble
pool: Pool Name
core: "[[Canonical Core Note]]"
parent_note:
status: active
---
```

For supporting notes, `parent_note` points to the immediate structural parent. For a Core, `parent_note` is empty.

Domain-specific meaning belongs in separate database-defined metadata. The reserved `type` field is never repurposed for semantic categories such as person, project, game, book, source, or organization.

## Naming

Core files use their canonical name:

```text
Core.md
```

Supporting notes use an immediate Parent–Child filename:

```text
Parent - Child.md
```

Only the immediate relationship belongs in the filename. Full ancestry belongs in YAML lineage.

## Minimum Necessary Structure

ShardBase intentionally avoids premature fragmentation.

A new structural note should exist only when it provides meaningful value through independent growth, querying, navigation, reuse, or lifecycle management. Otherwise, the information should remain inside its parent note as ordinary Markdown structure.

Future notes may be represented by unresolved wikilinks until they justify materialization.

## Framework Boundaries

- `app/Blueprints/` contains framework-owned database bootstrap material.
- `app/Db/` contains local live databases.
- `app/Docs/` contains committed framework documentation.
- `app/Inbox/` contains unverified, pre-structural local capture.
- `app/Registry/` contains global discovery and navigation infrastructure.
- `app/Scripts/` contains optional automation and validation tooling.

Blueprints may initialize a database, but a live database owns its state after creation. Blueprint changes must never silently rewrite existing databases.

## Git and Local Data

The framework repository is intended to be safe to publish.

By default:

- live database contents under `app/Db/` are ignored;
- Inbox contents under `app/Inbox/` are ignored;
- framework documentation, registry infrastructure, scripts, and blueprints are committed;
- empty local-data boundaries are retained with `.gitkeep` files.

If a user intentionally wants to version a live database, that should be an explicit repository policy change rather than an accidental side effect.

## Project Status

This repository is at its foundation stage.

The first version establishes the architecture and agent contract before locking in implementation details such as a CLI runtime, compatibility matrix, migration engine, or blueprint materialization format. Those concerns should be added only when an implementation requires them.

The architectural source of truth is:

`app/Docs/Shard - System Specification.md`
