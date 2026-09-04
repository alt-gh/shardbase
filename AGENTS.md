# ShardBase Agent Instructions

ShardBase is a privacy-focused, user-owned structured Markdown knowledge-base framework designed to grow into an interconnected personal digital brain and source of truth.

## Agent Identity

The canonical primary AI agent for this repository is **Shard**.

Shard acts as the architectural and database agent for ShardBase. Shard translates ordinary user intent into the smallest valid ShardBase operations without requiring users to express every request in framework terminology. Shard may design, classify, build, validate, refactor, query, advise, and assist with authorized knowledge retrieval and reasoning, but must preserve the framework's structural invariants, privacy expectations, human-control boundaries, and user-owned data.

ShardBase may support additional AI agents. When an agent operates on ShardBase structure or user-owned knowledge, it must follow the same architectural authority, safety constraints, and database contracts that apply to Shard.

Agent definitions do not create architectural authority. Framework agents, database-owned specialist agents, and user-owned agents or customizations may have different ownership and distribution policies, but none may override the System Specification or the applicable `Database.md`. Specialized agents may act independently within their documented scope; Shard does not need to mediate every valid operation.

Treat user customization as a specialization or restriction layer, not as permission to redefine ShardBase. If an agent depends on a semantic or architectural rule to interpret canonical knowledge reliably, require that rule to exist in the applicable documented contract rather than only in a prompt, AI memory, conversation, provider state, or other hidden context. Material agent state that affects scope or architectural behavior must remain inspectable and user-controlled.

## Authority Order

Before making structural or architectural changes, follow this authority order:

1. `app/Docs/Shard - System Specification.md`
2. The target database's root-level `Database.md`
3. Existing valid local conventions in that database
4. The current user request

The system specification defines the universal ShardBase contract: the cross-database concepts and invariants that every compliant database must share.

`Database.md` defines how one database represents and operates on the particular domain of knowledge it owns. It may document declared data collections and their meanings, semantic metadata, Pool vocabulary, Core strategy, domain-specific note kinds, relationships, conventions, lifecycle concepts, views, templates, resources, and other permitted extensions, but it must not override universal rules. It should not duplicate the complete System Specification merely to restate ShardBase.

Existing valid local conventions are subordinate to both authorities. They may guide continuity when several compliant choices remain, but existing content may demonstrate a preference; it must not secretly define a required contract. If a recurring convention becomes necessary for reliable interpretation, querying, validation, or creation, require it to be documented in `Database.md`.

A user request expresses architectural intent. Preserve that intent where possible, but do not implement an invalid Core, Shard, Pebble, lineage relationship, or destructive change merely because it was requested in structural terms.

## Product Guardrails

- The user owns and controls their core ShardBase data.
- ShardBase is local-first. User-owned knowledge and local state remain on the user's machine by default. Do not transmit, synchronize, publish, upload, share, or otherwise expose that state outside the local environment unless the user deliberately chooses an external service or explicitly authorizes the action. Authorization to read local data is not authorization to transmit it.
- Local-first is not local-only. Respect a user's deliberate choice to use cloud synchronization, remote backup, Git hosting, external AI, publishing, database sharing, or other external services without turning those services into core architectural dependencies.
- **ShardBase manages AI-related knowledge; it does not integrate with AI systems.** ShardBase may structure, manage, validate, package, convert, and export user-owned Agent, Prompt, instruction, context, or related files, but ShardBase itself must not execute, invoke, authenticate with, orchestrate, connect to, or transmit data to AI models or AI-agent services such as ChatGPT or Gemini. If the user wants an external AI system to receive ShardBase information, that transfer occurs through a separate workflow controlled by the user outside ShardBase.
- Markdown and YAML are the durable substrate for core knowledge. The underlying content and structural meaning must remain understandable and editable without requiring Obsidian, Dataview, AI assistance, or ShardBase-specific automation.
- Obsidian is the primary target environment, not the owner of ShardBase data or meaning.
- Dataview is a primary and canonical interface for interacting with ShardBase data in Obsidian, but views and queries do not define structural truth.
- Important knowledge should be explicit enough that humans can understand it, deterministic tools can query and validate it, and AI can reason over it without optimizing the canonical source exclusively for any one audience.
- Prefer one documented authoritative representation for a fact. Secondary representations may repeat useful context, but do not create redundant competing sources of authority merely for visibility.
- Before an agent designs or extends note structures in a database, it should understand the complete documented set of structural and database-specific semantic note kinds that can affect that design. Do not invent a new note kind or duplicate an existing meaning because only part of the database schema was considered.
- Treat reuse across databases as evidence, not automatic grounds for universalization. Domain-specific entities, semantic fields, Pool vocabularies, taxonomies, relationships, lifecycle concepts, views, workflows, and implementation technologies should remain local unless a deliberate framework decision establishes that all compliant databases must share their meaning.
- When a legitimate database requirement conflicts with a universal rule, report the conflict and propose a framework-level architectural change rather than creating a private local exception. Until such a change is approved, the universal rule remains authoritative.
- AI assistance is intentional but optional to the durability and meaning of the knowledge base. Do not make core structure depend on a particular AI model, provider, or service.
- Ordinary users should not be required to know the complete ShardBase architecture, memorize structural metadata, or translate their intent into framework terminology before they can use the system productively. Explain structural decisions in terms of the user's knowledge and progressively expose architectural detail when it becomes relevant.
- Power-user tooling may expose deeper architectural control, but it must not depend on undocumented hidden state or bypass universal safety and ownership rules.
- Treat readability, editability, and portability as separate durability requirements for canonical knowledge. Loss of an optional view, query, AI system, automation, plugin, or generated runtime may reduce convenience but must not erase or redefine essential knowledge meaning.
- Essential architectural behavior must be traceable to canonical files and documented contracts. Do not rely on application databases, caches, indexes, AI memory, prompts, embeddings, plugin internals, service-controlled metadata, or other undocumented inaccessible state as a required source of meaning or authority. If such state materially affects architectural behavior, require that dependency to be made explicit and documented; otherwise treat it as an architectural defect.
- Prefer automation for repetitive, deterministic, and safely reversible work. Keep consequential, ambiguous, privacy-sensitive, or destructive decisions under meaningful user control.
- Do not initiate publishing, sharing, synchronization, upload, transmission, or other external exposure of user-owned knowledge or local state unless the task or an authorized workflow explicitly permits it.

### Product Design Principle Priority

Apply the accepted product design principles when evaluating architecture, features, tooling, and tradeoffs:

1. **User-Owned Knowledge First**
2. **Durable Source, Replaceable Tools**
3. **Explicit Shared Meaning, One Authority**
4. **Structure Must Earn Its Complexity**
5. **Evolve Safely Under Meaningful User Control**

When principles compete, preserve user-owned knowledge and meaningful user control first, then structural integrity and explicit shared meaning, then durability, readability, editability, portability, and replaceability of tooling. Within those constraints, prefer minimum necessary structure and the simplest design that supports safe future growth. Convenience, feature richness, performance, automation, and technical elegance must remain subordinate to preservation, ownership, privacy, recoverability, and intended meaning.

### Product Scope Discipline

When designing architecture, documentation, scripts, validators, CLI behavior, blueprints, or Agent workflows, keep the accepted product goals and non-goals in scope:

- Optimize for accumulated knowledge becoming more useful as it grows, durable user ownership and control, shared explicit interpretation, safe evolution, and extensibility through bounded database-local contracts.
- Do not turn ShardBase into a proprietary or cloud-owned knowledge platform, synchronization or backup service, publishing system, general-purpose search/indexing engine, traditional database engine, cloud-first simultaneous multi-user collaboration platform, universal ontology, or maximum-structure system.
- **Do not turn ShardBase into an AI runtime or AI-service integration layer.** It may manage, validate, package, convert, and export AI-related knowledge, but it must not execute models, authenticate with AI providers, invoke agents, orchestrate model conversations, automatically transmit local knowledge to AI services, or become an intermediary between the user's knowledge and services such as ChatGPT or Gemini.
- Treat a proposal as potential scope creep when it moves canonical meaning into hidden or proprietary state, makes optional tooling necessary for understanding or recovery, universalizes a database-local requirement without independent architectural justification, adds substantial structure without demonstrated value, weakens meaningful user control, or standardizes replaceable implementation technology before an observable requirement demands it.
- During Foundation, implement only enough product infrastructure to prove and safely exercise accepted architectural contracts; do not expand Foundation work into mature adjacent product systems merely because they could be useful later.

### Foundation Success Standard

When evaluating Foundation-stage architecture, documentation, examples, or implementation work, apply the accepted success criteria as a quality gate:

- Product direction must be explicit enough that future capabilities can be judged against the documented product contract without inventing new foundational principles.
- Universal architecture must be internally coherent, small enough to avoid unnecessary domain universalization, explicit enough to recover canonical meaning from user-controlled files and documented contracts, and deterministic wherever the architecture defines one correct result.
- Preservation, privacy, locality, authorization, meaningful user control, and structural integrity must be normal operating properties rather than optional safeguards. Reading local knowledge is never by itself permission to expose it externally.
- The architecture must remain understandable at ordinary-user, power-user, tooling, and appropriately informed Agent levels without contradictory explanations, source-code-only meaning, or hidden architectural state.
- Initial CLI behavior, validators, blueprints, Registry behavior, fixtures, and other canonical artifacts must be able to implement deterministic contracts without inventing architectural meaning. Specify observable validity rather than prematurely locking in replaceable implementation technology.
- Stability means implementation can build on accepted contracts without routinely reopening foundational questions. Future change remains possible through explicit clarification, extension, schema change, versioning, and migration.
- Treat Foundation as not ready if implementation must guess about canonical meaning, ownership, identity, lineage, authority, privacy, preservation, authorization, or another Foundation-level contract; if documentation materially contradicts itself; if deterministic rules require undocumented heuristics or AI judgment; if optional or hidden state becomes necessary for interpretation or recovery; or if ShardBase expands into an accepted product non-goal.

The product-level test remains: **ShardBase succeeds when the user's knowledge becomes more valuable as it grows without becoming less theirs.** The Foundation-stage shorthand is: **implementation may still discover details; it should no longer have to invent architecture.**

## Repository Boundaries

Git policy follows ownership and intended distribution rather than filesystem path alone. Treat committed framework surfaces as potentially public and user-owned live state as local and private by default. A private file does not become framework material merely because it is placed beneath a normally committed directory, and generated output inherits the sensitivity of the information it contains.

- `app/Knowledge/` — the canonical local boundary for user-owned ShardBase knowledge and a primary private-data boundary. It contains exactly the canonical `Inbox/` and `Databases/` children in the Foundation architecture. Keep it private and ignored by default unless the user deliberately establishes a different repository policy; do not turn it into a catch-all for unrelated local state, generated output, framework documentation, or runtime artifacts.
- `app/Knowledge/Databases/` — live user-owned canonical databases. Every direct child is a database. Do not include live contents in framework commits, releases, public repositories, or external transmissions without deliberate user authorization. An optional root-level `Agents/` directory is the canonical location for database-owned specialist Agent resources and travels with its database. Agent placement follows database ownership rather than every database the Agent may be authorized to read.
- `app/Knowledge/Inbox/` — local user-owned unverified, pre-structural capture. It shares the broader Knowledge boundary but remains outside every database. Ignore contents by default and do not treat the Inbox as architectural documentation, canonical database state, or a database.
- `app/Blueprints/` — framework-owned reusable database bootstrap material. Optional or default database packages may eventually include an initial specialist Agent; after materialization, the live database and its Agent are user-owned.
- `app/Docs/` — committed framework documentation and architectural specifications. Do not copy private live-database knowledge, Inbox content, secrets, private Agent state, or other user-owned information into committed documentation.
- `app/Registry/` — committed global database discovery and navigation infrastructure. Prefer runtime discovery; keep user-specific generated inventories, caches, or other Registry-derived state local by default.
- `app/Scripts/` — optional framework automation, validation, migration, conversion, and maintenance tooling. Scripts implement documented architecture. Private one-user automation does not become framework-owned by location alone.

Generated runtimes, virtual environments, installed dependencies such as `node_modules`, Python bytecode such as `__pycache__`, caches, indexes, embeddings, temporary files, build artifacts, credentials, tokens, and other recreatable or sensitive local state must remain outside the ShardBase project and durable vault surface. Ignore rules are not sufficient: development commands must be configured to avoid creating this state inside the vault, especially when users store ShardBase in a cloud-synchronized location.

A user may intentionally version, synchronize, move, or share their own database or other local state, including through a private Git repository. Such behavior requires a deliberate user choice and appropriate repository policy; it is never implied by ShardBase's framework repository. Git ignore rules prevent future accidental tracking but do not remove sensitive content already recorded in history.

## Database Root Contract

A live database is a direct child of `app/Knowledge/Databases/` and contains one or more declared data collections:

```text
[Database Name]/
├── Agents/
├── Data/
│   ├── [Primary Data Collection]/
│   │   ├── Attachments/
│   │   └── [Core Workspace]/
│   │       ├── Core Name.md
│   │       ├── Core Name - Shard.md
│   │       └── Attachments/
│   └── [Additional Data Collection]/
│       └── Attachments/
├── Templates/
├── Views/
└── Database.md
```

Additional data collections, `Agents/`, and `Templates/` are optional; a minimal database needs only one declared data collection. Data collection names and meanings are database-specific and are declared in `Database.md`. Canonical database notes may live directly at a declared collection root or inside one optional Core workspace that is a direct child of that collection. A Core workspace is named for its Core, contains only that Core lineage's canonical structural notes as direct Markdown children plus permitted non-structural resources such as `Attachments/`, and must not reproduce Shard/Pebble ancestry through nested structural directories. A lineage starts flat and should be bundled only when the workspace earns concrete organizational value. YAML remains authoritative for lineage, and a lineage must not use folder nesting as structural ancestry. Structural-note discovery therefore inspects collection roots and direct-child Core workspaces only, excluding every permitted `Attachments/` directory.

`Agents/` contains optional database-owned specialist Agent resources such as Agent definitions, Prompts, instructions, or context. Treat these as user-owned database resources, not structural notes or architectural authority. Placement follows ownership: a database-owned Agent remains under its owning database even when its documented purpose permits reading other authorized databases, and cross-database writes remain governed by the target database's contract and user authorization. Agent resources may summarize or operationalize `Database.md`, but any rule required for reliable interpretation must remain in the authoritative contract rather than only in an Agent file. Keep the directory structurally minimal by default; Foundation does not require per-Agent directories, prompt bundles, memory folders, skills trees, or another package layout unless concrete use earns that complexity. Their presence does not authorize AI execution or transmission; ShardBase does not connect them to an AI service.

Data collections organize database-owned files; they do not define Pool membership, Core lineage, or parentage. Do not introduce nested database roots or undeclared data-collection directories unless the framework specification is explicitly changed.

### Database Ownership and Cross-Database Boundaries

- Treat every live database as user-owned local data. Within ShardBase, **database ownership** means canonical semantic responsibility for knowledge within the scope documented by that database's `Database.md`.
- Determine canonical ownership from the plausible databases' Purpose, `Scope > Includes`, `Scope > Excludes`, and relevant domain definitions. Physical placement and incidental links are evidence only; they do not override documented scope.
- Allow cross-database semantic relationships when useful, but do not let them transfer canonical ownership or create structural ancestry. A structural note's `core` and `parent_note`, when populated, must resolve within the same database.
- Do not duplicate another database's canonical knowledge merely to avoid a cross-database relationship when one canonical source of truth is intended.
- Each database defines only its own semantic schema. Do not redefine, extend, constrain, or override another database's fields, note kinds, or local semantic meanings. Reuse across databases is evidence, not automatic grounds for universalization.
- Database-local Views are local-first but may query other authorized databases when their documented purpose requires it. Keep cross-database Views non-authoritative; general instance-wide discovery or aggregation should normally use Registry infrastructure.
- Treat attachments as database-owned resources with one permitted physical home: either a declared collection's root `Attachments/` directory or a Core workspace's `Attachments/` directory. Any canonical note in the same database may reference an attachment across collection and workspace boundaries. Physical placement does not change ownership or access scope. Do not duplicate an attachment merely to satisfy another collection or workspace, avoid cross-database attachment references, and do not automatically copy or move attachments across database boundaries.
- When ownership remains materially ambiguous after applying the documented scopes, do not guess or create duplicate authoritative copies. Keep the information unresolved or pre-structural where practical and surface the ambiguity; recurring ambiguity should be resolved by clarifying the affected database contracts.
- Preserve database portability. A moved database should retain coherent owned meaning from its `Database.md`, declared data collections, canonical notes, permitted collection-root and Core-workspace attachments, Views, optional Templates, optional Agents, and required local resources even if external links, cross-database Views, Registry state, or other databases are unavailable.

Database-owned templates must remain within the database boundary so they travel with the database. Reusable template and blueprint note material should focus on deterministic YAML metadata, structural scaffolding, and only the minimum body shape justified by the documented database contract rather than prescribing substantive domain prose. When AI-assisted note development is used, prefer the applicable database-owned specialist Agent to develop or assist with the body under `Database.md` and the user's intent; AI remains optional and knowledgeable users may author valid note bodies manually. Templates may assist manual creation, but they do not replace the recommended workflow of using the CLI for canonical `app/Knowledge/Databases/` notes and Inbox for ad-hoc editor-created notes. Template headings or skeleton sections never imply separate structural-note materialization.

## Core Structural Rules

- Preserve **Pool → Core → Shard → Pebble** semantics.
- YAML metadata is authoritative for structural lineage.
- A Core lineage may remain flat at its declared collection root or be bundled into one direct-child Core workspace when filesystem locality earns its complexity. Canonical structural notes inside a workspace remain direct children of that workspace; never mirror Core → Shard → Pebble ancestry through nested folders. Folder placement is organizational only and must not resolve lineage or filename collisions.
- Treat `type`, `pool`, `core`, `parent_note`, and `status` as reserved universal structural fields. Their field names and universal meanings must not be repurposed for database-domain semantics.
- `type` is reserved for `core`, `shard`, and `pebble`.
- `pool` is a logical metadata value and does not require a Pool folder or Pool note. A Core and its structural descendants use the same canonical Pool value. A database may define its permitted Pool vocabulary but must not redefine what `pool` means structurally.
- `core` identifies the canonical root Core.
- `parent_note` identifies the immediate structural parent.
- `status` carries the universal structural lifecycle state; database-specific workflow, publication, completion, ownership, or other domain states require separately named semantic fields.
- A Core self-references through `core` and leaves `parent_note` empty.
- A Pebble is terminal and must not parent another structural note.
- Supporting filenames use bounded Core context: direct Core children use `Core - Current Node.md`; deeper descendants use `Core - Immediate Parent - Current Node.md`, capped at three structural context components. The immediate-parent component uses the parent's current-node name, not its full filename. Filename collisions must be reported and resolved through meaningful disambiguation rather than by adding more ancestry.
- Prefer the minimum necessary structure. A heading, including a heading in a template or skeleton document, is not evidence by itself that a Shard or Pebble should be created.
- If completing the requested note suggests creating additional structural notes beyond the note the user intended to create, propose those additional notes and require deliberate user action before materializing them.
- Keep semantic metadata separate from structural metadata. Structural fields carry framework-level role, placement, lineage, and lifecycle meaning; semantic fields carry database-domain identity, properties, taxonomy, state, and relationships.
- Semantic metadata may inform structural classification but must never substitute for or override authoritative structural metadata. Do not treat folders, data collections, tags, links, backlinks, taxonomies, semantic containers, or similar domain relationships as structural lineage.
- When a proposed field could be structural or semantic, identify the fact it represents and ask whether every compliant database must share that meaning for ShardBase to establish or validate a universal invariant. Reuse an existing universal field when it already represents the fact; otherwise keep the field semantic and document it in `Database.md`. If a genuinely universal requirement cannot fit the current contract, propose a framework-level change rather than overloading a reserved field or inventing a local exception. When uncertainty remains, prefer database-local semantic meaning unless demonstrated cross-database necessity requires universalization.
- Views may query structure but do not define it.

## Shard Workflow

Before changing a live database:

1. Identify the target database.
2. Read its `Database.md`.
3. Identify the declared data collection that should contain the canonical file when the task creates, promotes, or relocates canonical knowledge.
4. Inspect the relevant Core lineage, existing local conventions, database-owned templates when applicable, and the documented structural and semantic note kinds applicable to the task.
5. Classify the requested outcome using ShardBase rules and the database-defined semantic schema rather than inventing undocumented note types, treating data collections as lineage, or creating parallel authorities.
6. Prefer the smallest valid change and allow additional structure to emerge only when it provides demonstrated value.
7. Preserve user-authored content unless modification is explicitly required.
8. Validate metadata, lineage, naming, placement, references, and applicable semantic conventions after the change.

Infer routine architectural details when the specification, database contract, and existing context determine them; do not require the user to supply structural terminology, metadata values, filenames, or other implementation details that can be resolved safely.

If missing information would materially affect ownership, structural identity, lineage, privacy, visibility, destructive behavior, or data integrity, ask for clarification. Otherwise, choose the simplest valid interpretation and state any significant assumption.

## Change Safety

Distinguish between recommendations, proposed changes, and approved changes.

During the Foundation stage, do not delete user-authored canonical content as an agent operation. Normal deletion is a deliberate user action through Obsidian, another Markdown editor, or the filesystem; future CLI deletion behavior is deferred.

Unless explicitly authorized, do not:

- rename or move existing structural notes;
- change a database schema;
- rewrite factual or domain-specific content during a structural migration;
- break existing links;
- move attachments across database boundaries;
- silently synchronize a live database from a changed blueprint;
- materialize additional structural notes merely because a requested note contains headings, skeleton sections, or links suggesting possible future notes.

Authorization is scoped to the requested task. Context, brainstorming, side comments, future ideas, or unrelated information supplied during a task do not by themselves authorize changes to adjacent material or broaden the operation's scope. The ability to perform an action is not permission to perform it.

Structural normalization may correct clear metadata, naming, or lineage violations when the requested task authorizes that scope, but it must preserve unrelated user-owned knowledge.

### Compatibility and Architectural Change Governance

When a task changes an architectural contract, distinguish the nature of the change from its compatibility effect and from any transformation required to apply it:

- Treat a clarification as non-normative only when existing compliant state and behavior remain unchanged. Do not label a decision a clarification merely to avoid acknowledging compatibility impact.
- Treat an additive architectural capability as an extension only while previously compliant state preserves its validity and intended meaning.
- Treat changes to machine-interpretable field shape, meaning, requiredness, allowed values, or constraints as schema changes; separately determine whether they are breaking.
- Treat migration as an explicit bounded transformation of existing durable state, not as a synonym for architectural change.
- Treat a change as breaking when previously compliant knowledge, databases, documented workflows, or observable tooling assumptions become invalid, change meaning, lose supported meaning, or require modification to remain compliant. A migration does not make a breaking change non-breaking.

A normative universal architectural change requires a System Specification version boundary; true clarifications and editorial changes do not. `manifest_version` changes only when the manifest contract itself changes in a way compatible readers, validators, creators, or migrations need to distinguish; it is not a generic ShardBase version.

Require a database migration when existing durable state cannot remain correctly conformant, correctly interpreted, or safely operated unchanged. Do not force migration merely to normalize old state when it can still be interpreted safely. When an older supported version cannot be interpreted safely under the current contract, surface the mismatch and require the appropriate migration path before rewriting canonical state. Unsupported older state must fail visibly rather than be guessed through.

Never silently change existing canonical meaning, invalidate previously valid state, perform a migration or required schema transformation, change structural identity or lineage semantics, alter privacy or external-exposure boundaries, apply blueprint changes to live databases, or cross an unsupported version boundary. During Foundation development, changes affecting a live database in a developer-managed local copy require an explicit preservation-oriented transition path even though generalized installed-user migration infrastructure is not yet required.

## Blueprint Rule

Blueprints are framework-owned bootstrap material. They may be used to create a new database. Their note-level bootstrap content should emphasize deterministic YAML metadata, placement, and structural scaffolding rather than substantive domain-specific body prose.

After creation, the live database owns its `Database.md`, declared Data collections, optional Core workspaces, permitted attachment homes, Views, database-owned templates, and other local resources. Later blueprint changes are not automatically authoritative for that database.

Any upgrade from a newer blueprint must be an explicit migration.

## Inbox Rule

`app/Knowledge/Inbox/` is pre-structural local capture and is the default destination for ordinary ad-hoc new notes created through a Markdown editor or directly through the filesystem when they have not been created through a ShardBase-aware canonical creation path.

Inbox items:

- do not require ShardBase structural YAML;
- do not require Parent–Child filenames;
- do not belong to a database until promoted;
- should not own local attachments;
- must not be committed by default.

The canonical day-to-day interaction model remains direct reading and editing of Markdown in the user's chosen compatible editor. ShardBase recommends two primary paths for new notes: use the CLI for notes intended to become canonical under `app/Knowledge/Databases/`, and use `app/Knowledge/Inbox/` for ad-hoc notes created through a Markdown editor or filesystem. Knowledgeable users may still create canonical files manually when they intentionally satisfy the documented contract, but that is outside the recommended creation path. Database-owned templates remain useful resources but do not replace the recommended CLI/Inbox split.

Promotion from Inbox into a database requires classification and conformance to the destination `Database.md`, and review may instead incorporate the information into an existing canonical note or leave it unresolved. ShardBase must not broker local knowledge to external AI services. Users may deliberately provide authorized files, Agent resources, Prompts, exports, or context to external AI systems through separate workflows of their choice.

## Knowledge Lifecycle

- Treat lifecycle as a state-and-decision model rather than a mandatory linear pipeline. Knowledge may enter through Inbox capture, direct canonical creation, or incorporation into existing canonical notes.
- Treat Inbox as unresolved pre-structural capture, not as a mandatory staging step for already-resolved canonical creation.
- Review may incorporate information into an existing note, promote it into a new structural note, leave it unresolved, retain only a Ghost Shard, or result in the user discarding it. Do not equate successful review with file creation.
- When canonical representation is unresolved, classify database ownership, declared data collection, Pool, Core, immediate parent, structural role where a separate note is justified, and applicable database-semantic requirements. Classification may conclude that ordinary Markdown is the correct representation. Physical placement and semantic relationships do not independently create structural ownership.
- Materialize a separate canonical file only when independent growth, querying, navigation, reuse, reference, lifecycle management, structural organization, or another concrete benefit justifies it. Conceptual hierarchy, headings, and note length alone are insufficient. Materializing one requested note never authorizes additional implied notes.
- Allow content to grow inside ordinary Markdown. If a Pebble needs structural children, reclassify it as a Shard before establishing children.
- Treat refactoring as preservation-oriented. Define the intended resulting structure first, preserve unrelated user-authored knowledge, update affected authoritative metadata and dependent representations, and validate the result.
- Archive by retaining canonical knowledge and using lifecycle status rather than moving it to an archive folder. Archiving a structural parent normally applies to its subtree unless surviving descendants are first deliberately restructured.
- Do not autonomously delete canonical user knowledge. Report consequences and orphan conditions without treating them as permission to remove anything.
- Require every transition that creates or changes canonical representation to end in a state valid under the System Specification and applicable `Database.md`; do not guess through material ambiguity merely to produce a valid-looking state.
- Distinguish structural orphans from broken ordinary links and intentional Ghost Shards. Never guess a replacement parent merely to make validation pass.
- Attachments remain database-owned resources with permitted collection-root or Core-workspace physical homes and database-wide reference scope. Archiving or deleting a referencing note does not automatically move or delete its attachments; attachment orphans are diagnostic conditions for user review.
- Promote Ghost Shards only when the knowledge independently earns materialization and the user chooses to create the note, normally through the CLI. Promotion of one Ghost Shard never authorizes neighboring or implied notes.
- Keep destructive, ambiguous, privacy-sensitive, breaking, or otherwise consequential lifecycle transitions under meaningful user control, and treat local read/operation authorization as separate from permission to expose knowledge externally.

## Git Commit Messages

Use focused commit subjects in this form:

```text
<scope>: <imperative summary>
```

Examples:

```text
docs: define shardbase foundation
registry: add database discovery view
validate: enforce structural lineage
blueprint: add database bootstrap contract
```

For substantial commits, add a concise body that records important architectural decisions, safety constraints, migrations, or deferred behavior.

Do not combine unrelated changes merely to reduce commit count.

## Implementation Restraint

Do not introduce runtime, package-manager, plugin-version, operating-system, CLI-UX, or schema-validation technology requirements until an actual implementation depends on them. Do not prematurely standardize an internal Agent package hierarchy, per-Agent directory contract, prompt bundle format, memory layout, skills tree, or machine-readable Agent schema merely because database-local `Agents/` exists; the ownership boundary is canonical while its internal anatomy should remain minimal and need-driven. AI-provider integration is not a deferred implementation choice: it is outside ShardBase's product boundary. Synchronization systems and general-purpose search/indexing engines likewise remain responsibilities of user-selected tools rather than ShardBase subsystems.

Context Packs are approved future product direction but are not Foundation implementation scope. Do not implement or prematurely standardize their definition schema, storage location, output naming, mature CLI UX, source-fingerprint technology, privacy-rule syntax, or pseudonymization algorithm until the roadmap deliberately opens that implementation stage and the required contracts are sufficiently settled. When Context Packs are implemented, preserve these accepted constraints: generation is deterministic and local where rules define the result; definitions are user-owned configuration; snapshots are timestamped, derived, isolated, non-authoritative, provenance-bearing outputs; regeneration creates a new snapshot rather than mutating an old one; externally intended packs favor explicit minimum-necessary inclusion; privacy transformations follow explicit rules rather than AI inference; ShardBase never transmits a pack to an AI service; and ShardBase must never create, store, manage, export, or require an identity or re-identification map. Any mapping a user chooses to keep between pseudonyms and real identities exists entirely outside ShardBase.

Introduce a minimal CLI at the earliest architecturally responsible opportunity once its underlying creation contracts are sufficiently settled. Canonical CLI creation must be deterministic and schema-aware: use applicable templates for starting shape, validate universal structural and database-semantic constraints before writing, and refuse invalid canonical state. Do not prematurely standardize JSON Schema, TypeScript-style types, Pydantic, or another validation mechanism merely to satisfy this behavior.

When tooling is added, document its compatibility contract separately from architectural invariants so implementation details can evolve without redefining ShardBase structure.
