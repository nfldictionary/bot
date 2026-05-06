from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path, limit: int | None = None) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
            if limit is not None and len(rows) >= limit:
                break
    return rows


def count_jsonl(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def badge_class(status: str) -> str:
    return {
        "pass": "badge badge-pass",
        "warn": "badge badge-warn",
        "fail": "badge badge-fail",
    }.get(status, "badge")


def render_table(rows: list[dict], columns: list[tuple[str, str]], empty_message: str) -> str:
    if not rows:
        return f'<div class="empty-state">{escape(empty_message)}</div>'
    header = "".join(f"<th>{escape(label)}</th>" for key, label in columns)
    body_rows = []
    for row in rows:
        cells = []
        for key, _ in columns:
            value = row.get(key)
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            if value is None:
                value = "—"
            cells.append(f"<td>{escape(str(value))}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<div class="table-shell"><table>'
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table></div>"
    )


def build_html(repo_path: Path, local_data_root: Path, run_id: str) -> str:
    data_root = repo_path / "data" / "nfl-coaching-tree"
    manifests_dir = data_root / "manifests"
    staging_dir = data_root / "staging"
    canonical_dir = data_root / "canonical"
    validation_dir = data_root / "validation"

    crawl_manifest = read_json(manifests_dir / "latest_crawl_manifest.json")
    parse_manifest = read_json(manifests_dir / "latest_parse_manifest.json")
    normalize_manifest = read_json(manifests_dir / "latest_normalize_manifest.json")
    validation_report = read_json(validation_dir / "latest_validation_report.json")

    directory_rows = read_jsonl(staging_dir / "coaching_tree_app_directory_coaches.jsonl", 12)
    profile_rows = read_jsonl(staging_dir / "coaching_tree_app_profiles.jsonl", 6)
    career_rows = read_jsonl(staging_dir / "coaching_tree_app_career_history.jsonl", 10)
    unresolved_coaches = read_jsonl(validation_dir / "unresolved_coaches.jsonl", 10)
    unresolved_teams = read_jsonl(validation_dir / "unresolved_teams.jsonl", 10)

    raw_snapshot_dir = local_data_root / "raw" / "coaching-tree-app" / run_id
    raw_snapshot_count = len(list(raw_snapshot_dir.rglob("*.html.snapshot"))) if raw_snapshot_dir.exists() else 0

    cards = [
        ("Run ID", run_id),
        ("Validation", validation_report["status"].upper()),
        ("Raw Snapshots", str(raw_snapshot_count)),
        ("Directory Rows", str(parse_manifest["directoryCoachRowsWritten"])),
        ("Profiles", str(parse_manifest["profileRowsWritten"])),
        ("Career Rows", str(parse_manifest["careerHistoryRowsWritten"])),
        ("Canonical Coaches", str(normalize_manifest["coachesWritten"])),
        ("Canonical Franchises", str(normalize_manifest["franchisesWritten"])),
    ]

    file_map_rows = [
        {
            "class": "Git repo staging",
            "path": "data/nfl-coaching-tree/staging/",
            "notes": "Structured extraction rows",
        },
        {
            "class": "Git repo canonical",
            "path": "data/nfl-coaching-tree/canonical/",
            "notes": "Normalized graph import records",
        },
        {
            "class": "Git repo validation",
            "path": "data/nfl-coaching-tree/validation/",
            "notes": "Latest validation report and unresolved lists",
        },
        {
            "class": "Local raw snapshots",
            "path": f"<LOCAL_DATA_ROOT>/raw/coaching-tree-app/{run_id}/",
            "notes": "Raw HTML snapshots only",
        },
        {
            "class": "Local cache",
            "path": "<LOCAL_DATA_ROOT>/cache/coaching-tree-app/",
            "notes": "Resume checkpoint and response metadata",
        },
        {
            "class": "Local exports",
            "path": f"<LOCAL_DATA_ROOT>/exports/{run_id}/",
            "notes": "Copied canonical files and Neo4j CSVs",
        },
    ]

    profile_cards = []
    for row in profile_rows:
        profile_cards.append(
            """
            <article class="profile-card">
              <div class="profile-card__title-row">
                <h3>{name}</h3>
                <span class="inline-pill">{job_title}</span>
              </div>
              <p class="profile-card__meta">{team}</p>
              <p class="profile-card__meta">{years}</p>
              <p class="profile-card__body">{description}</p>
              <a href="{url}" target="_blank" rel="noreferrer">Source profile</a>
            </article>
            """.format(
                name=escape(row["coachName"]),
                job_title=escape(row.get("jobTitle") or "Unknown role"),
                team=escape(row.get("currentTeamName") or "Unknown team"),
                years=escape(f"{row.get('yearStart') or '—'} to {row.get('yearEnd') or '—'}"),
                description=escape(row.get("description") or ""),
                url=escape(row.get("canonicalUrl") or row.get("sourceUrl") or "#"),
            )
        )

    summary_cards_html = "".join(
        f'<article class="stat-card"><p class="stat-card__label">{escape(label)}</p><strong>{escape(value)}</strong></article>'
        for label, value in cards
    )

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NFL Coaching Tree Sample Report</title>
    <style>
      :root {{
        --bg: #f3f5f4;
        --panel: #ffffff;
        --line: rgba(17, 24, 39, 0.12);
        --text: #161b19;
        --muted: #5f6b65;
        --accent: #1f7a3f;
        --warn: #b76e00;
        --pass: #1f7a3f;
        --fail: #a1271f;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        background: linear-gradient(180deg, #ffffff 0%, var(--bg) 100%);
        color: var(--text);
        font: 14px/1.6 "Space Grotesk", "IBM Plex Sans", sans-serif;
      }}
      .page {{
        max-width: 1360px;
        margin: 0 auto;
        padding: 24px;
        display: grid;
        gap: 20px;
      }}
      .hero,
      .panel {{
        background: var(--panel);
        border: 1px solid var(--line);
        padding: 20px;
        box-shadow: 0 16px 40px rgba(16, 24, 40, 0.08);
      }}
      .eyebrow {{
        margin: 0 0 6px;
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-size: 12px;
      }}
      h1, h2, h3, p {{ margin-top: 0; }}
      h1 {{
        margin-bottom: 8px;
        font-size: 34px;
        line-height: 1.1;
      }}
      .hero-meta {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 12px 0 0;
      }}
      .badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border: 1px solid var(--line);
        background: #eef1ef;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 12px;
      }}
      .badge-pass {{ color: var(--pass); }}
      .badge-warn {{ color: var(--warn); }}
      .badge-fail {{ color: var(--fail); }}
      .stat-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 12px;
      }}
      .stat-card {{
        border: 1px solid var(--line);
        padding: 16px;
        background: #fbfcfb;
      }}
      .stat-card__label {{
        margin-bottom: 6px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 12px;
      }}
      .stat-card strong {{
        font-size: 28px;
        letter-spacing: -0.04em;
      }}
      .two-up {{
        display: grid;
        grid-template-columns: 1.2fr 0.8fr;
        gap: 20px;
      }}
      .table-shell {{
        overflow-x: auto;
        border: 1px solid var(--line);
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
        min-width: 640px;
      }}
      th, td {{
        padding: 10px 12px;
        border-bottom: 1px solid var(--line);
        text-align: left;
        vertical-align: top;
      }}
      th {{
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted);
        background: #f8faf8;
      }}
      .profile-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 12px;
      }}
      .profile-card {{
        border: 1px solid var(--line);
        padding: 16px;
        background: #fbfcfb;
      }}
      .profile-card__title-row {{
        display: flex;
        gap: 8px;
        align-items: flex-start;
        justify-content: space-between;
      }}
      .profile-card__meta {{
        margin-bottom: 6px;
        color: var(--muted);
      }}
      .profile-card__body {{
        min-height: 72px;
      }}
      .inline-pill {{
        display: inline-flex;
        padding: 3px 8px;
        border: 1px solid var(--line);
        background: #ffffff;
        font-size: 12px;
      }}
      .empty-state {{
        padding: 18px;
        border: 1px dashed var(--line);
        color: var(--muted);
      }}
      code {{
        font-family: "IBM Plex Mono", monospace;
        background: #eef1ef;
        padding: 2px 6px;
      }}
      a {{ color: var(--accent); text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
      @media (max-width: 960px) {{
        .two-up {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main class="page">
      <section class="hero">
        <p class="eyebrow">Today&apos;s Development Snapshot</p>
        <h1>NFL Coaching Tree Sample Report</h1>
        <p>
          This page previews the data produced today by the storage-aware migration pipeline for
          <a href="https://coaching-tree.app" target="_blank" rel="noreferrer">coaching-tree.app</a>.
          It summarizes raw capture, staging extraction, canonical normalization, and validation output for one sample run.
        </p>
        <div class="hero-meta">
          <span class="badge">Run ID: {escape(run_id)}</span>
          <span class="{badge_class(validation_report['status'])}">Validation: {escape(validation_report['status'])}</span>
          <span class="badge">Source: coaching-tree.app</span>
        </div>
      </section>

      <section class="panel">
        <h2>Topline Counts</h2>
        <div class="stat-grid">
          {summary_cards_html}
        </div>
      </section>

      <section class="two-up">
        <section class="panel">
          <h2>Directory Coach Samples</h2>
          {render_table(directory_rows, [('coachSlug', 'Coach Slug'), ('coachName', 'Coach Name'), ('sourceUrl', 'Source URL')], 'No directory coach rows were parsed.')}
        </section>
        <section class="panel">
          <h2>Storage Map</h2>
          {render_table(file_map_rows, [('class', 'Data Class'), ('path', 'Saved To'), ('notes', 'Notes')], 'No storage rows available.')}
        </section>
      </section>

      <section class="panel">
        <h2>Profile Samples</h2>
        <div class="profile-grid">
          {''.join(profile_cards)}
        </div>
      </section>

      <section class="two-up">
        <section class="panel">
          <h2>Career Timeline Samples</h2>
          {render_table(career_rows, [('coachName', 'Coach'), ('year', 'Year'), ('teamName', 'Team'), ('roles', 'Role(s)')], 'No career timeline rows were parsed.')}
        </section>
        <section class="panel">
          <h2>Validation Snapshot</h2>
          <p><strong>Status:</strong> {escape(validation_report['status'].upper())}</p>
          <p><strong>Unresolved Coach References:</strong> {validation_report['unresolvedCoachReferences']}</p>
          <p><strong>Unresolved Team References:</strong> {validation_report['unresolvedTeamReferences']}</p>
          <p><strong>Ambiguous Relationships:</strong> {validation_report['ambiguousRelationships']}</p>
          <p><strong>Generated At:</strong> {escape(validation_report['generatedAt'])}</p>
          <p><strong>Raw Snapshot Count:</strong> {raw_snapshot_count}</p>
        </section>
      </section>

      <section class="two-up">
        <section class="panel">
          <h2>Unresolved Coach References</h2>
          {render_table(unresolved_coaches, [('coachName', 'Coach'), ('mentorName', 'Mentor Name'), ('sourceUrl', 'Source URL')], 'No unresolved coach references in this sample run.')}
        </section>
        <section class="panel">
          <h2>Unresolved Team References</h2>
          {render_table(unresolved_teams, [('coachName', 'Coach'), ('year', 'Year'), ('franchiseId', 'Franchise ID'), ('teamName', 'Team Name')], 'No unresolved team references in this sample run.')}
        </section>
      </section>

      <section class="panel">
        <h2>Canonical Output Summary</h2>
        <p>
          The canonical layer currently contains <code>{normalize_manifest['coachesWritten']}</code> coaches,
          <code>{normalize_manifest['franchisesWritten']}</code> franchises,
          <code>{normalize_manifest['staffTenuresWritten']}</code> staff tenure rows, and
          <code>{normalize_manifest['claimsWritten']}</code> claims.
        </p>
        <p>
          This is a deliberately small sample run with <code>--max-pages 2</code> and <code>--max-coaches 6</code>,
          so unresolved items are expected until the crawl scope is expanded.
        </p>
      </section>
    </main>
  </body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a sample NFL coaching tree HTML report")
    parser.add_argument("--repo-path", required=True)
    parser.add_argument("--local-data-root", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    repo_path = Path(args.repo_path).expanduser().resolve()
    local_data_root = Path(args.local_data_root).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    html = build_html(repo_path, local_data_root, args.run_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
