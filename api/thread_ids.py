import os
import re
from pathlib import Path


_THREAD_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def validate_thread_id(thread_id: str) -> str:
    if not _THREAD_ID_PATTERN.fullmatch(thread_id):
        raise ValueError("thread_id must use 1-128 letters, digits, dots, underscores, or hyphens")
    return thread_id


def safe_session_dir(root: Path, thread_id: str) -> Path:
    validated = validate_thread_id(thread_id)
    resolved_root = os.path.realpath(root)
    safe_name = Path(validated).name
    if safe_name != validated:
        raise ValueError("thread_id resolves outside session root")
    session_dir = os.path.realpath(os.path.join(resolved_root, f"session_{safe_name}"))
    if os.path.commonpath([resolved_root, session_dir]) != resolved_root:
        raise ValueError("thread_id resolves outside session root")
    return Path(session_dir)


def _safe_relative_parts(path_value: str) -> tuple[str, ...]:
    normalized = path_value.replace("\\", "/").strip()
    if "\x00" in normalized:
        raise ValueError("path contains invalid characters")
    if not normalized:
        return ()

    parts = tuple(part for part in normalized.split("/") if part)
    for part in parts:
        if part in (".", "..") or Path(part).name != part:
            raise ValueError("path resolves outside root")
    return parts


def safe_child_path(root: Path, relative_path: str) -> Path:
    resolved_root = os.path.realpath(root)
    parts = _safe_relative_parts(relative_path)
    child = os.path.realpath(os.path.join(resolved_root, *parts))
    if os.path.commonpath([resolved_root, child]) != resolved_root:
        raise ValueError("path resolves outside root")
    return Path(child)


def safe_output_path(root: Path, requested_path: str) -> Path:
    resolved_root = root.resolve()
    requested = requested_path.replace("\\", "/").strip()
    root_text = resolved_root.as_posix()

    if requested == root_text:
        relative = ""
    elif requested.startswith(f"{root_text}/"):
        relative = requested[len(root_text) + 1:]
    elif requested.startswith("/"):
        raise ValueError("path resolves outside root")
    elif requested == "output":
        relative = ""
    elif requested.startswith("output/"):
        relative = requested[len("output/"):]
    elif requested == resolved_root.name:
        relative = ""
    elif requested.startswith(f"{resolved_root.name}/"):
        relative = requested[len(resolved_root.name) + 1:]
    else:
        relative = requested

    return safe_child_path(resolved_root, relative)
