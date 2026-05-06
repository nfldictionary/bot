from __future__ import annotations

import csv
import shutil
from pathlib import Path
from typing import Any

from schema import CANONICAL_FILENAMES
from shared import RuntimeConfig


def run_export(config: RuntimeConfig) -> dict[str, Any]:
    export_root = config.export_dir / config.run_id
    canonical_export_dir = export_root / "canonical"
    neo4j_export_dir = export_root / "neo4j"
    canonical_export_dir.mkdir(parents=True, exist_ok=True)
    neo4j_export_dir.mkdir(parents=True, exist_ok=True)

    copied_files = []
    for filename in CANONICAL_FILENAMES.values():
        source = config.canonical_dir / filename
        if not source.exists():
            continue
        destination = canonical_export_dir / filename
        shutil.copy2(source, destination)
        copied_files.append(str(destination))

    export_csv(config.canonical_dir / CANONICAL_FILENAMES["coaches"], neo4j_export_dir / "coaches.csv")
    export_csv(config.canonical_dir / CANONICAL_FILENAMES["franchises"], neo4j_export_dir / "franchises.csv")
    export_csv(
        config.canonical_dir / CANONICAL_FILENAMES["worked_under_edges"],
        neo4j_export_dir / "worked_under_edges.csv",
    )

    return {
        "runId": config.run_id,
        "exportRoot": str(export_root),
        "copiedCanonicalFiles": copied_files,
        "neo4jCsvDir": str(neo4j_export_dir),
    }


def export_csv(source_jsonl: Path, target_csv: Path) -> None:
    if not source_jsonl.exists():
        target_csv.write_text("", encoding="utf-8")
        return
    rows = [
        __import__("json").loads(line)
        for line in source_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        target_csv.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with target_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
