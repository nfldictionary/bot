from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from schema import (
    BACKUP_ROOT_SEGMENT,
    CACHE_ROOT_SEGMENT,
    DEFAULT_SOURCE_BASE_URL,
    DEFAULT_USER_AGENT,
    EXPORT_ROOT_SEGMENT,
    LOG_ROOT_SEGMENT,
    MANIFEST_FILENAMES,
    METHODOLOGY_VERSION,
    RAW_ROOT_SEGMENT,
    SCRIPT_VERSION,
)


class PipelineError(RuntimeError):
    pass


@dataclass
class RuntimeConfig:
    command: str
    repo_url: str
    branch: str
    repo_path: Path
    local_data_root: Path
    source_base_url: str
    run_id: str
    dry_run: bool
    resume: bool
    max_pages: int
    max_coaches: int
    verbose: bool
    concurrency: int
    request_delay_ms: int
    retry_limit: int
    timeout_ms: int
    methodology_version: str
    script_version: str
    user_agent: str

    @property
    def data_root(self) -> Path:
        return self.repo_path / "data" / "nfl-coaching-tree"

    @property
    def canonical_dir(self) -> Path:
        return self.data_root / "canonical"

    @property
    def staging_dir(self) -> Path:
        return self.data_root / "staging"

    @property
    def manifests_dir(self) -> Path:
        return self.data_root / "manifests"

    @property
    def validation_dir(self) -> Path:
        return self.data_root / "validation"

    @property
    def docs_dir(self) -> Path:
        return self.repo_path / "docs"

    @property
    def scripts_dir(self) -> Path:
        return self.repo_path / "scripts" / "nfl-coaching-tree"

    @property
    def migrations_dir(self) -> Path:
        return self.repo_path / "db" / "neo4j" / "migrations"

    @property
    def raw_snapshot_base_dir(self) -> Path:
        return self.local_data_root / RAW_ROOT_SEGMENT

    @property
    def raw_snapshot_run_dir(self) -> Path:
        return self.raw_snapshot_base_dir / self.run_id

    @property
    def cache_dir(self) -> Path:
        return self.local_data_root / CACHE_ROOT_SEGMENT

    @property
    def run_log_dir(self) -> Path:
        return self.local_data_root / LOG_ROOT_SEGMENT

    @property
    def export_dir(self) -> Path:
        return self.local_data_root / EXPORT_ROOT_SEGMENT

    @property
    def backup_dir(self) -> Path:
        return self.local_data_root / BACKUP_ROOT_SEGMENT

    @property
    def pipeline_manifest_path(self) -> Path:
        return self.manifests_dir / MANIFEST_FILENAMES["pipeline"]

    @property
    def git_commit_hash(self) -> str | None:
        try:
            return (
                subprocess.check_output(
                    ["git", "-C", str(self.repo_path), "rev-parse", "HEAD"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )
                .strip()
                or None
            )
        except Exception:
            return None


def build_common_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="NFL coaching-tree.app migration pipeline",
    )
    parser.add_argument("--repo-url", default=None)
    parser.add_argument("--branch", default=None)
    parser.add_argument("--repo-path", default=None)
    parser.add_argument("--local-data-root", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--max-coaches", type=int, default=10)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--config", default=None)
    return parser


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def generate_run_id() -> str:
    return f"{now_stamp()}-coaching-tree-app"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    atomic_write_text(path, content)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def append_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def normalize_name(value: str) -> str:
    return " ".join(value.lower().split())


def safe_slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    slug = parsed.path.strip("/").replace("/", "__") or "root"
    return slug


def is_placeholder(value: str | None) -> bool:
    if not value:
        return True
    return "<" in value or ">" in value or value.startswith("/absolute/path/to")


def resolve_runtime_config(command: str, args: argparse.Namespace) -> RuntimeConfig:
    config_payload = load_config_payload(args.config)
    repo_url = (
        args.repo_url
        or os.environ.get("TARGET_GIT_REPO_URL")
        or config_payload.get("targetGitRepoUrl")
        or "https://github.com/<owner>/<repo>.git"
    )
    branch = (
        args.branch
        or os.environ.get("TARGET_GIT_BRANCH")
        or config_payload.get("targetGitBranch")
        or "main"
    )
    repo_path_value = (
        args.repo_path
        or os.environ.get("TARGET_REPO_PATH")
        or config_payload.get("targetRepoPath")
    )
    local_data_root_value = (
        args.local_data_root
        or os.environ.get("LOCAL_DATA_ROOT")
        or config_payload.get("localDataRoot")
    )
    if is_placeholder(repo_path_value):
        raise PipelineError(
            "The target repository path is still a placeholder. "
            "Pass --repo-path /real/path/to/repo or set TARGET_REPO_PATH."
        )
    if is_placeholder(local_data_root_value):
        raise PipelineError(
            "The local data root is still a placeholder. "
            "Pass --local-data-root /real/path/to/nfl-coaching-tree-data or set LOCAL_DATA_ROOT."
        )

    return RuntimeConfig(
        command=command,
        repo_url=repo_url,
        branch=branch,
        repo_path=Path(repo_path_value).expanduser().resolve(),
        local_data_root=Path(local_data_root_value).expanduser().resolve(),
        source_base_url=config_payload.get("sourceBaseUrl", DEFAULT_SOURCE_BASE_URL),
        run_id=args.run_id or generate_run_id(),
        dry_run=bool(args.dry_run),
        resume=bool(args.resume),
        max_pages=max(1, int(args.max_pages or 2)),
        max_coaches=max(1, int(args.max_coaches or 10)),
        verbose=bool(args.verbose),
        concurrency=int(config_payload.get("concurrency", 2)),
        request_delay_ms=int(config_payload.get("requestDelayMs", 1000)),
        retry_limit=int(config_payload.get("retryLimit", 3)),
        timeout_ms=int(config_payload.get("timeoutMs", 30000)),
        methodology_version=config_payload.get("methodologyVersion", METHODOLOGY_VERSION),
        script_version=config_payload.get("scriptVersion", SCRIPT_VERSION),
        user_agent=config_payload.get("userAgent", DEFAULT_USER_AGENT),
    )


def load_config_payload(config_path: str | None) -> dict[str, Any]:
    if config_path:
        path = Path(config_path).expanduser().resolve()
        return load_json(path, {}) or {}
    local_default = Path(__file__).resolve().parents[2] / "config" / "nflCoachingTreeMigration.config.local.json"
    return load_json(local_default, {}) or {}


def ensure_target_repo(config: RuntimeConfig) -> None:
    if config.repo_path.exists():
        if not (config.repo_path / ".git").exists():
            raise PipelineError(
                f"TARGET_REPO_PATH exists but is not a Git repository: {config.repo_path}. "
                "Choose an existing repo path or provide a cloneable repo URL."
            )
        return
    if is_placeholder(config.repo_url):
        raise PipelineError(
            f"TARGET_REPO_PATH does not exist: {config.repo_path}. "
            "A real TARGET_GIT_REPO_URL is required to clone into that path."
        )
    parent = config.repo_path.parent
    if not parent.exists():
        raise PipelineError(
            f"Parent directory for TARGET_REPO_PATH does not exist: {parent}. "
            "Create it first or choose a writable path."
        )
    if config.dry_run:
        return
    subprocess.run(
        ["git", "clone", config.repo_url, str(config.repo_path)],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(config.repo_path), "checkout", config.branch],
        check=True,
    )


def ensure_local_root_parent(config: RuntimeConfig) -> None:
    parent = config.local_data_root.parent
    if not parent.exists():
        raise PipelineError(
            f"The parent directory for LOCAL_DATA_ROOT does not exist: {parent}. "
            "Create the parent folder or choose another writable path."
        )


def ensure_repo_and_local_paths(config: RuntimeConfig) -> None:
    ensure_target_repo(config)
    ensure_local_root_parent(config)


def repo_relative(config: RuntimeConfig, path: Path) -> str:
    try:
        return str(path.relative_to(config.repo_path))
    except ValueError:
        return str(path)


def display_repo_path(config: RuntimeConfig, path: Path) -> str:
    try:
        relative = path.relative_to(config.repo_path).as_posix()
        return f"<TARGET_REPO_PATH>/{relative}" if relative else "<TARGET_REPO_PATH>"
    except ValueError:
        return str(path)


def display_local_path(config: RuntimeConfig, path: Path) -> str:
    try:
        relative = path.relative_to(config.local_data_root).as_posix()
        return f"<LOCAL_DATA_ROOT>/{relative}" if relative else "<LOCAL_DATA_ROOT>"
    except ValueError:
        return str(path)


def backup_directory(source_dir: Path, backup_target: Path) -> None:
    if not source_dir.exists():
        return
    if backup_target.exists():
        shutil.rmtree(backup_target)
    backup_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, backup_target)


def ensure_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def update_pipeline_manifest(config: RuntimeConfig, updates: dict[str, Any]) -> None:
    payload = load_json(config.pipeline_manifest_path, {}) or {}
    payload.update(
        {
            "runId": config.run_id,
            "sourceBaseUrl": config.source_base_url,
            "targetRepoPath": "<TARGET_REPO_PATH>",
            "localDataRoot": "<LOCAL_DATA_ROOT>",
            "rawSnapshotDir": display_local_path(config, config.raw_snapshot_run_dir),
            "stagingOutputDir": display_repo_path(config, config.staging_dir),
            "canonicalOutputDir": display_repo_path(config, config.canonical_dir),
            "validationOutputDir": display_repo_path(config, config.validation_dir),
            "importManifestPath": display_repo_path(config, config.manifests_dir / MANIFEST_FILENAMES["import"]),
            "scriptVersion": config.script_version,
            "methodologyVersion": config.methodology_version,
            "gitCommitHash": config.git_commit_hash,
            "updatedAt": datetime.now().isoformat(timespec="seconds"),
        }
    )
    payload.update(updates)
    if not config.dry_run:
        write_json(config.pipeline_manifest_path, payload)
