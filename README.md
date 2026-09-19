# ShardBase

ShardBase is a privacy-focused, user-owned structured Markdown knowledge-base framework designed to grow into an interconnected personal digital brain and source of truth.

Its durable source is ordinary Markdown and YAML. Obsidian is the primary knowledge environment, Dataview is a primary query interface, and scripts or external AI systems may assist with the knowledge, but none of those tools owns or defines the canonical meaning of the data.

ShardBase is local-first: user-owned knowledge stays local unless the user deliberately chooses to synchronize, publish, share, back up, or provide it to an external service.

## The Core Idea

ShardBase adds a small shared architectural contract to familiar knowledge-management primitives such as Markdown, YAML, folders, wikilinks, tags, queries, templates, scripts, and AI assistance.

The structural model is:

**Pool → Core → Shard → Pebble**

- **Pool** groups related lineages inside a database.
- **Core** is the root note of one lineage.
- **Shard** is a reusable subdivision that may have structural children.
- **Pebble** is a terminal structural note.

Not everything should become a structural note. Ordinary Markdown headings and sections are preferred until a separate file earns independent value through growth, querying, navigation, reuse, reference, or lifecycle management.

For the complete structural contract, see [`app/Docs/Shard System Specification.md`](app/Docs/Shard%20System%20Specification.md).

## Documentation Authority

ShardBase deliberately avoids duplicating authoritative rules across documents.

| Document | Role | Authority |
|---|---|---|
| [`app/Docs/Shard System Specification.md`](app/Docs/Shard%20System%20Specification.md) | Universal architecture, invariants, compatibility, safety, validation contract | **Highest framework authority** |
| `app/Knowledge/Databases/<Database>/Database.md` | Purpose, scope, semantic schema, Pool vocabulary, local conventions and resources for one live database | **Database-local authority** |
| [`app/Blueprints/Games/Database.md`](app/Blueprints/Games/Database.md) | Bootstrap contract for a new Games database | Authoritative only as blueprint source before materialization |
| [`AGENTS.md`](AGENTS.md) | Operating instructions for agents working in this repository | Operational guidance; consumes the authorities above |
| [`app/Scripts/README.md`](app/Scripts/README.md) | Current CLI/validator setup, behavior, and implementation limits | Tooling documentation; does not define architecture |
| [`app/Registry/Registry.md`](app/Registry/Registry.md) | Runtime database discovery/navigation view | Navigational only |
| [`app/Docs/ShardBase Foundation Roadmap.md`](app/Docs/ShardBase%20Foundation%20Roadmap.md) | Current work, milestone status, blockers, and deferred work | Planning only; never architectural authority |
| [`app/Docs/ADR/`](app/Docs/ADR/) | Accepted architectural decisions and rationale | Historical rationale; current normative rules remain in the System Specification |

If supporting documentation and an authoritative contract disagree, correct the supporting documentation rather than treating the disagreement as a new rule.

## Repository Structure

```text
shardbase/
├── .obsidian/
├── app/
│   ├── Blueprints/
│   ├── Docs/
│   │   └── ADR/
│   ├── Knowledge/
│   │   ├── Inbox/
│   │   └── Databases/
│   │       └── <Database>/
│   │           ├── Agents/
│   │           ├── Data/
│   │           ├── Templates/
│   │           ├── Views/
│   │           └── Database.md
│   ├── Registry/
│   └── Scripts/
├── AGENTS.md
└── README.md
```

`app/Knowledge/` is the private-by-default boundary for user-owned knowledge. `Inbox/` contains unresolved pre-structural capture. `Databases/` contains live canonical databases. Every direct child of `app/Knowledge/Databases/` is a database governed by its own root `Database.md`.

`app/Blueprints/`, `app/Docs/`, `app/Registry/`, and `app/Scripts/` are framework surfaces intended to be distributable. They must not silently absorb private live knowledge.

## Working with Databases

Each database owns the domain meaning inside its documented scope. Universal ShardBase structure stays universal; domain-specific fields, relationships, classifications, and conventions stay in the owning database's `Database.md`.

A database may relate to knowledge in another database without taking ownership of it. Structural lineage remains database-local: `core` and `parent_note` never create cross-database ancestry.

Canonical notes may remain flat at a declared data-collection root or one Core lineage may be deliberately bundled into a direct-child Core workspace. Filesystem placement provides organization; YAML remains authoritative for lineage.

Under foundation-3, Core filenames remain human-readable title filenames. Shards and Pebbles use their local human-readable title plus a stable opaque note ID; ancestry is carried by `core` and `parent_note`, not repeated in filenames.

For exact manifest requirements, note metadata, naming, placement, lifecycle, attachment rules, and validation expectations, use the System Specification rather than this README.

## Current Tooling

ShardBase currently includes:

- a local draft-creation CLI;
- a read-only structural validator;
- regression tests and sanitized fixtures;
- runtime Registry discovery;
- a Games starter blueprint with draft templates and the optional Vera specialist Agent resource.

The current `new` command automatically creates pre-structural drafts in `app/Knowledge/Inbox/`. Users can organize drafts manually after capture. It does **not** yet create canonical database notes or automatically promote drafts. The validator checks the implemented `foundation-3` structural contract but does not yet consume database semantic schemas deterministically.

See [`app/Scripts/README.md`](app/Scripts/README.md) for commands, supported behavior, and implementation limits.

## Games Starter Database

`app/Blueprints/Games/` is the first framework-supplied proving database. Its `Database.md` defines Games-specific ownership, the `Games` Pool, Game Core strategy, semantic fields such as `release_date`, `genres`, and `play_state`, and database-local completion-record conventions.

The blueprint also contains three draft templates and [`Agents/Vera.md`](app/Blueprints/Games/Agents/Vera.md). These resources implement or operationalize the Games contract; they do not replace it.

After a blueprint is materialized into a live database, the live copy is user-owned. Later blueprint changes never silently synchronize into it.

## Product Boundaries

ShardBase is designed to preserve user-owned knowledge, shared explicit meaning, safe evolution, and replaceable tooling. It is intentionally **not**:

- a proprietary or cloud-owned knowledge platform;
- an AI runtime or AI-provider integration layer;
- a synchronization, backup, publishing, or general-purpose search/indexing service;
- a replacement for a transactional database engine;
- a universal ontology or maximum-structure system.

ShardBase may manage, validate, package, convert, or export user-owned AI-related files, but it does not execute models, authenticate with providers, orchestrate agents, or transmit local knowledge to AI services. Any external AI use is a separate user-controlled workflow.

## Project Status

ShardBase is in the **Foundation** stage. The universal architecture and substantial deterministic validation are already implemented, but Foundation is not complete.

The remaining work is primarily convergence and proof: finish the structural decision framework and canonical examples, make database semantic constraints machine-readable and deterministically validatable, implement safe canonical creation/promotion, prove the complete Games lifecycle, reconcile governance/status documentation, and complete Foundation sign-off.

See [`app/Docs/ShardBase Foundation Roadmap.md`](app/Docs/ShardBase%20Foundation%20Roadmap.md) for current status only. Architectural requirements belong in the System Specification, not the roadmap.
