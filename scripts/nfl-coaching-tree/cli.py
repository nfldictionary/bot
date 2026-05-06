from __future__ import annotations

import argparse
import sys

from config import ensure_data_readme, ensure_gitignore_entries, ensure_storage_layout
from crawler import run_crawl
from exporter import run_export
from neo4j_import import run_import
from normalizer import run_normalize
from parser import run_parse
from shared import PipelineError, build_common_parser, ensure_repo_and_local_paths, resolve_runtime_config
from validator import run_validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NFL coaching tree migration pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in (
        "setup-storage",
        "crawl",
        "parse",
        "normalize",
        "validate",
        "import",
        "export",
        "all",
    ):
        command_parser = subparsers.add_parser(command)
        common = build_common_parser()
        for action in common._actions:
            if action.dest == "help":
                continue
            command_parser._add_action(action)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        config = resolve_runtime_config(args.command, args)
        ensure_repo_and_local_paths(config)
        if args.command == "setup-storage":
            run_setup_storage(config)
        elif args.command == "crawl":
            run_setup_storage(config)
            run_crawl(config)
        elif args.command == "parse":
            run_setup_storage(config)
            run_parse(config)
        elif args.command == "normalize":
            run_setup_storage(config)
            run_normalize(config)
        elif args.command == "validate":
            run_setup_storage(config)
            run_validate(config)
        elif args.command == "import":
            run_setup_storage(config)
            run_import(config)
        elif args.command == "export":
            run_setup_storage(config)
            run_export(config)
        elif args.command == "all":
            run_setup_storage(config)
            run_crawl(config)
            run_parse(config)
            run_normalize(config)
            run_validate(config)
            run_import(config)
            run_export(config)
        return 0
    except PipelineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def run_setup_storage(config) -> None:
    if config.dry_run:
        print(f"[dry-run] repo path: {config.repo_path}")
        print(f"[dry-run] local data root: {config.local_data_root}")
        return
    ensure_storage_layout(config)
    ensure_data_readme(config)
    ensure_gitignore_entries(config.repo_path)


if __name__ == "__main__":
    raise SystemExit(main())
