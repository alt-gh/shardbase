# ShardBase

ShardBase is a privacy-focused, user-owned structured Markdown knowledge-base framework designed to grow into an interconnected personal digital brain and source of truth.

It uses human-readable Markdown and YAML to organize knowledge through explicit structure, metadata, relationships, links, search, views, and AI-assisted interaction while keeping the underlying information understandable and editable independently of any single tool. ShardBase targets Obsidian as its primary knowledge environment, supports modular databases and extensible tooling, and is designed to let a user's knowledge grow across many areas of life without sacrificing readability, portability, structural integrity, privacy, or control.

## Why ShardBase

Personal knowledge becomes more valuable as it accumulates, connects, and remains usable over time, but it also becomes harder to keep coherent, connected, understandable, and useful as it grows.

ShardBase provides a durable shared architecture for that growth. It is designed to reduce fragmentation, preserve lineage and context, support reliable retrieval and machine interpretation, and keep the organizational burden from growing faster than the usefulness of the knowledge itself.

The long-term goal is a user-owned personal source of truth that can support memory, understanding, discovery, decision-making, and AI-assisted interaction without requiring the user to surrender ownership or architectural control of their knowledge.

## What ShardBase Adds

ShardBase is not intended to replace folders, tags, YAML, wikilinks, backlinks, Dataview, templates, scripts, Git, or AI assistance. Each of those tools solves a useful part of the knowledge-management problem. ShardBase adds the shared architectural contract that lets them cooperate over the same user-owned knowledge without requiring any one tool to become the sole source of meaning.

That contract defines database ownership, structural lineage, universal structural metadata, the boundary between structural and semantic meaning, materialization expectations, authority, and change-safety rules. The result is a predictable shared interpretation for humans, Obsidian, Dataview, scripts, validators, and AI agents as the knowledge base grows.

ShardBase deliberately keeps Markdown and YAML as the durable source rather than requiring a traditional database engine or bespoke application for basic access. The files remain directly editable with widely available tools across devices and can be transformed into derived machine-readable formats such as JSON when interoperability or downstream processing requires it. Traditional databases remain a better fit when transactional guarantees, machine-scale relational workloads, or database-engine performance are the primary requirement.

## Core Design Commitments

- **User-owned and privacy-focused** — the user owns and controls their core data. ShardBase does not require that data to leave the user's local environment for core operation.
- **Local-first by default** — user-owned knowledge and local state stay on the user's machine unless the user deliberately chooses synchronization, backup, external AI, Git hosting, publishing, sharing, or another external service. Reading local data is not permission to transmit it.
- **Markdown is the foundation** — core knowledge remains stored in human-readable Markdown and YAML so it can be inspected, edited, copied, searched, versioned, and processed independently of ShardBase-specific tooling.
- **Obsidian is the primary target, not the data owner** — ShardBase is designed for a strong Obsidian experience, but its core knowledge and structural meaning must remain understandable outside Obsidian.
- **Tools enhance rather than define the knowledge** — Dataview is a primary and canonical interface for interacting with ShardBase data in Obsidian, while views, scripts, plugins, AI agents, and future tooling must not become the sole source of structural truth.
- **Shared understandability** — important knowledge should be explicit enough that humans can understand it, deterministic tools can query and validate it, and AI can reason over it without optimizing the canonical source exclusively for any one audience.
- **Explicit without redundant authority** — important architectural meaning should be inspectable and documented, but the same fact should not be duplicated across multiple competing authoritative representations merely for visibility.
- **AI assistance is intentional but optional** — AI can interpret, recommend, classify, retrieve, explain, and assist with maintenance, while explicit rules and deterministic validation preserve predictable structure. The knowledge base must remain durable and meaningful without AI.
- **Human authority is preserved** — ShardBase may automate repetitive, deterministic, and safely reversible work, but consequential, ambiguous, privacy-sensitive, or destructive decisions remain under meaningful user control.
- **Minimum necessary structure** — ShardBase uses the minimum structure necessary to preserve useful organization, relationships, growth, integrity, queryability, navigation, and lifecycle management, allowing structure to emerge as knowledge develops rather than requiring future complexity to be modeled in advance.
- **Simplicity without opacity** — ShardBase should minimize conceptual and operational burden, but simplicity must not hide necessary complexity in undocumented behavior, hidden state, or opaque tooling.
- **Readable, editable, and portable by construction** — canonical knowledge must remain readable, directly editable, and movable without requiring ShardBase-specific tooling; loss of an optional view, AI system, script, or generated runtime may reduce convenience but must not erase essential meaning.
- **No hidden architectural state** — essential knowledge meaning and architectural behavior must be traceable to canonical files and documented contracts. Undocumented inaccessible state must not become a required interpreter or silent authority merely because an implementation currently works.
- **Framework, not monolith** — universal rules define what it means to participate in ShardBase, while each database defines how it represents and operates on the particular domain of knowledge it owns. Database contracts may extend areas the framework intentionally leaves open, but they may not contradict universal invariants, and recurring local requirements should be documented rather than hidden in existing content.

External synchronization, backup, cloud storage, publishing, and sharing services are user choices and are separate from ShardBase's core operation.

## Who ShardBase Is For

ShardBase is primarily for individuals who want to build a long-lived personal source of truth across multiple subjects or areas of life without surrendering ownership, privacy, portability, or direct access to their underlying knowledge. It is designed for people who value interconnected, structured knowledge but want the structure to reduce long-term organizational burden rather than become a system they must constantly maintain for its own sake.

Ordinary use should not require programming, database administration, Git expertise, advanced YAML knowledge, or memorization of the complete ShardBase architecture. Users should be able to start with basic Markdown-oriented capture, reading, editing, and navigation, while deeper architectural concepts are disclosed when they become useful. Obsidian is the primary supported environment, but it is an interface over the durable Markdown and YAML source rather than a requirement for that source to remain understandable. AI assistance is similarly intentional and valuable but optional.

ShardBase is especially suited to knowledge that is expected to grow, connect, be queried, or remain useful over time. It is less suited to disposable note collections, users who want an opaque service to own all organization and decision-making, or workloads whose primary needs are traditional database transactions and machine-scale relational performance.

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

Shard translates ordinary user intent into safe, minimal operations over the documented ShardBase architecture. It is responsible for understanding database contracts, classifying information, preserving lineage, proposing or creating valid structure, auditing databases, designing queries, retrieving and reasoning over authorized knowledge, and helping the framework evolve safely without requiring users to memorize the complete architecture. ShardBase may support additional AI agents, but structural operations remain subject to the same architectural contracts and user-control boundaries.

ShardBase distinguishes framework-owned agents, database-owned specialist agents, and user-owned agents or customizations. A specialist agent may operate independently within its documented scope, but agent definitions and customizations never override the System Specification or the applicable database contract. The exact repository layout for agent definitions and local user customization remains a foundation design question; any eventual layout must preserve an obvious boundary between distributable framework material and user-owned private state. The ownership policy is already established: framework agents may be distributed, live database agents follow their database, and user-owned agents and customizations remain local and private by default.

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
│   │       │   ├── [Primary Data Collection]/
│   │       │   │   ├── Core.md
│   │       │   │   ├── Core - Shard.md
│   │       │   │   ├── Core - Shard - Pebble.md
│   │       │   │   └── Attachments/
│   │       │   └── [Additional Data Collection]/
│   │       │       └── Attachments/
│   │       ├── Templates/
│   │       ├── Views/
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

`Templates/` and additional data collections are optional. A minimal database needs only one declared data collection.

## Database Anatomy

Each live database is a direct child of `app/Db/` and is self-contained.

### `Database.md`

The database manifest and local contract. It defines database identity, scope, declared data collections, semantic schema, conventions, and resources.

### `Data/[Data Collection]/`

Contains canonical database notes for one database-defined data grouping. A database has one or more declared data collections; the primary collection is commonly the singular form of the database subject, while additional collections may represent other domain-owned kinds such as a series or collection concept.

Canonical Markdown notes live directly inside their declared data collection. `Attachments/` is a reserved non-structural resource subdirectory and must be excluded from structural-note discovery even if it contains a Markdown file. Tools should scan the declared collection roots rather than recursively treating every descendant beneath `Data/` as a Core, Shard, or Pebble candidate.

Data collections organize database-owned files; they do not define Pool membership, Core lineage, or structural parentage. Pools remain **logical metadata values**, not required filesystem folders.

### `Data/[Data Collection]/Attachments/`

Contains local non-structural files owned by the database and associated with that collection. Cross-database attachment references should be avoided so a database remains portable. A missing or deliberately offloaded attachment reference should be surfaced rather than silently removed; the exact offloading and restoration mechanism remains a lifecycle design question.

### `Templates/`

Optional database-owned note templates may live with the database so they remain portable with its schema and conventions. Templates may assist knowledgeable users with manual creation, but they do not replace the recommended workflow of using the CLI for canonical `app/Db/` notes and Inbox for ad-hoc editor-created notes. Headings or skeleton sections inside a template do not by themselves justify creating additional structural notes.

### `Views/`

Contains database-local views and queries. Dataview is a primary and canonical ShardBase interface in Obsidian. Views consume metadata; they do not define structural truth.

## Canonical Database Experience

ShardBase is designed to be used primarily through the user's chosen Markdown editor over ordinary local files. Existing canonical notes should remain comfortable to read and edit directly. The intended normal workflow recommends two primary entry paths for new notes: canonical notes intended for `app/Db/` should normally be created through the ShardBase CLI, while ad-hoc notes created through a Markdown editor or filesystem should normally enter `app/Inbox/` for review. The CLI runtime is not yet part of the Foundation implementation contract; until it exists, and for knowledgeable users who deliberately choose otherwise, canonical files may still be created manually subject to the documented contract.

The foundation does not require ShardBase scripts or the CLI to call AI-model APIs. ShardBase is not an intermediary, synchronization layer, or automatic connection between local knowledge and external AI services such as ChatGPT or Gemini. Users who want an external service to receive ShardBase information must deliberately provide, move, export, upload, or otherwise authorize that information through a separate workflow. AI assistance should reduce architectural burden without becoming the primary editor, a hidden source of truth, or a prerequisite for using the underlying Markdown knowledge.

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

For supporting notes, `parent_note` points to the immediate structural parent. For a Core, `parent_note` is empty. A Core and its structural descendants use the same canonical `pool` value.

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

A new structural note should exist only when it provides meaningful value through independent growth, querying, navigation, reuse, or lifecycle management. Otherwise, the information should remain inside its parent note as ordinary Markdown structure. A heading, including a heading in a skeleton or template, is never sufficient evidence by itself that a separate Shard or Pebble should be materialized. If creating the requested note suggests additional structural notes, those additional notes should be proposed rather than created without deliberate user action.

Future notes may be represented by unresolved wikilinks until they justify materialization.

## Knowledge Lifecycle

ShardBase allows knowledge to begin simply and gain structure only when that structure earns a purpose. Inbox capture may be incorporated into existing notes, promoted into new structural notes, left unresolved, represented by Ghost Shards, or discarded by the user. A separate canonical file is justified by meaningful independent growth, querying, navigation, reuse, reference, or lifecycle management rather than by conceptual hierarchy or note length alone.

Archived knowledge remains canonical and in place with an archived lifecycle status; archiving is not deletion. During the Foundation stage, normal deletion is a deliberate user action through Obsidian, another Markdown editor, or the filesystem rather than an autonomous ShardBase operation. Structural and attachment orphans may be reported for review but are never repaired or deleted through guesswork. Attachments remain database-owned resources whose existence does not silently follow the lifecycle of any one referencing note. Ghost Shards remain unresolved until the knowledge earns materialization and the user deliberately creates the real note.

## Framework Boundaries

- `app/Blueprints/` contains framework-owned reusable database bootstrap material. ShardBase may eventually ship optional or default database packages here, including an initial specialist Agent when agent packaging is finalized.
- `app/Db/` contains live user-owned databases and is a primary private-data boundary. Database-owned specialist Agents should travel with their databases once their canonical layout is finalized.
- `app/Docs/` contains committed framework documentation and architectural specifications and must not embed private user data.
- `app/Inbox/` contains local user-owned unverified, pre-structural capture.
- `app/Registry/` contains committed discovery and navigation infrastructure; user-specific Registry output remains local by default.
- `app/Scripts/` contains optional framework automation, validation, migration, conversion, and maintenance tooling, not generated runtimes or machine-specific dependency state.

Blueprints may initialize a database, but a live database owns its state after creation. Blueprint changes must never silently rewrite existing databases. Users may also create their own databases and database Agents.

## Local-First and Git Policy

ShardBase is local-first. User-owned knowledge and local state remain on the user's machine by default. ShardBase does not transmit, synchronize, publish, upload, share, or otherwise make that state available outside the local environment unless the user deliberately chooses an external service or explicitly authorizes the action. Local-first is not local-only: users remain free to choose cloud synchronization, remote backup, private or public Git hosting, external AI, publishing, database sharing, or other external services.

The framework repository is intended to be safe to publish. Git policy follows ownership and intended distribution rather than filesystem path alone: committed framework surfaces are potentially public, while user-owned live state is private and untracked by default. Putting private data beneath a normally committed directory does not make it framework data, and generated output inherits the sensitivity of the information it contains.

By default:

- live database contents under `app/Db/` are ignored;
- Inbox contents under `app/Inbox/` are ignored;
- user-owned Agents, customizations, private local configuration, sensitive Registry-derived state, credentials, and other user-local state are ignored;
- generated runtimes, virtual environments, installed dependencies, caches, indexes, embeddings, temporary files, and build artifacts are not durable repository content;
- framework documentation, generic Registry infrastructure, framework scripts, blueprints, repository guidance, and eventually framework-owned Agents are committed;
- committed Docs, Registry resources, scripts, examples, and other framework surfaces must not copy or embed private live user data;
- empty local-data boundaries may be retained with `.gitkeep` files or an equivalent minimal mechanism.

A user may deliberately version a live database or other user-owned state, including in a private Git repository. Tracking material that ShardBase ignores by default, or changing its normal distribution expectation, requires an explicit and inspectable repository-policy change rather than an accidental Git side effect. Git ignore rules prevent future accidental tracking; they do not erase private information already recorded in repository history.

## Project Status

ShardBase is in its foundation stage. Product Identity, Differentiation, Audience, the Shard AI-agent definition, Design Philosophy, Guarantees and Expectations, Universal vs Database-Specific Rules, Agent Architecture and Customization, Repository vs Local User Data, Canonical Database Experience, and Knowledge Lifecycle have been defined in the Foundation Roadmap Workbook, while the remaining conceptual language, governance, canonical implementation artifacts, validation behavior, and foundation proof are still in progress.

The foundation establishes product and architectural contracts before locking in implementation details such as a CLI runtime, compatibility matrix, migration engine, or blueprint materialization format. Those concerns should be added only when an implementation requires them.

The architectural source of truth is:

`app/Docs/Shard - System Specification.md`
