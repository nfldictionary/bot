from __future__ import annotations

import json

from src.sis_pipeline import (
    DEFAULT_LOCAL_SOURCE_ROOT,
    build_seasons,
    build_html_validation_report,
    copy_local_raw_data,
    validate_seasons,
)
from src.sis_visual_stories import build_story_html_bundle


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


def test_build_story_html_bundle(tmp_path) -> None:
    output_root = tmp_path / "sis"
    raw_dir = output_root / "raw" / "2025"
    raw_dir.mkdir(parents=True)

    team_rows = [
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
                    "passing": {"yards": 4200, "touchdowns": 35},
                    "rushing": {"yards": 2100, "touchdowns": 18},
                    "receiving": {"yards": 4300},
                    "defense": {"sacks": 48, "tackles": 620},
                },
                "record": {"games_played": 17, "touchdowns": {"total": 60}},
            },
        },
        {
            "status": "ok",
            "team_id": "t2",
            "team_alias": "BUF",
            "team_name": "Bills",
            "team_market": "Buffalo",
            "endpoint": "/seasons/2025/REG/teams/t2/statistics.json",
            "response": {
                "id": "t2",
                "alias": "BUF",
                "name": "Bills",
                "market": "Buffalo",
                "statistics": {
                    "passing": {"yards": 3800, "touchdowns": 30},
                    "rushing": {"yards": 2500, "touchdowns": 20},
                    "receiving": {"yards": 3900},
                    "defense": {"sacks": 41, "tackles": 590},
                },
                "record": {"games_played": 17, "touchdowns": {"total": 58}},
            },
        },
    ]
    player_rows = [
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
        },
        {
            "team_id": "t1",
            "team_alias": "KC",
            "team_name": "Chiefs",
            "player": {
                "id": "p2",
                "name": "Isiah Pacheco",
                "first_name": "Isiah",
                "last_name": "Pacheco",
                "position": "RB",
                "jersey": "10",
                "status": "ACT",
                "sr_id": "sr:player:2",
                "statistics": {
                    "rushing": {"yards": 1200, "touchdowns": 10},
                },
            },
        },
        {
            "team_id": "t1",
            "team_alias": "KC",
            "team_name": "Chiefs",
            "player": {
                "id": "p3",
                "name": "Travis Kelce",
                "first_name": "Travis",
                "last_name": "Kelce",
                "position": "TE",
                "jersey": "87",
                "status": "ACT",
                "sr_id": "sr:player:3",
                "statistics": {
                    "receiving": {"yards": 1100, "touchdowns": 8},
                },
            },
        },
        {
            "team_id": "t1",
            "team_alias": "KC",
            "team_name": "Chiefs",
            "player": {
                "id": "p4",
                "name": "Nick Bolton",
                "first_name": "Nick",
                "last_name": "Bolton",
                "position": "LB",
                "jersey": "32",
                "status": "ACT",
                "sr_id": "sr:player:4",
                "statistics": {
                    "defense": {"combined": 150, "sacks": 5},
                },
            },
        },
        {
            "team_id": "t2",
            "team_alias": "BUF",
            "team_name": "Bills",
            "player": {
                "id": "p5",
                "name": "Josh Allen",
                "first_name": "Josh",
                "last_name": "Allen",
                "position": "QB",
                "jersey": "17",
                "status": "ACT",
                "sr_id": "sr:player:5",
                "statistics": {
                    "passing": {"yards": "3,800", "touchdowns": 30},
                    "rushing": {"yards": 540},
                },
            },
        },
        {
            "team_id": "t2",
            "team_alias": "BUF",
            "team_name": "Bills",
            "player": {
                "id": "p6",
                "name": "James Cook",
                "first_name": "James",
                "last_name": "Cook",
                "position": "RB",
                "jersey": "4",
                "status": "ACT",
                "sr_id": "sr:player:6",
                "statistics": {
                    "rushing": {"yards": 1300, "touchdowns": 11},
                },
            },
        },
        {
            "team_id": "t2",
            "team_alias": "BUF",
            "team_name": "Bills",
            "player": {
                "id": "p7",
                "name": "Khalil Shakir",
                "first_name": "Khalil",
                "last_name": "Shakir",
                "position": "WR",
                "jersey": "10",
                "status": "ACT",
                "sr_id": "sr:player:7",
                "statistics": {
                    "receiving": {"yards": 980, "touchdowns": 7},
                },
            },
        },
        {
            "team_id": "t2",
            "team_alias": "BUF",
            "team_name": "Bills",
            "player": {
                "id": "p8",
                "name": "Terrel Bernard",
                "first_name": "Terrel",
                "last_name": "Bernard",
                "position": "LB",
                "jersey": "43",
                "status": "ACT",
                "sr_id": "sr:player:8",
                "statistics": {
                    "defense": {"combined": 140, "sacks": 4},
                },
            },
        },
        {
            "team_id": "t1",
            "team_alias": "KC",
            "team_name": "Chiefs",
            "player": {
                "id": "p9",
                "name": "Journeyman Player",
                "first_name": "Journey",
                "last_name": "Man",
                "position": "S",
                "jersey": "22",
                "status": "ACT",
                "sr_id": "sr:player:9",
                "statistics": {
                    "defense": {"combined": 88, "sacks": 1},
                },
            },
        },
        {
            "team_id": "t2",
            "team_alias": "BUF",
            "team_name": "Bills",
            "player": {
                "id": "p9",
                "name": "Journeyman Player",
                "first_name": "Journey",
                "last_name": "Man",
                "position": "S",
                "jersey": "22",
                "status": "ACT",
                "sr_id": "sr:player:9",
                "statistics": {
                    "defense": {"combined": 32, "sacks": 0},
                },
            },
        },
    ]

    team_payload = {
        "fetched_at": "2026-04-13T00:00:00+00:00",
        "source": "season_feed_v7",
        "teams": team_rows,
    }
    player_payload = {"players": player_rows}
    (raw_dir / "team_seasonal.json").write_text(json.dumps(team_payload), encoding="utf-8")
    (raw_dir / "player_seasonal.json").write_text(json.dumps(player_payload), encoding="utf-8")

    build_seasons(output_root=output_root, start_year=2025, end_year=2025)
    paths = build_story_html_bundle(output_root=output_root, season=2025)

    assert len(paths) == 7
    index_html = (output_root / "stories" / "2025" / "index.html").read_text(encoding="utf-8")
    strategy_html = (output_root / "stories" / "2025" / "strategy-atlas.html").read_text(encoding="utf-8")
    comparison_board_html = (output_root / "stories" / "2025" / "team-comparison-board.html").read_text(encoding="utf-8")
    comparison_wall_html = (output_root / "stories" / "2025" / "team-comparison-wall.html").read_text(encoding="utf-8")
    roster_html = (output_root / "stories" / "2025" / "roster-currents.html").read_text(encoding="utf-8")
    assert "SIS Visual Stories 2025" in index_html
    assert "Team Comparison Board 2025" in index_html
    assert "Patrick Mahomes" in strategy_html or "Strategy Atlas 2025" in strategy_html
    assert "League Comparison Matrix" in comparison_board_html
    assert "Chiefs" in comparison_board_html and "Bills" in comparison_board_html
    assert "Team Comparison Wall 2025" in comparison_wall_html
    assert "air-led" in comparison_wall_html or "balanced" in comparison_wall_html
    assert "Journeyman Player" in roster_html
