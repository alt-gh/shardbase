# ShardBase

ShardBase is a privacy-focused, user-owned structured Markdown knowledge-base framework designed to grow into an interconnected personal digital brain and source of truth.

It uses human-readable Markdown and YAML to organize knowledge through explicit structure, metadata, relationships, links, search, views, and AI-assisted interaction while keeping the underlying information understandable and editable independently of any single tool. ShardBase targets Obsidian as its primary knowledge environment, supports modular databases and extensible tooling, and is designed to let a user's knowledge grow across many areas of life without sacrificing readability, portability, structural integrity, privacy, or control.

## Why ShardBase

Personal knowledge becomes more valuable as it accumulates, connects, and remains usable over time, but it also becomes harder to keep coherent, connected, understandable, and useful as it grows. The problem is not simply storing more notes; it is allowing accumulated knowledge to become more useful and interconnected without the organizational system becoming harder to maintain than the knowledge is valuable.

Most of the useful primitives for personal knowledge management already exist: Markdown, YAML, folders, links and backlinks, tags, search, queries, templates, version control, automation, and AI assistance. ShardBase's central observation is that the missing piece is not another replacement for those primitives, but a durable shared contract that lets humans and tools interpret and operate over the same growing body of user-owned knowledge predictably.

ShardBase provides that shared architecture while keeping Markdown and YAML as the durable source. It is designed to reduce fragmentation, preserve lineage and context, support reliable retrieval and machine interpretation, and let structure grow only when it provides meaningful value. Sophisticated views, automation, and AI assistance can build on top of the knowledge without becoming prerequisites for understanding it.

The long-term goal is a user-owned personal source of truth that can support memory, understanding, discovery, learning, reasoning, decision-making, creation, and deliberate AI-assisted interaction without requiring the user to surrender ownership or architectural control of their knowledge. ShardBase succeeds when the user's knowledge becomes more valuable as it grows without becoming less theirs.

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
- **AI knowledge without AI integration** — ShardBase may structure, manage, validate, package, and export user-owned AI-related knowledge such as Agents, Prompts, instructions, and context, but ShardBase itself does not execute, invoke, authenticate with, orchestrate, connect to, or transmit data to AI models or AI-agent services. External AI use is a separate user-controlled workflow.
- **AI assistance is intentional but optional** — external AI agents may interpret, recommend, classify, retrieve, explain, and assist with maintenance when the user deliberately provides authorized ShardBase context, while explicit rules and deterministic validation preserve predictable structure. The knowledge base must remain durable and meaningful without AI.
- **Human authority is preserved** — ShardBase may automate repetitive, deterministic, and safely reversible work, but consequential, ambiguous, privacy-sensitive, or destructive decisions remain under meaningful user control.
- **Minimum necessary structure** — ShardBase uses the minimum structure necessary to preserve useful organization, relationships, growth, integrity, queryability, navigation, and lifecycle management, allowing structure to emerge as knowledge develops rather than requiring future complexity to be modeled in advance.
- **Simplicity without opacity** — ShardBase should minimize conceptual and operational burden, but simplicity must not hide necessary complexity in undocumented behavior, hidden state, or opaque tooling.
- **Readable, editable, and portable by construction** — canonical knowledge must remain readable, directly editable, and movable without requiring ShardBase-specific tooling; loss of an optional view, AI system, script, or generated runtime may reduce convenience but must not erase essential meaning.
- **No hidden architectural state** — essential knowledge meaning and architectural behavior must be traceable to canonical files and documented contracts. Undocumented inaccessible state must not become a required interpreter or silent authority merely because an implementation currently works.
- **Framework, not monolith** — universal rules define what it means to participate in ShardBase, while each database defines how it represents and operates on the particular domain of knowledge it owns. Database contracts may extend areas the framework intentionally leaves open, but they may not contradict universal invariants, and recurring local requirements should be documented rather than hidden in existing content.

External synchronization, backup, cloud storage, publishing, and sharing services are user choices and are separate from ShardBase's core operation.

### Approved Future Context Packs

ShardBase has an approved future **Context Pack** capability for packaging selected authorized context into a single local, provider-neutral artifact that a user can deliberately take to an external AI system or other tool. Context Packs will not make ShardBase an AI integration layer: generation remains local and ShardBase will not transmit the resulting artifact to ChatGPT, Gemini, DeepSeek, Claude, or another service.

A reusable Context Pack Definition will describe what to include, while each generated Context Pack Snapshot will be a timestamped, derived, non-authoritative, isolated snapshot with inspectable provenance. Different packs may select different databases, `Database.md` contracts, representative files, or knowledge for different purposes. Regeneration will create a new snapshot rather than modifying an older one in place.

Privacy-oriented packs will favor explicit inclusion of the minimum necessary context and deterministic filtering rules rather than AI inference. ShardBase will never create, store, manage, export, or require an identity or re-identification map connecting pseudonyms to real identities. A user who chooses to maintain such a mapping must keep it entirely outside ShardBase. Exact Context Pack schemas, locations, CLI syntax, privacy-transformation algorithms, and the relationship to any future universal visibility model remain deliberately deferred until implementation requirements justify standardization.

Context Packs are approved product direction but are **not part of the current Foundation implementation scope**.

### Product Design Principles

The commitments above are summarized by five product-level design principles that should guide feature, architecture, and implementation decisions:

1. **User-Owned Knowledge First** — preserve the user's ownership, privacy, recoverability, intended meaning, and meaningful authority over consequential outcomes before optimizing convenience or capability.
2. **Durable Source, Replaceable Tools** — keep canonical knowledge and architectural meaning in durable Markdown, YAML, and documented contracts so applications, views, automation, AI, and other tooling can be improved or replaced without redefining the source.
3. **Explicit Shared Meaning, One Authority** — make important architectural and semantic meaning explicit and inspectable while giving each fact one designated authoritative representation rather than creating competing sources of truth.
4. **Structure Must Earn Its Complexity** — add files, metadata, hierarchy, schemas, abstractions, workflows, and universal concepts only when they provide concrete value; allow knowledge to begin simply and structure to emerge from demonstrated need.
5. **Evolve Safely Under Meaningful User Control** — make structural evolution preservation-oriented and inspectable, automate deterministic low-risk mechanics where appropriate, and keep destructive, ambiguous, privacy-sensitive, breaking, or otherwise consequential decisions under meaningful user control.

When these principles conflict, preservation of user-owned knowledge and meaningful user control comes first, followed by structural integrity and explicit shared meaning, then durability and replaceability of the source and tooling. Within those boundaries, prefer the minimum necessary structure and the simplest design that supports safe future growth. Convenience, feature richness, performance, automation, and technical elegance are lower-order optimizations and must not justify sacrificing ownership, privacy, recoverability, or intended meaning.

## Who ShardBase Is For

ShardBase is primarily for individuals who want to build a long-lived personal source of truth across multiple subjects or areas of life without surrendering ownership, privacy, portability, or direct access to their underlying knowledge. The primary profile is defined by the knowledge problem rather than by profession or demographic category: the user expects their knowledge to remain useful and grow over years, wants it to become increasingly interconnected and reusable, and wants structure to reduce long-term organizational burden rather than become maintenance for its own sake.

Ordinary use should not require programming, database administration, Git expertise, advanced YAML knowledge, or memorization of the complete ShardBase architecture. Users should be able to start with basic Markdown-oriented capture, reading, editing, and navigation, while deeper architectural concepts are disclosed when they become useful. Obsidian is the primary supported environment, but it is an interface over the durable Markdown and YAML source rather than a requirement for that source to remain understandable. AI assistance is similarly intentional and valuable but optional.

Secondary profiles include Obsidian and personal-knowledge-management power users, researchers, writers, students, professionals, developers, and other knowledge-intensive users; people who adopt ShardBase for one substantial domain rather than a whole-life knowledge system; and technically inclined users who want to build views, validators, scripts, exports, or other tooling over a predictable Markdown and YAML architecture. AI users are not a separate audience: AI-assisted interaction may support these profiles, but AI adoption is not a prerequisite for ShardBase.

ShardBase is especially suited to knowledge that is expected to grow, connect, be queried, evolve, or remain useful over time. It is less suited to disposable note collections, autonomous systems that replace meaningful user control, cloud-hosted collaboration as a primary requirement, AI-provider integration or orchestration, synchronization or general-purpose search services, and workloads whose primary needs are traditional database transactions and machine-scale relational performance.

## Core Use Cases

ShardBase has three core product use cases:

1. **Build and grow a durable personal source of truth** — capture, develop, and organize knowledge across one or many areas while allowing structure to emerge as the knowledge earns it rather than requiring the complete future model up front.
2. **Find, connect, and use accumulated knowledge** — rediscover and work with knowledge through search, links, relationships, metadata, queries, views, and other compatible tools rather than depending primarily on remembered storage locations.
3. **Safely evolve the knowledge base as understanding changes** — expand, materialize, reorganize, refactor, classify, archive, or extend knowledge while preserving ownership, context, lineage, documented meaning, and user-authored source material.

Secondary use cases include maintaining a deep single-domain collection, building Dataview projections and other views, validating structural consistency, automating deterministic creation and maintenance work, using database-owned templates or specialist Agent resources, exporting user-owned knowledge for deliberate use elsewhere, and intentionally moving, backing up, synchronizing, versioning, or sharing databases through user-selected tools.

The product succeeds when accumulated knowledge becomes easier to understand, retrieve, connect, evolve, and build upon without organizational burden growing at the same rate. In the strongest form of that outcome: **ShardBase succeeds when the user's knowledge becomes more valuable as it grows without becoming less theirs.**

## Product Goals and Non-Goals

ShardBase pursues five product goals:

1. **Make accumulated knowledge increasingly useful as it grows** — knowledge should become more connected, discoverable, understandable, reusable, and valuable without organizational burden increasing at the same rate.
2. **Preserve durable user ownership and control** — canonical knowledge remains directly accessible as user-controlled Markdown and YAML, local-first by default, with consequential and external-exposure decisions under meaningful user control.
3. **Create a shared, explicit interpretation of knowledge** — humans, deterministic tooling, Obsidian, Dataview, validators, scripts, and deliberately used external AI systems should be able to operate over the same canonical source with a substantially shared understanding of important architectural meaning.
4. **Make knowledge safe to evolve** — users should be able to expand, materialize, reorganize, refactor, reclassify, archive, migrate, and otherwise evolve knowledge without routinely losing lineage, context, user-authored content, or intended meaning.
5. **Support extensible knowledge without creating a monolithic system** — a small stable universal framework should support modular databases whose domain-specific schemas, relationships, conventions, resources, and workflows remain local to the databases that need them.

ShardBase also has explicit product non-goals:

- It is **not a proprietary knowledge platform or cloud data service** that users must depend on to access or recover their canonical knowledge.
- It is **not an AI runtime, AI-service integration layer, or autonomous knowledge manager**. ShardBase may manage, validate, package, convert, and export AI-related knowledge, but it must not execute models, authenticate with AI providers, invoke agents, orchestrate model conversations, automatically transmit local knowledge to AI services, or become an intermediary between the user's knowledge and services such as ChatGPT or Gemini.
- It is **not a synchronization, backup, publishing, general-purpose search, or indexing service**; those responsibilities belong to user-selected tools.
- It is **not a replacement for a traditional database engine or cloud-first collaborative application platform** and does not target transactions, ACID guarantees, high-concurrency writes, machine-scale relational workloads, or simultaneous multi-user collaboration as core product responsibilities.
- It is **not a universal ontology or maximum-structure system**. Domain-specific complexity remains database-local, and new structure must justify itself through concrete value.

A proposed feature should be treated as possible scope creep when it moves canonical meaning into hidden or proprietary state, turns an optional tool into a prerequisite, universalizes a local requirement without independent justification, introduces substantial structure without concrete user value, reduces meaningful user control, prematurely standardizes implementation technology, or starts turning ShardBase into one of the adjacent products listed above.

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

ShardBase distinguishes framework-owned agents, database-owned specialist agents, and user-owned agents or customizations. A specialist agent may operate independently within its documented scope, but agent definitions and customizations never override the System Specification or the applicable database contract. Database-owned specialist Agent resources have an approved optional home at `app/Db/[Database Name]/Agents/` so they remain portable with their database. Framework-level and user-local Agent filesystem locations are intentionally deferred until concrete requirements justify standardizing them. Agent files are user-owned knowledge resources rather than an embedded AI runtime: ShardBase manages AI-related knowledge but does not integrate with AI systems.

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
│   │       ├── Agents/
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

`Agents/`, `Templates/`, and additional data collections are optional. A minimal database needs only one declared data collection.

## Database Anatomy

Each live database is a direct child of `app/Db/` and is self-contained.

### `Database.md`

The database manifest and local contract. It defines database identity, scope, declared data collections, semantic schema, conventions, and resources.

### `Agents/`

Optional database-owned specialist Agent resources live here so they remain portable with the database. These may include Agent definitions, Prompts, instructions, context, or related user-owned files intended for deliberate use with external AI systems. `Agents/` does not make ShardBase an AI runtime or integration layer, and Agent files never override the System Specification or `Database.md`.

### `Data/[Data Collection]/`

Contains canonical database notes for one database-defined data grouping. A database has one or more declared data collections; the primary collection is commonly the singular form of the database subject, while additional collections may represent other domain-owned kinds such as a series or collection concept.

Canonical Markdown notes live directly inside their declared data collection. `Attachments/` is a reserved non-structural resource subdirectory and must be excluded from structural-note discovery even if it contains a Markdown file. Tools should scan the declared collection roots rather than recursively treating every descendant beneath `Data/` as a Core, Shard, or Pebble candidate.

Data collections organize database-owned files; they do not define Pool membership, Core lineage, or structural parentage. Pools remain **logical metadata values**, not required filesystem folders.

### `Data/[Data Collection]/Attachments/`

Contains local non-structural files owned by the database and associated with that collection. Cross-database attachment references should be avoided so a database remains portable. A missing or deliberately offloaded attachment reference should be surfaced rather than silently removed; the exact offloading and restoration mechanism remains a lifecycle design question.

### `Templates/`

Optional database-owned note templates may live with the database so they remain portable with its schema and conventions. Templates and blueprint note material should focus on deterministic YAML metadata, structural scaffolding, and only the minimum body shape justified by the database contract rather than prescribing substantive domain prose. When AI-assisted note development is used, the database-owned specialist Agent is the appropriate domain-aware assistant for developing the body under `Database.md` and the user's intent; AI remains optional and knowledgeable users may author valid bodies manually. Templates may assist manual creation, but they do not replace the recommended workflow of using the CLI for canonical `app/Db/` notes and Inbox for ad-hoc editor-created notes. Headings or skeleton sections inside a template do not by themselves justify creating additional structural notes.

### `Views/`

Contains database-local views and queries. Dataview is a primary and canonical ShardBase interface in Obsidian. Views consume metadata; they do not define structural truth.

## Canonical Database Experience

ShardBase is designed to be used primarily through the user's chosen Markdown editor over ordinary local files. Existing canonical notes should remain comfortable to read and edit directly. The intended normal workflow recommends two primary entry paths for new notes: canonical notes intended for `app/Db/` should normally be created through the ShardBase CLI, while ad-hoc notes created through a Markdown editor or filesystem should normally enter `app/Inbox/` for review. A minimal CLI should be introduced at the earliest architecturally responsible opportunity once its underlying contracts are stable enough to implement safely. Canonical CLI creation should be schema-aware and type-safe in behavior: applicable templates may provide starting shape, while structural and database semantic contracts determine validity and are checked before a write. The exact runtime and validation technology remain implementation-defined. Until the CLI exists, and for knowledgeable users who deliberately choose otherwise, canonical files may still be created manually subject to the documented contract.

ShardBase manages AI-related knowledge; it does not integrate with AI systems. Framework scripts and the CLI do not call model-provider APIs, authenticate with providers, invoke or orchestrate external agents, or automatically broker local knowledge to services such as ChatGPT or Gemini. ShardBase may structure, validate, package, convert, or export local user-owned Agent, Prompt, instruction, context, or related files. Users who want an external AI system to receive those files or other ShardBase information perform that transfer through a separate deliberate workflow using the external system of their choice.

## Structural and Semantic Metadata

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

These fields record framework-level role, placement, lineage, and lifecycle state. `type`, `pool`, `core`, `parent_note`, and `status` are reserved structural fields whose universal meanings must not be repurposed for database-domain semantics. For supporting notes, `parent_note` points to the immediate structural parent. For a Core, `parent_note` is empty. A Core and its structural descendants use the same canonical `pool` value. A database may define its permitted Pool vocabulary, but it does not redefine what `pool` means structurally.

Domain-specific meaning belongs in separate database-defined semantic metadata, such as `entity_kind`, `developer`, `author`, `release_date`, `project_phase`, or `relationship_kind`. These are illustrative rather than universal fields; their meanings and constraints belong to the owning database's `Database.md`. Semantic metadata may inform a structural classification decision, but it never substitutes for or overrides structural metadata. In particular, `type` is never repurposed for semantic categories such as person, project, game, book, source, or organization, and structural `status` is not a substitute for a database-specific workflow or domain-state field.

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

ShardBase treats lifecycle as a state-and-decision model rather than a mandatory pipeline. Knowledge may enter through private pre-structural Inbox capture, direct canonical creation when its representation is already resolved, or incorporation into existing canonical notes. Review may incorporate information, leave it unresolved, retain only a Ghost Shard, materialize new canonical structure, or result in user discard. When canonical representation is unresolved, classification determines database ownership, declared data collection, Pool, root Core, immediate parent, structural role where applicable, and the database-semantic requirements needed for the intended outcome; classification may also conclude that ordinary Markdown is the correct representation.

ShardBase allows knowledge to begin simply and gain structure only when that structure earns a purpose. A separate canonical file is justified by meaningful independent growth, querying, navigation, reuse, reference, lifecycle management, structural organization, or another concrete benefit rather than by conceptual hierarchy, headings, or note length alone. Content may continue growing within an existing note indefinitely. Materializing one note does not authorize additional implied notes; each additional structural note must independently earn materialization and be deliberately created.

Refactoring is preservation-oriented and should move knowledge from one coherent representation to another through the smallest valid change. Archived knowledge remains canonical and in place with an archived lifecycle status; archiving is not deletion. During the Foundation stage, normal deletion is a deliberate user action through Obsidian, another Markdown editor, or the filesystem rather than an autonomous ShardBase operation. Structural and attachment orphans may be reported for review but are never repaired or deleted through guesswork. Attachments remain database-owned resources whose existence does not silently follow the lifecycle of any one referencing note. Ghost Shards may remain unresolved indefinitely and become real notes only when the knowledge earns materialization and the user deliberately creates them.

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
- generated runtimes, virtual environments, installed dependencies such as `node_modules`, Python bytecode such as `__pycache__`, caches, indexes, embeddings, temporary files, and build artifacts must remain outside the ShardBase vault and are not durable repository content;
- framework documentation, generic Registry infrastructure, framework scripts, blueprints, repository guidance, and eventually framework-owned Agents are committed;
- committed Docs, Registry resources, scripts, examples, and other framework surfaces must not copy or embed private live user data;
- empty local-data boundaries may be retained with `.gitkeep` files or an equivalent minimal mechanism.

A user may deliberately version a live database or other user-owned state, including in a private Git repository. Tracking material that ShardBase ignores by default, or changing its normal distribution expectation, requires an explicit and inspectable repository-policy change rather than an accidental Git side effect. Git ignore rules prevent future accidental tracking; they do not erase private information already recorded in repository history.

## Architectural Evolution and Compatibility

ShardBase distinguishes architectural clarification, extension, schema change, migration, and breaking change rather than treating all architectural evolution as equivalent. A breaking change is one that makes previously compliant knowledge, databases, documented workflows, or observable tooling assumptions invalid, changes their intended meaning, removes supported meaning, or requires modification for continued compliance. The existence of a migration does not make such a change non-breaking.

Normative changes to the universal System Specification require an explicit specification-version boundary, while `manifest_version` identifies only the database-manifest schema. Existing databases should not be migrated merely to normalize them when the newer contract can safely interpret them unchanged. When migration is required, it must be explicit and preservation-oriented; compatibility boundaries, unsupported versions, changes to existing canonical meaning, and other breaking transformations must never be silently guessed through or applied.

Backward compatibility means preserving the documented meaning of older supported state. It does not mean ShardBase architecture can never change or that every historical implementation detail must be supported indefinitely.

## Project Status

ShardBase is in its foundation stage. Product Identity, the Product Thesis, Target Users and Use Cases, Goals and Non-Goals, Design Principles, Foundation Success Criteria, Differentiation, Audience, the Shard AI-agent definition, Design Philosophy, Guarantees and Expectations, Universal vs Database-Specific Rules, Agent Architecture and Customization, Repository vs Local User Data, Canonical Database Experience, Knowledge Lifecycle, Foundation Boundaries, the Breaking Change Definition, and Foundation Exit Criteria have been defined in the Foundation Roadmap Workbook. Milestone 1 — Define the Product is complete. Detailed versioning, migration, and compatibility governance, canonical implementation artifacts, validation behavior, and foundation proof are still in progress. The exact universal `visibility` model is an approved post-Foundation deferral; existing local-first privacy, authorization, and external-exposure boundaries remain authoritative until a concrete requirement justifies a universal visibility contract.

The foundation standardizes durable and observable contracts before locking in replaceable implementation details. Its accepted success standard is that product direction is explicit, architecture is coherent and deterministic where appropriate, safety and user control are built into normal operation, the system remains understandable without hidden dependencies, and initial tooling can implement the documented contracts without inventing foundational meaning. Stability does not mean freezing ShardBase; implementation may still discover details, but it should no longer have to invent architecture.

A minimal CLI may begin as soon as the creation contracts it depends on are sufficiently settled so those contracts can be exercised through real use; mature CLI UX, compatibility matrices, migration engines, validation libraries, blueprint packaging details, and the approved Context Pack generator should be added only when implementation demonstrates the need and the contracts they depend on are sufficiently settled. Context Packs are approved post-Foundation product direction, not current Foundation implementation scope. AI-provider integration, synchronization systems, and general-purpose search/indexing engines are not deferred ShardBase implementation targets: AI integration remains outside the product boundary, while synchronization and search/indexing are provided by user-selected external tools.

The architectural source of truth is:

`app/Docs/Shard - System Specification.md`
