# NFL Coaching Tree Data

This directory is the Git-committed side of the `coaching-tree.app` migration pipeline.

- `canonical/` holds normalized graph import records.
- `staging/` holds structured extraction rows derived from raw snapshots.
- `manifests/` holds per-run manifests plus the consolidated pipeline manifest.
- `validation/` holds the latest validation summary and unresolved-reference files.

Raw HTML snapshots, cache files, logs, exports, and backups live in the local non-Git data root and are intentionally excluded from the repository.
