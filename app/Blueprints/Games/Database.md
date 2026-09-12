---
manifest_version: 1
database_id: games
database_name: Games
data_collections:
  - Game
database_status: active
---

# Games Database

## Purpose

The Games database owns the user's durable knowledge about games across physical and digital forms and game-specific subjects best understood in the context of a particular game. It supports long-term reference, play-related notes, discovery, querying, and growth without attempting to model an exhaustive games-industry ontology.

This file defines **Games-specific meaning only**. Universal ShardBase structure, metadata, lineage, placement, filename, lifecycle, attachment, safety, and validation rules come from the [System Specification](../../Docs/Shard%20System%20Specification.md).

## Scope

### Includes

- Video games, board games, card games, tabletop role-playing games, miniatures games, and other games the user wants to track, study, remember, reference, or develop knowledge about.
- Game-specific knowledge whose canonical meaning depends on a particular game, including rules, setup, components, mechanics, systems, scenarios, quests, characters, locations, strategies, builds, lore, session/progression notes, and similar subjects when they earn independent representation.
- Personal play-state information and other Games semantic metadata defined below.
- Semantic relationships from games to designers, developers, publishers, platforms, genres, and series.

### Excludes

- General-purpose canonical knowledge about people, companies, organizations, hardware platforms, storefronts, or other entities whose meaning is independent of a particular game. These may be referenced by name here but should be canonically owned elsewhere when a suitable database exists.
- General games-industry news, business analysis, or market information not primarily about a particular game.
- A universal category, franchise, series, platform, designer, developer, publisher, character, or genre ontology.
- Duplicate authoritative copies of knowledge canonically owned by another database.

## Architecture

### Data Collection — `Game`

`Game` is the initial and primary collection. Its root Cores are independently meaningful games.

The database intentionally begins with one collection. Additional collections require a demonstrated ownership, querying, navigation, lifecycle, or portability need and an explicit update to this contract.

Game lineages use universal flat/Core-workspace placement rules from the System Specification. Workspace placement never defines lineage.

### Pool Vocabulary

The canonical Pool vocabulary contains one value:

- `Games`

Every Game Core and structural descendant uses `pool: Games`.

Do not create Pools for genres, platforms, play state, franchises, or other domain classifications. Those concepts remain semantic unless a future database-contract change demonstrates a true broad lineage-grouping need.

### Core Strategy

One independently meaningful game normally owns one Core.

A game is a Core when it has stable identity and is useful to manage, query, navigate, link to, or grow as the root of its own lineage. It may remain a single Markdown file indefinitely.

Expansions, DLC, editions, remasters, ports, adaptations, rules revisions, seasons, campaigns, and similar related releases do not automatically become separate Cores. Give them independent canonical representation only when distinct identity plus independent growth, querying, navigation, reference, lifecycle, or another concrete need justifies it.

Categories, series, franchises, designers, developers, publishers, platforms, genres, characters, locations, quests, mechanics, and similar relationships are semantic. They do not create structural ancestry.

Supporting knowledge should remain ordinary Markdown inside the Game Core until a separate Shard or Pebble earns materialization under the System Specification.

## Schema

Universal structural/common note fields keep the meanings and shapes defined by the System Specification and are not repeated here. Games adds the following semantic fields.

Unless stated otherwise, these fields apply to Game Cores only and are optional. Omission means the database does not currently assert that fact.

### `game_categories`

- **Meaning:** broad physical or digital forms in which the game is represented.
- **Applies to:** Game Cores.
- **Required:** no.
- **Shape:** YAML list of one or more unique, non-empty strings when populated.
- **Vocabulary:** open; use lowercase `snake_case`.
- **Examples:** `video_game`, `board_game`, `card_game`, `tabletop_roleplaying_game`, `miniatures_game`.
- **Semantics:** values may overlap and list order has no precedence. Categories do not define collection placement, Pool membership, lineage, or canonical identity.

`game_categories` describes broad game form rather than genre. Multiple categories still describe one Game Core unless the underlying implementations have distinct identities that independently earn separate representation.

### `release_date`

- **Meaning:** original first public release date when the user chooses to record it.
- **Applies to:** Game Cores.
- **Required:** no.
- **Shape:** ISO date `YYYY-MM-DD`.
- **Constraint:** omit when a sufficiently precise date is not known rather than inventing a placeholder or mixing partial date formats.

### `developers`

- **Meaning:** developer names associated with the game.
- **Applies to:** Game Cores where development attribution is meaningful.
- **Required:** no.
- **Shape:** YAML list of non-empty strings.
- **Ownership:** values identify relationships; they do not make Games the canonical owner of developer entities.

### `designers`

- **Meaning:** game designer names associated with the game.
- **Applies to:** Game Cores where design attribution is meaningful.
- **Required:** no.
- **Shape:** YAML list of non-empty strings.
- **Ownership:** values identify relationships; they do not make Games the canonical owner of designer entities.

### `publishers`

- **Meaning:** publisher names associated with the game.
- **Applies to:** Game Cores.
- **Required:** no.
- **Shape:** YAML list of non-empty strings.
- **Ownership:** values identify relationships; they do not make Games the canonical owner of publisher entities.

### `platforms`

- **Meaning:** hardware or software platforms on which a digital game is available or relevant to the user's record.
- **Applies to:** Game Cores with a relevant digital implementation.
- **Required:** no.
- **Shape:** YAML list of non-empty strings.
- **Semantics:** platform values are semantic classifications, not structural ownership or lineage.

### `genres`

- **Meaning:** useful genre classifications for the game.
- **Applies to:** Game Cores.
- **Required:** no.
- **Shape:** YAML list of non-empty strings.
- **Vocabulary:** open until recurring query/validation needs justify a bounded vocabulary in this contract.

### `series`

- **Meaning:** series or franchise names useful for relating games.
- **Applies to:** Game Cores.
- **Required:** no.
- **Shape:** YAML list of non-empty strings.
- **Semantics:** series membership is semantic and never creates a structural parent, Core, or data collection.

### `play_state`

- **Meaning:** the user's current high-level play relationship to the game.
- **Applies to:** Game Cores.
- **Required:** no.
- **Shape:** scalar string.
- **Allowed values:**
  - `not_started`
  - `playing`
  - `paused`
  - `completed`
  - `stopped`

Omit `play_state` when these values do not meaningfully describe the user's relationship. Do not repurpose them for session state, repeatable play, or other incompatible concepts. `play_state` is unrelated to universal structural `status`.

### Semantic Note Kinds

Games currently defines no additional semantic note-kind field. Structural role remains the universal `type` field.

Add a domain-specific note-kind system only if real use shows that deterministic creation, interpretation, querying, or validation needs a bounded Games classification that cannot be represented adequately through existing semantics and ordinary Markdown.

### Supported Document Purposes

These are body-level purposes, not values of `type` and not a requirement to create multiple files per game.

| Purpose | Representation |
|---|---|
| Game reference | Game Core containing broad reference knowledge and applicable Core metadata |
| Focused reference or guide | Ordinary content until it earns a Shard or terminal Pebble under universal materialization rules |
| Completionist checklist | Personal completion record; when independently materialized, normally a direct-child Shard named `Completionist Checklist` |

A reference explains a game. A completionist checklist records the user's progress. Temporary guide checkboxes do not assert durable personal completion. The containing note or section must make checkbox purpose explicit.

## Conventions

### Identity and Naming

- A Game Core H1 uses the canonical human-facing game title. The filename uses the universal portable filename derivation.
- Do not duplicate the game title into semantic YAML merely for convenience.
- If distinct games would otherwise share a canonical name, add the shortest stable human-meaningful qualifier that distinguishes identity. Prefer category when sufficient, otherwise edition, year, platform, publisher, or another stable discriminator.
- Multiple `game_categories` values do not create duplicate Cores.
- Metadata, folders, or separate workspaces do not resolve identity/filename collisions.

### Structure

- Prefer ordinary headings inside the Game Core when a separate file provides no independent value.
- Do not materialize every rule, component, scenario, quest, character, location, mechanic, item, build, achievement, chapter, or lore topic.
- Domain relationships remain semantic rather than structural ancestry.
- Supporting structural notes stay inside the same Game lineage and inherit its `pool: Games` under the universal contract.
- Keep a lineage flat unless a specific Game Core earns a workspace for concrete organizational reasons.

### Semantic Data

- Missing optional semantic metadata is valid. Do not manufacture values for visual completeness.
- When a scalar/list field would make a richer domain fact misleading, preserve the richer fact in Markdown. If the need recurs, extend this schema deliberately.
- Prefer one authoritative representation for a fact. Do not maintain competing prose and metadata values that are both treated as canonical.

### Document Scaffolding

New documentation may begin as a compact game-specific skeleton with a brief scope statement and purposeful headings. Deliberately unfinished headings are allowed.

Use:

```markdown
> **TODO-DOC:** [Specific missing information or unresolved scope decision].
```

One marker may cover a clearly scoped group. A scaffold is not evidence of researched completeness, and headings never imply separate structural notes.

The starter draft templates are narrower: they create universal YAML plus only the title H1. Body development remains separate.

### Completion Records

The following convention applies to newly authored Games completion records that explicitly adopt it. It is optional for a valid Games database. Existing records retain their documented meanings until deliberately migrated.

#### Scope and Completeness

- A completion-bearing objective is a finite gameplay accomplishment included in the record's stated personal scope.
- State edition/platform differences, expansions, content snapshot, and exclusions where they affect scope.
- Equivalent shared objectives have one authoritative progress record. Distinct modes, difficulties, characters, or other independent completion axes remain separate when the game/user scope distinguishes them.
- Research establishes possible objectives, never personal completion. Research-only objectives begin unchecked with an empty timestamp.
- Containers group objectives without checkboxes/timestamps. Indentation is grouping, not structural lineage.
- `TODO-DOC` marks incomplete documentation, not a gameplay objective.
- **Documented-scope completion** means every currently documented in-scope objective is checked.
- **Authoritative 100% completion** additionally requires a verified complete objective set for the stated scope and no unresolved in-scope documentation gaps.
- Post-launch, seasonal, expansion, or other new objectives enter personal scope only through deliberate scope change.

#### Completion State and Timestamps

Use ordinary Markdown task items:

```markdown
- [ ] Objective `[Timestamp: ]`
- [x] Objective `[Timestamp: 2026-01-02T15:04:05+00:00]`
- [x] Objective `[Timestamp: Unknown]`
```

`Timestamp` means the time the objective was completed, not note creation, research, import, or edit time.

A known timestamp uses `YYYY-MM-DDTHH:MM:SS±HH:MM` with an explicit UTC offset. `Unknown` preserves confirmed completion whose original time is unavailable. Never fabricate date/time/timezone precision. Preserve known partial timing information in prose when useful.

A checked objective with an empty timestamp, or an unchecked objective with a populated timestamp, is an integrity warning. Preserve the existing values and report the inconsistency; do not silently repair it.

#### Dependencies and Rollups

A completion dependency applies only when explicitly documented for that game/record. Record affected objectives, direction of implication, conditions, and timestamp behavior.

A terminal milestone does not imply independent progression axes.

A task item that only aggregates other objectives is a **rollup**, not an additional gameplay objective. Optional summaries must state their scope and remain non-authoritative over the underlying objectives.

A rollup is complete only when every objective in its scope is complete and the scope's documentation is complete. If a stored rollup timestamp cannot be established, use `Unknown`; do not substitute reconciliation time.

#### Execution Aids and Other Personal Records

A reference guide may contain a clearly labeled temporary execution checklist with no completion timestamps. Those checkboxes track actions during a run and never enter completionist totals or personal history.

Personal bests, loadouts, recommendations, and annotations remain distinct from completion-bearing objectives unless the record explicitly defines a finite objective around them.

## Resources

### Views

`Views/` belongs to the Games database boundary. No View is required by the initial contract. Views remain non-authoritative projections over canonical source data.

### Attachments

Games uses the universal attachment model. The collection root is `Data/Game/Attachments/`; a valid Game Core workspace may also contain `Attachments/`. Attachment ownership remains database-level.

### Templates

The blueprint supplies:

- [`Templates/Game.md`](Templates/Game.md)
- [`Templates/Game Shard.md`](Templates/Game%20Shard.md)
- [`Templates/Game Pebble.md`](Templates/Game%20Pebble.md)

These are optional Inbox draft resources. They provide starting YAML and a title H1 but do not define canonical validity. Supporting templates intentionally leave unresolved lineage blank for later classification/promotion.

The current CLI may use a live Games database's matching template or fall back to the blueprint according to the behavior documented in [`../../Scripts/README.md`](../../Scripts/README.md). Template selection never synchronizes or modifies a live database.

### Agents

The blueprint ships [`Agents/Vera.md`](Agents/Vera.md), an optional Games specialist Agent resource. Vera contains Games-specific workflow guidance but does not define schema or architecture; this `Database.md` remains the Games authority.

Once materialized into a live database, the Vera copy becomes user-owned and travels with that database. Later blueprint edits do not silently update it.

ShardBase stores/manages the Agent resource but does not execute Vera, connect to an AI provider, or transmit database content. External use is a separate user-controlled workflow.

### Scripts

No Games-specific script is required. Framework tooling should consume this `Database.md` as the authoritative Games semantic contract rather than hard-code Games semantics as hidden framework behavior.
