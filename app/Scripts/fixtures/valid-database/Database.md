---
manifest_version: 1
database_id: example-database
database_name: Example Database
data_collections:
  - Game
database_status: active
---
# Example Database

## Purpose

A small, sanitized database used to prove the Foundation contracts.

## Scope

### Includes

Game knowledge owned by this database.

### Excludes

Personal capture and unrelated domains.

## Architecture

The example uses one Core, one Shard, and one Pebble.

## Schema

The `entity_kind` field is database-local semantic metadata.

## Conventions

Pool values use readable domain names.

The Core's opening level-one heading records its canonical entity name. Each supporting note's opening level-one heading records its canonical local node name; its filename supplies bounded Core and immediate-parent context under the System Specification.

## Resources

Attachments remain inside the collection boundary.
