from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from schema import MANIFEST_FILENAMES
from shared import RuntimeConfig, display_repo_path, write_json, update_pipeline_manifest


def run_import(config: RuntimeConfig) -> dict[str, Any]:
    neo4j_database = os.environ.get("NEO4J_DATABASE", "neo4j")
    neo4j_uri = os.environ.get("NEO4J_URI")
    errors: list[str] = []
    if not neo4j_uri:
        errors.append("NEO4J_URI was not set; import manifest recorded a dry-run style skip.")

    manifest = {
        "runId": config.run_id,
        "neo4jDatabase": neo4j_database,
        "constraintsCreated": 0,
        "indexesCreated": 0,
        "nodesImported": 0,
        "relationshipsImported": 0,
        "rowsSkipped": 0,
        "errors": errors,
        "importedAt": datetime.now().isoformat(timespec="seconds"),
    }
    if not config.dry_run:
        write_json(config.manifests_dir / MANIFEST_FILENAMES["import"], manifest)
        update_pipeline_manifest(
            config,
            {
                "importManifestPath": display_repo_path(config, config.manifests_dir / MANIFEST_FILENAMES["import"]),
                "importSummary": manifest,
            },
        )
    return manifest
