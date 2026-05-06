from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import robotparser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from schema import MANIFEST_FILENAMES
from shared import (
    RuntimeConfig,
    append_log,
    display_local_path,
    display_repo_path,
    load_json,
    safe_slug_from_url,
    sha256_bytes,
    update_pipeline_manifest,
    write_json,
    write_jsonl,
)

RESERVED_PATHS = {
    "/",
    "/about",
    "/analytics",
    "/coaches",
    "/degrees",
    "/mcp",
    "/teams",
}


def run_crawl(config: RuntimeConfig) -> dict[str, Any]:
    log_path = config.run_log_dir / f"{config.run_id}-crawl.log"
    started_at = datetime.now().isoformat(timespec="seconds")
    append_log(log_path, f"crawl started for {config.source_base_url}")

    rp = robotparser.RobotFileParser()
    robots_url = urljoin(config.source_base_url, "/robots.txt")
    robots_checked = False
    try:
        rp.set_url(robots_url)
        rp.read()
        robots_checked = True
    except Exception as exc:
        append_log(log_path, f"robots.txt check failed: {exc}")

    directory_urls = discover_directory_urls(config)
    team_urls = [urljoin(config.source_base_url, "/teams")]
    raw_records: list[dict[str, Any]] = []
    failed_urls: list[str] = []
    skipped_urls: list[str] = []

    for url in directory_urls + team_urls:
        status = fetch_snapshot(config, url, raw_records, skipped_urls, failed_urls, log_path)
        if config.verbose:
            append_log(log_path, f"fetched {url} -> {status}")

    coach_profile_urls = discover_coach_profile_urls(raw_records, config.max_coaches)
    for url in coach_profile_urls:
        status = fetch_snapshot(config, url, raw_records, skipped_urls, failed_urls, log_path)
        if config.verbose:
            append_log(log_path, f"fetched profile {url} -> {status}")

    if not config.dry_run:
        metadata_path = config.cache_dir / "response-metadata.jsonl"
        existing_metadata = []
        if metadata_path.exists():
            existing_metadata = [
                json.loads(line)
                for line in metadata_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        deduped = {(row["url"], row["contentHash"]): row for row in existing_metadata}
        for row in raw_records:
            deduped[(row["url"], row["contentHash"])] = row
        write_jsonl(metadata_path, deduped.values())

    manifest = {
        "runId": config.run_id,
        "sourceBaseUrl": config.source_base_url,
        "robotsTxtChecked": robots_checked,
        "startedAt": started_at,
        "completedAt": datetime.now().isoformat(timespec="seconds"),
        "directoryPagesDiscovered": len(directory_urls),
        "directoryPagesFetched": sum(1 for row in raw_records if row.get("kind") == "directory"),
        "coachProfileUrlsDiscovered": len(coach_profile_urls),
        "coachProfilePagesFetched": sum(1 for row in raw_records if row.get("kind") == "profile"),
        "teamPagesFetched": sum(1 for row in raw_records if row.get("kind") == "teams"),
        "failedUrls": failed_urls,
        "skippedUrls": skipped_urls,
        "rawSnapshotDir": display_local_path(config, config.raw_snapshot_run_dir),
        "cacheDir": display_local_path(config, config.cache_dir),
        "userAgent": config.user_agent,
        "concurrency": config.concurrency,
        "requestDelayMs": config.request_delay_ms,
        "retryLimit": config.retry_limit,
    }
    if not config.dry_run:
        write_json(config.manifests_dir / MANIFEST_FILENAMES["crawl"], manifest)
        update_pipeline_manifest(
            config,
            {
                "crawlManifestPath": display_repo_path(config, config.manifests_dir / MANIFEST_FILENAMES["crawl"]),
                "crawlSummary": {
                    "directoryPagesFetched": manifest["directoryPagesFetched"],
                    "coachProfilePagesFetched": manifest["coachProfilePagesFetched"],
                    "teamPagesFetched": manifest["teamPagesFetched"],
                    "failedUrls": len(failed_urls),
                },
            },
        )
    append_log(log_path, "crawl completed")
    return manifest


def discover_directory_urls(config: RuntimeConfig) -> list[str]:
    urls = [urljoin(config.source_base_url, "/coaches")]
    for page_number in range(2, config.max_pages + 1):
        urls.append(urljoin(config.source_base_url, f"/coaches/page/{page_number}"))
    return urls


def fetch_snapshot(
    config: RuntimeConfig,
    url: str,
    raw_records: list[dict[str, Any]],
    skipped_urls: list[str],
    failed_urls: list[str],
    log_path: Path,
) -> int:
    cache_index = load_json(config.cache_dir / "resume-checkpoint.json", {}) or {}
    if config.resume and url in cache_index:
        skipped_urls.append(url)
        return 304

    if config.dry_run:
        skipped_urls.append(url)
        return 0

    request = Request(url, headers={"User-Agent": config.user_agent})
    try:
        with urlopen(request, timeout=config.timeout_ms / 1000) as response:
            status = getattr(response, "status", 200)
            payload = response.read()
            fetched_at = datetime.now().isoformat(timespec="seconds")
            snapshot_path = snapshot_path_for_url(config, url)
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_bytes(payload)
            row = {
                "url": url,
                "statusCode": status,
                "contentHash": sha256_bytes(payload),
                "fetchedAt": fetched_at,
                "snapshotPath": str(snapshot_path),
                "kind": classify_url_kind(url),
            }
            raw_records.append(row)
            cache_index[url] = row
            write_json(config.cache_dir / "resume-checkpoint.json", cache_index)
            time.sleep(config.request_delay_ms / 1000)
            return status
    except Exception as exc:
        failed_urls.append(url)
        append_log(log_path, f"fetch failed for {url}: {exc}")
        return 500


def snapshot_path_for_url(config: RuntimeConfig, url: str) -> Path:
    parsed = urlparse(url)
    slug = safe_slug_from_url(url)
    if parsed.path.startswith("/coaches/page/"):
        return config.raw_snapshot_run_dir / "directory" / f"{slug}.html.snapshot"
    if parsed.path.startswith("/coaches"):
        return config.raw_snapshot_run_dir / "directory" / f"{slug}.html.snapshot"
    if parsed.path.startswith("/teams"):
        return config.raw_snapshot_run_dir / "teams" / f"{slug}.html.snapshot"
    return config.raw_snapshot_run_dir / "profiles" / f"{slug}.html.snapshot"


def classify_url_kind(url: str) -> str:
    parsed = urlparse(url)
    if parsed.path == "/teams" or parsed.path.startswith("/teams/"):
        return "teams"
    if parsed.path.startswith("/coaches"):
        return "directory"
    return "profile"


def discover_coach_profile_urls(raw_records: list[dict[str, Any]], max_coaches: int) -> list[str]:
    links: list[str] = []
    for row in raw_records:
        if row.get("kind") != "directory":
            continue
        snapshot_path = Path(row["snapshotPath"])
        html = snapshot_path.read_text(encoding="utf-8", errors="ignore")
        for href in re.findall(r'href="([^"]+)"', html):
            if not href.startswith("/"):
                continue
            if href in RESERVED_PATHS or href.startswith("/assets") or href.startswith("/teams/"):
                continue
            if href.count("/") != 1:
                continue
            if href in {"/icon.png", "/icon.svg"}:
                continue
            links.append(urljoin("https://coaching-tree.app", href))
    return sorted(dict.fromkeys(links))[:max_coaches]
