# Structural Decision Framework

## Purpose and Authority

This is non-normative supporting guidance for applying existing structural rules consistently. The [System Specification](Shard%20System%20Specification.md#5-structural-model) remains authoritative for universal structure; the owning database's root `Database.md` remains authoritative for database-local semantics and Pool vocabulary. If this guide conflicts with either authority, the higher authority controls.

The framework turns the specification's [classification and materialization principles](Shard%20System%20Specification.md#10-classification-and-materialization) into a repeatable decision process. Resolve database ownership before canonical structural classification. Structural classification determines a note's role in a lineage; it is not semantic categorization. Categories and domain relationships do not establish ancestry; [YAML remains authoritative for lineage](Shard%20System%20Specification.md#8-canonical-naming-and-lineage).

This guide does not alter the System Specification or create deterministic validator rules for materialization judgment. Concrete-value considerations require judgment; the current validator's [documented scope and limits](../Scripts/README.md#not-yet-implemented-generically) remain unchanged. A classification recommendation does not authorize additional note creation.

## Decision Sequence

### 1. Resolve Database Ownership

Does the target database's contract clearly own this knowledge? Read its scope before choosing canonical structure, following [Database Ownership](Shard%20System%20Specification.md#43-database-ownership).

If ownership is unresolved, leave the knowledge unresolved or pre-structural where appropriate and clarify the relevant database contracts. Do not force canonical placement or create duplicate authoritative copies. Physical folders, filenames, tags, links, and conceptual similarity do not establish ownership.

### 2. Decide Whether the Subject Is a Lineage Root

Is the subject a stable, independently meaningful root that should be managed as the root of its own lineage? If yes, it is a **Core candidate**, subject to the database's Core strategy and the [Core rules](Shard%20System%20Specification.md#52-core).

Importance, note length, popularity, category membership, semantic containment, and anticipated future complexity alone do not justify Core status. A Core can remain one Markdown file indefinitely; it does not need supporting notes to earn its role.

If the knowledge instead supports an existing Core or Shard, continue with that lineage. Resolve a missing or ambiguous root or parent rather than guessing one.

### 3. Consider Ordinary Markdown First

For knowledge inside an existing Core or Shard, what concrete independent value would a separate structural note provide? Consider the [Shard materialization principles](Shard%20System%20Specification.md#53-shard):

| Consideration | Practical question |
|---|---|
| Growth | Does the material benefit from developing independently now? |
| Querying | Does it need to be selected or analyzed independently? |
| Navigation/reference | Would direct linking or navigation materially improve use? |
| Reuse | Is it meaningfully referenced from more than one context? |
| Lifecycle management | Does it need independent archive, status, or evolution handling? |
| Structural organization | Would separate ancestry meaningfully improve management? |

These are considerations, not a numeric score or automatic threshold. Identify the demonstrated need rather than counting signals. Direct reference can justify separation when it improves use, but a link count alone cannot.

If independent structure adds no meaningful value, use an ordinary Markdown heading or section. Under [Ordinary Markdown and Ghost Shards](Shard%20System%20Specification.md#55-ordinary-markdown-and-ghost-shards), a heading may remain the correct permanent representation. If future separation is plausible, consider step 5 without creating a file.

### 4. Choose Shard or Pebble When Separation Is Justified

If the materialized supporting note may structurally parent other notes, classify it as a **Shard**. If it is terminal and should not structurally parent another note, classify it as a **Pebble**. Apply the specification's [Shard](Shard%20System%20Specification.md#53-shard) and [Pebble](Shard%20System%20Specification.md#54-pebble) roles within the resolved lineage.

Pebble means terminal structural role, not “small note.” Note length does not decide Shard versus Pebble. A Shard need not already have children, but speculative future complexity alone does not earn a separate file. If a Pebble later needs structural children, reclassify it as a Shard before establishing them.

### 5. Consider a Ghost Shard for Premature Structure

If separate structure is plausible but does not yet earn materialization, use a **Ghost Shard** when an unresolved wikilink is useful. Otherwise retain ordinary Markdown without adding a speculative reference.

A [Ghost Shard](Shard%20System%20Specification.md#55-ordinary-markdown-and-ghost-shards) has no file and no structural YAML. It may remain unresolved indefinitely. Age, reference count, or repeated appearance does not automatically justify materialization; revisit the concrete need first.

### 6. Apply the Minimum-Structure Tie-Breaker

When more than one representation is valid and no concrete need decides between them:

> Choose the least structural representation that satisfies the demonstrated need.

This applies the specification's [materialization principles](Shard%20System%20Specification.md#10-classification-and-materialization) and [Core Mission](Shard%20System%20Specification.md#19-core-mission):

- Prefer a heading or section before a materialized supporting note.
- Prefer a Ghost Shard before speculative file creation when a future-topic reference is useful.
- Choose a Pebble only when terminal independent structure is justified.
- Choose a Shard when independent structure is justified and its parenting role supports child topics or growth into them.
- Choose a Core only for an independently meaningful lineage root.

These are choices for the current need, not stages that every item must graduate through. Preserve a valid existing representation unless the requested change justifies restructuring.

## Compact Decision Table

| Question | Outcome |
|---|---|
| Is database ownership unresolved? | Keep unresolved/pre-structural; clarify ownership. |
| Is it a stable, independently meaningful lineage root? | Core candidate under the database contract. |
| Does separate representation add no concrete value? | Ordinary Markdown heading or section. |
| Is future separate structure plausible but not justified? | Ghost Shard if an unresolved wikilink is useful; otherwise ordinary Markdown. |
| Does justified independent supporting structure need a role that permits structural children? | Shard. |
| Is justified independent supporting structure terminal? | Pebble. |

The table summarizes the sequence; it does not replace ownership, lineage, or concrete-value judgment. A classification does not by itself establish canonical conformance. Before materialization, also resolve collection, Pool, lineage, metadata, naming, and placement against the specification and database contract.

## Non-Signals

The following do not, by themselves, justify structural materialization or classification:

- note length or importance;
- number of headings or links;
- age or repeated references;
- category membership or semantic containment;
- template availability;
- folder layout or filename shape;
- expected future growth without a present concrete need.

Use the [classification principles](Shard%20System%20Specification.md#10-classification-and-materialization) and [repository operating guidance](../../AGENTS.md#structural-work) to distinguish these incidental signals from demonstrated value. Conceptual hierarchy does not require matching file hierarchy.

## Re-evaluation Over Time

Structural decisions can legitimately change as knowledge evolves, following the specification's [Growth](Shard%20System%20Specification.md#113-growth) and [preservation boundaries](Shard%20System%20Specification.md#13-change-safety-and-authorization):

- A heading or section can become a Shard or Pebble when independent structure earns concrete value.
- A Ghost Shard can become a materialized Shard or Pebble when the need becomes concrete and its role is resolved.
- A Pebble can become a Shard before adding structural children.
- An existing valid materialized note can remain materialized even when another valid representation might now be preferred. Restructure only when a requested change justifies it.

Re-evaluation is not permission to delete, rename, move, or normalize existing knowledge. This guide introduces no dematerialization or migration procedure.

## Short Synthetic Examples

These invented subjects illustrate decisions, not a database schema. Assume ownership and supporting lineage have been resolved under a suitable database contract.

| Situation | Decision and reason |
|---|---|
| “Example Instrument” is a stable, independently meaningful subject managed as its own lineage root. | Core candidate; it can remain one file. |
| Its “Controls” section has no independent lifecycle, querying, or navigation need. | Keep the heading; separation adds no concrete value. |
| “Assembly Progress” needs independent development and direct navigation, with a demonstrated role for child topics as work grows. | Shard; separation is useful and the topic may parent structural notes. |
| “Connector Reference” benefits from independent linking and remains a terminal reference detail. | Pebble; independent reference is useful, but the note will not parent structural notes. |
| “Calibration Study” is a plausible future topic whose unresolved wikilink is useful, but no present need earns a file. | Ghost Shard; retain the reference without materializing speculative structure. |

## Final Checklist

- [ ] Target database ownership is resolved.
- [ ] Root versus supporting role is resolved.
- [ ] Concrete value for any independent structure is identified.
- [ ] An ordinary Markdown heading or section was considered first for supporting material.
- [ ] Shard versus Pebble follows parenting role, not size.
- [ ] A Ghost Shard was considered for premature structure when a reference is useful.
- [ ] The minimum-structure tie-breaker was applied where several choices remain valid.
- [ ] Unresolved ambiguity was surfaced rather than guessed.
- [ ] The final result was checked against the System Specification and owning database contract.
