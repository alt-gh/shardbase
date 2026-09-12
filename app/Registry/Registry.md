# ShardBase Registry

The Registry is the instance-wide **navigation and discovery** surface for live databases. It is not an architectural authority and does not certify database validity.

Universal discovery rules come from the [System Specification](../Docs/Shard%20System%20Specification.md). Each database's root `Database.md` remains authoritative for its identity and local contract.

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

This query discovers version-1 manifests at direct database-root locations for navigation. It does not prove that the manifest, database structure, canonical notes, or semantic data are valid.

## Validation Companion

Use [`../Scripts/README.md`](../Scripts/README.md) for the current read-only validator. The validator examines every direct database directory, including incomplete roots the Dataview query cannot present as valid manifests, and reports issues within its documented structural scope.

`manifest_version = 1` identifies the manifest schema only. It does not imply System Specification version compatibility.

The Registry maintains no generated authoritative inventory. An empty `app/Knowledge/Databases/` is valid during bootstrap.
