# ShardBase Registry

The registry is the global discovery surface for live ShardBase databases.

Database roots are direct children of `app/Db/` and are identified by a root-level `Database.md` manifest.

## Databases

```dataview
TABLE WITHOUT ID
  database_name AS "Database",
  database_status AS "Status",
  data_folder AS "Data Folder"
FROM "app/Db"
WHERE file.name = "Database" AND manifest_version = 1
SORT database_name ASC
```

This view is navigational only. Each database's `Database.md` remains authoritative for its identity and local contract.
