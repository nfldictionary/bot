from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from schema import CANONICAL_FILENAMES, STAGING_FILENAMES, VALIDATION_FILENAMES
from shared import (
    RuntimeConfig,
    display_repo_path,
    normalize_name,
    write_json,
    write_jsonl,
    update_pipeline_manifest,
)


def run_validate(config: RuntimeConfig) -> dict[str, Any]:
    coaches = read_jsonl(config.canonical_dir / CANONICAL_FILENAMES["coaches"])
    franchises = read_jsonl(config.canonical_dir / CANONICAL_FILENAMES["franchises"])
    team_aliases = read_jsonl(config.canonical_dir / CANONICAL_FILENAMES["team_aliases"])
    staff_tenures = read_jsonl(config.canonical_dir / CANONICAL_FILENAMES["staff_tenures"])
    worked_under_edges = read_jsonl(config.canonical_dir / CANONICAL_FILENAMES["worked_under_edges"])
    claims = read_jsonl(config.canonical_dir / CANONICAL_FILENAMES["claims"])
    staging_worked_under = read_jsonl(config.staging_dir / STAGING_FILENAMES["worked_under"])

    coach_ids = {row["coachId"] for row in coaches}
    franchise_ids = {row["franchiseId"] for row in franchises}
    coach_name_index: dict[str, list[str]] = {}
    for row in coaches:
        coach_name_index.setdefault(normalize_name(row["coachName"]), []).append(row["coachId"])

    unresolved_coaches = []
    ambiguous_relationships: list[dict[str, Any]] = []
    for row in staging_worked_under:
        candidates = coach_name_index.get(normalize_name(row["mentorName"]), [])
        if not candidates:
            unresolved_coaches.append(row)
        elif len(candidates) > 1:
            ambiguous_relationships.append({**row, "candidateCoachIds": candidates})
    unresolved_teams = [
        row for row in staff_tenures if row["franchiseId"] and row["franchiseId"] not in franchise_ids
    ]

    report = {
        "runId": config.run_id,
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "repoPath": "<TARGET_REPO_PATH>",
        "localDataRoot": "<LOCAL_DATA_ROOT>",
        "counts": {
            "coaches": len(coaches),
            "franchises": len(franchises),
            "teamAliases": len(team_aliases),
            "staffTenures": len(staff_tenures),
            "workedUnderEdges": len(worked_under_edges),
            "claims": len(claims),
        },
        "unresolvedCoachReferences": len(unresolved_coaches),
        "unresolvedTeamReferences": len(unresolved_teams),
        "ambiguousRelationships": len(ambiguous_relationships),
        "status": "pass" if not unresolved_coaches and not unresolved_teams else "warn",
    }

    if not config.dry_run:
        write_json(config.validation_dir / VALIDATION_FILENAMES["report"], report)
        write_jsonl(config.validation_dir / VALIDATION_FILENAMES["unresolved_coaches"], unresolved_coaches)
        write_jsonl(config.validation_dir / VALIDATION_FILENAMES["unresolved_teams"], unresolved_teams)
        write_jsonl(config.validation_dir / VALIDATION_FILENAMES["ambiguous_relationships"], ambiguous_relationships)
        update_pipeline_manifest(
            config,
            {
                "validationReportPath": display_repo_path(config, config.validation_dir / VALIDATION_FILENAMES["report"]),
                "validationSummary": {
                    "status": report["status"],
                    "unresolvedCoachReferences": len(unresolved_coaches),
                    "unresolvedTeamReferences": len(unresolved_teams),
                },
            },
        )
    return report


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(__import__("json").loads(line))
    return rows
