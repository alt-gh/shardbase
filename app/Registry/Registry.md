# ShardBase Registry

The registry is the global discovery surface for live ShardBase databases.

Database roots are direct children of `app/Knowledge/Databases/` and are identified by a root-level `Database.md` manifest.

## Databases

```dataview
TABLE WITHOUT ID
  database_name AS "Database",
  database_status AS "Status",
  data_collections AS "Data Collections"
FROM "app/Knowledge/Databases"
WHERE file.name = "Database" AND manifest_version = 1
  AND length(split(file.folder, "/")) = 4
SORT database_name ASC
```

This view is navigational only. Each database's `Database.md` remains authoritative for its identity and local contract.

## Deterministic Discovery Contract

The Registry discovers databases at runtime from direct children of `app/Knowledge/Databases/` that contain a root-level `Database.md`. It does not maintain a generated inventory and does not treat database names, views, or query output as authoritative.

The validator in `app/Scripts/validate_shardbase.py` is the deterministic companion to this view. It examines every direct database directory, including roots missing a manifest, and reports malformed manifests, unsafe collection paths, structural metadata and lineage errors, workspace placement errors, portable filename mismatches, and supported Markdown heading violations. Structural discovery includes collection roots and one Core-workspace level while excluding attachment subtrees, Agents, Templates, and Views.

Follow [validator setup and scope](../Scripts/README.md) to install its pinned dependency in an environment outside the vault. With the documented environment, run from the repository root:

```text
/tmp/shardbase-validator-venv/bin/python -B app/Scripts/validate_shardbase.py
```

Detected issues use stable issue codes and cause a non-zero exit status. An empty `app/Knowledge/Databases/` is valid during bootstrap and reports that no databases were found. Passing means the implemented structural checks passed, not that every database-semantic requirement was validated. The Registry query filters direct version-1 manifest locations for navigation; it does not certify manifest or database validity.

The validator targets System Specification `foundation-2`, including required `aliases`, `id`, and `tags` with validated value shapes, normalized wikilink-safe filenames, manifest heading structure, and review of misplaced root structural declarations. Registry `manifest_version = 1` filtering identifies the manifest schema only; it does not establish specification-version compatibility.

Python bytecode, virtual environments, package installations, Node dependencies, test caches, and other generated runtime state must remain outside the vault. The `-B` flag prevents the validator command from creating `__pycache__/` files.
