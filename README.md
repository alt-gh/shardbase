# Shardbase

Shardbase is a privacy-focused, user-owned, local-first framework for durable personal knowledge. It stores canonical knowledge as ordinary Markdown and YAML so your notes remain readable, editable, and portable without a proprietary platform.

Obsidian is the primary knowledge environment, but it does not own Shardbase's canonical meaning. Editors, queries, scripts, sync tools, and external AI systems may assist with your knowledge only when you choose to use them.

## Get Started

Private use is ZIP-first. You do not need Git or a development checkout.

1. On GitHub, choose **Code → Download ZIP**.
2. Extract the ZIP into the folder where you want your private Shardbase instance.
3. Open a terminal in the extracted folder.
4. With Python 3.10 or newer, run:

   ```sh
   python bootstrap.py
   ```

   On macOS or Linux, use `python3 bootstrap.py` if `python3` is your Python command. On Windows, you can use `py bootstrap.py`.

Bootstrap checks the instance, prepares or reuses a Python runtime outside it, installs the pinned runtime dependencies, safely creates or refreshes the external `shardbase` launcher, and verifies that the CLI starts. Dependency installation may access your configured Python package index. Bootstrap does not silently change `PATH` or shell profiles; if needed, it prints a command for the current terminal session.

For a fresh private ZIP instance in an interactive terminal, bootstrap can continue directly into guided setup. Guided setup offers three paths:

- start a new private instance from an available database blueprint;
- restore an encrypted Shardbase backup;
- finish tooling setup without creating knowledge.

After initializing a new instance, capture your first note in Inbox:

```sh
shardbase create new
```

Run `shardbase commands` to explore the available commands. Use `shardbase doctor` to inspect instance and tooling health, and `shardbase validate` for read-only structural validation of live databases.

For platform-specific setup, custom runtime locations, launcher safety, and all command details, use the [tooling guide](app/Scripts/README.md).

## Private by Default

The recommended private-user installation is a GitHub ZIP download, not `git clone`. A normal extracted ZIP has no `.git/` directory and no Git remote. Bootstrap does not initialize Git, add a remote, upload files, or connect the private instance to the public repository.

Shardbase does not automatically upload, publish, synchronize, or transmit your knowledge. You may deliberately use sync software, backups, Git hosting, external AI, or other services, but those are separate user-controlled workflows. Git-less operation does not prevent editors, operating-system services, or other local software from accessing files according to their own permissions and behavior.

`app/Knowledge/` is the private-by-default knowledge boundary. Inbox, each live database's Data and Views, and `.obsidian/` are user-owned state. A live database's `Database.md`, supplied Templates and Agents, and other blueprint package resources are Shardbase-managed so a compatible release can reconstruct them during restore. Path location alone does not determine ownership.

## Why Shardbase

Shardbase is for people who want structured, interconnected knowledge without surrendering control of the underlying files. Its design emphasizes:

- human-readable Markdown and explicit YAML rather than hidden application state;
- local ownership with optional, deliberate external services;
- durable meaning that survives changes in editors, scripts, and hosted tools;
- enough shared structure for navigation and validation without forcing every idea into a separate file;
- preservation-oriented evolution, encrypted user-state backups, and replaceable tooling.

Shardbase is not a hosted knowledge platform, synchronization service, publishing system, transactional database, universal ontology, or AI runtime. It does not execute models, authenticate with AI providers, orchestrate agents, or transmit local knowledge to AI services.

## How It Works

New CLI-created notes begin in `app/Knowledge/Inbox/` as database-independent, pre-structural captures. Each receives the complete universal YAML key set and a stable ID, while database ownership, Pool, lineage, database-specific metadata, and canonical placement remain unresolved.

Promotion is a later, deliberate decision that resolves those details and moves knowledge into a live database's canonical structure. Automated promotion is not yet implemented. Existing Inbox captures and canonical data remain unchanged.

Each live database owns the meaning of its domain through its root `Database.md`. Universal Shardbase structure remains universal, structural lineage stays within one database, and YAML—not folders, filenames, tags, or links—is authoritative for lineage.

## Core Concepts

The structural model is:

**Pool → Core → Shard → Pebble**

- **Pool** groups related lineages inside a database.
- **Core** is the root note of one lineage.
- **Shard** is a meaningful subdivision that may have structural children.
- **Pebble** is a terminal structural note.

Not everything should become a structural note. Ordinary Markdown headings and sections are preferred until a separate file provides concrete value through growth, querying, navigation, reuse, reference, or lifecycle management.

The [System Specification](app/Docs/Shard%20System%20Specification.md) defines the exact rules for metadata, lineage, naming, placement, lifecycle, attachments, validation, and compatibility.

## Repository Structure

```text
shardbase/
├── .github/                 # Repository automation
├── .obsidian/               # User-owned local Obsidian configuration
├── app/
│   ├── Blueprints/          # Distributable database packages
│   ├── Docs/                # Architecture and project documentation
│   ├── Knowledge/           # Private-by-default live knowledge
│   │   ├── Inbox/           # Unresolved user-owned captures
│   │   └── Databases/       # Live database packages and user data
│   ├── Registry/            # Database discovery and navigation
│   └── Scripts/             # CLI and validation tooling
├── tests/                   # Tests and synthetic fixtures
├── AGENTS.md
├── CONTRIBUTING.md
├── SECURITY.md
├── README.md
├── bootstrap.py
└── pyproject.toml
```

`app/Blueprints/`, `app/Docs/`, `app/Registry/`, and `app/Scripts/` are distributable framework surfaces and must not absorb private live knowledge. Generated runtimes, dependencies, caches, and temporary output stay outside the instance.

Games is the currently supplied starter and proving blueprint. Its [`Database.md`](app/Blueprints/Games/Database.md) owns Games-specific scope and semantics; its templates and optional specialist Agent resources support that contract but do not replace it or the System Specification.

## Tooling

The root README provides only the first-run path. The [tooling guide](app/Scripts/README.md) documents exact setup behavior, options, safety rules, limitations, and compatibility.

| Command | Purpose |
|---|---|
| `python bootstrap.py` | Prepare or reuse the external runtime and launcher, then begin guided setup when appropriate. |
| `shardbase init` | Run guided new-instance, encrypted-restore, or setup-only onboarding. |
| `shardbase create new` | Create a local Inbox-first capture with a stable ID and provisional structural role. It does not promote the note. |
| `shardbase commands` | List the complete current command set. |
| `shardbase doctor` | Run read-only health diagnostics and distinguish warnings from blocking failures; it performs no repair. |
| `shardbase validate` | Run read-only structural validation. Passing does not prove arbitrary database-semantic correctness or complete Foundation compliance. |
| `shardbase backup` | Create an encrypted backup of durable user state. |
| `shardbase restore` | Restore encrypted user state into a compatible Shardbase release. |

Backup and restore compatibility, encryption, conflicts, and wire-format behavior are documented in the [tooling guide](app/Scripts/README.md#encrypted-backup-and-restore) and [backup format contract](app/Scripts/BACKUP_FORMAT.md).

## Documentation

- The [System Specification](app/Docs/Shard%20System%20Specification.md) is the highest framework authority for universal architecture and safety rules.
- A live database's `Database.md` is the authority for that database's scope, semantic schema, Pool vocabulary, conventions, and resources.
- The [tooling guide](app/Scripts/README.md) documents current CLI and validator behavior and limitations.
- [AGENTS.md](AGENTS.md) defines operating behavior for agents working in this repository.
- [CONTRIBUTING.md](CONTRIBUTING.md) defines contributor and development workflows.
- The [Foundation Roadmap](app/Docs/Shardbase%20Foundation%20Roadmap.md) records project planning and status, not architecture.
- [Architecture Decision Records](app/Docs/ADR/) preserve accepted decisions and rationale; current normative rules remain in the System Specification.

When supporting documentation conflicts with a higher authority, correct the supporting documentation rather than treating the disagreement as a new rule.

## Project Status

Shardbase is in the **Foundation** stage. The universal architecture and substantial deterministic structural validation are implemented, but Foundation is not complete.

Remaining work includes clearer structural classification guidance, canonical examples and proof, deterministic database-semantic validation, deliberate Inbox draft promotion, complete Games lifecycle proof and second-domain generalization, governance/status reconciliation, and final Foundation sign-off.

See the [Foundation Roadmap](app/Docs/Shardbase%20Foundation%20Roadmap.md) for current status.

## Contributing

Private users should normally follow the ZIP workflow in [Get Started](#get-started). Contributors work from a Git clone and use separate development setup, linting, testing, and branch workflows documented in [CONTRIBUTING.md](CONTRIBUTING.md).
