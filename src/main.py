from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from sis_pipeline import (
    DEFAULT_BASE_URL,
    DEFAULT_LOCAL_SOURCE_ROOT,
    DEFAULT_OUTPUT_ROOT,
    build_seasons,
    build_html_validation_report,
    copy_local_raw_data,
    fetch_remote_raw_data,
    validate_seasons,
    write_manifest,
)
from sis_visual_stories import build_story_html_bundle


def add_year_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start-year", type=int, default=2016)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--season-type", choices=["REG", "PST"], default="REG")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync local SIS seasonal data and build parquet outputs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_local = subparsers.add_parser("sync-local", help="Copy existing local raw SIS data into this repo")
    add_year_args(sync_local)
    sync_local.add_argument("--source-root", type=Path, default=DEFAULT_LOCAL_SOURCE_ROOT)
    sync_local.add_argument("--overwrite", action="store_true")

    fetch = subparsers.add_parser("fetch", help="Fetch raw SIS data from the remote API into this repo")
    add_year_args(fetch)
    fetch.add_argument("--base-url", default=DEFAULT_BASE_URL)
    fetch.add_argument("--sleep-min", type=float, default=0.3)
    fetch.add_argument("--sleep-max", type=float, default=0.8)
    fetch.add_argument("--max-retries", type=int, default=5)
    fetch.add_argument("--include-rosters", action="store_true")

    build = subparsers.add_parser("build", help="Build parquet tables from raw SIS data")
    add_year_args(build)

    validate = subparsers.add_parser("validate", help="Validate parquet outputs")
    add_year_args(validate)

    report_html = subparsers.add_parser("report-html", help="Build a visual HTML validation report from parquet")
    report_html.add_argument("--season", type=int, default=2025)
    report_html.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    report_html.add_argument("--output", type=Path, default=None)
    report_html.add_argument("--limit", type=int, default=10)

    story_html = subparsers.add_parser("story-html", help="Build a bundle of editorial-style HTML story pages")
    story_html.add_argument("--season", type=int, default=2025)
    story_html.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)

    all_local = subparsers.add_parser("all-local", help="Copy local raw data, build parquet, and validate")
    add_year_args(all_local)
    all_local.add_argument("--source-root", type=Path, default=DEFAULT_LOCAL_SOURCE_ROOT)
    all_local.add_argument("--overwrite", action="store_true")

    all_fetch = subparsers.add_parser("all-fetch", help="Fetch remote raw data, build parquet, and validate")
    add_year_args(all_fetch)
    all_fetch.add_argument("--base-url", default=DEFAULT_BASE_URL)
    all_fetch.add_argument("--sleep-min", type=float, default=0.3)
    all_fetch.add_argument("--sleep-max", type=float, default=0.8)
    all_fetch.add_argument("--max-retries", type=int, default=5)
    all_fetch.add_argument("--include-rosters", action="store_true")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    sync_summary = None
    fetch_summary = None
    build_summary = None
    validation_summary = None
    source_mode = args.command
    source_root = getattr(args, "source_root", None)

    if args.command == "sync-local":
        sync_summary = copy_local_raw_data(
            source_root=args.source_root,
            output_root=args.output_root,
            start_year=args.start_year,
            end_year=args.end_year,
            overwrite=args.overwrite,
        )
    elif args.command == "fetch":
        fetch_summary = fetch_remote_raw_data(
            start_year=args.start_year,
            end_year=args.end_year,
            season_type=args.season_type,
            output_root=args.output_root,
            base_url=args.base_url,
            sleep_min=args.sleep_min,
            sleep_max=args.sleep_max,
            max_retries=args.max_retries,
            include_rosters=args.include_rosters,
        )
    elif args.command == "build":
        build_summary = build_seasons(
            output_root=args.output_root,
            start_year=args.start_year,
            end_year=args.end_year,
            season_type=args.season_type,
        )
    elif args.command == "validate":
        validation_summary = validate_seasons(
            output_root=args.output_root,
            start_year=args.start_year,
            end_year=args.end_year,
            season_type=args.season_type,
        )
    elif args.command == "report-html":
        report_path = build_html_validation_report(
            output_root=args.output_root,
            season=args.season,
            output_path=args.output,
            limit=args.limit,
        )
        print(f"[done] report -> {report_path}")
        return 0
    elif args.command == "story-html":
        story_paths = build_story_html_bundle(
            output_root=args.output_root,
            season=args.season,
        )
        for path in story_paths:
            print(f"[done] story -> {path}")
        return 0
    elif args.command == "all-local":
        sync_summary = copy_local_raw_data(
            source_root=args.source_root,
            output_root=args.output_root,
            start_year=args.start_year,
            end_year=args.end_year,
            overwrite=args.overwrite,
        )
        build_summary = build_seasons(
            output_root=args.output_root,
            start_year=args.start_year,
            end_year=args.end_year,
            season_type=args.season_type,
        )
        validation_summary = validate_seasons(
            output_root=args.output_root,
            start_year=args.start_year,
            end_year=args.end_year,
            season_type=args.season_type,
        )
    elif args.command == "all-fetch":
        fetch_summary = fetch_remote_raw_data(
            start_year=args.start_year,
            end_year=args.end_year,
            season_type=args.season_type,
            output_root=args.output_root,
            base_url=args.base_url,
            sleep_min=args.sleep_min,
            sleep_max=args.sleep_max,
            max_retries=args.max_retries,
            include_rosters=args.include_rosters,
        )
        build_summary = build_seasons(
            output_root=args.output_root,
            start_year=args.start_year,
            end_year=args.end_year,
            season_type=args.season_type,
        )
        validation_summary = validate_seasons(
            output_root=args.output_root,
            start_year=args.start_year,
            end_year=args.end_year,
            season_type=args.season_type,
        )

    manifest_path = write_manifest(
        output_root=args.output_root,
        start_year=args.start_year,
        end_year=args.end_year,
        season_type=args.season_type,
        source_mode=source_mode,
        source_root=source_root,
        sync_summary=sync_summary,
        fetch_summary=fetch_summary,
        build_summary=build_summary,
        validation_summary=validation_summary,
    )
    print(f"[done] manifest -> {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
