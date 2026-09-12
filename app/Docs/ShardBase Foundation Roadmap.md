# ShardBase Foundation Roadmap

document_role: Planning and status tracker; not architectural authority.
current_stage: foundation
roadmap_status: active
foundation_completion_status: incomplete
architectural_source_of_truth: app/Docs/Shard System Specification.md
database_local_authority: each live database's root Database.md
last_reconciled: 2026-09-12

This roadmap records **what remains to be done and what has been completed**. It intentionally does not restate the product thesis, universal architecture, lifecycle contract, schema rules, migration rules, or agent contract. Those belong in their authoritative documents.

Historical rationale is preserved by Git history and, once introduced, Architecture Decision Records. This file should remain a concise current-state planning surface rather than an append-only design notebook.

---

## 1. Foundation Objective

Foundation is complete when the product contract, conceptual language, universal architecture, governance model, minimum canonical implementation, and end-to-end proof are deliberately approved; Foundation-critical questions have explicit answers; safe deferrals are documented; authoritative and supporting documentation agree; and subsequent implementation no longer needs to invent foundational meaning.

Working shorthand:

> Implementation may still discover details; it should no longer have to invent architecture.

The final Foundation sign-off remains a project-owner decision. Passing automated checks is evidence, not sign-off.

---

## 2. Current State

current_assessment: late Foundation / convergence and proof
current_primary_goal: finish the vertical slice from intent to valid canonical knowledge and close remaining Foundation proof/governance gaps
current_architecture_status: substantially settled
current_implementation_status: substantial deterministic structural validation exists; draft creation exists; canonical semantic validation and canonical promotion/creation remain incomplete
current_proof_status: Games proving workflow partially complete
current_documentation_status: authority roles consolidated; duplicated architecture removed from supporting documents

### What Already Exists

- Universal System Specification at `foundation-2`.
- Private `app/Knowledge/` boundary with `Inbox/` and `Databases/`.
- Database manifest and ownership contracts.
- Pool → Core → Shard → Pebble structural model.
- Common required note fields `aliases`, `id`, and `tags` in addition to structural fields.
- Portable filename and bounded lineage naming contract.
- Flat and optional Core-workspace placement model.
- Database-local Agents, Templates, Views, and attachment boundaries.
- Games starter blueprint.
- Games draft templates: `Game.md`, `Game Shard.md`, and `Game Pebble.md`.
- Games specialist Agent resource: `Agents/Vera.md`.
- Runtime Registry discovery.
- Local draft-creation CLI.
- Read-only structural validator, tests, and sanitized fixtures.

### Main Remaining Gaps

1. Structural classification guidance is still more implicit than the desired Foundation standard; the planned Structural Decision Framework remains unfinished.
2. The architecture is not yet demonstrated through a deliberate set of good, bad, and ambiguous canonical examples.
3. Database semantic schemas are authoritative prose but are not yet machine-readable enough for deterministic generic validation.
4. The CLI cannot yet promote a draft or directly create validated canonical database state.
5. The Games proof has not yet completed query/navigation, growth/materialization, and archive lifecycle steps.
6. Governance substance exists in the System Specification, but the roadmap/decision-record surfaces have not yet been closed out and formally signed off.
7. A second independently designed domain has not yet tested generalization.

---

## 3. Milestone Status

| Milestone | Goal | Status | Remaining work |
|---|---|---|---|
| 1 — Define the Product | Establish product identity, audience, goals, non-goals, design principles, success criteria | **Complete** | None for Foundation unless new evidence exposes a contradiction |
| 2 — Define Conceptual Language | Canonical vocabulary and decision model | **In progress** | Commit 10 — Structural Decision Framework |
| 3 — Make Architecture Demonstrable | Canonical examples, walkthroughs, failure cases | **Planned** | Commits 11–15 |
| 4 — Establish Project Governance | Change/version/migration/ADR/compatibility governance | **Partially implemented** | Reconcile existing System Specification governance into concise project governance artifacts; add ADR practice |
| 5 — Create Canonical Implementation Artifacts | Blueprint, Registry, validator, fixtures | **Substantially complete** | Extend proof for semantic validation, attachment reference behavior, fragmentation judgment, and Inbox/promotion boundaries |
| 6 — Prove Entire Foundation | Real end-to-end proof and sign-off | **In progress** | Complete Games lifecycle, architecture overview/decision record as needed, post-Foundation plan, final review |

---

## 4. Commit Tracker

### Milestone 1 — Product Definition

| # | Commit | Status |
|---:|---|---|
| 1 | `docs: define shardbase product thesis` | complete |
| 2 | `docs: define target users and use cases` | complete |
| 3 | `docs: define project goals and non-goals` | complete |
| 4 | `docs: define shardbase design principles` | complete |
| 5 | `docs: define foundation success criteria` | complete |

The accepted product contract is summarized where needed by the README and normatively bounded by the System Specification. This roadmap does not duplicate the full product-definition prose.

### Milestone 2 — Conceptual Language

| # | Commit | Status |
|---:|---|---|
| 6 | `docs: add shardbase terminology glossary` | complete |
| 7 | `docs: define structural versus semantic concepts` | complete |
| 8 | `docs: define knowledge lifecycle model` | complete |
| 9 | `docs: define database ownership model` | complete |
| 10 | `docs: define structural decision framework` | **planned** |

Commit 10 should turn the already-approved classification principles into an explicit reusable decision sequence for Core vs Shard vs Pebble vs heading vs Ghost Shard, including independent lifecycle/query/navigation/reuse/growth tests and a minimum-structure tie-breaker. It must reference rather than duplicate the normative classification and materialization rules in the System Specification.

### Milestone 3 — Demonstrable Architecture

| # | Commit | Status |
|---:|---|---|
| 11 | `docs: add canonical database walkthrough` | planned |
| 12 | `docs: add structural classification examples` | planned |
| 13 | `docs: add lineage and naming examples` | planned |
| 14 | `docs: add database manifest example` | planned |
| 15 | `docs: document common architecture mistakes` | planned |

These commits should be example-driven and non-normative. They should point to the relevant authoritative rule for every example rather than restating full rules.

### Milestone 4 — Governance

| # | Commit | Status |
|---:|---|---|
| 16 | `docs: define architectural change policy` | partially represented in System Specification |
| 17 | `docs: define specification versioning policy` | partially represented in System Specification |
| 18 | `docs: define migration principles` | partially represented in System Specification |
| 19 | `docs: add architecture decision records` | planned |
| 20 | `docs: define compatibility policy` | partially represented in System Specification |

The System Specification already contains the normative change categories, `foundation-N` boundary, manifest-version distinction, migration principles, backward-compatibility expectations, and no-silent-change rules. Remaining governance work should avoid copying those sections into another competing authority. Instead, create lightweight process documentation and ADRs that **apply** the normative rules.

### Milestone 5 — Canonical Implementation Artifacts

| # | Commit | Status |
|---:|---|---|
| 21 | `blueprint: add minimal database blueprint` | complete |
| 22 | `registry: define database discovery contract` | complete |
| 23 | `validate: add database manifest validation` | complete |
| 24 | `validate: add structural metadata validation` | complete |
| 25 | `validate: add lineage integrity checks` | complete |
| 26 | `validate: add naming and placement checks` | complete |
| 27 | `validate: add markdown structure checks` | complete within stated scope |
| 28 | `test: add canonical validation fixtures` | complete for implemented structural checks; extension work remains |

Current validator scope includes manifest discovery/shape, safe path boundaries, structural/common metadata, same-database lineage, Pool consistency, archive ancestry, Core workspaces, portable filenames/collisions, and supported Markdown heading checks.

Not yet generic/deterministic: database semantic schema validation, Pool-vocabulary interpretation from database contracts, materialization/fragmentation judgment, attachment reference/orphan auditing, arbitrary database-local resources, historical specification-version migration, and canonical promotion/creation.

### Milestone 6 — Foundation Proof

| # | Commit | Status |
|---:|---|---|
| 29 | `example: add canonical shardbase database` | complete |
| 30 | `docs: document end-to-end shard workflow` | **in progress** |
| 31 | `docs: add foundation architecture overview` | evaluate after example/docs consolidation; likely concise |
| 32 | `docs: add foundation decision log` | replace with ADR practice rather than another duplicated history surface |
| 33 | `docs: define post-foundation roadmap` | planned |
| 34 | `release: complete shardbase foundation` | planned |

Commit 30 already has evidence for initial Games ownership, Pool/Core classification, materialization, and structural validation. It still needs:

- query/navigation proof;
- growth proof showing both retained-heading and materialized-note decisions;
- archive/restore behavior;
- canonical creation/promotion once tooling supports it;
- generic semantic validation evidence once implemented.

---

## 5. Starter Database Strategy

starter_database_decision: approved
starter_order:
  1. Games
  2. Movies

### Games

Games is the first starter database and primary real-use proving ground.

Current blueprint package includes:

```text
app/Blueprints/Games/
├── Agents/
│   └── Vera.md
├── Data/
│   └── Game/
│       └── Attachments/
├── Templates/
│   ├── Game.md
│   ├── Game Shard.md
│   └── Game Pebble.md
├── Views/
└── Database.md
```

The Games `Database.md` is the sole authority for Games-specific scope, Pool vocabulary, Core strategy, semantic fields, completion-record conventions, and resources. Vera and the templates consume that contract.

### Movies

Movies should be designed **after** the Games vertical slice is proven. It must be an independent second-domain design, not a renamed Games schema. Its purpose is to reveal whether proposed generic mechanisms actually generalize across domains.

Movies is not required to block every remaining Foundation task, but it should occur before ShardBase commits to broad post-Foundation generic capabilities whose design depends on database-semantic generalization.

---

## 6. Foundation Definition of Done

### Product

- purpose explicit: complete
- target users explicit: complete
- primary use cases explicit: complete
- goals/non-goals explicit: complete

### Architecture

- universal invariants documented: largely complete
- canonical vocabulary: largely complete; decision framework still needed
- database ownership: complete
- structural classification: partially complete; needs explicit decision framework/examples
- lifecycle behavior: documented; end-to-end proof incomplete
- lineage behavior: complete within Foundation contract

### Safety and Governance

- user-owned data protections: complete at architectural level
- breaking-change categories/version boundaries: documented in System Specification
- migration principles: documented in System Specification; generalized tooling incomplete
- ADR/project decision process: incomplete
- supporting governance documentation reconciled with normative authority: incomplete

### Understandability

- newcomer can understand product without source-code archaeology: improved by documentation consolidation; canonical examples still needed
- complete example database: exists as sanitized structural fixture
- good/bad/ambiguous examples: incomplete

### Implementability

- minimal blueprint: complete
- Registry discovery: complete
- deterministic universal structural validation: implemented within documented scope
- representative structural fixtures: complete within implemented scope
- deterministic database-semantic validation: incomplete
- canonical validated creation/promotion: incomplete
- attachment reference/orphan validation: incomplete
- fragmentation/materialization diagnostics: incomplete

### Stability and Proof

- Games end-to-end workflow: incomplete
- second-domain generalization test: not started
- remaining Foundation-critical questions explicitly closed or safely deferred: incomplete
- final Foundation sign-off: incomplete

---

## 7. Deferred and Out-of-Scope Work

### Explicit Product Non-Goals

- AI provider/model integration or orchestration
- ShardBase-owned sync system
- ShardBase-owned general-purpose search/indexing engine
- transactional database engine
- cloud-first collaborative platform

These are product boundaries, not backlog items.

### Deferred Until a Concrete Requirement

- mature/full CLI and interactive database wizard
- automated Inbox classification
- generalized migration engine
- schema migration framework
- Obsidian plugin
- API server or web UI
- packaging/distribution system
- large dashboard surface
- broad plugin/platform compatibility matrix
- user-local/framework-Agent filesystem standardization beyond currently required ownership rules
- attachment offloading/restoration
- universal visibility model
- performance caches/indexes

### Approved Future Capability — Context Packs

Context Packs remain post-Foundation. The accepted direction is a deterministic, local-only, provider-neutral packaging/export capability that creates inspectable non-authoritative snapshots for deliberate external use.

Do not standardize or implement their schema, generator, privacy transformations, output layout, or UX until the Foundation vertical slice and source-selection/semantic contracts they depend on are stable.

---

## 8. Final Foundation Sign-Off

foundation_product_definition_approved: no
foundation_conceptual_language_approved: no
foundation_demonstrable_architecture_approved: no
foundation_governance_approved: no
foundation_canonical_implementation_approved: no
foundation_proof_approved: no
foundation_definition_of_done_satisfied: no
foundation_ready_to_close: no

final_foundation_notes:
  - Do not close Foundation merely because documentation is shorter or structural tests pass.
  - Close only after semantic validity can participate in canonical creation/promotion and the end-to-end workflow has been proven without unresolved Foundation-level architectural invention.
