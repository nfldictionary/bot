from __future__ import annotations

import json
import re
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Any

from schema import MANIFEST_FILENAMES, STAGING_FILENAMES
from shared import (
    RuntimeConfig,
    display_local_path,
    display_repo_path,
    load_json,
    update_pipeline_manifest,
    write_json,
    write_jsonl,
)


def run_parse(config: RuntimeConfig) -> dict[str, Any]:
    crawl_manifest = load_json(config.manifests_dir / MANIFEST_FILENAMES["crawl"], {})
    raw_base = config.raw_snapshot_run_dir
    if not raw_base.exists():
        raise RuntimeError(
            f"No raw snapshots were found for run {config.run_id} at {raw_base}. "
            "Run crawl first or pass the matching --run-id."
        )

    accessed_at = datetime.now().isoformat(timespec="seconds")
    directory_rows: list[dict[str, Any]] = []
    profile_rows: list[dict[str, Any]] = []
    career_rows: list[dict[str, Any]] = []
    worked_under_rows: list[dict[str, Any]] = []
    protege_rows: list[dict[str, Any]] = []
    team_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []

    for snapshot_path in sorted((raw_base / "directory").glob("*.html.snapshot")):
        html = snapshot_path.read_text(encoding="utf-8", errors="ignore")
        source_url = infer_source_url(config.source_base_url, snapshot_path)
        source_rows.append(build_source_row(config, source_url, snapshot_path, accessed_at))
        directory_rows.extend(parse_directory_rows(source_url, html, accessed_at))

    for snapshot_path in sorted((raw_base / "profiles").glob("*.html.snapshot")):
        html = snapshot_path.read_text(encoding="utf-8", errors="ignore")
        source_url = infer_source_url(config.source_base_url, snapshot_path)
        source_rows.append(build_source_row(config, source_url, snapshot_path, accessed_at))
        parsed_profile = parse_profile_row(source_url, html, accessed_at)
        if parsed_profile:
            profile_rows.append(parsed_profile["profile"])
            career_rows.extend(parsed_profile["career_history"])
            worked_under_rows.extend(parsed_profile["worked_under"])
            protege_rows.extend(parsed_profile["proteges"])

    for snapshot_path in sorted((raw_base / "teams").glob("*.html.snapshot")):
        html = snapshot_path.read_text(encoding="utf-8", errors="ignore")
        source_url = infer_source_url(config.source_base_url, snapshot_path)
        source_rows.append(build_source_row(config, source_url, snapshot_path, accessed_at))
        team_rows.extend(parse_teams_rows(source_url, html, accessed_at))

    if not config.dry_run:
        write_jsonl(config.staging_dir / STAGING_FILENAMES["directory_coaches"], directory_rows)
        write_jsonl(config.staging_dir / STAGING_FILENAMES["profiles"], profile_rows)
        write_jsonl(config.staging_dir / STAGING_FILENAMES["career_history"], career_rows)
        write_jsonl(config.staging_dir / STAGING_FILENAMES["worked_under"], worked_under_rows)
        write_jsonl(config.staging_dir / STAGING_FILENAMES["proteges"], protege_rows)
        write_jsonl(config.staging_dir / STAGING_FILENAMES["teams_raw"], team_rows)
        write_jsonl(config.staging_dir / STAGING_FILENAMES["sources"], source_rows)

    manifest = {
        "runId": config.run_id,
        "sourceBaseUrl": config.source_base_url,
        "rawSnapshotDir": display_local_path(config, raw_base),
        "stagingOutputDir": display_repo_path(config, config.staging_dir),
        "canonicalOutputDir": display_repo_path(config, config.canonical_dir),
        "validationOutputDir": display_repo_path(config, config.validation_dir),
        "importManifestPath": display_repo_path(config, config.manifests_dir / MANIFEST_FILENAMES["import"]),
        "accessedAt": accessed_at,
        "directoryCoachRowsWritten": len(directory_rows),
        "profileRowsWritten": len(profile_rows),
        "careerHistoryRowsWritten": len(career_rows),
        "workedUnderRowsWritten": len(worked_under_rows),
        "protegeRowsWritten": len(protege_rows),
        "teamsRowsWritten": len(team_rows),
        "sourcesRowsWritten": len(source_rows),
        "crawlSummary": crawl_manifest,
    }
    if not config.dry_run:
        write_json(config.manifests_dir / MANIFEST_FILENAMES["parse"], manifest)
        update_pipeline_manifest(
            config,
            {
                "parseManifestPath": display_repo_path(config, config.manifests_dir / MANIFEST_FILENAMES["parse"]),
                "parseSummary": {
                    "directoryCoachRowsWritten": len(directory_rows),
                    "profileRowsWritten": len(profile_rows),
                    "careerHistoryRowsWritten": len(career_rows),
                },
            },
        )
    return manifest


def build_source_row(config: RuntimeConfig, source_url: str, snapshot_path: Path, accessed_at: str) -> dict[str, Any]:
    return {
        "sourceUrl": source_url,
        "accessedAt": accessed_at,
        "snapshotPath": display_local_path(config, snapshot_path),
    }


def infer_source_url(source_base_url: str, snapshot_path: Path) -> str:
    stem = snapshot_path.stem.replace("__", "/")
    if stem == "root.html":
        return source_base_url
    raw = stem.replace(".html", "")
    if raw == "coaches":
        return f"{source_base_url}/coaches"
    if raw.startswith("teams"):
        suffix = raw.replace("teams", "", 1).strip("/")
        return f"{source_base_url}/teams/{suffix}" if suffix else f"{source_base_url}/teams"
    if raw.startswith("coaches"):
        suffix = raw.replace("coaches", "", 1).strip("/")
        return f"{source_base_url}/coaches/{suffix}" if suffix else f"{source_base_url}/coaches"
    return f"{source_base_url}/{raw}"


def parse_directory_rows(source_url: str, html: str, accessed_at: str) -> list[dict[str, Any]]:
    rows = []
    pattern = re.compile(
        r'href="(/[^"]+)"[^>]*>.*?<h[23][^>]*>\s*([^<]+?)\s*</h[23]>',
        re.I | re.S,
    )
    for href, name in pattern.findall(html):
        if href.count("/") != 1 or href in {"/icon.png", "/icon.svg"}:
            continue
        if href.startswith("/assets") or href in {"/", "/about", "/analytics", "/coaches", "/degrees", "/mcp", "/teams"}:
            continue
        rows.append(
            {
                "coachSlug": href.strip("/"),
                "coachName": unescape(name.strip()),
                "sourceUrl": source_url,
                "accessedAt": accessed_at,
            }
        )
    deduped = {(row["coachSlug"], row["coachName"]): row for row in rows}
    return list(deduped.values())


def parse_profile_row(source_url: str, html: str, accessed_at: str) -> dict[str, Any] | None:
    person = parse_person_json_ld(html)
    title = match_first(html, r"<title>([^<]+)</title>")
    description = match_first(html, r'<meta name="description" content="([^"]+)"')
    canonical_url = match_first(html, r'<link rel="canonical" href="([^"]+)"')
    if not title:
        return None
    name = (person or {}).get("name") or title.split(" Coaching Tree", 1)[0]
    job_title = (person or {}).get("jobTitle")
    current_team = ((person or {}).get("worksFor") or {}).get("name")
    birth_place = (person or {}).get("birthPlace")
    alumni_of = ((person or {}).get("alumniOf") or {}).get("name")
    year_span = extract_year_span(unescape(description or ""))
    mentor_rows = parse_relationship_table(html, r"Worked\s+Under")
    protege_table_rows = parse_relationship_table(html, r"Prot(?:&eacute;|é)g(?:&eacute;|é)s")

    coach_id = slug_from_url(canonical_url or source_url)
    profile = {
        "coachId": coach_id,
        "coachSlug": coach_id,
        "coachName": unescape(name),
        "profileTitle": unescape(title),
        "description": unescape(description or ""),
        "canonicalUrl": canonical_url or source_url,
        "jobTitle": job_title,
        "currentTeamName": current_team,
        "birthPlace": birth_place,
        "alumniOf": alumni_of,
        "yearStart": year_span[0] if year_span else None,
        "yearEnd": year_span[1] if year_span else None,
        "sourceUrl": source_url,
        "accessedAt": accessed_at,
    }

    career_history = []
    for entry in parse_timeline_data(html):
        career_history.append(
            {
                "coachId": coach_id,
                "coachName": unescape(name),
                "year": entry.get("year"),
                "teamName": entry.get("team"),
                "teamSlug": entry.get("team_slug"),
                "roles": entry.get("roles"),
                "sourceUrl": source_url,
                "accessedAt": accessed_at,
            }
        )

    worked_under = []
    if mentor_rows:
        for mentor in mentor_rows:
            worked_under.append(
                {
                    "coachId": coach_id,
                    "coachName": unescape(name),
                    "mentorName": mentor["coachName"],
                    "mentorSlug": mentor["coachSlug"],
                    "teamName": mentor.get("teamName"),
                    "years": mentor.get("years"),
                    "sourceUrl": source_url,
                    "accessedAt": accessed_at,
                }
            )
    else:
        for mentor_name in extract_mentor_names(unescape(description or "")):
            if not is_probable_coach_name(mentor_name):
                continue
            worked_under.append(
                {
                    "coachId": coach_id,
                    "coachName": unescape(name),
                    "mentorName": mentor_name,
                    "mentorSlug": None,
                    "teamName": None,
                    "years": None,
                    "sourceUrl": source_url,
                    "accessedAt": accessed_at,
                }
            )

    proteges = [
        {
            "coachId": coach_id,
            "coachName": unescape(name),
            "protegeName": protege["coachName"],
            "protegeSlug": protege["coachSlug"],
            "teamName": protege.get("teamName"),
            "years": protege.get("years"),
            "sourceUrl": source_url,
            "accessedAt": accessed_at,
        }
        for protege in protege_table_rows
    ]

    return {
        "profile": profile,
        "career_history": career_history,
        "worked_under": worked_under,
        "proteges": proteges,
    }


def parse_teams_rows(source_url: str, html: str, accessed_at: str) -> list[dict[str, Any]]:
    rows = []
    pattern = re.compile(
        r'href="(/teams/[^"]+)"[^>]*>.*?<h3[^>]*>\s*([^<]+?)\s*</h3>',
        re.I | re.S,
    )
    for href, name in pattern.findall(html):
        team_slug = href.replace("/teams/", "", 1)
        rows.append(
            {
                "teamSlug": team_slug,
                "teamName": unescape(name.strip()),
                "teamUrl": f"https://coaching-tree.app{href}",
                "sourceUrl": source_url,
                "accessedAt": accessed_at,
            }
        )
    deduped = {(row["teamSlug"], row["teamName"]): row for row in rows}
    return list(deduped.values())


def parse_person_json_ld(html: str) -> dict[str, Any] | None:
    scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    for script in scripts:
        try:
            payload = json.loads(script)
        except json.JSONDecodeError:
            continue
        if payload.get("@type") == "Person":
            return payload
    return None


def parse_timeline_data(html: str) -> list[dict[str, Any]]:
    raw = match_first(html, r'data-timeline-data-value="([^"]+)"')
    if not raw:
        return []
    try:
        return json.loads(unescape(raw))
    except json.JSONDecodeError:
        return []


def extract_year_span(text: str) -> tuple[int, int] | None:
    match = re.search(r"\((\d{4})[–-](\d{4})\)", text)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def parse_relationship_table(html: str, heading_pattern: str) -> list[dict[str, Any]]:
    heading_match = re.search(
        rf"<h2[^>]*>[^<]*{heading_pattern}.*?</h2>",
        html,
        re.I | re.S,
    )
    if not heading_match:
        return []

    next_heading = re.search(r"<h2[^>]*>", html[heading_match.end() :], re.I | re.S)
    section = html[heading_match.end() : heading_match.end() + next_heading.start()] if next_heading else html[heading_match.end() :]
    tbody_match = re.search(r"<tbody>(.*?)</tbody>", section, re.I | re.S)
    table = tbody_match.group(1) if tbody_match else section
    rows = []
    for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.I | re.S):
        link_match = re.search(r'<a[^>]+href="/([^"]+)"[^>]*>\s*([^<]+?)\s*</a>', row_html, re.I | re.S)
        if not link_match:
            continue
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.I | re.S)
        team_name = clean_cell_text(cells[1]) if len(cells) > 1 else None
        years = clean_cell_text(cells[2]) if len(cells) > 2 else None
        rows.append(
            {
                "coachSlug": link_match.group(1).strip("/"),
                "coachName": unescape(link_match.group(2).strip()),
                "teamName": team_name,
                "years": years,
            }
        )
    return rows


def clean_cell_text(html_fragment: str) -> str | None:
    text = re.sub(r"<script.*?</script>", " ", html_fragment, flags=re.I | re.S)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = " ".join(unescape(text).split())
    return text or None


def extract_mentor_names(text: str) -> list[str]:
    match = re.search(r"worked under (.+?)\.", text, re.I | re.S)
    if not match:
        return []
    raw_names = match.group(1)
    raw_names = raw_names.replace(" and ", ", ")
    return [
        " ".join(name.split())
        for name in raw_names.split(",")
        if " ".join(name.split())
    ]


def is_probable_coach_name(value: str) -> bool:
    text = " ".join(unescape(value or "").split())
    if not text:
        return False
    if "<" in text or ">" in text:
        return False
    if any(token in text.lower() for token in ("no head coach", "mentors found", "protégé", "protege", "class=")):
        return False
    if len(text) > 80:
        return False
    return bool(re.match(r"^[A-Z][A-Za-z.'\- ]+$", text))


def slug_from_url(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def match_first(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, re.I | re.S)
    return match.group(1).strip() if match else None
