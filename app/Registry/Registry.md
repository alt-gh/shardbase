# ShardBase Registry

The registry is the global discovery surface for live ShardBase databases.

Database roots are direct children of `app/Db/` and are identified by a root-level `Database.md` manifest.

## Databases

```dataview
TABLE WITHOUT ID
  database_name AS "Database",
  database_status AS "Status",
  data_collections AS "Data Collections"
FROM "app/Db"
WHERE file.name = "Database" AND manifest_version = 1
SORT database_name ASC
```

This view is navigational only. Each database's `Database.md` remains authoritative for its identity and local contract.

## Deterministic Discovery Contract

The Registry discovers databases at runtime from direct children of `app/Db/` that contain a root-level `Database.md`. It does not maintain a generated inventory and does not treat database names, views, or query output as authoritative.

The validator in `app/Scripts/validate_shardbase.py` is the deterministic companion to this view. It validates manifest fields, declared collections, required manifest sections, structural metadata, lineage, bounded filenames, placement, and the minimum Markdown heading rule. It scans only declared collection roots and excludes `Attachments/`, `Agents/`, and other non-structural resources.

Run it from the repository root with:

```text
python3 -B app/Scripts/validate_shardbase.py
```

An invalid database is reported with stable issue codes and causes a non-zero exit status. An empty `app/Db/` is valid during bootstrap and reports that no databases were found.

Python bytecode, virtual environments, package installations, Node dependencies, test caches, and other generated runtime state must remain outside the vault. The `-B` flag prevents the validator command from creating `__pycache__/` files.
