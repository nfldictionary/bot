from __future__ import annotations

import json

from src.sis_pipeline import (
    DEFAULT_LOCAL_SOURCE_ROOT,
    build_seasons,
    build_html_validation_report,
    copy_local_raw_data,
    validate_seasons,
)


def test_default_local_source_root_points_to_workspace_data() -> None:
    assert str(DEFAULT_LOCAL_SOURCE_ROOT).endswith(
        "nfldictionary/nfldictionary.github.io/data_archive/season_feed/v7"
    )


def test_copy_local_raw_data_accepts_source_with_raw_subdir(tmp_path) -> None:
    source_root = tmp_path / "source"
    raw_root = source_root / "raw" / "2025"
    raw_root.mkdir(parents=True)
    (raw_root / "team_seasonal.json").write_text("{}", encoding="utf-8")
    (raw_root / "player_seasonal.json").write_text("{}", encoding="utf-8")

    output_root = tmp_path / "output"
    summary = copy_local_raw_data(
        source_root=source_root,
        output_root=output_root,
        start_year=2025,
        end_year=2025,
    )

    assert summary["copied_files"] == 2
    assert (output_root / "raw" / "2025" / "team_seasonal.json").exists()
    assert (output_root / "raw" / "2025" / "player_seasonal.json").exists()


def test_build_and_validate_seasons(tmp_path) -> None:
    output_root = tmp_path / "sis"
    raw_dir = output_root / "raw" / "2025"
    raw_dir.mkdir(parents=True)

    team_payload = {
        "fetched_at": "2026-04-13T00:00:00+00:00",
        "source": "season_feed_v7",
        "teams": [
            {
                "status": "ok",
                "team_id": "t1",
                "team_alias": "KC",
                "team_name": "Chiefs",
                "team_market": "Kansas City",
                "endpoint": "/seasons/2025/REG/teams/t1/statistics.json",
                "response": {
                    "id": "t1",
                    "alias": "KC",
                    "name": "Chiefs",
                    "market": "Kansas City",
                    "statistics": {"games_played": 17, "points": {"for": 450}},
                    "record": {"wins": 15, "losses": 2},
                    "ranks": {"offense": {"yards": 1}},
                },
            }
        ],
    }
    player_payload = {
        "players": [
            {
                "team_id": "t1",
                "team_alias": "KC",
                "team_name": "Chiefs",
                "player": {
                    "id": "p1",
                    "name": "Patrick Mahomes",
                    "first_name": "Patrick",
                    "last_name": "Mahomes",
                    "position": "QB",
                    "jersey": "15",
                    "status": "ACT",
                    "sr_id": "sr:player:1",
                    "statistics": {
                        "passing": {"yards": "4,000", "touchdowns": 30},
                        "rushing": {"yards": 250},
                    },
                },
            }
        ]
    }

    (raw_dir / "team_seasonal.json").write_text(json.dumps(team_payload), encoding="utf-8")
    (raw_dir / "player_seasonal.json").write_text(json.dumps(player_payload), encoding="utf-8")

    build_summary = build_seasons(output_root=output_root, start_year=2025, end_year=2025)
    validation_summary = validate_seasons(output_root=output_root, start_year=2025, end_year=2025)

    assert build_summary[0]["status"] == "ok"
    assert validation_summary[0]["ok"] is True
    assert (output_root / "parquet" / "2025" / "team_seasonal.parquet").exists()
    assert (output_root / "parquet" / "2025" / "player_seasonal.parquet").exists()
    assert (output_root / "parquet" / "2025" / "_validation.json").exists()


def test_build_html_validation_report(tmp_path) -> None:
    output_root = tmp_path / "sis"
    raw_dir = output_root / "raw" / "2025"
    raw_dir.mkdir(parents=True)

    team_payload = {
        "fetched_at": "2026-04-13T00:00:00+00:00",
        "source": "season_feed_v7",
        "teams": [
            {
                "status": "ok",
                "team_id": "t1",
                "team_alias": "KC",
                "team_name": "Chiefs",
                "team_market": "Kansas City",
                "endpoint": "/seasons/2025/REG/teams/t1/statistics.json",
                "response": {
                    "id": "t1",
                    "alias": "KC",
                    "name": "Chiefs",
                    "market": "Kansas City",
                    "statistics": {
                        "passing": {"yards": 4200},
                        "rushing": {"yards": 2100},
                        "receiving": {"yards": 4300},
                        "defense": {"sacks": 48},
                    },
                    "record": {"games_played": 17},
                    "ranks": {"offense": {"yards": 1}},
                },
            }
        ],
    }
    player_payload = {
        "players": [
            {
                "team_id": "t1",
                "team_alias": "KC",
                "team_name": "Chiefs",
                "player": {
                    "id": "p1",
                    "name": "Patrick Mahomes",
                    "first_name": "Patrick",
                    "last_name": "Mahomes",
                    "position": "QB",
                    "jersey": "15",
                    "status": "ACT",
                    "sr_id": "sr:player:1",
                    "statistics": {
                        "passing": {"yards": "4,200", "touchdowns": 35},
                        "rushing": {"yards": 320},
                    },
                },
            }
        ]
    }

    (raw_dir / "team_seasonal.json").write_text(json.dumps(team_payload), encoding="utf-8")
    (raw_dir / "player_seasonal.json").write_text(json.dumps(player_payload), encoding="utf-8")

    build_seasons(output_root=output_root, start_year=2025, end_year=2025)
    validate_seasons(output_root=output_root, start_year=2025, end_year=2025)
    report_path = build_html_validation_report(output_root=output_root, season=2025)

    html = report_path.read_text(encoding="utf-8")
    assert "SIS Extraction Visual Check" in html
    assert "Patrick Mahomes" in html
    assert "Chiefs" in html
