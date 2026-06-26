from __future__ import annotations

import argparse
import json
from pathlib import Path


FORBIDDEN_TERMS = (
    "deep-search-agent",
    "Deep Search Agent",
    "deep_search_agent",
    "deep_search",
    "DEEP_SEARCH_AGENT_",
    "deep_search_agent_tool",
    "TASKS_DB_PATH",
    "/api/task",
    "/api/tasks",
    "/api/research/runs",
)

HISTORICAL_PREFIXES = (
    "docs/evidence/",
    "docs/superpowers/",
    "openspec/",
)

HISTORICAL_FILES = {
    "CHANGELOG.md",
}

NEGATIVE_CONTRACT_FILES = {
    "scripts/check_canonical_identity.py",
    "tests/integration/test_legacy_runtime_removed.py",
}

SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "htmlcov",
}

SKIP_SUFFIXES = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".pyc",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
}


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_skipped(relative_path: str) -> bool:
    if relative_path in HISTORICAL_FILES:
        return True
    if relative_path in NEGATIVE_CONTRACT_FILES:
        return True
    if any(relative_path.startswith(prefix) for prefix in HISTORICAL_PREFIXES):
        return True
    return False


def _iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        relative_path = _relative(path, root)
        parts = set(Path(relative_path).parts)
        if parts & SKIP_DIRS:
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if _is_skipped(relative_path):
            continue
        yield path, relative_path


def find_forbidden_terms(root: Path) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    for path, relative_path in _iter_files(root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            for term in FORBIDDEN_TERMS:
                if term in line:
                    violations.append(
                        {
                            "path": relative_path,
                            "line": line_number,
                            "term": term,
                        }
                    )
    return violations


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check that active files use the canonical technical identity."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    violations = find_forbidden_terms(args.root.resolve())
    result = {
        "status": "ok" if not violations else "failed",
        "violations": violations,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
