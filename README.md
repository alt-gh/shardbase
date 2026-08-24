# ShardBase

ShardBase is a privacy-focused, user-owned structured Markdown knowledge-base framework designed to grow into an interconnected personal digital brain and source of truth.

It uses human-readable Markdown and YAML to organize knowledge through explicit structure, metadata, relationships, links, search, views, and AI-assisted interaction while keeping the underlying information understandable and editable independently of any single tool. ShardBase targets Obsidian as its primary knowledge environment, supports modular databases and extensible tooling, and is designed to let a user's knowledge grow across many areas of life without sacrificing readability, portability, structural integrity, privacy, or control.

## Why ShardBase

Personal knowledge becomes more valuable as it accumulates, connects, and remains usable over time, but it also becomes harder to keep coherent, connected, understandable, and useful as it grows.

ShardBase provides a durable shared architecture for that growth. It is designed to reduce fragmentation, preserve lineage and context, support reliable retrieval and machine interpretation, and keep the organizational burden from growing faster than the usefulness of the knowledge itself.

The long-term goal is a user-owned personal source of truth that can support memory, understanding, discovery, decision-making, and AI-assisted interaction without requiring the user to surrender ownership or architectural control of their knowledge.

## Core Design Commitments

- **User-owned and privacy-focused** — the user owns and controls their core data. ShardBase does not require that data to leave the user's local environment for core operation.
- **Markdown is the foundation** — core knowledge remains stored in human-readable Markdown and YAML so it can be inspected, edited, copied, searched, versioned, and processed independently of ShardBase-specific tooling.
- **Obsidian is the primary target, not the data owner** — ShardBase is designed for a strong Obsidian experience, but its core knowledge and structural meaning must remain understandable outside Obsidian.
- **Tools enhance rather than define the knowledge** — Dataview is a primary and canonical interface for interacting with ShardBase data in Obsidian, while views, scripts, plugins, AI agents, and future tooling must not become the sole source of structural truth.
- **AI assistance is intentional but optional** — AI can interpret, recommend, classify, retrieve, explain, and assist with maintenance, while explicit rules and deterministic validation preserve predictable structure. The knowledge base must remain durable and meaningful without AI.
- **Human authority is preserved** — ShardBase may automate repetitive, deterministic, and safely reversible work, but consequential, ambiguous, privacy-sensitive, or destructive decisions remain under meaningful user control.
- **Minimum necessary structure** — ShardBase uses the minimum structure necessary to preserve useful organization, relationships, growth, integrity, queryability, navigation, and lifecycle management.
- **Framework, not monolith** — ShardBase defines universal structural rules while allowing individual databases to own their domain-specific scope, semantic metadata, conventions, views, and resources.

External synchronization, backup, cloud storage, publishing, and sharing services are user choices and are separate from ShardBase's core operation.

## Structural Model

ShardBase organizes structural knowledge through four concepts:

**Pool → Core → Shard → Pebble**

- **Pool** — a logical grouping inside a database.
- **Core** — the root entity of a knowledge lineage.
- **Shard** — a meaningful, reusable subdivision of a Core or another Shard.
- **Pebble** — a terminal structural note that must not have structural children.

Structural YAML is authoritative for lineage. Filenames provide human-readable relationship context, filesystem paths provide database ownership context, and Markdown headings provide internal document hierarchy.

## Shard

**Shard** is the canonical primary architectural and database AI agent for ShardBase.

Shard is responsible for understanding database contracts, classifying information, preserving lineage, proposing or creating valid structure, auditing databases, designing queries, and helping the framework evolve safely. ShardBase may support additional AI agents, but structural operations remain subject to the same architectural contracts and user-control boundaries.

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
│   │       │       ├── Core - Shard.md
│   │       │       └── Core - Shard - Pebble.md
│   │       ├── Views/
│   │       ├── Attachments/
│   │       └── Database.md
│   ├── Docs/
│   │   ├── Shard - System Specification.md
│   │   └── ShardBase - Foundation Roadmap Workbook.md
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

Contains database-local views and queries. Dataview is a primary and canonical ShardBase interface in Obsidian. Views consume metadata; they do not define structural truth.

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

Supporting notes use bounded Core context:

```text
Core - Current Node.md
Core - Immediate Parent - Current Node.md
```

A direct child of the Core uses two structural context components. A deeper descendant uses three: the root Core, the immediate parent's current-node name, and the current node. The immediate-parent component is not the parent's full filename, so filenames never accumulate beyond three structural context components.

Full ancestry remains in YAML lineage through `core` and `parent_note`. If two notes would still produce the same filename, the collision must be reported and resolved through meaningful disambiguation rather than by adding more ancestor components.

## Minimum Necessary Structure

ShardBase intentionally avoids premature fragmentation.

A new structural note should exist only when it provides meaningful value through independent growth, querying, navigation, reuse, or lifecycle management. Otherwise, the information should remain inside its parent note as ordinary Markdown structure.

Future notes may be represented by unresolved wikilinks until they justify materialization.

## Framework Boundaries

- `app/Blueprints/` contains framework-owned database bootstrap material.
- `app/Db/` contains local live databases.
- `app/Docs/` contains committed framework documentation and architectural specifications.
- `app/Inbox/` contains local unverified, pre-structural capture.
- `app/Registry/` contains global discovery and navigation infrastructure.
- `app/Scripts/` contains optional automation, validation, migration, and maintenance tooling.

Blueprints may initialize a database, but a live database owns its state after creation. Blueprint changes must never silently rewrite existing databases.

## Git and Local Data

The framework repository is intended to be safe to publish while keeping user-owned live knowledge local by default.

By default:

- live database contents under `app/Db/` are ignored;
- Inbox contents under `app/Inbox/` are ignored;
- framework documentation, registry infrastructure, scripts, and blueprints are committed;
- empty local-data boundaries are retained with `.gitkeep` files.

If a user intentionally wants to version a live database, that should be an explicit repository policy change rather than an accidental side effect.

## Project Status

ShardBase is in its foundation stage. Product Identity has been defined in the Foundation Roadmap Workbook, while the remaining conceptual language, governance, canonical implementation artifacts, validation behavior, and foundation proof are still in progress.

The foundation establishes product and architectural contracts before locking in implementation details such as a CLI runtime, compatibility matrix, migration engine, or blueprint materialization format. Those concerns should be added only when an implementation requires them.

The architectural source of truth is:

`app/Docs/Shard - System Specification.md`
