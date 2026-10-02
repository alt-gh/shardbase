# Shardbase Foundation Roadmap

document_role: Planning and status tracker; not architectural authority.
current_stage: foundation
roadmap_status: active
foundation_completion_status: incomplete
architectural_source_of_truth: app/Docs/Shard System Specification.md
database_local_authority: each live database's root Database.md
last_reconciled: 2026-10-02

This roadmap records **what remains to be done and what has been completed**. It intentionally does not restate the product thesis, universal architecture, lifecycle contract, schema rules, migration rules, or agent contract. Those belong in their authoritative documents.

Historical rationale is preserved by Git history and Architecture Decision Records. This file should remain a concise current-state planning surface rather than an append-only design notebook.

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
current_implementation_status: substantial deterministic structural validation, database scaffolding, universal Inbox-first CLI capture with stable IDs, external bootstrap/launcher setup, doctor, and guided init are implemented; canonical preparation machinery remains tested; canonical semantic validation and draft promotion remain incomplete
current_proof_status: Games proving workflow partially complete
current_documentation_status: authority roles consolidated; root README and detailed tooling guide reconciled with guided private-instance onboarding and encrypted-backup-based updates; contributor/security documentation exists; ADRs record foundation-3 naming, foundation-4 canonical preparation/placement, foundation-5 user-state ownership/transfer, and foundation-6 Inbox-first capture

### What Already Exists

- Universal System Specification at `foundation-6`, preserving foundation-3 naming, existing flat/workspace state, and manifest version 1.
- Private `app/Knowledge/` boundary with user-owned Inbox/Data/Views and managed live database packages.
- Database manifest and ownership contracts.
- Pool → Core → Shard → Pebble structural model.
- Supporting [Structural Decision Framework](Structural%20Decision%20Framework.md) with a reusable classification sequence, concrete-value considerations, and minimum-structure tie-breaker.
- Common required note fields `aliases`, `id`, and `tags` in addition to structural fields.
- Portable Core filenames plus local-title + stable opaque-ID supporting filenames; ancestry remains metadata-authoritative.
- Flat and optional Core-workspace placement model.
- Database-local Agents, Templates, Views, and attachment boundaries.
- Games starter blueprint.
- Games draft templates: `Game.md`, `Game Shard.md`, and `Game Pebble.md`.
- Games specialist Agent resource: `Agents/Vera.md`.
- Runtime Registry discovery.
- Local Inbox-first creation CLI with database-independent universal metadata, provisional structural fields, capture-time stable IDs, and preservation-oriented collision handling.
- Retained canonical preparation and commit primitives with live database/template selection, lineage inheritance, workspace defaults, structural validation, and safe rollback as the basis for future promotion.
- Blueprint-based database scaffolding with dynamic selection, external preflight validation, and no overwrite/merge behavior.
- Read-only structural validator, tests, and sanitized fixtures.
- Format-v2 encrypted user-state backup/restore with destination-package reconstruction and legacy-v1 reading.
- ZIP-first private-instance onboarding through root `bootstrap.py`, cross-platform external runtime/launcher setup, `shardbase doctor`, and guided `shardbase init`; encrypted-backup-based updates are documented in the [tooling guide](../Scripts/README.md#updating-a-private-instance).
- Top-level `tests/` separated from runtime tooling, root `pyproject.toml`, separate `requirements-dev.txt`, and Ruff lint configuration.
- Active, green [GitHub Actions CI](../../.github/workflows/ci.yml), verified for `3c9aa5054b3a30f24675e27c20b2fdec982c2e18` in [run 36933988549](https://github.com/shardbase-md/shardbase/actions/runs/36933988549): tracked private-state and generated-artifact hygiene, Ruff lint, unit tests and CLI smoke checks on Ubuntu/Python 3.10 and 3.14 and Windows/Python 3.14, plus macOS/Python 3.14 bootstrap smoke coverage. All six jobs passed, including the final hygiene enforcement.
- Weekly [Dependabot](../../.github/dependabot.yml) coverage for Python and GitHub Actions dependencies.
- [CONTRIBUTING.md](../../CONTRIBUTING.md), [SECURITY.md](../../SECURITY.md), Apache License 2.0 in [LICENSE](../../LICENSE), and existing [ADR practice](ADR/).
- Reconciled [root README](../../README.md) and [detailed tooling documentation](../Scripts/README.md).

### Main Remaining Gaps

1. The architecture is not yet demonstrated through a deliberate set of good, bad, and ambiguous canonical examples.
2. Database semantic schemas are authoritative prose but are not yet machine-readable enough for deterministic generic validation.
3. Canonical preparation has structural validation, but a user-facing promotion workflow and generic semantic validation remain unfinished.
4. The Games proof has not yet completed query/navigation, growth/materialization, and archive lifecycle steps.
5. Governance substance exists in the System Specification and supporting contributor/security documents; remaining decision-process closure and formal Foundation sign-off are incomplete.
6. A second independently designed domain has not yet tested generalization.

Repository professionalization: implementation and expanded CI verification are complete. Explicit tracked-file CI enforcement rejects private Knowledge and Obsidian state, Python bytecode/caches, local virtual environments, build/package output, and local backup archives. Administrative closure remains incomplete: GitHub reported `main` as unprotected with no repository rulesets on 2026-10-01. The connected GitHub integration lacks branch-protection administration access (HTTP 403), and the local `gh` CLI is unavailable.

The remaining closure task is to require pull-request integration and the verified checks `repository-hygiene`, `lint`, `test (ubuntu-latest, 3.10)`, `test (ubuntu-latest, 3.14)`, `test (windows-latest, 3.14)`, and `bootstrap-macos` on `main`, while blocking force pushes and deletion. The intended solo-maintainer configuration requires no reviewer approvals or up-to-date-branch gate and adds no unrelated policies. Verify the effective protection before declaring professionalization complete. This administrative task does not implement or complete any remaining Foundation milestone.

---

## 3. Milestone Status

| Milestone | Goal | Status | Remaining work |
|---|---|---|---|
| 1 — Define the Product | Establish product identity, audience, goals, non-goals, design principles, success criteria | **Complete** | None for Foundation unless new evidence exposes a contradiction |
| 2 — Define Conceptual Language | Canonical vocabulary and decision model | **Complete** | None for Foundation unless new evidence exposes a conceptual-language gap |
| 3 — Make Architecture Demonstrable | Canonical examples, walkthroughs, failure cases | **Planned** | Commits 11–15 |
| 4 — Establish Project Governance | Change/version/migration/ADR/compatibility governance | **Partially implemented** | ADR practice and contributor/security documentation exist; complete remaining decision-process closure and Foundation governance approval without duplicating the System Specification |
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
| 10 | `docs: define structural decision framework` | complete |

The [Structural Decision Framework](Structural%20Decision%20Framework.md) now provides a reusable Core/Shard/Pebble/heading/Ghost Shard decision sequence, concrete-value tests for independent growth, querying, navigation, reuse/reference, lifecycle, and structural organization, and a minimum-structure tie-breaker. Normative classification and materialization rules remain in the System Specification.

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
| 19 | `docs: add architecture decision records` | **partially complete — ADR practice and accepted records exist; process closure remains** |
| 20 | `docs: define compatibility policy` | partially represented in System Specification |

The System Specification already contains the normative change categories, `foundation-N` boundary, manifest-version distinction, migration principles, backward-compatibility expectations, and no-silent-change rules. Contributor guidance now covers architectural proposals and when to write an ADR. Remaining process closure and approval should apply the normative rules through supporting guidance and ADRs without creating a competing authority.

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

Current validator scope includes manifest discovery/shape, safe path boundaries, structural/common metadata, foundation-3 note-ID format/uniqueness, same-database lineage, Pool consistency, archive ancestry, Core workspaces, portable Core/supporting filenames and collisions, and supported Markdown heading checks.

Not yet generic/deterministic: database semantic schema validation, Pool-vocabulary interpretation from database contracts, materialization/fragmentation judgment, attachment reference/orphan auditing, arbitrary database-local resources, historical specification-version migration, and canonical draft promotion.

Manual encrypted user-state backup and restore are implemented with format-v2 destination-package reconstruction, complete Obsidian configuration transfer, synthetic compatibility vectors, and preservation/failure tests. The legacy format-v1 reader retains its historical full-Knowledge semantics. Historical schema migration and custom-database packaging remain deferred. See the [tooling guide](../Scripts/README.md#encrypted-backup-and-restore).

### Milestone 6 — Foundation Proof

| # | Commit | Status |
|---:|---|---|
| 29 | `example: add canonical shardbase database` | complete |
| 30 | `docs: document end-to-end shard workflow` | **in progress** |
| 31 | `docs: add foundation architecture overview` | evaluate after example/docs consolidation; likely concise |
| 32 | `docs: add foundation decision log` | replaced by ADR practice; ADR 0001 now records the first accepted architectural decision |
| 33 | `docs: define post-foundation roadmap` | planned |
| 34 | `release: complete shardbase foundation` | planned |

Commit 30 already has evidence for initial Games ownership, Pool/Core classification, materialization, and structural validation. It still needs:

- query/navigation proof;
- growth proof showing both retained-heading and materialized-note decisions;
- archive/restore behavior;
- Inbox-first capture has synthetic CLI proof, including stable IDs and template-independent metadata; canonical preparation retains direct primitive-level proof, while promotion of Inbox drafts remains future work;
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

Movies is not required to block every remaining Foundation task, but it should occur before Shardbase commits to broad post-Foundation generic capabilities whose design depends on database-semantic generalization.

---

## 6. Foundation Definition of Done

### Product

- purpose explicit: complete
- target users explicit: complete
- primary use cases explicit: complete
- goals/non-goals explicit: complete

### Architecture

- universal invariants documented: largely complete
- canonical vocabulary and decision framework: complete
- database ownership: complete
- structural classification: decision framework complete; broader examples remain incomplete
- lifecycle behavior: documented; end-to-end proof incomplete
- lineage behavior: complete within Foundation contract

### Safety and Governance

- user-owned data protections: complete at architectural level
- breaking-change categories/version boundaries: documented in System Specification
- migration principles: documented in System Specification; generalized tooling incomplete
- ADR/project decision process: partially complete; ADR practice and contributor guidance exist; closure and Foundation approval remain incomplete
- supporting contributor/security documentation and Apache-2.0 license: implemented; final governance reconciliation/sign-off remains incomplete
- repository automation: CI, weekly Dependabot, and explicit tracked-private/generated-artifact CI enforcement implemented and expanded CI verified green at `3c9aa505`; required status checks and `main` protection remain the outstanding professionalization closure task

### Understandability

- newcomer can understand product without source-code archaeology: root README and detailed tooling guide reconciled; canonical examples still needed
- private-instance onboarding/tooling discoverability: ZIP-first bootstrap, external runtime/launcher setup, doctor, guided init, and encrypted-backup-based update workflow implemented/documented
- complete example database: exists as sanitized structural fixture
- good/bad/ambiguous examples: incomplete

### Implementability

- minimal blueprint: complete
- Registry discovery: complete
- deterministic universal structural validation: implemented within documented scope
- representative structural fixtures: complete within implemented scope
- deterministic database-semantic validation: incomplete
- Inbox-first CLI capture: implemented with stable-ID and safety proof
- canonical preparation/commit primitives: retained with structural validation and synthetic proof; user-facing promotion and semantic validation remain incomplete
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
- Shardbase-owned sync system
- Shardbase-owned general-purpose search/indexing engine
- transactional database engine
- cloud-first collaborative platform

These are product boundaries, not backlog items.

### Deferred Until a Concrete Requirement

- mature/full CLI and interactive custom-database design wizard
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
