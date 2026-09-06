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

The five universal structural fields and the required common note fields `aliases`, `id`, and `tags` retain their System Specification meanings and value shapes. Every Core, Shard, and Pebble includes all eight fields; the three common fields default to blank YAML values. This database does not add an ID convention or required alias/tag vocabulary.

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

### Supported Document Purposes

The initial documentation workflows support three purposes. These are body-level purposes, not additional values of `type`, a required semantic discriminator, or a requirement to create three files for every game.

| Purpose | Representation |
|---|---|
| Game reference | A Game Core containing broad reference knowledge and applicable Game Core metadata. |
| Focused reference or guide | Ordinary content until independent materialization earns a Shard or terminal Pebble under the System Specification. Modes, systems, maps, quests, and procedural routes are possible subjects, not automatic structural levels. |
| Completionist checklist | A personal completion record, normally a direct-child Shard named with the local node name `Completionist Checklist` when requested as an independent record. A smaller record may remain a section in an existing note. |

Reference content explains the game; a completionist checklist records the user's progress. A guide's temporary execution checkboxes do not assert durable personal completion. Document purpose and checkbox meaning must be explicit in the containing note or section; tools must not classify them from filenames, indentation, or checkbox syntax alone.

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

### Document Scaffolding

New documentation defaults to a compact, game-specific heading skeleton with a brief scope statement and valid structural metadata when canonical. Deliberately unfinished headings are permitted; use precise `TODO-DOC` markers to identify missing information, with one marker covering a group when its scope is clear. Headings do not require separate notes. Granular reference content and objective catalogs may be supplied by the user or developed when requested. A scaffold is not evidence of documentation or gameplay completeness, and this authoring default does not require removing existing content or restructuring valid notes.

Empty-note creation is a narrower authoring operation: the starter Game template provides required YAML and only the game's title as an H1. Body development remains a separate user-directed step; no scope statement, additional headings, or prose is inserted by the initial CLI.

### Completion Records

The following is the Games completion-record convention for newly authored checklists that explicitly adopt it in their scope or conventions section. It is optional for a valid Games database. Existing records retain their documented meanings; applying this convention to an existing record requires a deliberate, preservation-oriented transition. It does not introduce YAML fields or change structural `status` or semantic `play_state`.

#### Scope and Completeness

- A completion-bearing objective is a finite gameplay accomplishment included in the record's stated personal completion scope. State relevant game edition, platform differences, expansions, content snapshot, and exclusions where they affect that scope.
- Equivalent shared objectives have one authoritative progress record. Distinct modes, difficulties, characters, or other independent completion axes remain separate when the game and the user's scope distinguish them.
- Research establishes possible objectives, never personal completion. Research-only entries start unchecked with an empty timestamp.
- Containers group objectives without checkboxes or timestamps. Indentation is grouping, not structural lineage or proof of completion.
- `> **TODO-DOC:** [Specific gap or unresolved scope decision].` marks incomplete documentation, not a gameplay objective. A gap within tracked scope prevents a claim of authoritative completeness for that scope.
- Documented-scope completion means all currently documented in-scope objectives are checked. Authoritative 100% completion additionally requires a verified objective set for the stated scope and no unresolved documentation gaps within it. Removing markers alone does not establish completeness. Do not infer 100% from an empty or unverified objective set.
- New post-launch, seasonal, or expansion objectives enter personal scope only through a deliberate scope update. Research does not silently redefine an existing completion record.

#### Completion State and Timestamps

Use ordinary Markdown task items for completion-bearing objectives:

```markdown
- [ ] Objective `[Timestamp: ]`
- [x] Objective `[Timestamp: 2026-01-02T15:04:05+00:00]`
- [x] Objective `[Timestamp: Unknown]`
```

`Timestamp` means when the objective was completed, not when the note was created, researched, imported, or edited. A known timestamp uses `YYYY-MM-DDTHH:MM:SS±HH:MM` with an explicit UTC offset. `Unknown` preserves confirmed completion whose original time is unavailable; it does not mean incomplete. Never fabricate missing date, time, or timezone precision. Preserve any supplied partial time information in ordinary prose alongside `Unknown` until the full completion time is established.

A checked objective with an empty timestamp or an unchecked objective with a non-empty timestamp is an integrity warning. Preserve both values and report the inconsistency; do not silently repair it. Changes to existing progress and timestamps require the user's authorized update or reconciliation.

#### Dependencies and Summaries

A completion dependency applies only when explicitly documented for that game and record. State the affected objectives, direction of implication, conditions, and timestamp behavior, including unknown or missing timestamps. A terminal milestone does not imply independent progression axes. A task item that merely aggregates other objectives is a rollup and is excluded from objective totals, even if nested among them.

Optional completion summaries are explicitly labeled rollups over a stated scope, never additional gameplay objectives. A rollup can be complete only when every objective in that scope is complete and that scope's documentation is complete. Prefer derived summaries without stored checkboxes; if stored summary checkboxes are used, update them only during authorized reconciliation. Their timestamp records the completion that made the scope complete; use `Unknown` when that event's time cannot be established, and preserve/report inconsistent existing timestamps. Do not use the reconciliation time or guess a triggering event from an incomplete history.

Game-specific completion criteria and dependencies are explicit record content governed by these conventions, not new database-wide rules. If a recurring interpretation or automated behavior needs a shared field or note-kind contract, extend this `Database.md` deliberately before relying on it.

#### Execution Aids and Other Personal Records

A reference guide may contain a clearly labeled temporary run checklist with checkboxes and no completion timestamps. These boxes track actions during a run and never enter completionist totals or automatically update personal history. Personal bests, loadouts, recommendations, and annotations remain distinct from completion-bearing objectives unless the record explicitly defines a finite objective around them; do not infer completion from them.

## Resources

### Views

`Views/` is part of the database boundary. No View is required by this initial contract. Starter Views may be added after this contract is accepted when they provide concrete navigation or querying value over the documented schema. Views remain non-authoritative projections over canonical source data.

### Attachments

`Data/Game/Attachments/` is the root attachment home for the Game collection. A valid Game Core workspace may also contain its own `Attachments/` directory. Attachments remain database-owned resources and may be referenced by canonical notes anywhere in the Games database regardless of which permitted attachment home contains them.

### Templates

The blueprint supplies [Templates/Game.md](Templates/Game.md), an optional starter resource for a draft Game Core. It includes all eight required note fields, `pool: Games`, `status: draft`, an empty parent, and blank `aliases`, `id`, and `tags`. Optional semantic facts are omitted until known. A valid Games database still does not require a template.

The CLI selects `Templates/Game.md`, `Templates/Game Shard.md`, or `Templates/Game Pebble.md` according to the requested type. These are Inbox draft resources: the supporting templates leave `core` and `parent_note` blank, and no existing ancestors are required to create a capture. Game Core semantic fields still do not apply to canonical supporting notes; draft creation postpones conformance checks until promotion.

The CLI uses the template from an identified live Games database when available, otherwise the instance's Games blueprint. A missing selected live template is reported rather than copied or synchronized. Database manifests are used for template-owner lookup only, not validated as an Inbox creation gate. Existing databases and notes are never modified by this operation.

In the Core starter, `[[{{stem}}]]` means a provisional self-link based on the entered title. `{{title}}` illustrates the H1. Supporting starters provide blank lineage fields for review; legacy unresolved Core/parent placeholders are also rendered blank without resolving ancestors. The optional alias prompt supplies a one-item `aliases` list, or leaves the template default when skipped. The CLI includes all eight fields and preserves other unverified template defaults without applying a semantic schema. It always generates only the title H1, ignores template body prose, and executes no template code.

These creation conventions do not relax canonical Games rules. At promotion, complete structural metadata and lineage, apply bounded filenames and valid placement, and establish conformance to this contract and the System Specification. No automatic validation is triggered by a filesystem move; the current validator is a separate read-only command.

### Agents

The Games blueprint ships [Vera](Agents/Vera.md), an optional specialist Agent resource for Game Core references, focused references and guides, and completionist checklists. Vera operationalizes this contract; it does not define additional schema or architectural authority. A valid Games database does not require Vera or any AI assistance.

The shipped definition is framework-owned bootstrap material. When materialized into a new database's `Agents/` directory, that copy becomes user-owned and portable with the database. Later blueprint edits do not update the live copy or its contract; adopting them requires an explicit preservation-oriented migration. ShardBase stores the resource but does not execute Vera, connect to an AI provider, or transmit database content. Any external use is a separate workflow deliberately controlled by the user.

### Scripts

No Games-specific script is required by the initial contract. Framework validation and future canonical creation tooling should consume this documented contract rather than introduce hidden Games semantics.
