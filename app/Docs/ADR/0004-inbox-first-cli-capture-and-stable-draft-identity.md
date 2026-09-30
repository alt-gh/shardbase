# ADR 0004 — Inbox-First CLI Capture and Stable Draft Identity

Status: Accepted

Date: 2026-09-30

Specification boundary: `foundation-6`; `manifest_version: 1` retained

## Context

The CLI previously asked users to choose between provisional Inbox capture and direct canonical database creation. That made initial capture depend on database selection, templates, Pool, collection, and complete lineage decisions. The Inbox path was also coupled to Games defaults and could leave a draft without a stable ID.

Capture should remain quick and database-independent. Canonical ownership and structure require a more deliberate promotion boundary where the destination contract, semantic metadata, lineage, placement, filename, and collisions can be resolved together.

## Decision

Every note created through `shardbase create new` or `shardbase new` enters `app/Knowledge/Inbox/`. The CLI asks only for title, provisional Core/Shard/Pebble type, and optional alias. It does not select or inspect a database, template, Pool, Core, parent, collection, or canonical destination.

Each CLI capture receives the complete universal YAML key set and a stable 10-character lowercase Crockford Base32 ID immediately. `status` starts as `draft`; `pool`, `core`, and `parent_note` remain blank for every provisional type, including Core. Database-specific semantic metadata is not manufactured. Existing valid IDs in parseable nested Inbox drafts are reserved during generation, while plain or malformed Inbox Markdown does not block capture.

Direct canonical note creation is removed from the public CLI. Existing canonical preparation, placement, collision checking, validation, exclusive commit, and rollback machinery is retained as the implementation basis for a future promotion workflow. This decision does not implement `shardbase promote`.

## Compatibility and Consequences

This decision supersedes only the direct-canonical-CLI-creation portion of ADR 0002. ADR 0002's canonical workspace defaults, placement representations, lineage inheritance, and safe materialization rules remain in force. It also supersedes ADR 0001's capture-time allowance only for new CLI-created notes; arbitrary and historical Inbox files may still have blank IDs.

No existing Inbox or canonical files are moved, rewritten, or normalized. A CLI capture remains pre-structural despite its metadata: Inbox placement establishes no database ownership, its selected type is provisional, and canonical validation has not succeeded. Promotion must preserve the draft ID, recheck destination uniqueness, resolve the complete canonical contract, and fail safely on collision rather than silently changing identity.

The System Specification advances to `foundation-6`. The durable user-state layout and backup format remain unchanged, so format v2 accepts foundation-4/5/6 user state into foundation-6 without content conversion. Downgrades remain unsupported.

## Alternatives Considered

- Keep both intents: retains an early branching workflow and makes capture depend on structural decisions.
- Continue Games-aware Inbox scaffolding: leaks one database's defaults into universal pre-structural capture.
- Delay ID assignment until promotion: weakens draft identity and complicates stable references before structure is resolved.
- Implement promotion in the same change: expands scope beyond establishing a safe, consistent capture boundary.
