# ADR 0003: User-State-Only Backup and Managed Database Packages

Status: Accepted

Date: 2026-09-30

Specification boundary: `foundation-5`; `manifest_version: 1` retained

## Context

Foundation-4 treated every materialized database file as user-owned, so format-v1 backup transferred complete live packages. That made release upgrades preserve old manifests, supplied Templates, and supplied Agents instead of obtaining the destination release's current package. Obsidian configuration was excluded even though it is durable local user state.

## Decision

Materialized databases now combine Shardbase-managed package resources with user-owned Data and Views. Format v2 embeds Inbox, database Data and Views, and the complete `.obsidian/` tree. Databases are represented by stable `database_id`; restore resolves and stages the destination release's current blueprint/package, then adds user state conflict-safely. User files are always payload, independent of Git status.

Existing destination packages must be equivalent to the current release's managed package. Missing/custom package identities, managed differences, user-file differences, unsafe paths, and collisions fail complete preflight. Restore does not overwrite or execute restored content.

## Compatibility and Consequences

This ownership change advances the System Specification to foundation-5 without changing the database-manifest schema. Format v2 accepts foundation-4/5 sources for restore into foundation-5. Existing foundation-4 live packages are not rewritten or synchronized in place. Their managed-file customizations remain in the old instance but are deliberately outside format-v2 durable user state; users restore into a fresh foundation-5 checkout.

Format v1 remains readable under its original full-`app/Knowledge/` and Git-reference semantics for its recorded foundation-3/foundation-4 transitions. It is not reinterpreted and does not cross the foundation-5 ownership boundary automatically. Custom database packaging and managed-file overrides remain future explicit features.
