# ADR 0002 — Direct Canonical Database Creation and Core Workspace Creation Defaults

Status: Accepted

Date: 2026-09-28

Specification boundary: `foundation-4`; foundation-3 naming retained

## Context

Mandatory Inbox staging made deliberate database creation produce a provisional file and a manual move target. Users had already selected ownership but still needed to complete a filesystem operation outside the CLI's validation boundary. Supporting creation could also leave lineage unresolved.

Core workspaces provide a predictable location for a subject and its future supporting notes. Existing flat lineages remain useful and valid; changing a creation default does not justify moving user knowledge.

## Decision

Database intent creates directly in a selected live database after resolving identity, collection, Pool, Core, immediate parent, filename, and destination. Inbox intent remains pre-structural capture. Blueprint-only identities require explicit materialization before canonical creation.

New CLI-created Cores prefer workspaces. An optional manifest creation preference allows `workspace` or `flat`, with workspace as the omitted default. The Games blueprint declares its preference explicitly; framework creation contains no Games-specific placement branch.

Supporting notes resolve their root Core and immediate Core/Shard parent through canonical YAML. Pool, collection, and location inherit from that Core. Parent choices are limited to eligible members of its lineage. Filesystem siblings can have different structural depths; directories never establish ancestry.

Existing flat lineages stay flat. Existing workspaces remain bundled. Historical prepared Inbox files are left unchanged. Explicit workspace refactoring and draft promotion are separate operations.

The [System Specification](../Shard%20System%20Specification.md) owns the exact manifest, placement, lifecycle, and safety requirements. [CLI documentation](../../Scripts/README.md#note-creation) describes implemented behavior and validation limits.

## Safety and Validation

Direct writes replace the old manual boundary with preflight validation of existing structure, complete supporting lineage, collision checks, exclusive creation, and post-write validation. Caught failure or interruption rolls back only the command's new file and its new workspace when empty. Preexisting directories, notes, and competing content must survive.

Creation retains the documented stable-filesystem assumption. It is not a crash-safe transaction. Database-semantic validation and materialization judgment remain outside the deterministic checks and require review.

## Compatibility

Section 14.2 requires a specification increment for this universal extension, so the current specification becomes `foundation-4`. The optional addition retains `manifest_version: 1`. Foundation-3 IDs, filenames, lineage semantics, and valid flat/workspace state remain conformant without migration.

CLI scripts using database intent must expect a canonical destination and supply a live database and complete supporting lineage. Parent-only selection remains supported; unresolved parents and blueprint write targets are refused. Inbox capture stays compatible.

Backup format v1 is unchanged. Explicit compatibility permits unchanged foundation-3 to foundation-4 transfer and same-version transfers. Downgrades and unknown transitions remain refused; backup compatibility is not schema migration or semantic certification.

## Alternatives Considered

- Retain mandatory staging: leaves intended database creation incomplete and its final write outside automatic validation.
- Hard-code Games workspaces: makes a universal organizational preference domain-specific and prevents independent database choice.
- Bundle existing flat lineages on new child creation: introduces an unrelated, potentially disruptive refactor.
- Infer ancestry from directory nesting: duplicates and conflicts with authoritative YAML lineage.
