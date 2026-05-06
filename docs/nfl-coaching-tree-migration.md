# NFL Coaching Tree Migration

This pipeline migrates public `https://coaching-tree.app` data into a reproducible repository/local-storage split.

## Storage model

- Git repository: scripts, docs, manifests, validation outputs, staging data, canonical data, and Neo4j migration files.
- Local non-Git folder: raw HTML snapshots, cache state, logs, exports, and backups.

## Commands

The repository currently has no package manager, so the pipeline is exposed as a Python CLI:

```bash
python3 scripts/nfl-coaching-tree/cli.py setup-storage --repo-path /real/repo/path --local-data-root /real/local-data-root
python3 scripts/nfl-coaching-tree/cli.py crawl --repo-path /real/repo/path --local-data-root /real/local-data-root --run-id 20260506-120000-coaching-tree-app --max-pages 2 --max-coaches 10
python3 scripts/nfl-coaching-tree/cli.py parse --repo-path /real/repo/path --local-data-root /real/local-data-root --run-id 20260506-120000-coaching-tree-app
python3 scripts/nfl-coaching-tree/cli.py normalize --repo-path /real/repo/path --local-data-root /real/local-data-root --run-id 20260506-120000-coaching-tree-app
python3 scripts/nfl-coaching-tree/cli.py validate --repo-path /real/repo/path --local-data-root /real/local-data-root --run-id 20260506-120000-coaching-tree-app
python3 scripts/nfl-coaching-tree/cli.py import --repo-path /real/repo/path --local-data-root /real/local-data-root --run-id 20260506-120000-coaching-tree-app
python3 scripts/nfl-coaching-tree/cli.py export --repo-path /real/repo/path --local-data-root /real/local-data-root --run-id 20260506-120000-coaching-tree-app
python3 scripts/nfl-coaching-tree/cli.py all --repo-path /real/repo/path --local-data-root /real/local-data-root --run-id 20260506-120000-coaching-tree-app --max-pages 2 --max-coaches 10
```

## Notes

- Runtime paths must be supplied by CLI, environment variables, or a local ignored config file.
- The committed example config intentionally uses placeholders.
- Canonical files are backed up to the local non-Git folder before overwrite.
