# Shardbase

Shardbase is a privacy-focused, user-owned structured Markdown knowledge-base framework designed to grow into an interconnected personal digital brain.

Its durable source is ordinary Markdown and YAML. Obsidian is the primary knowledge environment, Dataview is a primary query interface, and scripts or external AI systems may assist with the knowledge, but none of those tools owns or defines the canonical meaning of the data.

Shardbase is local-first: user-owned knowledge stays local unless the user deliberately chooses to synchronize, publish, share, back up, or provide it to an external service.

## The Core Idea

Shardbase adds a small shared architectural contract to familiar knowledge-management primitives such as Markdown, YAML, folders, wikilinks, tags, queries, templates, scripts, and AI assistance.

The structural model is:

**Pool → Core → Shard → Pebble**

- **Pool** groups related lineages inside a database.
- **Core** is the root note of one lineage.
- **Shard** is a reusable subdivision that may have structural children.
- **Pebble** is a terminal structural note.

Not everything should become a structural note. Ordinary Markdown headings and sections are preferred until a separate file earns independent value through growth, querying, navigation, reuse, reference, or lifecycle management.

For the complete structural contract, see [`app/Docs/Shard System Specification.md`](app/Docs/Shard%20System%20Specification.md).

## Documentation Authority

Shardbase deliberately avoids duplicating authoritative rules across documents.

| Document | Role | Authority |
|---|---|---|
| [`app/Docs/Shard System Specification.md`](app/Docs/Shard%20System%20Specification.md) | Universal architecture, invariants, compatibility, safety, validation contract | **Highest framework authority** |
| `app/Knowledge/Databases/<Database>/Database.md` | Purpose, scope, semantic schema, Pool vocabulary, local conventions and resources for one live database | **Database-local authority** |
| [`app/Blueprints/Games/Database.md`](app/Blueprints/Games/Database.md) | Bootstrap contract for a new Games database | Authoritative only as blueprint source before materialization |
| [`AGENTS.md`](AGENTS.md) | Operating instructions for agents working in this repository | Operational guidance; consumes the authorities above |
| [`app/Scripts/README.md`](app/Scripts/README.md) | Current CLI/validator setup, behavior, and implementation limits | Tooling documentation; does not define architecture |
| [`app/Registry/Registry.md`](app/Registry/Registry.md) | Runtime database discovery/navigation view | Navigational only |
| [`app/Docs/Shardbase Foundation Roadmap.md`](app/Docs/Shardbase%20Foundation%20Roadmap.md) | Current work, milestone status, blockers, and deferred work | Planning only; never architectural authority |
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
├── tests/
│   └── fixtures/
├── AGENTS.md
└── README.md
```

`app/Knowledge/` is the private-by-default live knowledge boundary. `Inbox/` contains user-owned unresolved capture. Each direct child of `Databases/` combines a Shardbase-managed package (`Database.md`, supplied Templates and Agents, and other package resources) with user-owned `Data/` and `Views/`. Path location alone no longer determines ownership.

`app/Blueprints/`, `app/Docs/`, `app/Registry/`, and `app/Scripts/` are framework surfaces intended to be distributable. They must not silently absorb private live knowledge.

## Working with Databases

Each database owns the domain meaning inside its documented scope. Universal Shardbase structure stays universal; domain-specific fields, relationships, classifications, and conventions stay in the owning database's `Database.md`.

A database may relate to knowledge in another database without taking ownership of it. Structural lineage remains database-local: `core` and `parent_note` never create cross-database ancestry.

Canonical notes may remain flat at a declared data-collection root or one Core lineage may be deliberately bundled into a direct-child Core workspace. Filesystem placement provides organization; YAML remains authoritative for lineage.

Under foundation-3, Core filenames remain human-readable title filenames. Shards and Pebbles use their local human-readable title plus a stable opaque note ID; ancestry is carried by `core` and `parent_note`, not repeated in filenames.

For exact manifest requirements, note metadata, naming, placement, lifecycle, attachment rules, and validation expectations, use the System Specification rather than this README.

## Current Tooling

Shardbase currently includes:

- guided initialization for new, restored, or tooling-only private instances;
- a local CLI for blueprint-based database scaffolding and direct canonical note creation;
- a read-only structural validator;
- manual encrypted user-state backup and restore commands;
- regression tests and sanitized fixtures;
- runtime Registry discovery;
- a Games starter blueprint with draft templates and the optional Vera specialist Agent resource.

Use `shardbase create new` to choose **Inbox capture** or **database creation**. Database creation selects a live database, resolves canonical identity and lineage, and writes directly after structural validation. New Cores normally receive a workspace; supporting notes inherit the selected Core’s Pool, collection, and existing workspace or flat location. Each canonical note receives a stable ID and the required filename. Inbox captures remain provisional in `app/Knowledge/Inbox/`.

For temporary captures, create notes directly in your Markdown editor, preferably Obsidian, or filesystem. Configure the editor's default new-note location as `app/Knowledge/Inbox/`. These notes can remain ordinary Markdown without structural metadata. Shardbase does not change your editor settings automatically.

Canonical creation checks structural validity before and after writing and rolls back its own new artifacts on failure. Database-specific semantics still require review. Existing flat lineages and historical Inbox notes remain unchanged; release upgrades reconstruct managed packages during restore into a fresh checkout and never synchronize them into an existing live database in place.

Start with the [external-runtime setup](app/Scripts/README.md#runtime-setup), then run `shardbase commands` to browse the available commands. The [command reference](app/Scripts/README.md#command-reference) collects every command and links to the supported behavior and implementation limits. `shardbase new` remains a compatibility alias.

Use `shardbase doctor` for read-only framework, privacy, runtime, and structural database health checks. It distinguishes warnings from blocking issues and performs no repairs; see [instance health diagnostics](app/Scripts/README.md#instance-health-diagnostics).

Use `shardbase backup` and `shardbase restore` to preserve user state or transfer it into a fresh compatible checkout. Format v2 supports foundation-4/5 sources into foundation-5, encrypts Inbox, every database's Data and Views, and the entire `.obsidian/` tree; the destination release supplies current managed database packages by stable `database_id`. See [encrypted backup and restore](app/Scripts/README.md#encrypted-backup-and-restore) for passphrase handling, conflict safety, and compatibility limits.

## Get Started

For a private instance, download the repository ZIP, extract it, and open a terminal in the extracted folder. Git is not required. With Python 3.10 or newer, run:

```sh
python bootstrap.py
```

Use `python3 bootstrap.py` if that is your Python command on macOS/Linux, or `py bootstrap.py` on Windows. Bootstrap prepares the external runtime and launcher, installs pinned dependencies (which may access the network), and checks that the CLI starts. It prints a current-session PATH command if needed; it never changes PATH or shell profiles automatically.

For a fresh private ZIP-style instance in an interactive terminal, bootstrap continues directly into guided setup. You can also start or rerun it manually once the launcher is on PATH:

```sh
shardbase init
```

Guided setup offers three choices: start a new private instance from one available blueprint, restore an encrypted backup, or finish tooling setup without creating knowledge. The setup-only path creates no Knowledge directory or setup marker. Git-managed/development and noninteractive bootstrap runs print `shardbase init` as the manual next step instead of entering an interactive session.

The new-instance path lets you choose from `app/Blueprints/`. Games is currently the supplied option; additional blueprint packages appear automatically. Choosing Games creates `app/Knowledge/Databases/Games/` with its manifest, collection, attachments folder, templates, Views, and optional Agent resource. It also creates Inbox if needed. Existing databases are recognized and never merged or overwritten.

After a new database is ready, run `shardbase create new` to create your first note. Choose database intent and your new database; the CLI prints its actual canonical path after structural checks pass. Use `shardbase validate` for later edits and `shardbase commands` to explore the CLI.

The Python environment and launcher stay outside the project. For platform defaults, persistent PATH configuration, custom locations, and safe reruns, see the [tooling guide](app/Scripts/README.md#runtime-setup) and [database creation guide](app/Scripts/README.md#database-creation).

## Games Starter Database

`app/Blueprints/Games/` is the first framework-supplied proving database. Its `Database.md` defines Games-specific ownership, the `Games` Pool, Game Core strategy, semantic fields such as `release_date`, `genres`, and `play_state`, and database-local completion-record conventions.

The blueprint also contains three draft templates and [`Agents/Vera.md`](app/Blueprints/Games/Agents/Vera.md). These resources implement or operationalize the Games contract; they do not replace it.

After materialization, Data and Views are user-owned while the live manifest, supplied Templates and Agents, and other package resources are Shardbase-managed. Existing live packages are never silently synchronized or overwritten; the upgrade path restores user state into a fresh release checkout.

## Product Boundaries

Shardbase is designed to preserve user-owned knowledge, shared explicit meaning, safe evolution, and replaceable tooling. It is intentionally **not**:

- a proprietary or cloud-owned knowledge platform;
- an AI runtime or AI-provider integration layer;
- a synchronization, backup, publishing, or general-purpose search/indexing service;
- a replacement for a transactional database engine;
- a universal ontology or maximum-structure system.

Shardbase may manage, validate, package, convert, or export AI-related files under the ownership rules of their surface, but it does not execute models, authenticate with providers, orchestrate agents, or transmit local knowledge to AI services. Any external AI use is a separate user-controlled workflow.

## Project Status

Shardbase is in the **Foundation** stage. The universal architecture and substantial deterministic validation are already implemented, but Foundation is not complete.

The remaining work is primarily convergence and proof: finish the structural decision framework and canonical examples, make database semantic constraints machine-readable and deterministically validatable, extend creation with semantic validation and add deliberate draft promotion, prove the complete Games lifecycle, reconcile governance/status documentation, and complete Foundation sign-off.

See [`app/Docs/Shardbase Foundation Roadmap.md`](app/Docs/Shardbase%20Foundation%20Roadmap.md) for current status only. Architectural requirements belong in the System Specification, not the roadmap.
