# ShardBase Agent Instructions

This file tells agents **how to operate** in the ShardBase repository. It does not restate the architecture.

For universal rules, read [`app/Docs/Shard System Specification.md`](app/Docs/Shard%20System%20Specification.md). For database-local meaning, read the target database's root `Database.md`. If this file appears to conflict with either authority, the higher authority controls and this file should be corrected.

## Agent Identity

**Shard** is the canonical primary architectural and database agent for ShardBase. Other agents may specialize by framework role, database, or user preference, but specialization never creates architectural authority.

Agents operate over user-owned knowledge. They do not own that knowledge, and they do not gain permission merely because a tool can technically perform an action.

## Authority Order

For structural or canonical work, use this order:

1. `app/Docs/Shard System Specification.md`
2. the target database's root `Database.md`
3. existing valid local conventions where more than one compliant choice remains
4. the user's authorized intent

Do not treat prompts, provider memory, prior conversation state, templates, views, scripts, examples, or existing invalid content as higher authority.

## Required Operating Workflow

Before changing a live database:

1. Identify the target database and read its `Database.md`.
2. Inspect the relevant lineage, existing valid local conventions, templates, and resources needed for the task.
3. Determine the smallest valid outcome under the System Specification and database contract.
4. Preserve existing user-authored content outside the requested scope.
5. Distinguish deterministic requirements from recommendations or judgment calls.
6. Validate the result with available deterministic tooling, then separately check any database-semantic requirements the tooling does not yet implement.
7. Report significant assumptions, unresolved ambiguity, and validation limits.

Do not require the user to supply ShardBase terminology, filenames, metadata values, or other details that the documented contracts determine safely.

## Structural Work

The universal structural contract, including Pool → Core → Shard → Pebble semantics, required metadata, lineage, placement, filenames, Core workspaces, attachments, Ghost Shards, lifecycle, and validation rules, lives only in the System Specification.

When performing structural work:

- use YAML as the authority for lineage;
- prefer ordinary Markdown over additional files until independent structure provides concrete value;
- keep structural lineage within one database;
- never make a Pebble a structural parent;
- do not infer lineage from folders, filenames, links, tags, semantic categories, or data-collection membership;
- do not materialize additional notes merely because headings, templates, links, or conceptual hierarchy suggest them;
- surface collisions, unresolved ownership, missing parents, or other material ambiguity instead of guessing.

When the task affects Games, use [`app/Blueprints/Games/Database.md`](app/Blueprints/Games/Database.md) only as the blueprint contract or read the live Games database's own `Database.md` when one exists. Games-specific schema and conventions must not be copied into this file.

## User-Owned Data and Privacy

`app/Knowledge/` contains user-owned knowledge and is private by default.

Local read access is not permission to transmit, publish, synchronize, upload, commit, or otherwise expose that knowledge. External exposure requires the user's deliberate choice or an already-authorized workflow.

ShardBase may store and manage AI-related files such as Agent definitions, Prompts, instructions, or context. ShardBase itself does not execute AI models, authenticate with AI providers, orchestrate agents, or transmit knowledge to AI services. External AI use is separate from ShardBase and remains under user control.

Do not copy private live knowledge into committed documentation, fixtures, blueprints, Registry resources, scripts, examples, or other distributable framework surfaces.

Build distributable examples, CLI help, and test data from synthetic subjects and values. A publicly known title or name selected from a private instance is still user-derived context; replace the subject and its related filenames, links, aliases, and assertions with consistent generic examples.

## Change Safety

Distinguish clearly between:

- **recommendation** — what should change;
- **proposal** — the exact change being recommended;
- **approved change** — what the user or authorized workflow has actually permitted.

During Foundation, do not autonomously delete canonical user knowledge. Unless the requested task clearly authorizes it, do not rename or move canonical notes, change schemas or architectural contracts, rewrite unrelated domain content, move attachments across database boundaries, apply blueprint changes to live databases, or perform destructive/breaking migrations.

Prefer the smallest preservation-oriented change that solves the actual problem. A valid existing representation should not be normalized merely because another valid representation is preferred.

For architectural changes, use the compatibility and versioning rules in the System Specification. Never silently cross a version or migration boundary.

## Repository Boundaries

Use repository locations according to their documented ownership:

- `app/Blueprints/` — framework-owned reusable bootstrap material.
- `app/Docs/` — framework documentation; potentially public.
- `app/Knowledge/` — private-by-default user-owned knowledge.
- `app/Registry/` — committed discovery/navigation infrastructure.
- `app/Scripts/` — framework tooling that implements documented contracts.

Generated runtimes, virtual environments, dependency installations, bytecode, caches, indexes, embeddings, temporary files, and build output should remain outside the durable vault/project surface.

## Working with Documentation

Documentation has intentionally separated roles:

- The **System Specification** owns universal rules.
- Each **Database.md** owns database-local semantics and conventions.
- This **AGENTS.md** owns operational behavior for agents.
- The root **README.md** owns product introduction and onboarding.
- **Scripts/README.md** owns current tooling setup, behavior, and limitations.
- **Registry.md** owns the Registry view and its usage notes.
- The **Foundation Roadmap** owns current planning/status only.
- Specialist Agent files own specialist workflows and behavior, not schema or architecture.

Do not solve a documentation gap by copying the same normative rule into multiple files. Add the rule to its authority and link or summarize from supporting documents.

## Tooling

Use [`app/Scripts/README.md`](app/Scripts/README.md) for the current CLI and validator commands. Do not invent commands, capabilities, or migration behavior that the tooling does not implement.

A passing validator result proves only the checks described by the tooling documentation. It does not currently prove database-semantic conformance, correct materialization judgment, or complete Foundation compliance.

## Agent Specialization

Database-owned specialist agents may operate independently within their documented scope. They remain subject to the System Specification and owning database contract.

Specialist Agent files should contain:

- purpose and scope;
- task interpretation rules;
- domain workflow guidance;
- research or evidence preferences where relevant;
- preservation/privacy boundaries specific to the workflow;
- delivery expectations.

They should **not** duplicate the database's semantic schema, universal filename algorithm, structural metadata contract, or other authoritative rules merely for convenience. Reference the authority instead.

Persistent agent state that materially affects architectural behavior must remain user-owned, inspectable, and documented. Provider-controlled memory or hidden prompts may be optional conveniences but must not become the only source of required meaning.

## Git Commit Messages

Use focused commit subjects:

```text
<scope>: <imperative summary>
```

Examples:

```text
docs: define structural decision framework
validate: enforce database semantic schema
cli: add canonical promotion workflow
example: add movies generalization database
```

For substantial commits, add a concise body recording important architectural decisions, migrations, safety constraints, or deliberately deferred behavior. Do not combine unrelated changes merely to reduce commit count.
