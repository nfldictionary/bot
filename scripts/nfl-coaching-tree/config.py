from __future__ import annotations

from pathlib import Path

from shared import RuntimeConfig, ensure_directories


def ensure_storage_layout(config: RuntimeConfig) -> None:
    ensure_directories(
        [
            config.canonical_dir,
            config.staging_dir,
            config.manifests_dir,
            config.validation_dir,
            config.docs_dir,
            config.scripts_dir,
            config.migrations_dir,
            config.raw_snapshot_base_dir,
            config.cache_dir,
            config.run_log_dir,
            config.export_dir,
            config.backup_dir,
        ]
    )


def ensure_data_readme(config: RuntimeConfig) -> None:
    readme_path = config.data_root / "README.md"
    if readme_path.exists():
        return
    readme_path.write_text(
        "# NFL Coaching Tree Data\n\n"
        "This directory holds staging, canonical, manifests, and validation artifacts for the "
        "coaching-tree.app migration pipeline.\n",
        encoding="utf-8",
    )


def ensure_gitignore_entries(repo_path: Path) -> None:
    gitignore_path = repo_path / ".gitignore"
    existing = gitignore_path.read_text(encoding="utf-8").splitlines() if gitignore_path.exists() else []
    desired = [
        ".cache/nfl-coaching-tree/",
        "data/nfl-coaching-tree/raw/",
        "*.html.snapshot",
        "*.raw.json",
        "*.tmp",
        "config/nflCoachingTreeMigration.config.local.json",
        "nfl-coaching-tree-data/",
    ]
    missing = [entry for entry in desired if entry not in existing]
    if missing:
        with gitignore_path.open("a", encoding="utf-8") as handle:
            if existing and existing[-1] != "":
                handle.write("\n")
            for entry in missing:
                handle.write(entry + "\n")
