---
manifest_version: 1
database_id: example-database
database_name: Example Database
data_collections:
  - Game
database_status: draft
---
# Example Database

## Purpose

A sanitized starter database demonstrating the minimum ShardBase contract.

## Scope

### Includes

Example domain notes created from this blueprint.

### Excludes

Private user knowledge and unrelated domains.

## Architecture

The materialized database begins with an empty declared collection and can grow from a Core.

## Schema

Database-local semantic fields are defined after materialization.

## Conventions

Use the universal structural metadata and keep domain semantics separate.

## Resources

The blueprint intentionally contains no private data or external-service integration.
