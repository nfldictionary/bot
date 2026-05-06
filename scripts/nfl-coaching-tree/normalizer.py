from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from schema import CANONICAL_FILENAMES, MANIFEST_FILENAMES, STAGING_FILENAMES
from shared import (
    RuntimeConfig,
    backup_directory,
    display_repo_path,
    load_json,
    normalize_name,
    update_pipeline_manifest,
    write_json,
    write_jsonl,
)


def run_normalize(config: RuntimeConfig) -> dict[str, Any]:
    staging_profiles = read_jsonl(config.staging_dir / STAGING_FILENAMES["profiles"])
    staging_directory = read_jsonl(config.staging_dir / STAGING_FILENAMES["directory_coaches"])
    staging_career = read_jsonl(config.staging_dir / STAGING_FILENAMES["career_history"])
    staging_worked_under = read_jsonl(config.staging_dir / STAGING_FILENAMES["worked_under"])
    staging_teams = read_jsonl(config.staging_dir / STAGING_FILENAMES["teams_raw"])
    staging_sources = read_jsonl(config.staging_dir / STAGING_FILENAMES["sources"])
    if not config.dry_run:
        backup_directory(config.canonical_dir, config.backup_dir / config.run_id / "canonical")

    coaches = normalize_coaches(staging_profiles, staging_directory)
    franchises = normalize_franchises(staging_teams)
    aliases = normalize_aliases(franchises)
    staff_tenures = normalize_staff_tenures(staging_career)
    worked_under_edges, unresolved_coach_refs, ambiguous_relationships = normalize_worked_under_edges(
        staging_worked_under,
        coaches,
    )
    lineage_edges = list(worked_under_edges)
    protege_edges: list[dict[str, Any]] = []
    influence_edges: list[dict[str, Any]] = []
    claims = normalize_claims(staging_profiles, staging_worked_under)

    if not config.dry_run:
        write_jsonl(config.canonical_dir / CANONICAL_FILENAMES["coaches"], coaches)
        write_jsonl(config.canonical_dir / CANONICAL_FILENAMES["franchises"], franchises)
        write_jsonl(config.canonical_dir / CANONICAL_FILENAMES["team_aliases"], aliases)
        write_jsonl(config.canonical_dir / CANONICAL_FILENAMES["staff_tenures"], staff_tenures)
        write_jsonl(config.canonical_dir / CANONICAL_FILENAMES["worked_under_edges"], worked_under_edges)
        write_jsonl(config.canonical_dir / CANONICAL_FILENAMES["protege_edges"], protege_edges)
        write_jsonl(config.canonical_dir / CANONICAL_FILENAMES["lineage_edges"], lineage_edges)
        write_jsonl(config.canonical_dir / CANONICAL_FILENAMES["influence_edges"], influence_edges)
        write_jsonl(config.canonical_dir / CANONICAL_FILENAMES["sources"], staging_sources)
        write_jsonl(config.canonical_dir / CANONICAL_FILENAMES["claims"], claims)

    manifest = {
        "runId": config.run_id,
        "stagingInputDir": display_repo_path(config, config.staging_dir),
        "canonicalOutputDir": display_repo_path(config, config.canonical_dir),
        "coachesWritten": len(coaches),
        "franchisesWritten": len(franchises),
        "aliasesWritten": len(aliases),
        "staffTenuresWritten": len(staff_tenures),
        "workedUnderEdgesWritten": len(worked_under_edges),
        "protegeEdgesWritten": len(protege_edges),
        "lineageEdgesWritten": len(lineage_edges),
        "influenceEdgesWritten": len(influence_edges),
        "sourcesWritten": len(staging_sources),
        "claimsWritten": len(claims),
        "unresolvedCoachReferences": len(unresolved_coach_refs),
        "unresolvedTeamReferences": 0,
        "ambiguousRelationships": len(ambiguous_relationships),
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
    }
    if not config.dry_run:
        write_json(config.manifests_dir / MANIFEST_FILENAMES["normalize"], manifest)
        update_pipeline_manifest(
            config,
            {
                "normalizeManifestPath": display_repo_path(config, config.manifests_dir / MANIFEST_FILENAMES["normalize"]),
                "normalizeSummary": {
                    "coachesWritten": len(coaches),
                    "franchisesWritten": len(franchises),
                    "staffTenuresWritten": len(staff_tenures),
                    "workedUnderEdgesWritten": len(worked_under_edges),
                },
            },
        )
    return manifest


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(__import__("json").loads(line))
    return rows


def normalize_coaches(profiles: list[dict[str, Any]], directory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = {}
    for row in directory_rows:
        coach_id = row["coachSlug"]
        rows.setdefault(
            coach_id,
            {
                "coachId": coach_id,
                "coachSlug": row["coachSlug"],
                "coachName": row["coachName"],
                "profileUrl": None,
                "jobTitle": None,
                "currentTeamName": None,
                "birthPlace": None,
                "alumniOf": None,
                "sourceUrl": row["sourceUrl"],
            },
        )
    for row in profiles:
        coach_id = row["coachId"]
        rows[coach_id] = {
            "coachId": coach_id,
            "coachSlug": row["coachSlug"],
            "coachName": row["coachName"],
            "profileUrl": row["canonicalUrl"],
            "jobTitle": row["jobTitle"],
            "currentTeamName": row["currentTeamName"],
            "birthPlace": row["birthPlace"],
            "alumniOf": row["alumniOf"],
            "sourceUrl": row["sourceUrl"],
        }
    return sorted(rows.values(), key=lambda row: row["coachName"])


def normalize_franchises(team_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = {}
    for row in team_rows:
        rows[row["teamSlug"]] = {
            "franchiseId": row["teamSlug"],
            "teamSlug": row["teamSlug"],
            "teamName": row["teamName"],
            "teamUrl": row["teamUrl"],
            "sourceUrl": row["sourceUrl"],
        }
    return sorted(rows.values(), key=lambda row: row["teamName"])


def normalize_aliases(franchises: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in franchises:
        rows.append(
            {
                "alias": row["teamName"],
                "aliasNormalized": normalize_name(row["teamName"]),
                "franchiseId": row["franchiseId"],
                "sourceUrl": row["sourceUrl"],
            }
        )
    return rows


def normalize_staff_tenures(career_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for row in career_rows:
        normalized.append(
            {
                "coachId": row["coachId"],
                "coachName": row["coachName"],
                "year": row["year"],
                "franchiseId": row["teamSlug"],
                "teamName": row["teamName"],
                "roles": row["roles"],
                "sourceUrl": row["sourceUrl"],
            }
        )
    return normalized


def normalize_worked_under_edges(
    worked_under_rows: list[dict[str, Any]],
    coaches: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    coach_index: dict[str, list[str]] = {}
    for coach in coaches:
        coach_index.setdefault(normalize_name(coach["coachName"]), []).append(coach["coachId"])

    edges = []
    unresolved = []
    ambiguous = []
    for row in worked_under_rows:
        mentor_ids = coach_index.get(normalize_name(row["mentorName"]), [])
        if not mentor_ids:
            unresolved.append(row)
            continue
        if len(mentor_ids) > 1:
            ambiguous.append({**row, "candidateCoachIds": mentor_ids})
            continue
        edges.append(
            {
                "fromCoachId": row["coachId"],
                "toCoachId": mentor_ids[0],
                "relationshipType": "worked_under",
                "sourceUrl": row["sourceUrl"],
            }
        )
    return edges, unresolved, ambiguous


def normalize_claims(
    profiles: list[dict[str, Any]],
    worked_under_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    claims = []
    for row in profiles:
        claims.append(
            {
                "claimId": f"profile-meta:{row['coachId']}",
                "subjectId": row["coachId"],
                "predicate": "profile_summary",
                "object": row["description"],
                "sourceUrl": row["sourceUrl"],
                "confidence": "medium",
            }
        )
    for row in worked_under_rows:
        claims.append(
            {
                "claimId": f"worked-under:{row['coachId']}:{normalize_name(row['mentorName']).replace(' ', '-')}",
                "subjectId": row["coachId"],
                "predicate": "worked_under_name",
                "object": row["mentorName"],
                "sourceUrl": row["sourceUrl"],
                "confidence": "medium",
            }
        )
    return claims
