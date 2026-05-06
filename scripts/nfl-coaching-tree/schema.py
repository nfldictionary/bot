from __future__ import annotations

SCRIPT_VERSION = "0.1.0"
METHODOLOGY_VERSION = "nfl-coaching-tree-v1"
DEFAULT_SOURCE_BASE_URL = "https://coaching-tree.app"
DEFAULT_USER_AGENT = "NFLCoachingTreeMigrationBot/0.1 (+https://coaching-tree.app)"

RAW_ROOT_SEGMENT = "raw/coaching-tree-app"
CACHE_ROOT_SEGMENT = "cache/coaching-tree-app"
LOG_ROOT_SEGMENT = "logs"
EXPORT_ROOT_SEGMENT = "exports"
BACKUP_ROOT_SEGMENT = "backups"

STAGING_FILENAMES = {
    "directory_coaches": "coaching_tree_app_directory_coaches.jsonl",
    "profiles": "coaching_tree_app_profiles.jsonl",
    "career_history": "coaching_tree_app_career_history.jsonl",
    "worked_under": "coaching_tree_app_worked_under.jsonl",
    "proteges": "coaching_tree_app_proteges.jsonl",
    "teams_raw": "coaching_tree_app_teams_raw.jsonl",
    "sources": "coaching_tree_app_sources.jsonl",
}

CANONICAL_FILENAMES = {
    "coaches": "coaches.jsonl",
    "franchises": "franchises.jsonl",
    "team_aliases": "team_aliases.jsonl",
    "staff_tenures": "staff_tenures.jsonl",
    "worked_under_edges": "worked_under_edges.jsonl",
    "protege_edges": "protege_edges.jsonl",
    "lineage_edges": "lineage_edges.jsonl",
    "influence_edges": "influence_edges.jsonl",
    "sources": "sources.jsonl",
    "claims": "claims.jsonl",
}

MANIFEST_FILENAMES = {
    "crawl": "latest_crawl_manifest.json",
    "parse": "latest_parse_manifest.json",
    "normalize": "latest_normalize_manifest.json",
    "import": "latest_import_manifest.json",
    "pipeline": "latest_pipeline_manifest.json",
}

VALIDATION_FILENAMES = {
    "report": "latest_validation_report.json",
    "unresolved_coaches": "unresolved_coaches.jsonl",
    "unresolved_teams": "unresolved_teams.jsonl",
    "ambiguous_relationships": "ambiguous_relationships.jsonl",
}

REQUIRED_EMPTY_JSONL_GROUPS = (
    "career_history",
    "worked_under",
    "proteges",
)
