# ADR 0001 — Stable Note IDs and Local-Title Supporting Filenames

Status: Accepted

Date: 2026-09-19

Specification boundary: `foundation-3`

## Context

Before `foundation-3`, canonical Shard and Pebble filenames repeated Core and immediate-parent names to provide bounded structural context. That representation was readable in isolation, but it duplicated lineage already expressed authoritatively by `core` and `parent_note` metadata.

The duplication created avoidable costs as databases grew:

- reparenting a note could require a filename change even when the note's own identity and title had not changed;
- supporting filenames became visually repetitive inside Core workspaces and other already-contextualized folders;
- similarly named local subjects depended on ancestry text for filesystem disambiguation;
- filenames mixed human-facing labels with structural encoding, making identity less stable across reorganizations.

ShardBase also needs canonical filenames to remain understandable to people rather than becoming opaque machine keys.

## Decision

`foundation-3` adopts two complementary rules:

1. Core filenames remain title-based: `Portable Core Name.md`.
2. Shard and Pebble filenames become `Portable Local Title - Opaque ID.md`.

Every canonical structural note receives one stable database-unique 10-character lowercase Crockford Base32 `id`. The ID is opaque: it carries no structural type, parentage, date, sequence, database identity, or other semantic meaning.

The note ID is assigned when canonical state is materialized and remains unchanged across title changes, moves, structural-type changes, and reparenting. A supporting note's filename uses its local H1 plus that ID. Structural ancestry remains authoritative only through `core` and `parent_note`.

Pre-structural Inbox drafts may keep a blank `id`; assigning and validating the canonical ID is part of promotion/materialization rather than capture.

The System Specification is the normative authority for the exact ID format, portable normalization algorithm, filename construction, migration requirements, and validation contract. This ADR records rationale and tradeoffs only.

## Consequences

Benefits:

- folders remain substantially cleaner as a lineage grows;
- filenames stay recognizable to people while carrying a stable machine-friendly discriminator;
- reparenting no longer creates filename churn solely because ancestry changed;
- multiple supporting notes may share the same local title without relying on encoded ancestry;
- tools can validate a small universal ID format without interpreting domain semantics.

Costs and constraints:

- `foundation-3` is a breaking migration for existing supporting filenames and for canonical notes with blank, invalid, or colliding IDs;
- title changes still require renaming the human-readable filename component and updating filename-based wikilinks;
- IDs must be generated and collision-checked before canonical writes;
- IDs do not replace `core` or `parent_note`, and structural links do not resolve by alias or ID alone.

## Alternatives Considered

### Keep ancestry-derived filenames

Rejected because it preserves duplicate structural context and makes reparenting unnecessarily rename files.

### Use ID-only filenames

Rejected because canonical Markdown should remain understandable and navigable without specialized tooling.

### Encode type or ancestry in the ID

Rejected because semantic IDs would become unstable when structure changes and would duplicate metadata.

### Use sequential IDs

Rejected because sequence conveys incidental ordering, is harder to allocate safely across independent workflows, and is less anonymous than a random opaque token.

## Migration

Existing canonical state must use the preservation-oriented `foundation-3` migration defined in Section 15.3 of the System Specification. In particular, IDs are assigned or reconciled before supporting filenames and dependent links are renamed as one coordinated migration.
