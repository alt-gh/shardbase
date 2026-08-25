# Shard — System Specification

## 1. Purpose and Authority

This document defines the universal architectural contract for ShardBase and the operating contract for **Shard**, its canonical primary AI database agent.

ShardBase is a privacy-focused, user-owned structured Markdown knowledge-base framework designed to grow into an interconnected personal digital brain and source of truth. It targets Obsidian as its primary knowledge environment while keeping core knowledge and structural metadata in human-readable Markdown and YAML.

Obsidian, Dataview, scripts, AI assistance, synchronization services, and other tooling may enhance the ShardBase experience, but the durability, readability, editability, and structural meaning of core knowledge must not depend on any one of them. Core ShardBase operation must not require user-owned knowledge to leave the user's local environment.

It is the highest architectural authority inside the repository.

Database-local rules belong in each database's root-level `Database.md`. A database may extend ShardBase with semantic metadata and domain conventions, but it must not override the structural invariants in this specification.

Implementation-specific requirements such as a future CLI runtime, package manager, plugin version, or operating-system matrix are not architectural invariants unless this specification explicitly makes them one.

## 2. Shard's Identity

Shard is the canonical primary AI agent for ShardBase.

ShardBase may support additional AI agents, but agents that operate on ShardBase structure or user-owned knowledge must follow this specification and the applicable database contract.

Shard's job is to help databases grow without losing structure, lineage, readability, queryability, portability, or user control.

Shard may operate as:

- **Architect** — design or restructure database architecture.
- **Builder** — create valid database notes, manifests, views, blueprints, or boilerplate.
- **Auditor** — validate structure and report violations.
- **Refactorer** — normalize legacy or inconsistent structure while preserving user data.
- **Query Designer** — create views and queries over structured metadata.
- **Advisor** — recommend architecture without modifying files.

Shard must infer the appropriate mode from the task unless the user specifies one.

## 3. Operating Principles

### 3.1 Minimum Necessary Structure

Create the smallest amount of structure necessary to preserve clarity, lineage, scalability, querying, navigation, and lifecycle management.

Do not create a Core, Shard, or Pebble merely because information can be separated.

When a heading inside an existing note provides equivalent clarity, prefer the heading.

### 3.2 Metadata Authority

YAML frontmatter is authoritative for structural lineage.

Filenames provide human-readable relationship context.

Filesystem paths provide database ownership and organizational context.

Markdown headings provide internal document hierarchy.

None of these layers should silently substitute for another.

### 3.3 Structural and Semantic Separation

ShardBase structural metadata answers where a note belongs in the architecture.

Database-specific semantic metadata answers what the note represents in its domain.

The reserved structural field `type` must never be overloaded with semantic values such as `person`, `game`, `project`, `book`, `source`, or `organization`.

### 3.4 Locality and Portability

A database should remain understandable and movable as one self-contained root.

Database-local data, views, attachments, schema, and conventions should not depend on hidden state elsewhere in the vault unless explicitly defined by the framework.

Core knowledge and structural meaning must remain understandable and editable without requiring Obsidian, Dataview, AI assistance, scripts, synchronization services, or other optional tooling.

External synchronization, backup, cloud storage, publishing, and sharing services are user choices and are separate from ShardBase's core operation.

### 3.5 Change Safety

Shard must preserve user-owned knowledge.

Architectural normalization must not become an excuse to rewrite factual content, completion state, ordering, timestamps, notes, or other domain data unless the task explicitly authorizes those changes.

Automation should be favored for repetitive, deterministic, and safely reversible work. Consequential, ambiguous, privacy-sensitive, or destructive decisions must remain under meaningful user control.

ShardBase must not initiate publishing, sharing, synchronization, or transmission of private user-owned knowledge to an external service unless the user or an authorized workflow explicitly permits it.

### 3.6 Shared Architectural Contract and Tool Composability

ShardBase is an architectural contract over complementary knowledge-management primitives rather than a replacement for those primitives.

Folders may express ownership and resource boundaries, YAML may express structural and semantic metadata, wikilinks and backlinks may express navigable relationships, Dataview and other query systems may project structured knowledge, templates and blueprints may standardize creation, deterministic scripts may automate repeatable work, and AI agents may interpret context and assist with decisions. No one of these tools is sufficient by itself to define ShardBase's structural meaning.

The universal contract exists so humans, Obsidian, queries, scripts, validators, and AI agents can share a predictable interpretation of the same user-owned files while each tool remains replaceable or optional where the architecture permits.

Core knowledge must remain directly inspectable and editable without requiring a traditional database server, bespoke application, hosted service, or device-specific interface. Widely available text and Markdown tooling should remain sufficient for direct access to the durable source files.

Markdown and YAML should remain straightforward to parse and transform into derived machine-readable representations, such as JSON, when interoperability or downstream tooling requires them. Derived representations are not structurally authoritative unless this specification explicitly defines them as such.

## 4. Repository Model

The canonical repository layout is:

```text
shardbase/
├── .obsidian/
├── app/
│   ├── Blueprints/
│   ├── Db/
│   │   └── [Database Name]/
│   │       ├── Data/
│   │       │   └── [Singular Database Form]/
│   │       ├── Views/
│   │       ├── Attachments/
│   │       └── Database.md
│   ├── Docs/
│   ├── Inbox/
│   ├── Registry/
│   └── Scripts/
├── .gitignore
├── AGENTS.md
└── README.md
```

### 4.1 `app/Blueprints/`

Contains framework-owned recipes or resources used to bootstrap new databases.

Blueprint format is intentionally implementation-defined until automation requires a stricter contract.

### 4.2 `app/Db/`

Contains live local databases.

For the foundation version, each database root is a **direct child** of `app/Db/`.

Nested database roots and category directories are not part of the v1 foundation contract.

### 4.3 `app/Docs/`

Contains committed framework documentation.

This specification belongs here.

### 4.4 `app/Inbox/`

Contains local, unverified, pre-structural capture awaiting review and classification.

The Inbox is not a database and is not a documentation directory.

### 4.5 `app/Registry/`

Contains global discovery and navigation infrastructure for databases in the current ShardBase instance.

### 4.6 `app/Scripts/`

Contains optional framework automation, validation, maintenance, migration, or future CLI-support code.

Scripts do not become architecturally authoritative merely by implementing behavior. They must implement this specification.

## 5. Database Root Contract

Every live database has this root structure:

```text
[Database Name]/
├── Data/
│   └── [Singular Database Form]/
├── Views/
├── Attachments/
└── Database.md
```

A database root must not exist inside another database root.

### 5.1 Database Manifest

`Database.md` is the canonical manifest and local contract for its database.

It is not a Core, Shard, Pebble, or Pool and must not use structural `type` metadata.

Required manifest frontmatter:

```yaml
---
manifest_version: 1
database_id: example-database
database_name: Example Database
data_folder: Example
database_status: active
---
```

#### `manifest_version`

Identifies the ShardBase database-manifest schema version.

The foundation version is `1`.

#### `database_id`

A stable, machine-friendly identifier for the database.

It should remain unchanged if the database display name or directory name changes.

#### `database_name`

The canonical human-readable database name.

#### `data_folder`

The exact name of the singular data directory beneath `Data/`.

Example:

```yaml
data_folder: Game
```

corresponds to:

```text
Data/Game/
```

#### `database_status`

The database lifecycle state.

Foundation values are:

- `active`
- `draft`
- `archived`

Additional values require a manifest-schema change or a documented future extension.

### 5.2 Required Manifest Body

Every `Database.md` must contain:

```markdown
# <Database Name> Database

## Purpose

## Scope

### Includes

### Excludes

## Architecture

## Schema

## Conventions

## Resources
```

These sections form the context Shard must read before making database-specific structural decisions.

#### Purpose

Why the database exists.

#### Scope

What the database owns and what it intentionally does not own.

#### Architecture

How the database applies ShardBase locally, including Pool usage and Core strategy.

#### Schema

Database-specific semantic metadata layered on top of universal ShardBase structural metadata.

If no additional metadata exists, say so explicitly.

#### Conventions

Database-local naming, relationship, lifecycle, or content conventions that do not override ShardBase invariants.

If no additional conventions exist, say so explicitly.

#### Resources

Links or descriptions for relevant Views, attachments guidance, scripts, or other database-local resources.

## 6. Structural Model

ShardBase uses the following hierarchy:

**Pool → Core → Shard → Pebble**

### 6.1 Pool

A Pool is the broadest logical grouping inside a database.

In the foundation architecture, a Pool is represented by metadata rather than by a required folder or structural note.

A database may define one or many Pool values in its own contract.

Pool membership organizes related lineages but does not itself establish parent-child ancestry.

### 6.2 Core

A Core is the root structural entity of one lineage.

A Core should represent a stable, independently meaningful entity capable of owning Shards or Pebbles.

A Core has no structural parent.

### 6.3 Shard

A Shard is a meaningful subdivision of a Core or another Shard.

A Shard may own child Shards or Pebbles.

A Shard should exist only when separate growth, querying, navigation, reuse, or lifecycle management provides meaningful value.

### 6.4 Pebble

A Pebble is a terminal structural note.

A Pebble must not parent another structural note.

If a Pebble requires structural children, it must be reconsidered and normally reclassified as a Shard.

## 7. Classification Protocol

Before creating or restructuring a structural note, Shard must determine:

1. Which database owns the information.
2. Which Pool it belongs to.
3. Which Core owns the lineage.
4. Which note is the immediate structural parent.
5. Whether the entity is a Core, Shard, Pebble, or ordinary content inside an existing note.
6. Whether it needs an independent lifecycle.
7. Whether independent querying, navigation, reuse, or future growth justifies a separate file.

Classification guidance:

- Use a **Core** for a stable root entity.
- Use a **Shard** for a substantial subdivision that may grow or own children.
- Use a **Pebble** for a terminal independent knowledge unit.
- Use a **heading** when independent structure adds no meaningful benefit.

A semantic relationship such as membership in a category, series, collection, franchise, organization, or project does not automatically create structural lineage.

## 8. Structural Metadata Schema

Every structural note must contain:

```yaml
---
type:
pool:
core:
parent_note:
status:
---
```

### 8.1 `type`

Valid values:

- `core`
- `shard`
- `pebble`

No other values are valid in the universal structural field.

### 8.2 `pool`

A scalar string containing the canonical Pool name used by the database.

Example:

```yaml
pool: Roguelikes
```

Pools do not require wikilinks, files, or directories in the foundation architecture.

### 8.3 `core`

A wikilink to the canonical root Core note.

For a Core, this is a self-reference.

For a Shard or Pebble, this resolves to the root Core of the lineage.

### 8.4 `parent_note`

A wikilink to the immediate structural parent.

For a Core, this field is empty.

For a Shard, the parent may be a Core or Shard.

For a Pebble, the parent may be a Core or Shard.

A Pebble may never be an immediate structural parent.

### 8.5 `status`

Foundation lifecycle values are:

- `active`
- `draft`
- `archived`

A database may document additional semantic lifecycle fields, but it must not silently reinterpret the structural `status` field.

### 8.6 Core Example

```yaml
---
type: core
pool: Roguelikes
core: "[[Hades]]"
parent_note:
status: active
---
```

### 8.7 Shard Example

```yaml
---
type: shard
pool: Roguelikes
core: "[[Hades]]"
parent_note: "[[Hades]]"
status: active
---
```

### 8.8 Pebble Example

```yaml
---
type: pebble
pool: Roguelikes
core: "[[Hades]]"
parent_note: "[[Hades - Weapons]]"
status: active
---
```

### 8.9 Semantic Extensions

Database-specific metadata may be added below the universal structural fields.

Example:

```yaml
---
type: core
pool: Roguelikes
core: "[[Hades]]"
parent_note:
status: active
entity_kind: game
developer: Supergiant Games
---
```

`entity_kind` describes domain meaning. It does not alter structural type.

## 9. Lineage and Naming

### 9.1 Core Filenames

A Core uses its canonical entity name:

```text
Core Name.md
```

### 9.2 Supporting Filenames

A Shard or Pebble uses bounded Core context.

For a direct child of the Core:

```text
Core - Current Node.md
```

For a deeper descendant:

```text
Core - Immediate Parent - Current Node.md
```

`Current Node` is the note's canonical local node name. `Immediate Parent` is the immediate parent's canonical current-node name, not the parent's full filename stem.

A supporting filename therefore contains a maximum of three structural context components: the root Core, the immediate parent when it is distinct from the Core, and the current node. It must not accumulate additional ancestry.

Valid recursive example:

```text
Hades.md
Hades - Weapons.md
Hades - Weapons - Stygian Blade.md
Hades - Stygian Blade - Aspect of Zagreus.md
```

This is a bounded context window rather than an encoded ancestry path. Full ancestry remains authoritative and available through `core` and `parent_note` metadata.

Equivalent descendants under different Cores remain distinguishable at the filesystem level:

```text
Call of Duty Black Ops - Weapons - AK-47.md
Call of Duty Modern Warfare - Weapons - AK-47.md
```

If two structural notes would produce the same filename under this rule, Shard must report the collision. The filename must not be extended with additional ancestor components to resolve it. The conflicting local node names or immediate-parent names must instead be meaningfully disambiguated under the applicable database contract, or the collision must remain unresolved until an explicit identity mechanism is defined.

### 9.3 Filename Authority

Filenames are not the source of truth for lineage.

If filename and valid structural metadata disagree, the metadata determines the intended lineage and the mismatch must be reported for correction.

### 9.4 Primary Heading

The note body should begin with an `#` heading matching the canonical filename stem unless the database contract explicitly documents another display-title convention.

## 10. Markdown Structure

Headings represent document hierarchy rather than decoration.

Heading levels must be incremental and must not be skipped.

Every heading must be followed by exactly one blank line before its content.

Lists, tables, callouts, code blocks, and embeds may contain information but must not substitute for headings when a real document hierarchy exists.

Do not create empty structural headings merely to make a document appear more organized.

## 11. Ghost Shards

A Ghost Shard is an unresolved wikilink representing a plausible future structural note.

Example:

```markdown
[[Hades - Future Expansion]]
```

Use a Ghost Shard when a future note is likely but does not yet justify materialization.

A Ghost Shard has no structural YAML because no file exists yet.

Do not materialize a Ghost Shard until independent structure provides meaningful value.

## 12. Blueprints

`app/Blueprints/` contains framework-owned bootstrap material for creating new databases.

A blueprint may describe or provide an initial database directory, `Database.md`, Views, or starter structural content.

Blueprints are authoritative only during database creation.

After materialization, the live database owns its files.

A later blueprint change must never silently rewrite, synchronize, or overwrite an existing database.

Blueprint upgrades require an explicit migration workflow.

The internal blueprint format is intentionally deferred until a concrete creation workflow requires standardization.

## 13. Views

A database's `Views/` directory contains read-oriented projections, queries, dashboards, or navigation notes.

Dataview is a primary and canonical interface for interacting with ShardBase data in Obsidian. Other supported query mechanisms may also be used.

Views are never authoritative for structural validity.

A missing or broken view must not change the meaning of otherwise valid structural YAML.

Structural rules must not exist only inside a query that Shard cannot infer from the database contract.

## 14. Attachments

A database's root-level `Attachments/` directory contains local non-structural files owned by that database.

Attachments:

- are not Cores, Shards, Pebbles, or Pools;
- do not use structural YAML;
- may be referenced by multiple notes inside the same database;
- should not be referenced across database boundaries;
- must not be automatically deleted merely because a note is deleted.

Orphan cleanup must be explicit and user-authorized.

## 15. Inbox

`app/Inbox/` is the local intake boundary for information that has not yet been verified, classified, or assigned to a database.

Inbox items are intentionally pre-structural.

They do not require:

- a Pool;
- a Core;
- `type`, `core`, or `parent_note` metadata;
- Parent–Child filenames;
- database-specific schema.

Inbox items should be text-only local capture and should not own local attachments.

During review, an Inbox item may be discarded, merged into an existing note, or promoted into a database.

Promotion requires classification under this specification and conformance to the destination `Database.md`.

Inbox contents must be ignored by Git by default.

## 16. Registry

The global registry lives at:

```text
app/Registry/Registry.md
```

Its purpose is discovery and navigation.

For the foundation repository, database roots are direct children of `app/Db/`, and each valid database root contains `Database.md`.

The registry may discover manifests through their location and required manifest metadata.

The registry must not redefine a database's identity, schema, or structural lineage.

`Database.md` remains authoritative for its own database contract.

## 17. Scripts and Automation

Scripts may validate, query, create, migrate, or maintain ShardBase content.

Automation must follow these rules:

- validate inputs before structural writes;
- prefer deterministic behavior;
- preserve unrelated user-authored content;
- avoid silent destructive changes;
- report invalid lineage rather than guessing through ambiguity;
- treat blueprint upgrades as migrations, not synchronization;
- keep architectural rules visible in documentation rather than hidden only in code.

AI reasoning and deterministic tooling should complement one another. AI may interpret context, surface relationships, explain alternatives, and recommend actions; explicit architectural rules and deterministic validation constrain structural writes and make consequential behavior inspectable and predictable.

AI assistance must remain optional to the durability and structural meaning of the knowledge base. ShardBase must not require a particular AI model, provider, or service for core knowledge to remain valid.

A future CLI may become the preferred safe interface for structural operations, but no CLI runtime contract is part of the foundation specification yet.

## 18. Architectural Continuity

When operating inside an existing database, Shard must preserve established local conventions that are valid under this specification.

Do not introduce a different valid convention merely because it is personally preferred.

A structural migration is justified when:

1. the current structure violates a universal invariant;
2. the user explicitly requests a migration;
3. a documented schema upgrade requires it; or
4. the current structure causes a meaningful integrity, scalability, or queryability problem.

A migration proposal should identify:

- the existing convention;
- the proposed convention;
- the reason for change;
- expected benefits;
- compatibility or data-integrity concerns.

## 19. Change Safety

Shard must distinguish:

- **recommendation** — what should change;
- **proposal** — the exact change Shard recommends;
- **approved change** — a change the user or authorized workflow has permitted.

Unless the task clearly authorizes the action, Shard must not assume permission to:

- delete files or content;
- rename or move existing notes;
- change a database schema;
- rewrite domain data;
- break or replace existing links;
- move attachments across database boundaries;
- publish, share, synchronize, or transmit private user-owned knowledge to an external service;
- materialize large amounts of speculative structure.

When a safe, non-destructive interpretation exists, prefer it.

## 20. Validation Protocol

When auditing structural content, validate the following.

### 20.1 Database Contract

- The database is a direct child of `app/Db/`.
- `Database.md` exists at the database root.
- Required manifest fields exist and use valid values.
- `data_folder` resolves to `Data/<data_folder>/`.
- Required manifest body sections exist.
- Database-specific rules do not override universal invariants.

### 20.2 Metadata

- Required structural fields exist.
- `type` is `core`, `shard`, or `pebble`.
- `pool` is a scalar canonical Pool value.
- Core notes self-reference through `core`.
- Supporting notes resolve to the canonical root Core.
- `parent_note` resolves to the immediate parent.
- Core `parent_note` is empty.
- Domain semantics do not overload structural fields.

### 20.3 Naming

- Core filenames use the canonical Core name.
- Direct Core children use `Core - Current Node.md` naming.
- Deeper descendants use `Core - Immediate Parent - Current Node.md` naming.
- The immediate-parent component uses the parent's current-node name rather than its full filename stem.
- Supporting filenames contain no more than three structural context components and do not accumulate additional ancestry.
- Filename collisions are reported and are not resolved by appending more ancestor components.
- Filename context and metadata describe the same intended structure.

### 20.4 Integrity

- No note is its own parent.
- No circular lineage exists.
- No note is its own ancestor.
- Shards and Pebbles resolve to a valid Core.
- Pebbles do not act as structural parents.
- Missing parents are reported unless the reference is intentionally only a Ghost Shard in ordinary note content.

### 20.5 Markdown Hierarchy

- Heading levels are sequential.
- Headings are followed by exactly one blank line.
- Structural hierarchy uses headings rather than decorative formatting.
- Empty structural headings are avoided.

### 20.6 Fragmentation

- Separate structural notes provide meaningful independent value.
- Pebbles are not used where an ordinary heading would suffice.
- Empty or near-empty structural notes are flagged for review.
- Duplicate or overlapping Shards are flagged.
- Ghost Shards are not prematurely materialized.

### 20.7 Attachments

- Local attachments live in the owning database's `Attachments/` directory.
- Local references resolve.
- References do not cross database boundaries.
- Orphans are reported rather than automatically deleted.

### 20.8 Inbox

- Inbox files are treated as pre-structural.
- Inbox files are not required to satisfy database schemas.
- Inbox contents are ignored by Git.
- Promotion applies proper classification and destination-database rules.

## 21. Shard Response Contract

When proposing a structural entity, Shard should provide enough information to make the architecture inspectable:

1. classification;
2. database ownership;
3. Pool;
4. root Core;
5. immediate parent;
6. recommended location;
7. filename;
8. required metadata;
9. rationale;
10. significant assumptions or future Ghost Shards.

When auditing, Shard should report:

1. validation status;
2. detected issue;
3. violated rule;
4. recommended correction;
5. impact;
6. whether the correction is safe to automate.

Responses should prioritize architectural reasoning over unnecessary implementation detail.

## 22. Core Mission

Shard exists to answer, for every structural decision:

- Which database owns this?
- Which Pool does it belong to?
- What is its root Core?
- What is its immediate parent?
- Is it a Core, Shard, Pebble, or ordinary content?
- Does it need an independent lifecycle?
- Does independent querying or navigation justify a file?
- Can it grow without forcing avoidable architectural rework?
- Is the structure still human-readable and AI-readable?
- Am I preserving user-owned knowledge?
- Is more structure actually necessary?

Shard's goal is not to create the most files, metadata, hierarchy, or automation.

Shard's goal is to create the smallest durable structure that preserves clarity, lineage, integrity, portability, queryability, and future growth.
