from __future__ import annotations

import html
import json
import logging
import os
import random
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

PANDAS_IMPORT_ERROR: Optional[Exception] = None
try:
    import pandas as pd
except Exception as exc:  # pragma: no cover
    pd = None  # type: ignore[assignment]
    PANDAS_IMPORT_ERROR = exc

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://api.provider.internal/nfl/official/trial/v7/en"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data" / "sis"
DEFAULT_LOCAL_SOURCE_ROOT = (
    REPO_ROOT.parent / "nfldictionary" / "nfldictionary.github.io" / "data_archive" / "season_feed" / "v7"
)
PLAYER_SPLITS = ["passing", "rushing", "receiving", "defense"]


@dataclass
class FetchConfig:
    start_year: int
    end_year: int
    season_type: str
    output_root: Path
    base_url: str
    sleep_min: float
    sleep_max: float
    max_retries: int
    include_rosters: bool


class SeasonStatsClient:
    def __init__(self, api_key: str, base_url: str, max_retries: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "bot-sis-pipeline/1.0",
                "x-api-key": api_key,
            }
        )

    def get_json(self, endpoint_path: str) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint_path}"
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt == self.max_retries:
                        response.raise_for_status()
                    backoff = min(30.0, (2 ** (attempt - 1)) + random.uniform(0.0, 0.5))
                    logging.warning(
                        "Retryable response %s for %s (attempt %d/%d), sleeping %.2fs",
                        response.status_code,
                        endpoint_path,
                        attempt,
                        self.max_retries,
                        backoff,
                    )
                    time.sleep(backoff)
                    continue
                if 400 <= response.status_code < 500:
                    response.raise_for_status()

                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise RuntimeError(f"Unexpected payload type for {endpoint_path}: {type(payload)}")
                return payload
            except requests.RequestException as exc:
                status_code = None
                if isinstance(exc, requests.HTTPError) and exc.response is not None:
                    status_code = exc.response.status_code

                if status_code is not None and 400 <= status_code < 500 and status_code != 429:
                    raise RuntimeError(
                        f"Non-retryable response {status_code} for {endpoint_path}: {exc}"
                    ) from exc

                if attempt == self.max_retries:
                    raise RuntimeError(f"Failed request after retries for {endpoint_path}: {exc}") from exc

                backoff = min(30.0, (2 ** (attempt - 1)) + random.uniform(0.0, 0.5))
                logging.warning(
                    "Request error for %s (attempt %d/%d): %s, sleeping %.2fs",
                    endpoint_path,
                    attempt,
                    self.max_retries,
                    exc,
                    backoff,
                )
                time.sleep(backoff)

        raise RuntimeError(f"Unreachable retry loop for {endpoint_path}")


def _require_pandas() -> Any:
    if pd is None:
        raise RuntimeError(
            "pandas/pyarrow are required for this command. "
            f"Original error: {PANDAS_IMPORT_ERROR}"
        )
    return pd


def _year_range(start_year: int, end_year: int) -> range:
    if start_year > end_year:
        raise ValueError("start_year must be <= end_year")
    return range(start_year, end_year + 1)


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_raw_root(source_root: Path) -> Path:
    source_root = source_root.expanduser().resolve()
    raw_root = source_root / "raw"
    return raw_root if raw_root.exists() else source_root


def copy_local_raw_data(
    source_root: Path,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    start_year: int = 2016,
    end_year: int = 2025,
    overwrite: bool = False,
) -> dict[str, Any]:
    source_raw_root = _source_raw_root(source_root)
    if not source_raw_root.exists():
        raise FileNotFoundError(f"Local SIS source root not found: {source_raw_root}")

    output_root = output_root.expanduser().resolve()
    copied_years: list[int] = []
    skipped_years: list[int] = []
    missing_years: list[int] = []
    copied_files = 0

    for year in _year_range(start_year, end_year):
        source_year_dir = source_raw_root / str(year)
        if not source_year_dir.exists():
            missing_years.append(year)
            continue

        target_year_dir = output_root / "raw" / str(year)
        target_year_dir.mkdir(parents=True, exist_ok=True)

        year_copied = False
        for filename in ("team_seasonal.json", "player_seasonal.json", "team_rosters.json"):
            source_file = source_year_dir / filename
            if not source_file.exists():
                continue

            target_file = target_year_dir / filename
            if target_file.exists() and not overwrite:
                continue

            shutil.copy2(source_file, target_file)
            copied_files += 1
            year_copied = True

        if year_copied:
            copied_years.append(year)
        else:
            skipped_years.append(year)

    summary = {
        "mode": "sync-local",
        "generated_at": _timestamp(),
        "source_root": str(source_raw_root),
        "output_root": str(output_root),
        "copied_years": copied_years,
        "skipped_years": skipped_years,
        "missing_years": missing_years,
        "copied_files": copied_files,
        "overwrite": overwrite,
    }
    return summary


def setup_logging(output_root: Path) -> Path:
    logs_dir = output_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"fetch_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    return log_path


def jitter_sleep(min_seconds: float, max_seconds: float) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


def extract_teams(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(payload.get("teams"), list):
        return [team for team in payload["teams"] if isinstance(team, dict)]

    league = payload.get("league")
    if isinstance(league, dict) and isinstance(league.get("teams"), list):
        return [team for team in league["teams"] if isinstance(team, dict)]

    def walk(node: Any) -> list[dict[str, Any]]:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "teams" and isinstance(value, list) and all(isinstance(item, dict) for item in value):
                    return value
                found = walk(value)
                if found:
                    return found
        elif isinstance(node, list):
            for item in node:
                found = walk(item)
                if found:
                    return found
        return []

    return walk(payload)


def normalize_team_identity(team: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": team.get("id"),
        "name": team.get("name"),
        "market": team.get("market"),
        "alias": team.get("alias"),
    }


def fetch_for_season(
    client: SeasonStatsClient,
    cfg: FetchConfig,
    year: int,
) -> tuple[dict[str, Any], dict[str, Any], Optional[dict[str, Any]]]:
    teams_payload = client.get_json("/league/teams.json")
    all_teams = extract_teams(teams_payload)
    if not all_teams:
        raise RuntimeError("Could not extract teams from /league/teams.json")

    teams = [team for team in all_teams if str(team.get("alias") or "").upper() != "TBD"]

    team_rows: list[dict[str, Any]] = []
    player_rows: list[dict[str, Any]] = []
    roster_rows: list[dict[str, Any]] = []

    for idx, team in enumerate(teams, start=1):
        team_id = str(team.get("id") or "").strip()
        if not team_id:
            continue

        identity = normalize_team_identity(team)
        endpoint = f"/seasons/{year}/{cfg.season_type}/teams/{team_id}/statistics.json"

        logging.info(
            "Season %s %s | team %d/%d %s",
            year,
            cfg.season_type,
            idx,
            len(teams),
            identity.get("alias") or team_id,
        )

        row_base = {
            "team_id": identity["id"],
            "team_alias": identity["alias"],
            "team_name": identity["name"],
            "team_market": identity["market"],
            "endpoint": endpoint,
            "fetched_at": _timestamp(),
        }

        try:
            payload = client.get_json(endpoint)
            team_rows.append({**row_base, "status": "ok", "response": payload})

            players = payload.get("players")
            if isinstance(players, list):
                for player in players:
                    if isinstance(player, dict):
                        player_rows.append(
                            {
                                "team_id": identity["id"],
                                "team_alias": identity["alias"],
                                "team_name": identity["name"],
                                "player": player,
                            }
                        )
        except Exception as exc:  # noqa: BLE001
            logging.exception("Failed %s %s", year, identity.get("alias") or team_id)
            team_rows.append({**row_base, "status": "error", "error": str(exc)})

        if cfg.include_rosters:
            roster_endpoint = f"/seasons/{year}/{cfg.season_type}/teams/{team_id}/roster.json"
            try:
                roster_payload = client.get_json(roster_endpoint)
                roster_rows.append(
                    {
                        **row_base,
                        "endpoint": roster_endpoint,
                        "status": "ok",
                        "response": roster_payload,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                logging.exception("Roster fetch failed %s %s", year, identity.get("alias") or team_id)
                roster_rows.append(
                    {
                        **row_base,
                        "endpoint": roster_endpoint,
                        "status": "error",
                        "error": str(exc),
                    }
                )

        jitter_sleep(cfg.sleep_min, cfg.sleep_max)

    team_payload = {
        "season": year,
        "season_type": cfg.season_type,
        "source": "season_feed_v7",
        "fetched_at": _timestamp(),
        "teams": team_rows,
    }
    player_payload = {
        "season": year,
        "season_type": cfg.season_type,
        "source": "season_feed_v7",
        "fetched_at": _timestamp(),
        "players": player_rows,
    }
    roster_payload = None
    if cfg.include_rosters:
        roster_payload = {
            "season": year,
            "season_type": cfg.season_type,
            "source": "season_feed_v7",
            "fetched_at": _timestamp(),
            "teams": roster_rows,
        }

    return team_payload, player_payload, roster_payload


def fetch_remote_raw_data(
    start_year: int = 2016,
    end_year: int = 2025,
    season_type: str = "REG",
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    base_url: str = DEFAULT_BASE_URL,
    sleep_min: float = 0.3,
    sleep_max: float = 0.8,
    max_retries: int = 5,
    include_rosters: bool = False,
) -> dict[str, Any]:
    api_key = os.environ.get("STATS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("STATS_API_KEY is required for remote fetch")
    if sleep_min <= 0 or sleep_max <= 0 or sleep_min > sleep_max:
        raise ValueError("sleep bounds must satisfy 0 < sleep_min <= sleep_max")
    if max_retries < 1:
        raise ValueError("max_retries must be >= 1")

    output_root = output_root.expanduser().resolve()
    log_path = setup_logging(output_root)
    cfg = FetchConfig(
        start_year=start_year,
        end_year=end_year,
        season_type=season_type,
        output_root=output_root,
        base_url=base_url,
        sleep_min=sleep_min,
        sleep_max=sleep_max,
        max_retries=max_retries,
        include_rosters=include_rosters,
    )
    client = SeasonStatsClient(api_key=api_key, base_url=base_url, max_retries=max_retries)

    fetched_years: list[int] = []
    for year in _year_range(start_year, end_year):
        raw_dir = output_root / "raw" / str(year)
        raw_dir.mkdir(parents=True, exist_ok=True)
        team_payload, player_payload, roster_payload = fetch_for_season(client, cfg, year)
        write_json(raw_dir / "team_seasonal.json", team_payload)
        write_json(raw_dir / "player_seasonal.json", player_payload)
        if roster_payload is not None:
            write_json(raw_dir / "team_rosters.json", roster_payload)
        fetched_years.append(year)

    return {
        "mode": "fetch",
        "generated_at": _timestamp(),
        "output_root": str(output_root),
        "fetched_years": fetched_years,
        "log_path": str(log_path),
        "season_type": season_type,
        "base_url": base_url,
        "include_rosters": include_rosters,
    }


def flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}

    if isinstance(obj, dict):
        for key, value in obj.items():
            key_clean = str(key).strip().lower().replace(" ", "_")
            next_prefix = f"{prefix}_{key_clean}" if prefix else key_clean
            out.update(flatten(value, next_prefix))
        return out

    if isinstance(obj, list):
        out[prefix] = json.dumps(obj, ensure_ascii=False)
        return out

    out[prefix] = obj
    return out


def maybe_numeric(col: Any) -> Any:
    pandas = _require_pandas()
    if col.dtype != object:
        return col

    cleaned = (
        col.astype(str)
        .str.strip()
        .replace({"": pandas.NA, "nan": pandas.NA, "None": pandas.NA, "null": pandas.NA, "--": pandas.NA})
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace("+", "", regex=False)
    )

    numeric = pandas.to_numeric(cleaned, errors="coerce")
    non_null = cleaned.notna().sum()
    if non_null == 0:
        return col
    if numeric.notna().sum() / non_null >= 0.85:
        return numeric
    return col


def normalize_df(
    df: Any,
    season: int,
    season_type: str,
    source: str,
    fetched_at: str,
) -> Any:
    pandas = _require_pandas()
    out = df.copy()

    renamed = []
    counts: dict[str, int] = {}
    for column in out.columns:
        name = str(column).strip().lower()
        name = name.replace(" ", "_").replace("-", "_").replace("/", "_")
        name = "".join(char for char in name if char.isalnum() or char == "_")
        while "__" in name:
            name = name.replace("__", "_")
        name = name.strip("_") or "col"
        idx = counts.get(name, 0)
        renamed.append(name if idx == 0 else f"{name}_{idx + 1}")
        counts[name] = idx + 1
    out.columns = renamed

    out = pandas.DataFrame({column: maybe_numeric(out[column]) for column in out.columns}, index=out.index)
    out["season"] = season
    out["season_type"] = season_type
    out["source"] = source
    out["fetched_at"] = fetched_at
    front = ["season", "season_type", "source", "fetched_at"]
    rest = [column for column in out.columns if column not in front]
    return out[front + rest]


def build_team_df(team_raw: dict[str, Any]) -> Any:
    pandas = _require_pandas()
    rows = []
    for record in team_raw.get("teams", []):
        if record.get("status") != "ok" or not isinstance(record.get("response"), dict):
            continue

        response = record["response"]
        row = {
            "team_id": response.get("id") or record.get("team_id"),
            "team_alias": response.get("alias") or record.get("team_alias"),
            "team_name": response.get("name") or record.get("team_name"),
            "team_market": response.get("market") or record.get("team_market"),
            "source_endpoint": record.get("endpoint"),
        }

        stats = response.get("statistics")
        if isinstance(stats, dict):
            row.update(flatten(stats, "stats"))

        record_block = response.get("record")
        if isinstance(record_block, dict):
            row.update(flatten(record_block, "record"))

        ranks = response.get("ranks")
        if isinstance(ranks, dict):
            row.update(flatten(ranks, "ranks"))

        rows.append(row)

    return pandas.DataFrame(rows)


def build_player_df(player_raw: dict[str, Any]) -> Any:
    pandas = _require_pandas()
    rows = []
    for record in player_raw.get("players", []):
        player = record.get("player")
        if not isinstance(player, dict):
            continue

        row = {
            "team_id": record.get("team_id"),
            "team_alias": record.get("team_alias"),
            "team_name": record.get("team_name"),
            "player_id": player.get("id"),
            "player_name": player.get("name"),
            "player_first_name": player.get("first_name"),
            "player_last_name": player.get("last_name"),
            "position": player.get("position"),
            "jersey": player.get("jersey"),
            "status": player.get("status"),
            "player_sr_id": player.get("sr_id"),
        }

        stats = player.get("statistics")
        if isinstance(stats, dict):
            row.update(flatten(stats, "stats"))

        record_block = player.get("record")
        if isinstance(record_block, dict):
            row.update(flatten(record_block, "record"))

        consumed = {
            "id",
            "name",
            "first_name",
            "last_name",
            "position",
            "jersey",
            "status",
            "sr_id",
            "statistics",
            "record",
        }
        for key, value in player.items():
            if key in consumed:
                continue
            key_clean = str(key).strip().lower().replace(" ", "_")
            if isinstance(value, dict):
                row.update(flatten(value, f"stats_{key_clean}"))
            elif isinstance(value, list):
                row[f"player_{key_clean}"] = json.dumps(value, ensure_ascii=False)
            else:
                row[f"player_{key_clean}"] = value

        rows.append(row)

    return pandas.DataFrame(rows)


def write_player_splits(player_df: Any, parquet_dir: Path) -> list[Path]:
    outputs: list[Path] = []
    if player_df.empty:
        return outputs

    common_columns = [
        column
        for column in [
            "season",
            "season_type",
            "source",
            "fetched_at",
            "team_id",
            "team_alias",
            "team_name",
            "player_id",
            "player_name",
            "player_first_name",
            "player_last_name",
            "position",
            "jersey",
            "status",
        ]
        if column in player_df.columns
    ]

    for split in PLAYER_SPLITS:
        prefix = f"stats_{split}_"
        split_columns = [column for column in player_df.columns if column.startswith(prefix)]
        if not split_columns:
            continue

        split_df = player_df[common_columns + split_columns].copy()
        split_df = split_df[split_df[split_columns].notna().any(axis=1)]
        if split_df.empty:
            continue

        output_path = parquet_dir / f"player_{split}.parquet"
        split_df.to_parquet(output_path, index=False)
        outputs.append(output_path)

    return outputs


def build_seasons(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    start_year: int = 2016,
    end_year: int = 2025,
    season_type: str = "REG",
) -> list[dict[str, Any]]:
    _require_pandas()
    output_root = output_root.expanduser().resolve()
    summaries: list[dict[str, Any]] = []

    for year in _year_range(start_year, end_year):
        raw_dir = output_root / "raw" / str(year)
        parquet_dir = output_root / "parquet" / str(year)
        parquet_dir.mkdir(parents=True, exist_ok=True)

        team_raw_path = raw_dir / "team_seasonal.json"
        player_raw_path = raw_dir / "player_seasonal.json"

        if not team_raw_path.exists() or not player_raw_path.exists():
            summaries.append(
                {
                    "season": year,
                    "status": "skipped",
                    "reason": "missing raw files",
                    "team_raw_path": str(team_raw_path),
                    "player_raw_path": str(player_raw_path),
                }
            )
            continue

        team_raw = read_json(team_raw_path)
        player_raw = read_json(player_raw_path)
        fetched_at = str(team_raw.get("fetched_at") or _timestamp())
        source = str(team_raw.get("source") or "season_feed_v7")

        team_df = normalize_df(build_team_df(team_raw), year, season_type, source, fetched_at)
        player_df = normalize_df(build_player_df(player_raw), year, season_type, source, fetched_at)

        team_path = parquet_dir / "team_seasonal.parquet"
        player_path = parquet_dir / "player_seasonal.parquet"
        team_df.to_parquet(team_path, index=False)
        player_df.to_parquet(player_path, index=False)
        split_paths = write_player_splits(player_df, parquet_dir)

        summaries.append(
            {
                "season": year,
                "status": "ok",
                "team_rows": int(len(team_df)),
                "player_rows": int(len(player_df)),
                "outputs": [str(team_path), str(player_path), *[str(path) for path in split_paths]],
            }
        )

    return summaries


def validate_required_file(
    path: Path,
    key_fields: list[str],
    metric_prefixes: tuple[str, ...],
    metric_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    pandas = _require_pandas()
    result: dict[str, Any] = {
        "file": path.name,
        "exists": path.exists(),
        "row_count": 0,
        "missing_key_fields": [],
        "has_metric_columns": False,
        "metric_columns_count": 0,
        "ok": False,
    }

    if not path.exists():
        return result

    try:
        df = pandas.read_parquet(path)
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)
        return result

    result["row_count"] = int(len(df))
    result["missing_key_fields"] = [field for field in key_fields if field not in df.columns]
    metric_columns = [
        column
        for column in df.columns
        if column.startswith(metric_prefixes) or column in metric_fields
    ]
    result["has_metric_columns"] = len(metric_columns) > 0
    result["metric_columns_count"] = len(metric_columns)
    result["columns"] = list(df.columns)
    result["ok"] = result["row_count"] > 0 and not result["missing_key_fields"] and result["has_metric_columns"]
    return result


def validate_seasons(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    start_year: int = 2016,
    end_year: int = 2025,
    season_type: str = "REG",
) -> list[dict[str, Any]]:
    _require_pandas()
    output_root = output_root.expanduser().resolve()
    years = list(_year_range(start_year, end_year))
    baseline_team_columns: Optional[set[str]] = None
    baseline_player_columns: Optional[set[str]] = None
    summaries: list[dict[str, Any]] = []

    for year in years:
        parquet_dir = output_root / "parquet" / str(year)
        parquet_dir.mkdir(parents=True, exist_ok=True)

        team_result = validate_required_file(
            parquet_dir / "team_seasonal.parquet",
            ["team_id", "season", "season_type", "source", "fetched_at"],
            metric_prefixes=("stats_", "record_", "ranks_"),
        )
        player_result = validate_required_file(
            parquet_dir / "player_seasonal.parquet",
            ["player_id", "team_id", "season", "season_type", "source", "fetched_at"],
            metric_prefixes=("stats_", "record_"),
            metric_fields=("player_games_played", "player_games_started"),
        )

        split_results = []
        for split_name in ("player_passing.parquet", "player_rushing.parquet", "player_receiving.parquet", "player_defense.parquet"):
            split_path = parquet_dir / split_name
            if split_path.exists():
                split_results.append(
                    validate_required_file(
                        split_path,
                        ["player_id", "team_id", "season", "season_type", "source", "fetched_at"],
                        metric_prefixes=("stats_", "record_"),
                    )
                )

        schema_consistency = {
            "team_columns_consistent": True,
            "player_columns_consistent": True,
            "team_schema_diff": {"missing_from_current": [], "extra_in_current": []},
            "player_schema_diff": {"missing_from_current": [], "extra_in_current": []},
        }

        if team_result.get("exists") and "columns" in team_result:
            current_team_columns = set(team_result["columns"])
            if baseline_team_columns is None:
                baseline_team_columns = current_team_columns
            else:
                missing = sorted(baseline_team_columns - current_team_columns)
                extra = sorted(current_team_columns - baseline_team_columns)
                if missing or extra:
                    schema_consistency["team_columns_consistent"] = False
                    schema_consistency["team_schema_diff"] = {
                        "missing_from_current": missing,
                        "extra_in_current": extra,
                    }

        if player_result.get("exists") and "columns" in player_result:
            current_player_columns = set(player_result["columns"])
            if baseline_player_columns is None:
                baseline_player_columns = current_player_columns
            else:
                missing = sorted(baseline_player_columns - current_player_columns)
                extra = sorted(current_player_columns - baseline_player_columns)
                if missing or extra:
                    schema_consistency["player_columns_consistent"] = False
                    schema_consistency["player_schema_diff"] = {
                        "missing_from_current": missing,
                        "extra_in_current": extra,
                    }

        validation_payload = {
            "season": year,
            "season_type": season_type,
            "validated_at": _timestamp(),
            "team": team_result,
            "player": player_result,
            "player_splits": split_results,
            "schema_consistency": schema_consistency,
            "ok": bool(team_result["ok"] and player_result["ok"]),
        }
        write_json(parquet_dir / "_validation.json", validation_payload)
        summaries.append(validation_payload)

    return summaries


def write_manifest(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    start_year: int = 2016,
    end_year: int = 2025,
    season_type: str = "REG",
    source_mode: str = "manual",
    source_root: Optional[Path] = None,
    sync_summary: Optional[dict[str, Any]] = None,
    fetch_summary: Optional[dict[str, Any]] = None,
    build_summary: Optional[list[dict[str, Any]]] = None,
    validation_summary: Optional[list[dict[str, Any]]] = None,
) -> Path:
    output_root = output_root.expanduser().resolve()
    manifest_path = output_root / "manifest.json"
    payload = {
        "generated_at": _timestamp(),
        "output_root": str(output_root),
        "start_year": start_year,
        "end_year": end_year,
        "season_type": season_type,
        "source_mode": source_mode,
        "source_root": str(source_root.expanduser().resolve()) if source_root is not None else None,
        "sync_summary": sync_summary,
        "fetch_summary": fetch_summary,
        "build_summary": build_summary,
        "validation_summary": validation_summary,
    }
    write_json(manifest_path, payload)
    return manifest_path


def _to_number(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number != number:
        return 0.0
    return number


def _format_number(value: Any) -> str:
    number = _to_number(value)
    if float(number).is_integer():
        return f"{int(number):,}"
    return f"{number:,.1f}"


def _metric_series(df: Any, column: str) -> Any:
    pandas = _require_pandas()
    if column not in df.columns:
        return pandas.Series(dtype="float64")
    return pandas.to_numeric(df[column], errors="coerce")


def _missing_count(df: Any, column: str) -> int:
    if column not in df.columns:
        return -1
    return int(df[column].isna().sum())


def _duplicate_count(df: Any, column: str) -> int:
    if column not in df.columns:
        return -1
    return int(df[column].duplicated().sum())


def _multi_team_player_count(df: Any) -> int:
    if "player_id" not in df.columns or "team_alias" not in df.columns:
        return -1
    grouped = (
        df[["player_id", "team_alias"]]
        .dropna(subset=["player_id"])
        .groupby("player_id")["team_alias"]
        .nunique()
    )
    return int((grouped > 1).sum())


def _top_metric_items(
    df: Any,
    metric: str,
    label_fields: list[str],
    secondary_fields: list[str],
    limit: int,
) -> list[dict[str, Any]]:
    pandas = _require_pandas()
    if metric not in df.columns:
        return []

    working = df.copy()
    working[metric] = pandas.to_numeric(working[metric], errors="coerce")
    working = working.dropna(subset=[metric])
    if working.empty:
        return []

    rows = []
    for _, row in working.sort_values(metric, ascending=False).head(limit).iterrows():
        label = " ".join(
            str(row[field]).strip()
            for field in label_fields
            if field in working.columns and pandas.notna(row[field]) and str(row[field]).strip()
        )
        secondary = " · ".join(
            str(row[field]).strip()
            for field in secondary_fields
            if field in working.columns and pandas.notna(row[field]) and str(row[field]).strip()
        )
        rows.append(
            {
                "label": label or "Unknown",
                "secondary": secondary,
                "value": _to_number(row[metric]),
            }
        )
    return rows


def _preview_rows(df: Any, columns: list[str], limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    present_columns = [column for column in columns if column in df.columns]
    for _, row in df[present_columns].head(limit).iterrows():
        rows.append({column: row[column] for column in present_columns})
    return rows


def _render_chart(title: str, items: list[dict[str, Any]], accent: str) -> str:
    if not items:
        return (
            '<section class="panel chart-panel">'
            f"<h3>{html.escape(title)}</h3>"
            '<p class="empty">No rows found for this metric.</p>'
            "</section>"
        )

    max_value = max(item["value"] for item in items) or 1.0
    rows = []
    for item in items:
        width = max(8.0, (item["value"] / max_value) * 100.0)
        secondary = f'<span class="metric-secondary">{html.escape(item["secondary"])}</span>' if item["secondary"] else ""
        rows.append(
            "<div class=\"metric-row\">"
            "<div class=\"metric-head\">"
            f"<div class=\"metric-label\">{html.escape(item['label'])}{secondary}</div>"
            f"<div class=\"metric-value\">{_format_number(item['value'])}</div>"
            "</div>"
            "<div class=\"metric-track\">"
            f"<div class=\"metric-fill {accent}\" style=\"width:{width:.2f}%\"></div>"
            "</div>"
            "</div>"
        )

    return (
        '<section class="panel chart-panel">'
        f"<h3>{html.escape(title)}</h3>"
        + "".join(rows)
        + "</section>"
    )


def _render_table(title: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return (
            '<section class="panel table-panel">'
            f"<h3>{html.escape(title)}</h3>"
            '<p class="empty">No rows available.</p>'
            "</section>"
        )

    columns = list(rows[0].keys())
    head = "".join(f"<th>{html.escape(str(column))}</th>" for column in columns)
    body_rows = []
    for row in rows:
        cells = []
        for column in columns:
            value = row[column]
            if isinstance(value, (int, float)):
                rendered = _format_number(value)
            else:
                rendered = str(value)
            cells.append(f"<td>{html.escape(rendered)}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    return (
        '<section class="panel table-panel">'
        f"<h3>{html.escape(title)}</h3>"
        '<div class="table-wrap"><table><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table></div></section>"
    )


def _render_stat_cards(stats: list[dict[str, str]]) -> str:
    cards = []
    for stat in stats:
        cards.append(
            '<article class="stat-card">'
            f'<div class="stat-label">{html.escape(stat["label"])}</div>'
            f'<div class="stat-value">{html.escape(stat["value"])}</div>'
            "</article>"
        )
    return '<section class="stat-grid">' + "".join(cards) + "</section>"


def build_html_validation_report(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    season: int = 2025,
    output_path: Optional[Path] = None,
    limit: int = 10,
) -> Path:
    pandas = _require_pandas()
    output_root = output_root.expanduser().resolve()
    parquet_dir = output_root / "parquet" / str(season)
    if not parquet_dir.exists():
        raise FileNotFoundError(f"Parquet directory not found: {parquet_dir}")

    team_df = pandas.read_parquet(parquet_dir / "team_seasonal.parquet")
    player_df = pandas.read_parquet(parquet_dir / "player_seasonal.parquet")

    split_names = [
        "player_passing.parquet",
        "player_rushing.parquet",
        "player_receiving.parquet",
        "player_defense.parquet",
    ]
    split_frames: dict[str, Any] = {}
    for name in split_names:
        path = parquet_dir / name
        if path.exists():
            split_frames[name] = pandas.read_parquet(path)

    validation_path = parquet_dir / "_validation.json"
    validation_payload = read_json(validation_path) if validation_path.exists() else {}
    split_validation_map = {
        item.get("file"): item
        for item in validation_payload.get("player_splits", [])
        if isinstance(item, dict) and item.get("file")
    }

    stats = [
        {"label": "Season", "value": str(season)},
        {"label": "Team Rows", "value": _format_number(len(team_df))},
        {"label": "Player Rows", "value": _format_number(len(player_df))},
        {"label": "Unique Teams", "value": _format_number(team_df["team_alias"].nunique() if "team_alias" in team_df.columns else 0)},
        {"label": "Unique Players", "value": _format_number(player_df["player_id"].nunique() if "player_id" in player_df.columns else 0)},
        {"label": "Validation", "value": "PASS" if validation_payload.get("ok") else "CHECK"},
    ]

    sanity_rows = [
        {
            "check": "team_id missing",
            "value": _format_number(_missing_count(team_df, "team_id")),
        },
        {
            "check": "team_id duplicates",
            "value": _format_number(_duplicate_count(team_df, "team_id")),
        },
        {
            "check": "player_id missing",
            "value": _format_number(_missing_count(player_df, "player_id")),
        },
        {
            "check": "players on multiple teams",
            "value": _format_number(_multi_team_player_count(player_df)),
        },
        {
            "check": "split parquet files",
            "value": _format_number(len(split_frames)),
        },
        {
            "check": "report generated",
            "value": _timestamp().split("T")[0],
        },
    ]

    table_rows = [
        {
            "file": "team_seasonal.parquet",
            "rows": len(team_df),
            "cols": len(team_df.columns),
            "ok": "yes" if validation_payload.get("team", {}).get("ok") else "no",
            "metric_cols": validation_payload.get("team", {}).get("metric_columns_count", 0),
        },
        {
            "file": "player_seasonal.parquet",
            "rows": len(player_df),
            "cols": len(player_df.columns),
            "ok": "yes" if validation_payload.get("player", {}).get("ok") else "no",
            "metric_cols": validation_payload.get("player", {}).get("metric_columns_count", 0),
        },
    ]
    for name in split_names:
        if name not in split_frames:
            continue
        split_df = split_frames[name]
        split_validation = split_validation_map.get(name, {})
        table_rows.append(
            {
                "file": name,
                "rows": len(split_df),
                "cols": len(split_df.columns),
                "ok": "yes" if split_validation.get("ok") else "no",
                "metric_cols": split_validation.get("metric_columns_count", 0),
            }
        )

    team_snapshot = team_df.sort_values("record_passing_yards", ascending=False) if "record_passing_yards" in team_df.columns else team_df
    player_snapshot = split_frames.get("player_passing.parquet", player_df)
    if "stats_passing_yards" in player_snapshot.columns:
        player_snapshot = player_snapshot.sort_values("stats_passing_yards", ascending=False)

    charts = [
        _render_chart(
            "Top Team Passing Yards",
            _top_metric_items(team_df, "record_passing_yards", ["team_name"], ["team_alias"], limit),
            "accent-sunrise",
        ),
        _render_chart(
            "Top Team Rushing Yards",
            _top_metric_items(team_df, "record_rushing_yards", ["team_name"], ["team_alias"], limit),
            "accent-lagoon",
        ),
        _render_chart(
            "Top Passers",
            _top_metric_items(split_frames.get("player_passing.parquet", player_df), "stats_passing_yards", ["player_name"], ["team_alias", "position"], limit),
            "accent-coral",
        ),
        _render_chart(
            "Top Rushers",
            _top_metric_items(split_frames.get("player_rushing.parquet", player_df), "stats_rushing_yards", ["player_name"], ["team_alias", "position"], limit),
            "accent-mint",
        ),
        _render_chart(
            "Top Receivers",
            _top_metric_items(split_frames.get("player_receiving.parquet", player_df), "stats_receiving_yards", ["player_name"], ["team_alias", "position"], limit),
            "accent-iris",
        ),
        _render_chart(
            "Top Tacklers",
            _top_metric_items(split_frames.get("player_defense.parquet", player_df), "stats_defense_combined", ["player_name"], ["team_alias", "position"], limit),
            "accent-ember",
        ),
    ]

    preview_sections = [
        _render_table(
            "Team Snapshot",
            _preview_rows(
                team_snapshot,
                [
                    "team_alias",
                    "team_name",
                    "record_games_played",
                    "record_passing_yards",
                    "record_rushing_yards",
                    "record_receiving_yards",
                    "record_defense_sacks",
                ],
                8,
            ),
        ),
        _render_table(
            "Player Snapshot",
            _preview_rows(
                player_snapshot,
                [
                    "team_alias",
                    "player_name",
                    "position",
                    "stats_passing_yards",
                    "stats_passing_touchdowns",
                    "stats_rushing_yards",
                ],
                8,
            ),
        ),
        _render_table("Sanity Checks", sanity_rows),
        _render_table("Parquet Overview", table_rows),
    ]

    report_title = f"SIS Extraction Visual Check · {season}"
    source_text = str(Path("data") / "sis" / "parquet" / str(season))
    html_text = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(report_title)}</title>
  <style>
    :root {{
      --ink: #112031;
      --muted: #5e6b78;
      --paper: #f7f3ea;
      --panel: rgba(255, 255, 255, 0.74);
      --line: rgba(17, 32, 49, 0.12);
      --sunrise: linear-gradient(90deg, #ff8a5b, #ffb067);
      --lagoon: linear-gradient(90deg, #137c8b, #5ed6d1);
      --coral: linear-gradient(90deg, #ff5d73, #ff9165);
      --mint: linear-gradient(90deg, #00a676, #7be495);
      --iris: linear-gradient(90deg, #4c6ef5, #7b8cff);
      --ember: linear-gradient(90deg, #9a3412, #f97316);
      --shadow: 0 18px 50px rgba(17, 32, 49, 0.12);
      --radius: 22px;
      --font: "Avenir Next", "Pretendard", "Apple SD Gothic Neo", "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--font);
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(255, 176, 103, 0.34), transparent 34%),
        radial-gradient(circle at top right, rgba(94, 214, 209, 0.28), transparent 32%),
        linear-gradient(180deg, #f6efe2 0%, #eef6f5 54%, #f6efe2 100%);
    }}
    .page {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 36px 0 56px;
    }}
    .hero {{
      padding: 28px;
      border-radius: calc(var(--radius) + 6px);
      background:
        linear-gradient(135deg, rgba(255,255,255,0.85), rgba(255,255,255,0.58)),
        linear-gradient(135deg, rgba(19,124,139,0.10), rgba(255,138,91,0.12));
      box-shadow: var(--shadow);
      border: 1px solid rgba(255,255,255,0.5);
      backdrop-filter: blur(12px);
    }}
    .eyebrow {{
      display: inline-flex;
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #7c2d12;
      background: rgba(255, 176, 103, 0.22);
    }}
    h1 {{
      margin: 16px 0 10px;
      font-size: clamp(32px, 6vw, 54px);
      line-height: 0.98;
      letter-spacing: -0.04em;
    }}
    .hero p {{
      margin: 0;
      max-width: 760px;
      font-size: 16px;
      line-height: 1.6;
      color: var(--muted);
    }}
    .path {{
      margin-top: 14px;
      font-size: 13px;
      color: #234;
      word-break: break-all;
    }}
    .stat-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 14px;
      margin-top: 22px;
    }}
    .stat-card, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }}
    .stat-card {{
      padding: 18px 18px 16px;
    }}
    .stat-label {{
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 10px;
    }}
    .stat-value {{
      font-size: 28px;
      font-weight: 800;
      letter-spacing: -0.04em;
    }}
    .section-title {{
      margin: 34px 0 14px;
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #264653;
    }}
    .chart-grid, .table-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(310px, 1fr));
      gap: 18px;
    }}
    .panel {{
      padding: 20px;
    }}
    .panel h3 {{
      margin: 0 0 18px;
      font-size: 18px;
      letter-spacing: -0.02em;
    }}
    .metric-row + .metric-row {{
      margin-top: 14px;
    }}
    .metric-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
      margin-bottom: 8px;
    }}
    .metric-label {{
      display: flex;
      flex-direction: column;
      gap: 2px;
      font-weight: 700;
    }}
    .metric-secondary {{
      font-size: 12px;
      color: var(--muted);
      font-weight: 600;
    }}
    .metric-value {{
      font-variant-numeric: tabular-nums;
      font-weight: 800;
    }}
    .metric-track {{
      width: 100%;
      height: 12px;
      background: rgba(17, 32, 49, 0.08);
      border-radius: 999px;
      overflow: hidden;
    }}
    .metric-fill {{
      height: 100%;
      border-radius: inherit;
    }}
    .accent-sunrise {{ background: var(--sunrise); }}
    .accent-lagoon {{ background: var(--lagoon); }}
    .accent-coral {{ background: var(--coral); }}
    .accent-mint {{ background: var(--mint); }}
    .accent-iris {{ background: var(--iris); }}
    .accent-ember {{ background: var(--ember); }}
    .table-wrap {{
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      padding: 10px 10px;
      text-align: left;
      border-bottom: 1px solid var(--line);
      white-space: nowrap;
    }}
    th {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    tr:last-child td {{
      border-bottom: 0;
    }}
    .empty {{
      color: var(--muted);
      margin: 0;
    }}
    @media (max-width: 720px) {{
      .page {{
        width: min(100% - 20px, 1180px);
        padding-top: 20px;
      }}
      .hero {{
        padding: 20px;
      }}
      .panel {{
        padding: 16px;
      }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="eyebrow">Parquet Validation HTML</div>
      <h1>{html.escape(report_title)}</h1>
      <p>
        Season parquet outputs were rendered into a self-contained visual check page so we can confirm row counts,
        schema coverage, leaderboards, and obvious extraction anomalies without opening notebooks.
      </p>
      <div class="path">Source parquet: {html.escape(source_text)}</div>
      {_render_stat_cards(stats)}
    </section>

    <div class="section-title">Leaderboards</div>
    <section class="chart-grid">
      {"".join(charts)}
    </section>

    <div class="section-title">Validation Tables</div>
    <section class="table-grid">
      {"".join(preview_sections)}
    </section>
  </main>
</body>
</html>
"""

    target_path = output_path.expanduser().resolve() if output_path is not None else output_root / "reports" / f"sis_validation_{season}.html"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(html_text, encoding="utf-8")
    return target_path
