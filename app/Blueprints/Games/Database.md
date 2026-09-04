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

The Games database owns the user's durable knowledge about video games and game-specific subjects that are best understood in the context of a particular game. It is intended to support long-term personal reference, play-related notes, discovery, querying, and growth without requiring an exhaustive games-industry ontology.

The database should begin with the smallest useful domain contract. Additional collections, semantic fields, note kinds, Views, templates, or specialist Agent resources should be introduced only when real use demonstrates concrete value.

## Scope

### Includes

- Video games that the user wants to track, study, remember, reference, or develop knowledge about.
- Game-specific knowledge whose canonical meaning depends on a particular game, including mechanics, systems, quests, characters, locations, strategies, builds, lore, progression notes, and similar subjects when they earn independent materialization.
- Personal play-state information and other documented game-specific semantic metadata defined by this database.
- Relationships from a game to developers, publishers, platforms, genres, and series when represented by the semantic fields defined below.

### Excludes

- General-purpose canonical knowledge about people, companies, organizations, hardware platforms, storefronts, or other entities whose meaning is independent of a particular game. Those subjects may be referenced by name here but should be canonically owned by another database if a suitable database exists.
- General games-industry news, business analysis, or market information that is not primarily knowledge about a particular game.
- A universal franchise, series, platform, developer, publisher, character, or genre ontology. These concepts must not become new data collections, structural parents, or universal ShardBase concepts merely because individual games relate to them.
- Duplicate authoritative copies of knowledge canonically owned by another database. Cross-database relationships do not transfer ownership.

## Architecture

### Data Collections

#### `Game`

`Game` is the initial and primary data collection. It contains canonical structural notes whose root Core is an independently meaningful video game.

The database intentionally begins with one declared data collection. Additional collections must earn their complexity through demonstrated ownership, querying, navigation, lifecycle, or portability needs and require an explicit update to this contract before use.

Canonical Game lineages use flat placement at `Data/Game/` by default. A Game Core lineage may be bundled into one direct-child Core workspace only when concrete organizational value justifies the additional directory. Workspace placement is physical organization only and never defines lineage.

### Pools

The canonical Pool vocabulary initially contains one value:

- `Games`

Every Game Core and its structural descendants use `pool: Games`.

The single Pool is intentional. Additional Pools should not be introduced for genres, platforms, play state, franchises, or other classifications that are better represented through semantic metadata unless future use demonstrates a genuinely broad lineage-grouping need.

### Core Strategy

A Core normally represents one independently meaningful video game title.

A game should become its own Core when it has a stable identity and is useful to manage, query, navigate, link to, or grow as the root of its own knowledge lineage. A Game Core may remain a single Markdown note indefinitely.

Expansions, downloadable content, editions, remasters, ports, seasons, campaigns, and similar related releases do not automatically become separate Cores. They should remain ordinary content or semantic relationships unless independent growth, querying, navigation, reference, lifecycle management, or another concrete benefit justifies separate canonical representation.

Game series, franchises, developers, publishers, platforms, genres, characters, locations, quests, mechanics, and other concepts do not become structural ancestors merely because they group or relate to games. Structural ancestry expresses decomposition within one Game Core lineage; domain relationships remain semantic.

Supporting knowledge should remain ordinary Markdown headings or sections inside the Game Core unless a separate Shard or Pebble independently earns materialization under the universal ShardBase materialization rules.

## Schema

The universal structural fields `type`, `pool`, `core`, `parent_note`, and `status` retain their System Specification meanings and are not redefined here.

The initial Games semantic schema is deliberately small. Unless stated otherwise, these fields apply to Game Cores only and are optional. Omitted optional fields mean the database does not currently assert that fact.

### `release_date`

- Meaning: the game's original first public release date when the user chooses to record it.
- Applies to: Game Cores.
- Required: no.
- Shape: ISO calendar date in `YYYY-MM-DD` form.
- Constraint: omit the field when a sufficiently precise date is not known rather than inventing a placeholder or mixing year-only and full-date values.

### `developers`

- Meaning: developer names associated with the game.
- Applies to: Game Cores.
- Required: no.
- Shape: YAML list of non-empty strings.
- Relationship semantics: the values identify developers by name for Games-domain querying; they do not make the Games database the canonical owner of the developer entity.

### `publishers`

- Meaning: publisher names associated with the game.
- Applies to: Game Cores.
- Required: no.
- Shape: YAML list of non-empty strings.
- Relationship semantics: the values identify publishers by name for Games-domain querying; they do not make the Games database the canonical owner of the publisher entity.

### `platforms`

- Meaning: platforms on which the user wants to record that the game is available or relevant.
- Applies to: Game Cores.
- Required: no.
- Shape: YAML list of non-empty strings.
- Relationship semantics: platform names are semantic classifications for this database and are not structural ownership or lineage.

### `genres`

- Meaning: useful genre classifications for the game.
- Applies to: Game Cores.
- Required: no.
- Shape: YAML list of non-empty strings.
- Vocabulary: initially open rather than centrally enumerated. If inconsistent vocabulary becomes a recurring query or validation problem, the vocabulary should be deliberately bounded in this contract rather than inferred from existing notes.

### `series`

- Meaning: a series or franchise name that is useful for relating the game to other games.
- Applies to: Game Cores.
- Required: no.
- Shape: YAML list of non-empty strings.
- Relationship semantics: series membership is semantic. It does not make a series a structural parent, Core, or data collection.

### `play_state`

- Meaning: the user's current high-level play relationship to the game.
- Applies to: Game Cores.
- Required: no.
- Shape: one scalar string.
- Allowed values:
  - `not_started`
  - `playing`
  - `paused`
  - `completed`
  - `stopped`
- Constraint: `play_state` is a database-local semantic field and must never replace or alter universal structural `status`.

### Semantic Note Kinds

The Games database currently defines no additional semantic note-kind field. Structural role is represented only by the universal `type` field, and game-specific subject matter should normally be expressed through the note body, links, and the semantic fields above.

A new semantic note-kind system should be added only if real use shows that deterministic creation, interpretation, querying, or validation needs a bounded domain classification that cannot be represented adequately without it.

## Conventions

- A Game Core level-one heading uses the game's canonical human-facing title. Its filename uses the deterministic portable filename stem derived from that title by the System Specification; do not duplicate the title into semantic YAML merely for convenience.
- Prefer ordinary Markdown headings inside a Game Core for information that does not independently justify a structural file.
- Do not materialize every quest, character, location, mechanic, item, build, achievement, chapter, or piece of lore as a Shard or Pebble. Materialize only when the knowledge independently earns it under the System Specification.
- Domain relationships such as developer, publisher, platform, genre, series, sequel/prequel, adaptation, and shared universe are semantic relationships, not structural ancestry.
- When a scalar/list semantic field cannot represent a domain fact without becoming misleading, preserve the richer fact in Markdown rather than forcing it into the current schema. Extend the schema deliberately if the need recurs.
- Prefer one authoritative representation for a fact. Do not maintain competing metadata and prose values that are both treated as canonical merely for visibility.
- Missing optional semantic metadata is valid. Do not manufacture values solely to make notes look complete.
- Supporting structural notes inherit the root Game Core's `pool: Games` and remain within the same database and Game lineage.
- The initial database should preserve flat placement unless a specific Game lineage earns a Core workspace through concrete organizational value.

## Resources

### Views

`Views/` is part of the database boundary. No View is required by this initial contract. Starter Views may be added after this contract is accepted when they provide concrete navigation or querying value over the documented schema. Views remain non-authoritative projections over canonical source data.

### Attachments

`Data/Game/Attachments/` is the root attachment home for the Game collection. A valid Game Core workspace may also contain its own `Attachments/` directory. Attachments remain database-owned resources and may be referenced by canonical notes anywhere in the Games database regardless of which permitted attachment home contains them.

### Templates

No database-owned template is required by the initial contract. If a starter template is added later, it should provide only deterministic structural YAML, applicable semantic fields, and minimal body scaffolding justified by this contract; it must not prescribe substantive game prose or create additional structural notes from headings.

### Agents

No database-owned specialist Agent resource is required by the initial contract. If one is added later, it remains an optional user-owned database resource after materialization and cannot override the System Specification or this `Database.md`.

### Scripts

No Games-specific script is required by the initial contract. Framework validation and future canonical creation tooling should consume this documented contract rather than introduce hidden Games semantics.
