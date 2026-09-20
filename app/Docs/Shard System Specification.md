# Shard — System Specification

Specification version: `foundation-3` (2026-09-19)

Editorial revision: 2026-09-19

Foundation-3 change note: this edition replaces ancestry-derived supporting filenames with human-readable local titles plus stable opaque note IDs, and makes canonical structural IDs required and database-unique. Universal rules remain here; database-local semantics belong in each `Database.md`; operational and planning documents must reference these authorities rather than duplicate them.

## 1. Purpose and Authority

This document is the highest architectural authority inside the ShardBase repository. It defines the universal contract every compliant ShardBase database, tool, agent, and implementation must share.

ShardBase is a privacy-focused, user-owned structured Markdown knowledge-base framework. Canonical knowledge uses human-readable Markdown and YAML. Obsidian is the primary target environment, but canonical content and architectural meaning must remain understandable and editable without Obsidian, Dataview, AI assistance, scripts, generated indexes, or hosted services.

Database-specific meaning belongs in the root `Database.md` of the owning database. A database may define domain-specific collections, Pool values, semantic fields, relationships, conventions, templates, views, and other local resources, but it may not override this specification.

### 1.1 Authority Order

For structural and canonical decisions, use:

1. this System Specification;
2. the target database's root `Database.md`;
3. existing valid local conventions where several compliant choices remain;
4. the user's authorized intent.

Examples, templates, agents, scripts, views, existing content, prompts, provider memory, and conversations do not create architectural authority.

### 1.2 Universal vs. Database-Local Rules

A rule belongs here when independently designed compliant databases must agree on it for ShardBase or its tooling to interpret them safely and consistently.

Domain concepts that a valid database can reasonably exist without understanding remain database-local unless a deliberate framework change establishes a universal requirement.

Local rules may extend only areas this specification leaves open. A local rule that conflicts with a universal invariant is invalid rather than an authorized exception.

## 2. Product Boundaries and Guarantees

ShardBase is local-first and user-owned. User-owned knowledge and local state remain on the user's machine by default. Reading or operating on local information does not authorize transmission, synchronization, publication, upload, sharing, or other external exposure.

Local-first is not local-only. Users may deliberately choose cloud synchronization, backup, Git hosting, publishing, database sharing, or external AI systems. Those choices remain external workflows and must not become prerequisites for interpreting canonical ShardBase knowledge.

ShardBase may manage, validate, package, convert, and export user-owned AI-related files such as Agent definitions, Prompts, instructions, and context. **ShardBase does not execute models, authenticate with AI providers, invoke or orchestrate agents, or transmit local knowledge to AI services.** This is a product boundary, not deferred implementation work.

ShardBase does not aim to become a proprietary knowledge platform, synchronization or backup service, publishing platform, general-purpose search/indexing engine, transactional database engine, cloud-first collaboration system, or universal ontology.

Canonical knowledge must remain:

- **readable** as ordinary documents and inspectable metadata;
- **editable** with compatible text or Markdown tooling;
- **portable** without requiring a ShardBase export merely to possess or move it;
- **recoverable in meaning** without hidden application, provider, cache, index, embedding, or runtime state.

Optional tooling may reduce convenience when unavailable; it must not redefine otherwise valid canonical knowledge.

## 3. Repository and Ownership Model

The canonical Foundation layout is:

```text
shardbase/
├── .obsidian/
├── app/
│   ├── Blueprints/
│   ├── Docs/
│   ├── Knowledge/
│   │   ├── Inbox/
│   │   └── Databases/
│   │       └── <Database>/
│   │           ├── Agents/
│   │           ├── Data/
│   │           │   └── <Collection>/
│   │           │       ├── Attachments/
│   │           │       └── <Core Workspace>/
│   │           │           ├── Core Name.md
│   │           │           ├── Topic - 2gmcy7r7dr.md
│   │           │           └── Attachments/
│   │           ├── Templates/
│   │           ├── Views/
│   │           └── Database.md
│   ├── Registry/
│   └── Scripts/
├── AGENTS.md
└── README.md
```

### 3.1 Framework Surfaces

- `app/Blueprints/` contains framework-owned reusable database bootstrap material.
- `app/Docs/` contains committed framework documentation.
- `app/Registry/` contains framework-owned discovery and navigation infrastructure.
- `app/Scripts/` contains framework-owned automation and validation tooling.

These surfaces should be safe to distribute and must not silently embed private live knowledge.

### 3.2 Knowledge Boundary

`app/Knowledge/` is the canonical local boundary for user-owned ShardBase knowledge. During Foundation it has exactly two canonical direct children:

- `Inbox/` — unresolved pre-structural capture;
- `Databases/` — live canonical databases.

These contents are private and untracked by the framework repository by default unless the user deliberately establishes another policy.

Every direct child of `app/Knowledge/Databases/` is a database. Nested database roots and category directories between `Databases/` and a database root are not part of the Foundation contract.

Git policy follows ownership and intended distribution rather than path alone. Private information placed beneath a normally committed path does not become framework-owned merely because of its location. Generated artifacts inherit the sensitivity of the information they contain.

Generated runtimes, virtual environments, dependency installations, bytecode, caches, indexes, embeddings, temporary files, build output, credentials, and other recreatable or sensitive local state should remain outside the durable project/vault surface.

## 4. Database Contract

A live database is a direct child of `app/Knowledge/Databases/` and contains one or more declared data collections beneath `Data/`.

A minimal database contains:

```text
<Database>/
├── Data/
│   └── <Collection>/
│       └── Attachments/
├── Views/
└── Database.md
```

`Agents/`, `Templates/`, additional collections, and Core workspaces are optional.

### 4.1 Database Manifest

`Database.md` is the canonical manifest and local contract for its database. It is not a Core, Shard, Pebble, or Pool and must not use structural `type` metadata.

Required frontmatter:

```yaml
---
manifest_version: 1
database_id: example-database
database_name: Example Database
data_collections:
  - Example
database_status: active
---
```

- `manifest_version` identifies the database-manifest schema, not the System Specification version. Foundation uses integer `1`.
- `database_id` is a non-empty stable machine-friendly string identifier.
- `database_name` is a non-empty canonical human-readable string.
- `data_collections` is a non-empty list of unique direct-child directory names beneath `Data/`.
- `database_status` is one of `active`, `draft`, or `archived`.

Each declared collection requires its root `Attachments/` directory. `Views/` is required and may be empty.

### 4.2 Required Manifest Body

Every `Database.md` contains:

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

These sections document the database's own contract, not the complete ShardBase architecture.

- **Purpose** explains why the database exists.
- **Scope** defines canonical semantic ownership, including realistic inclusions and exclusions.
- **Architecture** defines collection meanings, Pool vocabulary, Core strategy, and database-local placement guidance where needed.
- **Schema** defines the complete semantic contract needed for reliable interpretation: fields, applicability, requiredness, shapes, bounded values, relationships, and domain-specific note kinds where applicable.
- **Conventions** defines repeatable database-local practices needed for reliable operation.
- **Resources** points to Views, attachments, templates, Agents, scripts, and other database-local resources.

If a database has no additional semantic fields, semantic note kinds, or conventions in an area, state that explicitly.

### 4.3 Database Ownership

Within ShardBase, database ownership means canonical semantic responsibility for knowledge inside the scope documented by `Database.md`. It is distinct from the user's ownership of all live database data.

Physical placement should follow determined ownership rather than define it after the fact. If multiple databases plausibly claim knowledge and their contracts do not resolve the ambiguity, do not guess or create duplicate authoritative copies. Leave the knowledge unresolved or pre-structural where practical and clarify the affected contracts.

Cross-database semantic relationships are permitted. They do not transfer ownership, redefine another database's schema, or create structural ancestry.

A portable database should retain coherent owned meaning when moved independently with its `Database.md`, declared collections, canonical notes, permitted attachments, Views, optional Templates, optional Agents, and other documented local resources.

## 5. Structural Model

ShardBase uses:

**Pool → Core → Shard → Pebble**

### 5.1 Pool

A Pool is the broadest logical grouping inside a database. It is represented by `pool` metadata rather than by a required folder or Pool note.

A database defines its permitted Pool vocabulary in `Database.md`. One Core lineage uses one canonical Pool value shared by the Core and all structural descendants.

### 5.2 Core

A Core is the canonical root structural note of one lineage. It has no structural parent, self-references through `core`, and may parent Shards or Pebbles.

A Core should represent a stable, independently meaningful root subject. Importance, size, category membership, or semantic containment alone does not justify Core status.

### 5.3 Shard

A Shard is a meaningful subdivision of a Core or another Shard. It has one root Core and one immediate parent and may have structural children.

A Shard should exist only when separate representation provides concrete value such as independent growth, querying, navigation, reuse, reference, lifecycle management, or structural organization.

### 5.4 Pebble

A Pebble is a terminal structural note. It has a valid Core or Shard parent and must never parent another structural note.

Pebble describes structural role, not note length. If a Pebble later needs structural children, reclassify it as a Shard before establishing them.

### 5.5 Ordinary Markdown and Ghost Shards

Use ordinary Markdown headings or sections when independent structure adds no meaningful value. A heading may remain the correct durable representation indefinitely.

A **Ghost Shard** is an unresolved wikilink representing plausible future structure that does not yet earn materialization. It has no file or structural YAML and may remain unresolved indefinitely. Its existence, age, or reference count does not by itself justify creation.

## 6. Structural and Common Note Metadata

Every canonical Core, Shard, and Pebble contains all five structural fields and all three common note fields:

```yaml
---
type:
pool:
core:
parent_note:
status:
aliases:
id:
tags:
---
```

This requirement does not apply to documentation, `Database.md`, Agent resources, Views, attachments, or pre-structural Inbox captures.

### 6.1 Structural Fields

`type` is one of:

- `core`
- `shard`
- `pebble`

`pool` is a non-empty scalar string using the owning database's permitted Pool vocabulary.

`core` is a wikilink to the canonical root Core. A Core self-references. Every Shard and Pebble resolves to the root Core in the same database.

`parent_note` is empty for a Core and is a wikilink to the immediate Core or Shard parent for a Shard or Pebble. A Pebble is never a parent.

`status` is one of:

- `active`
- `draft`
- `archived`

Database-specific workflow or domain state must use separately named semantic fields rather than reinterpret structural `status`.

### 6.2 Common Note Fields

`aliases`, `id`, and `tags` are universal common note fields but are not lineage fields.

- `aliases` defaults to blank YAML. When populated, it is a YAML list of non-empty strings; `[]` is valid.
- `id` is required on every canonical Core, Shard, and Pebble. It is a stable opaque 10-character lowercase Crockford Base32 token matching `[0-9a-hjkmnp-tv-z]{10}` and must be unique among canonical structural notes in the same database. The token is assigned once when canonical state is materialized, or prepared earlier for that purpose, and must not encode note type, ancestry, date, sequence, database identity, or other semantic meaning. If a generated token collides, generate another before writing canonical state.
- `tags` defaults to blank YAML. When populated, it is a YAML list of non-empty strings; `[]` is valid.

A note's `id` remains unchanged when its title, filename, placement, structural type, or parent changes. Existing valid populated IDs must be preserved during updates. `aliases`, `id`, and `tags` never replace `pool`, `core`, `parent_note`, or structural lineage. Pre-structural Inbox captures may leave `id` blank because they are not canonical structural notes.

### 6.3 Semantic Metadata

Database-specific semantic metadata is additional to the universal fields and is defined only by the owning `Database.md`.

Semantic metadata may inform classification but never substitutes for structural metadata. Folder placement, data-collection membership, tags, links, backlinks, categories, series, organizations, and other domain relationships are not structural lineage.

If a proposed field could be structural or semantic, ask whether every compliant database must share its meaning for ShardBase to establish or validate a universal invariant. If not, keep it database-local.

## 7. Placement, Collections, Workspaces, and Attachments

A **data collection** is a database-defined filesystem grouping for canonical notes. It does not define Pool membership, structural type, Core lineage, or parentage.

Canonical structural notes may use one of two placement modes within a declared collection:

1. **Flat placement** — the Core and descendants live directly at the collection root.
2. **Core workspace placement** — exactly one Core lineage is bundled into one direct-child directory named for the Core's portable canonical filename stem.

Flat placement is the default and remains valid indefinitely. A workspace should be introduced only when filesystem locality provides concrete organizational value.

A Core may have at most one workspace. A lineage must not be split between the collection root and its workspace. Structural notes inside a workspace remain direct Markdown children; nested Core → Shard → Pebble folder ancestry is invalid. YAML remains authoritative for lineage.

Structural discovery therefore inspects collection roots and one valid Core-workspace level only.

### 7.1 Attachments

Each declared collection reserves `Data/<collection>/Attachments/`. A Core workspace may also reserve its own `Attachments/` directory.

Attachments are non-structural, database-owned resources. They:

- never use structural YAML;
- are excluded from structural discovery even if the file extension is `.md`;
- may be referenced by canonical notes anywhere in the same database;
- should not be duplicated merely to satisfy another collection or workspace;
- cross-database attachment references should be avoided so a database remains portable and self-contained;
- must not be automatically moved across database boundaries;
- must not be automatically deleted when a referencing note is archived or deleted.

For a newly introduced attachment, prefer a Core workspace attachment home when the resource is primarily contextualized by that lineage; otherwise prefer the collection-root attachment home, especially for flat lineages or resources shared across Cores. When no permitted home is clearly primary, choose one reasonable home rather than duplicate the resource.

If canonical knowledge references a missing attachment, preserve the reference and report the resource as unavailable rather than silently removing the reference. An unreferenced attachment is an attachment orphan that may be reported for review but is not permission to delete it.

Inbox remains text-oriented and does not own attachments.

## 8. Canonical Naming and Lineage

YAML is authoritative for lineage. Filenames identify notes for people and tools without encoding structural ancestry. Core filenames use the Core's human-readable title; supporting filenames use the note's human-readable local title plus its stable opaque `id`.

### 8.1 Portable Filename Components

Before composing a canonical filename, derive a portable filename component from each canonical structural name:

1. Start with the canonical structural name exactly as established.
2. Replace every ASCII control character `U+0000` through `U+001F` and every character in `< > : " / \ | ? * # [ ]` with one ASCII space.
3. Collapse consecutive whitespace to one ASCII space and trim leading and trailing whitespace.
4. Remove the entire trailing sequence of ASCII spaces and periods, including alternating spaces and periods.
5. If the result is empty, `.` or `..`, stop materialization and require meaningful disambiguation.
6. If the result case-insensitively equals `CON`, `PRN`, `AUX`, `NUL`, `COM1` through `COM9`, or `LPT1` through `LPT9`, prefix `_`.
7. Do not otherwise transliterate Unicode, change case, remove allowed punctuation, abbreviate, or rewrite words.

Portable normalization changes only the filesystem representation. The canonical display title remains unchanged.

Structural wikilinks target the derived filename stem or an unambiguous supported path to it. A heading fragment or display alias does not change the selected structural note.

### 8.2 Core Filenames

A Core filename is:

```text
Portable Core Name.md
```

The level-one heading preserves the canonical human-facing title.

### 8.3 Supporting Filenames

Every Shard and Pebble uses:

```text
Portable Local Title - Opaque ID.md
```

`Portable Local Title` is derived from the note's opening H1 using Section 8.1. `Opaque ID` is the note's required stable `id` from Section 6.2. The filename never includes the Core title, parent title, structural type, or other ancestry merely to provide context.

Example using synthetic titles:

```text
Example Game.md
Topics - 2gmcy7r7dr.md
Subtopic - 11hq8bbd1p.md
Detail - 3j84q9k6fc.md
```

The supporting note's opening H1 is its canonical local human-facing title, such as `# Topics` or `# Detail`. Parentage and root lineage are expressed only through `parent_note` and `core`. A title change updates the human-readable filename component and dependent wikilinks while preserving the note's `id`. Reparenting alone does not require a filename change.

A Core workspace does not create another filename namespace. Canonical `id` values are database-unique, so two supporting notes may legitimately share the same local title while remaining distinguishable by ID. Core title collisions still require meaningful identity disambiguation. Do not overwrite, silently number, encode ancestry, or rely on separate workspace paths to resolve an identity collision.

### 8.4 Integrity Rules

- no note is its own parent;
- no circular lineage or self-ancestry exists;
- every supporting note resolves to one valid root Core in the same database;
- the parent chain agrees with the declared root Core;
- a Pebble never acts as a structural parent;
- supporting notes use the root Core's Pool;
- every canonical structural note has one valid database-unique stable `id`;
- an active structural descendant must not remain beneath an archived structural ancestor unless deliberately restructured first;
- a missing required parent or root Core is a structural orphan and must be reported without guessing a replacement.

Broken ordinary links and intentional Ghost Shards are not structural orphans.

## 9. Markdown Structure

Canonical structural notes use a level-one opening heading for the canonical human-facing note title unless the database documents another display-title convention.

Top-level ATX heading levels are sequential and must not skip levels. Each heading is followed by exactly one blank line before content.

Lists, tables, callouts, code blocks, and embeds may contain information but do not substitute for headings where genuine document hierarchy exists.

A heading-only skeleton may be intentional unfinished content. Headings never authorize creation of separate structural notes by themselves.

## 10. Classification and Materialization

Before creating or restructuring canonical knowledge, determine:

1. database ownership;
2. declared data collection;
3. Pool;
4. root Core;
5. immediate parent;
6. whether the information is a Core, Shard, Pebble, or ordinary content;
7. whether it needs an independent lifecycle;
8. whether independent querying, navigation, reuse, reference, growth, or another concrete need justifies a separate file.

Use:

- **Core** for a stable independent root subject;
- **Shard** for a meaningful subdivision that may own children;
- **Pebble** for an independently useful terminal unit;
- **heading/ordinary Markdown** when separation adds no meaningful value;
- **Ghost Shard** when a plausible future note is useful to reference but has not earned materialization.

Conceptual depth does not require matching file depth. Categories, taxonomies, headings, template sections, and note length alone are insufficient evidence for structural materialization.

Creating one requested note never authorizes additional implied notes. Additional materialization requires separate deliberate user action.

## 11. Knowledge Lifecycle

The lifecycle is a state-and-decision model rather than a mandatory linear pipeline.

### 11.1 Entry

ShardBase recommends two primary creation paths:

- notes intended to become canonical under `app/Knowledge/Databases/` should normally use the CLI to prepare their filename and metadata, then be reviewed and moved manually into the owning database;
- temporary or ad-hoc notes created through a Markdown editor (preferably Obsidian) or filesystem should normally enter `app/Knowledge/Inbox/`.

Knowledgeable users may create canonical files manually if they intentionally satisfy the complete contract.

### 11.2 Inbox

Inbox items are pre-structural. They do not require a database, Pool, Core, structural `type`, lineage, canonical filename, or database semantic schema.

A database-intended note may already carry a prepared canonical filename, metadata, and ID while it waits in Inbox. Preparation does not make it canonical or prove conformance. Preserve its valid prepared ID during manual promotion and check uniqueness against the destination at that time.

Review may incorporate an item into an existing note, promote it into new canonical structure, retain it unresolved, leave only a Ghost Shard, or result in deliberate user discard. Successful review does not imply a new file.

Current CLI capture behavior is documented in [`../Scripts/README.md`](../Scripts/README.md).

### 11.3 Growth

Content should normally grow inside ordinary Markdown first. A section may remain embedded indefinitely.

Materialize a separate canonical file only after it earns independent value. If a Pebble needs structural children, reclassify it before establishing them.

**Content grows freely; structure grows when it earns a purpose.**

### 11.4 Refactoring

Structural refactoring is preservation-oriented. Define the intended result first, preserve unrelated user-authored knowledge, update affected authoritative metadata and dependent representations, and validate the resulting state.

Refactoring may materialize embedded content, consolidate a note back into Markdown, reclassify a structural role, change parentage or Pool, rename canonical knowledge, change database ownership, or bundle/unbundle a Core workspace.

Do not refactor valid structure merely because another compliant representation is preferred.

### 11.5 Archival

Archiving retains canonical knowledge while marking it inactive. Structural notes normally stay in place with `status: archived`; no universal archive folder is required.

Archiving a Core normally applies to its lineage and archiving a Shard normally applies to its descendants. Descendants that should remain active must first be deliberately restructured.

Database archival uses `database_status: archived` and does not require duplicating that state on every note.

Restoring archived structural knowledge normally means returning its structural `status` to `active` when its ownership and lineage remain valid. If the surrounding architecture has changed, review restoration against the current contracts before reactivation.

### 11.6 Deletion

During Foundation, normal deletion is a deliberate user action through the Markdown editor or filesystem. ShardBase agents and tooling must not autonomously delete canonical user knowledge.

Archived, obsolete, orphaned, duplicate-looking, invalid, or unreferenced content is not automatically deletable. Orphan detection is diagnostic, not cleanup permission.

## 12. Views, Registry, Blueprints, Agents, and Automation

### 12.1 Views

Database `Views/` contain read-oriented projections, queries, dashboards, or navigation notes. Views may query other authorized databases when their documented purpose requires it, but they remain non-authoritative.

A missing or broken View must not change canonical meaning.

### 12.2 Registry

The framework Registry lives at `app/Registry/Registry.md` and provides instance-wide discovery and navigation. It should discover live databases at runtime rather than store a generated authoritative inventory.

`Database.md` remains authoritative for database identity and local meaning.

### 12.3 Blueprints

Blueprints are reusable framework-owned bootstrap material. They may provide a starter `Database.md`, directory structure, Views, Templates, Agent resources, and minimal structural scaffolding.

After materialization, the live database owns its files. Later blueprint changes never silently synchronize into a live database. Adoption of changes that affect existing live state is an explicit migration.

### 12.4 Agents

A database may contain an optional root `Agents/` directory for database-owned specialist Agent resources. Placement follows ownership rather than total read scope.

Agent resources are ordinary user-owned files, not structural notes and not architectural authority. Rules needed for reliable canonical interpretation belong in this specification or the applicable `Database.md`, not only in an Agent prompt or memory.

Foundation standardizes the database-owned `Agents/` boundary, not a mandatory internal package anatomy.

### 12.5 Scripts and CLI

Scripts implement documented architecture; they do not define it.

Automation should:

- validate deterministic inputs before canonical structural writes;
- preserve unrelated user-authored content;
- report ambiguity instead of guessing;
- avoid silent destructive changes;
- treat blueprint upgrades and compatibility transformations as migrations when applicable;
- keep rules visible in documented contracts.

Canonical creation should eventually validate universal and database-semantic constraints before writing. Templates may provide starting shape or defaults but do not define validity.

Current implementation details and limitations are documented in [`../Scripts/README.md`](../Scripts/README.md).

## 13. Change Safety and Authorization

Distinguish:

- **recommendation** — what should change;
- **proposal** — the exact recommended change;
- **approved change** — an action the user or authorized workflow has permitted.

Authorization is scoped to the requested task. Context, brainstorming, future ideas, or unrelated information do not silently broaden it.

Unless authorized by the task, do not:

- rename or move existing canonical structural notes;
- change a database schema or universal architecture;
- rewrite unrelated factual/domain content during structural work;
- break links or references;
- move attachments across database boundaries;
- apply blueprint changes to a live database;
- publish, synchronize, upload, transmit, or otherwise expose user-owned knowledge externally;
- materialize additional structural notes beyond the user's intended note;
- perform destructive, irreversible, breaking, or large-scale migrations.

Prefer deterministic, reversible automation for low-risk mechanical work. Keep destructive, ambiguous, privacy-sensitive, breaking, or otherwise consequential decisions under meaningful user control.

## 14. Architectural Change, Versioning, and Migration

ShardBase distinguishes the nature of a change, its compatibility effect, and any transformation used to apply it.

### 14.1 Change Categories

- **Architectural clarification** — explains an existing rule without changing what compliant state is required to do.
- **Architectural extension** — adds a capability while preserving previously compliant state and meaning.
- **Schema change** — changes a machine-interpretable field, shape, meaning, requiredness, value set, or constraint.
- **Migration** — an explicit bounded transformation of durable state from one representation to another.
- **Breaking change** — causes previously compliant state, workflows, or observable assumptions to become invalid, change meaning, lose supported meaning, or require modification.

A migration does not make a breaking change non-breaking.

### 14.2 Specification Version

The System Specification version changes when the normative universal contract changes, including universal extensions, schema changes, added/removed invariants, materially changed meanings, breaking changes, or changed universal compatibility, ownership, privacy, or safety obligations.

Editorial restructuring, formatting, non-normative examples, and true clarifications do not require a version increment.

During Foundation, versions use `foundation-N`.

### 14.3 Manifest Version

`manifest_version` changes only when the database-manifest contract itself changes in a way compatible readers, validators, creators, or migrations need to distinguish. A System Specification change does not automatically change `manifest_version`, and database-local semantic schema changes do not use it as a generic version.

### 14.4 Migration Principles

A migration is required when existing durable state cannot remain correctly conformant, correctly interpreted, or safely operated unchanged under an approved contract.

A migration defines its source condition, target condition, authorized scope, preservation expectations, validation criteria, and known compatibility impact. Preserve unrelated user-authored knowledge.

When older supported state can remain valid and correctly interpreted unchanged, do not force migration merely to normalize it.

Unsupported or unsafe version mismatches must fail visibly rather than be guessed through or partially normalized.

### 14.5 Changes That Must Never Be Silent

Never silently change existing canonical meaning, required schema, structural identity, ownership, lineage, naming, placement, lifecycle semantics, privacy/exposure boundaries, compatibility support, or live database state because of a newer blueprint or specification.

A compatibility boundary must be inspectable before it becomes a data transformation.

## 15. Recorded Foundation Compatibility Boundaries

### 15.1 `foundation-1`

`foundation-1` records the first explicit Foundation version boundary. It included the then-current portable-filename contract and the approved canonical knowledge boundary at `app/Knowledge/Databases/` and `app/Knowledge/Inbox/`.

Portable filename changes are breaking only for existing canonical state whose derived filenames differ. Affected state requires a preservation-oriented transition: retain a recoverable copy, identify affected files/workspaces/references, resolve collisions before rename, update dependent references together, preserve canonical display titles and unrelated content, and validate the result.

The historical relocation from `app/Databases/` and `app/Inbox/` to the `app/Knowledge/` boundary likewise requires affected local state to be moved intact with discovery, validation, ignore, view, script, and documentation assumptions updated. Database identity and manifest schema do not change; `manifest_version` remains `1`.

### 15.2 `foundation-2`

`foundation-2` required `aliases`, `id`, and `tags` on every canonical Core, Shard, and Pebble. At that boundary, `aliases` and `tags` could be blank or lists of non-empty strings, while `id` could be blank or any scalar string; uniqueness and a universal ID format were not yet required.

This was breaking for previously compliant notes that omitted those keys or used incompatible values. Foundation-3 supersedes the historical `id` value rule for current canonical state.

The bounded transition is:

1. review the target database and templates for missing keys and incompatible existing uses;
2. retain a recoverable local copy before an authorized live-data update;
3. add only missing keys with blank YAML values;
4. preserve all existing valid values, metadata, bodies, filenames, lineage, links, and attachments;
5. resolve incompatible existing values deliberately rather than coercing or clearing them;
6. validate the result and verify preservation.

`manifest_version` remains `1`.

`foundation-2` remains a recorded historical compatibility boundary.

### 15.3 `foundation-3`

`foundation-3` changes canonical structural identity and filename requirements in two coordinated ways:

1. every canonical Core, Shard, and Pebble must have a database-unique stable opaque `id` matching `[0-9a-hjkmnp-tv-z]{10}`;
2. every Shard and Pebble filename changes from ancestry-derived context to `Portable Local Title - Opaque ID.md`, while Core filenames remain `Portable Core Name.md`.

This is a breaking change for existing canonical state with blank, incompatible, or duplicate IDs and for every supporting filename derived under an earlier naming contract. `manifest_version` remains `1` because the database-manifest schema is unchanged.

The bounded transition is:

1. retain a recoverable local copy of the affected database before changing canonical state;
2. inventory every canonical structural note, its current filename, `core`, `parent_note`, and inbound structural/ordinary wikilinks;
3. preserve every already-valid foundation-3 ID; assign a new opaque ID only where the existing value is blank, invalid, or colliding;
4. rename Shards and Pebbles to `Portable Local Title - Opaque ID.md`; leave Core filenames title-based;
5. update `core`, `parent_note`, and ordinary wikilinks that target renamed notes in the same coordinated migration;
6. preserve display titles, aliases, semantic metadata, note bodies, attachments, lineage meaning, completion state, and unrelated user-authored content;
7. resolve any remaining title or ID collision before finalizing;
8. validate the migrated database and verify that no intended note or link target was lost.

IDs assigned by this migration become stable thereafter. Reparenting does not change the filename because ancestry is no longer encoded in it.

The current validator targets current `foundation-3` conformance within its documented scope. It does not infer historical specification versions or automatically migrate live state.

## 16. Validation Protocol

A deterministic audit should validate the following within the capabilities documented by the implementation.

### 16.1 Database Contract

- database root is a direct child of `app/Knowledge/Databases/`;
- root `Database.md` exists;
- required manifest fields, values, shapes, and body sections exist;
- `data_collections` is non-empty and unique;
- every declared collection exists with root `Attachments/`;
- `Views/` exists;
- structural discovery scans collection roots and one Core-workspace level only;
- attachment subtrees and root `Agents/`, `Templates/`, and `Views/` are not structural-note sources;
- unsafe paths, escapes, or unsupported roots are reported.

### 16.2 Metadata and Semantics

- all eight universal note fields exist on canonical structural notes;
- structural values and common-field shapes satisfy this specification;
- canonical note IDs match the foundation-3 opaque-token format and are unique within the database;
- structural and semantic meanings are not conflated;
- database-local semantic constraints are validated when an implementation can consume the authoritative `Database.md` contract deterministically.

### 16.3 Lineage and Placement

- Core self-reference, parent resolution, same-database root Core, Pool consistency, terminal Pebbles, no cycles/self-parentage, and archive ancestry are valid;
- canonical notes occupy valid flat or Core-workspace placement without split lineages or nested structural ancestry;
- structural orphans are reported without guessed repair.

### 16.4 Naming

- portable normalization is applied to the Core title or supporting local-title filename component;
- Core filenames match `Portable Core Name.md`;
- Shard and Pebble filenames match `Portable Local Title - Opaque ID.md`;
- supporting filenames do not encode Core or parent ancestry;
- Core-title, actual-stem, derived-filename, and note-ID collisions are reported rather than resolved through path placement, numbering, overwrite, or encoded ancestry;
- opening H1 preserves the canonical human-facing Core title or supporting local title.

### 16.5 Markdown

- opening H1 exists for structural notes;
- heading levels are sequential;
- headings use exactly one following blank line;
- template/skeleton headings are not interpreted as materialization instructions.

### 16.6 Fragmentation and Attachments

Where implemented, validation should flag structural notes that appear not to provide independent value, duplicate/overlapping structural notes, invalid attachment homes/references, and attachment orphans. These judgments must remain diagnostic where the contract does not define one deterministic answer.

### 16.7 Inbox

Inbox files are excluded from canonical database conformance until promotion. Promotion must classify and validate the resulting canonical state under this specification and the destination `Database.md`.

## 17. Foundation Agent Contract

Shard is the canonical primary AI architectural and database agent for ShardBase. Other agents may specialize, but all agents that operate on ShardBase structure or user-owned knowledge remain subject to the same authority, privacy, preservation, and authorization rules.

Shard should translate ordinary user intent into the smallest valid ShardBase operation rather than requiring users to know the full architecture first.

When proposing a structural entity, an agent should make the decision inspectable by identifying the classification, database ownership, data collection, Pool, root Core, immediate parent, recommended location, filename, required metadata, rationale, and significant assumptions where relevant.

When auditing, report validation status, issue, violated rule, recommended correction, impact, and whether the correction is safe to automate.

Operational instructions for repository agents live in [`../../AGENTS.md`](../../AGENTS.md). Database-owned Agent resources may summarize workflows but do not replace their owning `Database.md`.

## 18. Glossary

**Attachment** — non-structural resource owned by one database and stored in a permitted collection-root or Core-workspace `Attachments/` directory.

**Attachment orphan** — attachment currently referenced by no canonical note; diagnostic only.

**Blueprint** — framework-owned reusable bootstrap material for creating a database; materialized live state becomes user-owned.

**Canonical note** — a conformant Core, Shard, or Pebble Markdown file in a valid declared-collection location.

**Core** — canonical root structural note of one lineage.

**Core workspace** — optional direct-child collection directory that physically bundles exactly one Core lineage without representing structural ancestry.

**Cross-database relationship** — semantic relationship between knowledge owned by different databases; never structural ancestry.

**Data collection** — database-defined filesystem grouping for canonical notes; not a structural lineage mechanism.

**Database** — self-contained user-owned canonical knowledge boundary directly beneath `app/Knowledge/Databases/` and governed by its root `Database.md`.

**Database ownership** — canonical semantic responsibility within a database's documented scope.

**Ghost Shard** — unresolved wikilink for plausible future structure that has not earned materialization.

**Immediate parent** — directly preceding structural note identified by `parent_note`.

**Inbox** — private-by-default pre-structural capture outside every database.

**Knowledge boundary** — `app/Knowledge/`, containing `Inbox/` and `Databases/`.

**Lineage** — structural ancestry expressed authoritatively through `core` and `parent_note`.

**Materialization** — deliberate creation of a separate canonical structural file after it earns independent value.

**Opaque note ID** — stable database-unique 10-character lowercase Crockford Base32 token assigned to a canonical structural note without semantic encoding.

**Migration** — explicit bounded preservation-oriented transformation of durable state required by an approved contract change.

**Pebble** — terminal structural note in a Core lineage.

**Pool** — database-local logical grouping shared by a Core and its structural descendants.

**Registry** — framework-owned discovery/navigation projection over live databases; never authority over `Database.md`.

**Root Core** — the one canonical Core at the root of a structural lineage.

**Semantic metadata** — database-defined metadata describing domain identity, properties, taxonomy, state, or relationships.

**Shard** — meaningful subdivision of a Core or Shard that may have structural children.

**Structural metadata** — universal fields `type`, `pool`, `core`, `parent_note`, and `status`.

**Structural orphan** — Shard or Pebble whose required root Core or immediate parent cannot be validly resolved.

**View** — non-authoritative query, presentation, or navigation resource over canonical knowledge.

## 19. Core Mission

ShardBase should create the smallest durable structure that preserves ownership, clarity, lineage, integrity, portability, queryability, and future growth.

Implementation may still discover details; it should no longer have to invent architecture.
