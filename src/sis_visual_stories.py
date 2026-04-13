from __future__ import annotations

import html
import math
from pathlib import Path
from typing import Any

try:
    from sis_pipeline import DEFAULT_OUTPUT_ROOT, _format_number, _require_pandas
except ModuleNotFoundError:  # pragma: no cover
    from src.sis_pipeline import DEFAULT_OUTPUT_ROOT, _format_number, _require_pandas


def _slugify(value: str) -> str:
    cleaned = []
    for char in value.lower().strip():
        if char.isalnum():
            cleaned.append(char)
        elif char in {" ", "_", "-"}:
            cleaned.append("-")
    slug = "".join(cleaned).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "story"


def _story_root(output_root: Path, season: int) -> Path:
    return output_root.expanduser().resolve() / "stories" / str(season)


def _load_story_frames(output_root: Path, season: int) -> dict[str, Any]:
    pandas = _require_pandas()
    parquet_root = output_root.expanduser().resolve() / "parquet" / str(season)
    frames: dict[str, Any] = {
        "team": pandas.read_parquet(parquet_root / "team_seasonal.parquet"),
        "player": pandas.read_parquet(parquet_root / "player_seasonal.parquet"),
        "passing": pandas.read_parquet(parquet_root / "player_passing.parquet"),
        "rushing": pandas.read_parquet(parquet_root / "player_rushing.parquet"),
        "receiving": pandas.read_parquet(parquet_root / "player_receiving.parquet"),
        "defense": pandas.read_parquet(parquet_root / "player_defense.parquet"),
    }
    return frames


def _safe_numeric(df: Any, column: str) -> Any:
    pandas = _require_pandas()
    if column not in df.columns:
        return pandas.Series([0.0] * len(df), index=df.index, dtype="float64")
    return pandas.to_numeric(df[column], errors="coerce").fillna(0.0)


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _render_story_shell(title: str, eyebrow: str, intro: str, body: str, theme: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --ink: #0f172a;
      --muted: #546274;
      --line: rgba(15, 23, 42, 0.12);
      --panel: rgba(255, 255, 255, 0.78);
      --shadow: 0 24px 60px rgba(15, 23, 42, 0.14);
      --radius: 26px;
      --font: "Avenir Next", "Pretendard", "Apple SD Gothic Neo", "Segoe UI", sans-serif;
      {theme}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: var(--font);
      background: var(--bg);
    }}
    a {{
      color: inherit;
      text-decoration: none;
    }}
    .page {{
      width: min(1240px, calc(100% - 32px));
      margin: 0 auto;
      padding: 30px 0 60px;
    }}
    .hero {{
      position: relative;
      overflow: hidden;
      border-radius: calc(var(--radius) + 8px);
      padding: 28px;
      background: linear-gradient(135deg, rgba(255,255,255,0.88), rgba(255,255,255,0.52));
      box-shadow: var(--shadow);
      border: 1px solid rgba(255,255,255,0.45);
      backdrop-filter: blur(10px);
    }}
    .hero::after {{
      content: "";
      position: absolute;
      inset: auto -40px -70px auto;
      width: 260px;
      height: 260px;
      background: var(--orb);
      filter: blur(10px);
      opacity: 0.75;
      border-radius: 50%;
    }}
    .eyebrow {{
      display: inline-flex;
      padding: 9px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      background: rgba(255,255,255,0.58);
      border: 1px solid rgba(15,23,42,0.08);
    }}
    h1 {{
      position: relative;
      margin: 18px 0 12px;
      max-width: 820px;
      font-size: clamp(34px, 6vw, 64px);
      line-height: 0.96;
      letter-spacing: -0.05em;
      z-index: 1;
    }}
    .hero p {{
      position: relative;
      margin: 0;
      max-width: 760px;
      font-size: 16px;
      line-height: 1.7;
      color: var(--muted);
      z-index: 1;
    }}
    .nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
      position: relative;
      z-index: 1;
    }}
    .nav a {{
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(255,255,255,0.62);
      border: 1px solid rgba(15,23,42,0.08);
      font-size: 13px;
      font-weight: 700;
    }}
    .section-title {{
      margin: 32px 0 14px;
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #334155;
    }}
    .grid {{
      display: grid;
      gap: 18px;
    }}
    .grid.two {{
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    }}
    .grid.three {{
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
      padding: 20px;
    }}
    .panel h2, .panel h3 {{
      margin: 0 0 14px;
      letter-spacing: -0.03em;
    }}
    .kicker {{
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 12px;
    }}
    .stat-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
    }}
    .stat-card {{
      padding: 16px;
      border-radius: 20px;
      background: rgba(255,255,255,0.52);
      border: 1px solid rgba(15,23,42,0.06);
    }}
    .stat-label {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    .stat-value {{
      font-size: 28px;
      font-weight: 800;
      letter-spacing: -0.04em;
    }}
    .note {{
      margin: 0;
      font-size: 14px;
      line-height: 1.6;
      color: var(--muted);
    }}
    .list {{
      display: grid;
      gap: 12px;
    }}
    .list-item {{
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(255,255,255,0.58);
      border: 1px solid rgba(15,23,42,0.06);
    }}
    .list-top {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: baseline;
      margin-bottom: 8px;
    }}
    .list-label {{
      font-weight: 800;
      letter-spacing: -0.02em;
    }}
    .list-meta {{
      font-size: 12px;
      color: var(--muted);
      margin-top: 4px;
    }}
    .list-value {{
      font-size: 22px;
      font-weight: 800;
      letter-spacing: -0.04em;
      white-space: nowrap;
    }}
    .track {{
      height: 10px;
      border-radius: 999px;
      background: rgba(15,23,42,0.08);
      overflow: hidden;
    }}
    .fill {{
      height: 100%;
      border-radius: inherit;
      background: var(--accent);
    }}
    .chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .chip {{
      padding: 7px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      background: rgba(255,255,255,0.68);
      border: 1px solid rgba(15,23,42,0.08);
    }}
    .table-wrap {{
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      text-align: left;
      padding: 10px 8px;
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
    .footer {{
      margin-top: 28px;
      font-size: 13px;
      color: var(--muted);
    }}
    @media (max-width: 760px) {{
      .page {{
        width: min(100% - 20px, 1240px);
        padding-top: 20px;
      }}
      .hero {{
        padding: 22px;
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
      <div class="eyebrow">{html.escape(eyebrow)}</div>
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(intro)}</p>
      <nav class="nav">
        <a href="./index.html">Index</a>
        <a href="./strategy-atlas.html">Strategy Atlas</a>
        <a href="./skill-stars.html">Skill Stars</a>
        <a href="./franchise-fingerprints.html">Fingerprints</a>
        <a href="./roster-currents.html">Roster Currents</a>
      </nav>
    </section>
    {body}
    <div class="footer">Generated from local SIS parquet for visual exploration.</div>
  </main>
</body>
</html>
"""


def _render_stat_cards(cards: list[dict[str, str]]) -> str:
    return (
        '<section class="section-title">At A Glance</section><section class="panel"><div class="stat-grid">'
        + "".join(
            '<article class="stat-card">'
            f'<div class="stat-label">{html.escape(card["label"])}</div>'
            f'<div class="stat-value">{html.escape(card["value"])}</div>'
            "</article>"
            for card in cards
        )
        + "</div></section>"
    )


def _render_rank_list(items: list[dict[str, Any]], accent: str) -> str:
    if not items:
        return '<p class="note">No rows available.</p>'
    max_value = max(float(item["value"]) for item in items) or 1.0
    blocks = []
    for item in items:
        width = max(7.0, (float(item["value"]) / max_value) * 100.0)
        blocks.append(
            '<article class="list-item">'
            '<div class="list-top">'
            f'<div><div class="list-label">{html.escape(item["label"])}</div><div class="list-meta">{html.escape(item["meta"])}</div></div>'
            f'<div class="list-value">{html.escape(_format_number(item["value"]))}</div>'
            "</div>"
            '<div class="track">'
            f'<div class="fill" style="width:{width:.2f}%;background:{accent};"></div>'
            "</div>"
            "</article>"
        )
    return '<div class="list">' + "".join(blocks) + "</div>"


def _story_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="note">No table rows available.</p>'
    columns = list(rows[0].keys())
    head = "".join(f"<th>{html.escape(str(column))}</th>" for column in columns)
    body = []
    for row in rows:
        cells = []
        for column in columns:
            value = row[column]
            if isinstance(value, (int, float)):
                rendered = _format_number(value)
            else:
                rendered = _safe_text(value)
            cells.append(f"<td>{html.escape(rendered)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return '<div class="table-wrap"><table><thead><tr>' + head + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>"


def _render_scatter_svg(rows: list[dict[str, Any]], x_label: str, y_label: str) -> str:
    width = 960
    height = 620
    margin = 80
    xs = [float(row["x"]) for row in rows]
    ys = [float(row["y"]) for row in rows]
    max_x = max(xs) if xs else 1.0
    max_y = max(ys) if ys else 1.0
    min_x = min(xs) if xs else 0.0
    min_y = min(ys) if ys else 0.0
    pad_x = max((max_x - min_x) * 0.08, 80.0)
    pad_y = max((max_y - min_y) * 0.08, 80.0)
    low_x = min_x - pad_x
    high_x = max_x + pad_x
    low_y = min_y - pad_y
    high_y = max_y + pad_y
    span_x = max(high_x - low_x, 1.0)
    span_y = max(high_y - low_y, 1.0)
    median_x = sorted(xs)[len(xs) // 2] if xs else 0.0
    median_y = sorted(ys)[len(ys) // 2] if ys else 0.0

    def scale_x(value: float) -> float:
        return margin + ((value - low_x) / span_x) * (width - margin * 2)

    def scale_y(value: float) -> float:
        return height - margin - ((value - low_y) / span_y) * (height - margin * 2)

    x_ticks = []
    y_ticks = []
    for step in range(5):
        value = low_x + span_x * (step / 4)
        pos = scale_x(value)
        x_ticks.append(
            f'<g><line x1="{pos:.1f}" y1="{height - margin}" x2="{pos:.1f}" y2="{margin}" stroke="rgba(15,23,42,0.08)" />'
            f'<text x="{pos:.1f}" y="{height - margin + 26}" text-anchor="middle" font-size="12" fill="#475569">{html.escape(_format_number(value))}</text></g>'
        )
    for step in range(5):
        value = low_y + span_y * (step / 4)
        pos = scale_y(value)
        y_ticks.append(
            f'<g><line x1="{margin}" y1="{pos:.1f}" x2="{width - margin}" y2="{pos:.1f}" stroke="rgba(15,23,42,0.08)" />'
            f'<text x="{margin - 14}" y="{pos + 4:.1f}" text-anchor="end" font-size="12" fill="#475569">{html.escape(_format_number(value))}</text></g>'
        )

    points = []
    for row in rows:
        cx = scale_x(float(row["x"]))
        cy = scale_y(float(row["y"]))
        radius = row["radius"]
        color = row["color"]
        label = html.escape(row["label"])
        meta = html.escape(row["meta"])
        points.append(
            f'<g>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="{color}" fill-opacity="0.74" stroke="rgba(15,23,42,0.28)" stroke-width="2" />'
            f'<text x="{cx:.1f}" y="{cy - radius - 8:.1f}" text-anchor="middle" font-size="12" font-weight="800" fill="#0f172a">{label}</text>'
            f'<text x="{cx:.1f}" y="{cy + radius + 16:.1f}" text-anchor="middle" font-size="11" fill="#475569">{meta}</text>'
            f'</g>'
        )

    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="Strategy atlas scatter plot">'
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="28" fill="rgba(255,255,255,0.4)" />'
        + "".join(x_ticks)
        + "".join(y_ticks)
        + f'<line x1="{scale_x(median_x):.1f}" y1="{margin}" x2="{scale_x(median_x):.1f}" y2="{height - margin}" stroke="rgba(15,23,42,0.22)" stroke-dasharray="10 10" />'
        + f'<line x1="{margin}" y1="{scale_y(median_y):.1f}" x2="{width - margin}" y2="{scale_y(median_y):.1f}" stroke="rgba(15,23,42,0.22)" stroke-dasharray="10 10" />'
        + "".join(points)
        + f'<text x="{width / 2:.1f}" y="{height - 20}" text-anchor="middle" font-size="14" font-weight="700" fill="#334155">{html.escape(x_label)}</text>'
        + f'<text x="24" y="{height / 2:.1f}" transform="rotate(-90 24 {height / 2:.1f})" text-anchor="middle" font-size="14" font-weight="700" fill="#334155">{html.escape(y_label)}</text>'
        + "</svg>"
    )


def _render_radar(values: list[float], color: str) -> str:
    cx = 120.0
    cy = 120.0
    radius = 82.0
    rings = [0.25, 0.5, 0.75, 1.0]
    labels = ["Pass", "Rush", "Air", "Sacks", "TDs"]
    guides = []
    for ring in rings:
        points = []
        for idx in range(5):
            angle = math.radians(-90 + idx * 72)
            x = cx + math.cos(angle) * radius * ring
            y = cy + math.sin(angle) * radius * ring
            points.append(f"{x:.1f},{y:.1f}")
        guides.append(f'<polygon points="{" ".join(points)}" fill="none" stroke="rgba(15,23,42,0.10)" stroke-width="1" />')
    axes = []
    polygon_points = []
    label_nodes = []
    for idx, value in enumerate(values):
        angle = math.radians(-90 + idx * 72)
        outer_x = cx + math.cos(angle) * radius
        outer_y = cy + math.sin(angle) * radius
        point_x = cx + math.cos(angle) * radius * value
        point_y = cy + math.sin(angle) * radius * value
        polygon_points.append(f"{point_x:.1f},{point_y:.1f}")
        axes.append(f'<line x1="{cx}" y1="{cy}" x2="{outer_x:.1f}" y2="{outer_y:.1f}" stroke="rgba(15,23,42,0.12)" />')
        label_x = cx + math.cos(angle) * (radius + 24)
        label_y = cy + math.sin(angle) * (radius + 24)
        label_nodes.append(f'<text x="{label_x:.1f}" y="{label_y:.1f}" text-anchor="middle" font-size="12" font-weight="700" fill="#334155">{labels[idx]}</text>')
    return (
        '<svg viewBox="0 0 240 240" width="100%" role="img" aria-label="Team fingerprint radar">'
        + "".join(guides)
        + "".join(axes)
        + f'<polygon points="{" ".join(polygon_points)}" fill="{color}" fill-opacity="0.26" stroke="{color}" stroke-width="3" />'
        + "".join(label_nodes)
        + "</svg>"
    )


def _build_index_story(output_root: Path, season: int, story_defs: list[dict[str, str]], frames: dict[str, Any]) -> Path:
    team = frames["team"]
    player = frames["player"]
    multi_team_players = (
        player.groupby("player_id")["team_alias"].nunique().gt(1).sum()
        if "player_id" in player.columns and "team_alias" in player.columns
        else 0
    )
    cards = [
        {"label": "Team Rows", "value": _format_number(len(team))},
        {"label": "Player Rows", "value": _format_number(len(player))},
        {"label": "Multi-Team Players", "value": _format_number(multi_team_players)},
        {"label": "Stories", "value": _format_number(len(story_defs))},
    ]
    story_cards = []
    for story in story_defs:
        story_cards.append(
            '<a class="panel" href="./{slug}.html">'
            '<div class="kicker">{eyebrow}</div>'
            '<h2>{title}</h2>'
            '<p class="note">{description}</p>'
            '<div class="chips"><span class="chip">{tag_one}</span><span class="chip">{tag_two}</span></div>'
            "</a>".format(
                slug=html.escape(story["slug"]),
                eyebrow=html.escape(story["eyebrow"]),
                title=html.escape(story["title"]),
                description=html.escape(story["description"]),
                tag_one=html.escape(story["tag_one"]),
                tag_two=html.escape(story["tag_two"]),
            )
        )
    body = (
        _render_stat_cards(cards)
        + '<section class="section-title">Story Deck</section>'
        + '<section class="grid two">'
        + "".join(story_cards)
        + "</section>"
    )
    html_text = _render_story_shell(
        title=f"SIS Visual Stories {season}",
        eyebrow="HTML Story Bundle",
        intro="팀 전략, 스타 플레이어, 프랜차이즈 성향, 멀티팀 이동을 각각 다른 톤의 HTML로 분리해 바로 퍼블리싱하거나 검토할 수 있게 구성했습니다.",
        body=body,
        theme="--bg: radial-gradient(circle at top left, rgba(255,189,105,0.42), transparent 32%), radial-gradient(circle at right, rgba(93,173,226,0.28), transparent 28%), linear-gradient(180deg, #fbf4ea 0%, #eef5fb 48%, #f9f3ea 100%); --orb: radial-gradient(circle, rgba(255,138,91,0.68), rgba(255,138,91,0.0) 72%); --accent: linear-gradient(90deg, #f97316, #fb7185);",
    )
    path = _story_root(output_root, season) / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_text, encoding="utf-8")
    return path


def _build_strategy_story(output_root: Path, season: int, frames: dict[str, Any]) -> Path:
    team = frames["team"].copy()
    team["record_passing_yards"] = _safe_numeric(team, "record_passing_yards")
    team["record_rushing_yards"] = _safe_numeric(team, "record_rushing_yards")
    team["record_touchdowns_total"] = _safe_numeric(team, "record_touchdowns_total")
    team["record_defense_sacks"] = _safe_numeric(team, "record_defense_sacks")
    team["ratio"] = team["record_passing_yards"] / team["record_rushing_yards"].replace(0, 1)
    team["offense_total"] = team["record_passing_yards"] + team["record_rushing_yards"]
    max_touchdowns = max(float(team["record_touchdowns_total"].max()), 1.0)

    scatter_rows = []
    for _, row in team.iterrows():
        sacks = float(row["record_defense_sacks"])
        hue = 190 - min(sacks * 1.6, 120.0)
        color = f"hsl({hue:.0f} 74% 54%)"
        scatter_rows.append(
            {
                "label": _safe_text(row["team_alias"]),
                "meta": f'{_safe_text(row["team_name"])} · {int(sacks)} sacks',
                "x": float(row["record_rushing_yards"]),
                "y": float(row["record_passing_yards"]),
                "radius": 9.0 + (float(row["record_touchdowns_total"]) / max_touchdowns) * 12.0,
                "color": color,
            }
        )

    top_offense = team.sort_values("offense_total", ascending=False).head(8)
    balanced = team.assign(balance_gap=(team["record_passing_yards"] - team["record_rushing_yards"]).abs()).sort_values("balance_gap").head(8)
    pressure = team.sort_values("record_defense_sacks", ascending=False).head(8)

    body = (
        _render_stat_cards(
            [
                {"label": "Median Pass/Rush Ratio", "value": f'{team["ratio"].median():.2f}x'},
                {"label": "Top Total Offense", "value": f'{_safe_text(top_offense.iloc[0]["team_alias"])} · {_format_number(top_offense.iloc[0]["offense_total"])}'},
                {"label": "Top Sack Unit", "value": f'{_safe_text(pressure.iloc[0]["team_alias"])} · {_format_number(pressure.iloc[0]["record_defense_sacks"])}'},
                {"label": "Balanced Leader", "value": _safe_text(balanced.iloc[0]["team_alias"])},
            ]
        )
        + '<section class="section-title">League Map</section>'
        + '<section class="panel">'
        + '<div class="kicker">Pass vs Rush, bubble sized by total touchdowns and shaded by sacks</div>'
        + _render_scatter_svg(scatter_rows, "Rushing Yards", "Passing Yards")
        + "</section>"
        + '<section class="section-title">Story Angles</section>'
        + '<section class="grid three">'
        + '<section class="panel"><h3>Total Offense Leaders</h3>'
        + _render_rank_list(
            [
                {
                    "label": _safe_text(row["team_name"]),
                    "meta": f'{_safe_text(row["team_alias"])} · pass/rush {_format_number(row["ratio"])}x',
                    "value": float(row["offense_total"]),
                }
                for _, row in top_offense.iterrows()
            ],
            "linear-gradient(90deg,#ff7a18,#ffb347)",
        )
        + "</section>"
        + '<section class="panel"><h3>Most Balanced Attacks</h3>'
        + _render_rank_list(
            [
                {
                    "label": _safe_text(row["team_name"]),
                    "meta": f'{_safe_text(row["team_alias"])} · gap {_format_number(abs(row["record_passing_yards"] - row["record_rushing_yards"]))}',
                    "value": float(row["record_rushing_yards"] + row["record_passing_yards"]),
                }
                for _, row in balanced.iterrows()
            ],
            "linear-gradient(90deg,#0ea5e9,#22c55e)",
        )
        + "</section>"
        + '<section class="panel"><h3>Pressure Packages</h3>'
        + _render_rank_list(
            [
                {
                    "label": _safe_text(row["team_name"]),
                    "meta": f'{_safe_text(row["team_alias"])} · offense {_format_number(row["offense_total"])}',
                    "value": float(row["record_defense_sacks"]),
                }
                for _, row in pressure.iterrows()
            ],
            "linear-gradient(90deg,#7c3aed,#f43f5e)",
        )
        + "</section></section>"
    )
    html_text = _render_story_shell(
        title=f"Strategy Atlas {season}",
        eyebrow="Team Geometry",
        intro="팀별 러시/패스 생산량을 좌표로 찍고 터치다운과 압박 수치를 겹쳐서, 공격 구조와 수비 압박을 한 번에 읽는 페이지입니다.",
        body=body,
        theme="--bg: radial-gradient(circle at top left, rgba(34,211,238,0.34), transparent 28%), radial-gradient(circle at bottom right, rgba(251,146,60,0.26), transparent 32%), linear-gradient(180deg, #eff9ff 0%, #eef6f4 52%, #fff4e8 100%); --orb: radial-gradient(circle, rgba(14,165,233,0.7), rgba(14,165,233,0.0) 72%); --accent: linear-gradient(90deg, #0ea5e9, #f97316);",
    )
    path = _story_root(output_root, season) / "strategy-atlas.html"
    path.write_text(html_text, encoding="utf-8")
    return path


def _build_skill_story(output_root: Path, season: int, frames: dict[str, Any]) -> Path:
    categories = [
        {
            "title": "Quarterback Ceiling",
            "df": frames["passing"],
            "metric": "stats_passing_yards",
            "metric_label": "Passing Yards",
            "accent": "linear-gradient(90deg,#fb7185,#f97316)",
        },
        {
            "title": "Backfield Engine",
            "df": frames["rushing"],
            "metric": "stats_rushing_yards",
            "metric_label": "Rushing Yards",
            "accent": "linear-gradient(90deg,#22c55e,#14b8a6)",
        },
        {
            "title": "Receiver Gravity",
            "df": frames["receiving"],
            "metric": "stats_receiving_yards",
            "metric_label": "Receiving Yards",
            "accent": "linear-gradient(90deg,#6366f1,#8b5cf6)",
        },
        {
            "title": "Defensive Erasers",
            "df": frames["defense"],
            "metric": "stats_defense_combined",
            "metric_label": "Combined Tackles",
            "accent": "linear-gradient(90deg,#f59e0b,#ef4444)",
        },
    ]

    panels = []
    hero_cards = []
    for category in categories:
        df = category["df"].copy()
        df[category["metric"]] = _safe_numeric(df, category["metric"])
        leaders = df.sort_values(category["metric"], ascending=False).head(8)
        champion = leaders.iloc[0]
        hero_cards.append(
            {
                "label": category["title"],
                "value": f'{_safe_text(champion["player_name"])} · {_format_number(champion[category["metric"]])}',
            }
        )
        panels.append(
            '<section class="panel"><div class="kicker">{metric_label}</div><h3>{title}</h3>{list_html}</section>'.format(
                metric_label=html.escape(category["metric_label"]),
                title=html.escape(category["title"]),
                list_html=_render_rank_list(
                    [
                        {
                            "label": _safe_text(row["player_name"]),
                            "meta": f'{_safe_text(row["team_alias"])} · {_safe_text(row["position"])}',
                            "value": float(row[category["metric"]]),
                        }
                        for _, row in leaders.iterrows()
                    ],
                    category["accent"],
                ),
            )
        )

    spotlight_rows = []
    for category in categories:
        df = category["df"].copy().sort_values(category["metric"], ascending=False).head(5)
        for rank, (_, row) in enumerate(df.iterrows(), start=1):
            spotlight_rows.append(
                {
                    "track": category["title"],
                    "rank": rank,
                    "player": _safe_text(row["player_name"]),
                    "team": _safe_text(row["team_alias"]),
                    "position": _safe_text(row["position"]),
                    "value": _format_number(row[category["metric"]]),
                }
            )

    body = (
        _render_stat_cards(hero_cards)
        + '<section class="section-title">Category Leaders</section>'
        + '<section class="grid two">'
        + "".join(panels)
        + "</section>"
        + '<section class="section-title">Editorial Pull Quote Table</section>'
        + '<section class="panel"><h3>Top 5 by Track</h3>'
        + _story_table(spotlight_rows)
        + "</section>"
    )
    html_text = _render_story_shell(
        title=f"Skill Stars {season}",
        eyebrow="Player Showcase",
        intro="포지션별 리더보드를 바로 기사형 카드로 쓸 수 있도록 정리한 페이지입니다. 쿼터백, 러닝백, 리시버, 수비 리더를 한 장씩 뽑아도 되고 통으로 써도 됩니다.",
        body=body,
        theme="--bg: radial-gradient(circle at top left, rgba(251,113,133,0.34), transparent 28%), radial-gradient(circle at bottom right, rgba(99,102,241,0.22), transparent 30%), linear-gradient(180deg, #fff3f5 0%, #f7f3ff 50%, #eef7ff 100%); --orb: radial-gradient(circle, rgba(244,114,182,0.68), rgba(244,114,182,0.0) 72%); --accent: linear-gradient(90deg, #f472b6, #6366f1);",
    )
    path = _story_root(output_root, season) / "skill-stars.html"
    path.write_text(html_text, encoding="utf-8")
    return path


def _build_fingerprint_story(output_root: Path, season: int, frames: dict[str, Any]) -> Path:
    team = frames["team"].copy()
    metrics = [
        "record_passing_yards",
        "record_rushing_yards",
        "record_receiving_yards",
        "record_defense_sacks",
        "record_touchdowns_total",
    ]
    for metric in metrics:
        team[metric] = _safe_numeric(team, metric)

    leaders = team.sort_values("record_touchdowns_total", ascending=False).head(12).copy()
    for metric in metrics:
        max_value = max(float(team[metric].max()), 1.0)
        leaders[f"{metric}_norm"] = leaders[metric] / max_value

    cards = []
    for _, row in leaders.iterrows():
        norm_values = [float(row[f"{metric}_norm"]) for metric in metrics]
        dominant_metric = metrics[norm_values.index(max(norm_values))]
        dominant_label = {
            "record_passing_yards": "air-led",
            "record_rushing_yards": "ground-led",
            "record_receiving_yards": "spacing-heavy",
            "record_defense_sacks": "pressure-first",
            "record_touchdowns_total": "finishers",
        }[dominant_metric]
        radar = _render_radar(norm_values, "#0f766e")
        cards.append(
            '<article class="panel">'
            f'<div class="kicker">{html.escape(_safe_text(row["team_alias"]))} · {html.escape(dominant_label)}</div>'
            f'<h3>{html.escape(_safe_text(row["team_name"]))}</h3>'
            f"{radar}"
            '<div class="chips">'
            f'<span class="chip">Pass {_format_number(row["record_passing_yards"])}</span>'
            f'<span class="chip">Rush {_format_number(row["record_rushing_yards"])}</span>'
            f'<span class="chip">Sacks {_format_number(row["record_defense_sacks"])}</span>'
            "</div>"
            "</article>"
        )

    summary_rows = [
        {
            "team": _safe_text(row["team_alias"]),
            "touchdowns": _format_number(row["record_touchdowns_total"]),
            "passing": _format_number(row["record_passing_yards"]),
            "rushing": _format_number(row["record_rushing_yards"]),
            "sacks": _format_number(row["record_defense_sacks"]),
        }
        for _, row in leaders.iterrows()
    ]

    body = (
        _render_stat_cards(
            [
                {"label": "Fingerprint Cards", "value": _format_number(len(leaders))},
                {"label": "Top Finisher", "value": f'{_safe_text(leaders.iloc[0]["team_alias"])} · {_format_number(leaders.iloc[0]["record_touchdowns_total"])} TD'},
                {"label": "Top Pressure Team", "value": f'{_safe_text(team.sort_values("record_defense_sacks", ascending=False).iloc[0]["team_alias"])} · {_format_number(team["record_defense_sacks"].max())}'},
                {"label": "Radar Axes", "value": "5"},
            ]
        )
        + '<section class="section-title">Small Multiples</section>'
        + '<section class="grid three">'
        + "".join(cards)
        + "</section>"
        + '<section class="section-title">Reference Table</section>'
        + '<section class="panel"><h3>Top Touchdown Profiles</h3>'
        + _story_table(summary_rows)
        + "</section>"
    )
    html_text = _render_story_shell(
        title=f"Franchise Fingerprints {season}",
        eyebrow="Identity Cards",
        intro="상위 득점 팀들의 성향을 5축 레이더 카드로 압축했습니다. 팀별 스타일을 한눈에 비교하거나 썸네일형 콘텐츠로 잘라 쓰기 좋습니다.",
        body=body,
        theme="--bg: radial-gradient(circle at top left, rgba(45,212,191,0.28), transparent 28%), radial-gradient(circle at right, rgba(251,191,36,0.22), transparent 30%), linear-gradient(180deg, #ecfeff 0%, #effcf6 48%, #fff8ea 100%); --orb: radial-gradient(circle, rgba(13,148,136,0.58), rgba(13,148,136,0.0) 72%); --accent: linear-gradient(90deg, #14b8a6, #f59e0b);",
    )
    path = _story_root(output_root, season) / "franchise-fingerprints.html"
    path.write_text(html_text, encoding="utf-8")
    return path


def _build_roster_story(output_root: Path, season: int, frames: dict[str, Any]) -> Path:
    pandas = _require_pandas()
    player = frames["player"].copy()
    team_counts = (
        player.groupby(["team_alias", "team_name"])["player_id"]
        .nunique()
        .reset_index(name="unique_players")
    )

    journeys = (
        player.groupby("player_id")
        .agg(
            player_name=("player_name", "first"),
            position=("position", "first"),
            team_count=("team_alias", "nunique"),
            teams=("team_alias", lambda values: sorted(set(values.dropna()))),
        )
        .reset_index()
    )
    journeys = journeys[journeys["team_count"] > 1].copy()

    team_hits: list[dict[str, Any]] = []
    for _, row in journeys.iterrows():
        for team_alias in row["teams"]:
            team_name_row = player[player["team_alias"] == team_alias].head(1)
            team_name = _safe_text(team_name_row.iloc[0]["team_name"]) if not team_name_row.empty else team_alias
            team_hits.append(
                {
                    "team_alias": team_alias,
                    "team_name": team_name,
                    "player_name": _safe_text(row["player_name"]),
                    "team_count": int(row["team_count"]),
                }
            )
    involvement = pandas.DataFrame(team_hits)
    involvement_rank = (
        involvement.groupby(["team_alias", "team_name"])
        .size()
        .reset_index(name="multi_team_players")
        .sort_values("multi_team_players", ascending=False)
        .head(12)
    )
    top_journeys = journeys.sort_values(["team_count", "player_name"], ascending=[False, True]).head(16)

    cards = []
    for _, row in top_journeys.iterrows():
        cards.append(
            '<article class="panel">'
            f'<div class="kicker">{html.escape(_safe_text(row["position"]))} · {html.escape(_format_number(row["team_count"]))} teams</div>'
            f'<h3>{html.escape(_safe_text(row["player_name"]))}</h3>'
            '<div class="chips">'
            + "".join(f'<span class="chip">{html.escape(_safe_text(team_alias))}</span>' for team_alias in row["teams"])
            + "</div></article>"
        )

    body = (
        _render_stat_cards(
            [
                {"label": "Multi-Team Players", "value": _format_number(len(journeys))},
                {"label": "Most Involved Team", "value": f'{_safe_text(involvement_rank.iloc[0]["team_alias"])} · {_format_number(involvement_rank.iloc[0]["multi_team_players"])}'},
                {"label": "Max Journey", "value": _format_number(top_journeys.iloc[0]["team_count"]) + " teams"},
                {"label": "League Teams", "value": _format_number(team_counts["team_alias"].nunique())},
            ]
        )
        + '<section class="section-title">Churn Hotspots</section>'
        + '<section class="grid two">'
        + '<section class="panel"><h3>Teams Touched by Multi-Team Players</h3>'
        + _render_rank_list(
            [
                {
                    "label": _safe_text(row["team_name"]),
                    "meta": _safe_text(row["team_alias"]),
                    "value": float(row["multi_team_players"]),
                }
                for _, row in involvement_rank.iterrows()
            ],
            "linear-gradient(90deg,#1d4ed8,#60a5fa)",
        )
        + "</section>"
        + '<section class="panel"><h3>Journey Cards</h3><div class="grid">'
        + "".join(cards[:8])
        + "</div></section></section>"
        + '<section class="section-title">Reference Table</section>'
        + '<section class="panel"><h3>Top Journeys</h3>'
        + _story_table(
            [
                {
                    "player": _safe_text(row["player_name"]),
                    "position": _safe_text(row["position"]),
                    "team_count": int(row["team_count"]),
                    "teams": " / ".join(_safe_text(team_alias) for team_alias in row["teams"]),
                }
                for _, row in top_journeys.iterrows()
            ]
        )
        + "</section>"
    )
    html_text = _render_story_shell(
        title=f"Roster Currents {season}",
        eyebrow="Movement Watch",
        intro="같은 시즌 안에서 여러 팀에 걸친 선수들을 따로 묶어, 변동성이 큰 팀과 회전 폭이 큰 선수들을 콘텐츠처럼 볼 수 있게 만든 페이지입니다.",
        body=body,
        theme="--bg: radial-gradient(circle at top left, rgba(59,130,246,0.32), transparent 28%), radial-gradient(circle at bottom right, rgba(14,165,233,0.22), transparent 32%), linear-gradient(180deg, #eef6ff 0%, #f4fbff 46%, #eef8ff 100%); --orb: radial-gradient(circle, rgba(59,130,246,0.64), rgba(59,130,246,0.0) 72%); --accent: linear-gradient(90deg, #2563eb, #38bdf8);",
    )
    path = _story_root(output_root, season) / "roster-currents.html"
    path.write_text(html_text, encoding="utf-8")
    return path


def build_story_html_bundle(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    season: int = 2025,
) -> list[Path]:
    output_root = output_root.expanduser().resolve()
    story_dir = _story_root(output_root, season)
    story_dir.mkdir(parents=True, exist_ok=True)
    frames = _load_story_frames(output_root, season)

    story_defs = [
        {
            "slug": "strategy-atlas",
            "title": f"Strategy Atlas {season}",
            "eyebrow": "Team Geometry",
            "description": "패스와 러시 생산량을 좌표로 배치해 팀 공격 구조와 수비 압박을 동시에 읽는 지도형 콘텐츠.",
            "tag_one": "Scatter",
            "tag_two": "Quadrants",
        },
        {
            "slug": "skill-stars",
            "title": f"Skill Stars {season}",
            "eyebrow": "Player Showcase",
            "description": "QB, RB, WR, 수비 리더를 카드형 리더보드로 정리한 기사형 HTML.",
            "tag_one": "Leaderboards",
            "tag_two": "Editorial",
        },
        {
            "slug": "franchise-fingerprints",
            "title": f"Franchise Fingerprints {season}",
            "eyebrow": "Identity Cards",
            "description": "상위 득점 팀의 스타일을 5축 레이더 카드로 비교하는 브랜드형 콘텐츠.",
            "tag_one": "Radar",
            "tag_two": "Small Multiples",
        },
        {
            "slug": "roster-currents",
            "title": f"Roster Currents {season}",
            "eyebrow": "Movement Watch",
            "description": "멀티팀 선수와 팀별 변동성을 정리한 움직임 중심 HTML 페이지.",
            "tag_one": "Churn",
            "tag_two": "Journeys",
        },
    ]

    paths = [
        _build_index_story(output_root, season, story_defs, frames),
        _build_strategy_story(output_root, season, frames),
        _build_skill_story(output_root, season, frames),
        _build_fingerprint_story(output_root, season, frames),
        _build_roster_story(output_root, season, frames),
    ]
    return paths
