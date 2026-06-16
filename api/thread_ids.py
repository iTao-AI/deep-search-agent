import os
import re
import shutil
from pathlib import Path
from typing import BinaryIO


_THREAD_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def validate_thread_id(thread_id: str) -> str:
    if not _THREAD_ID_PATTERN.fullmatch(thread_id):
        raise ValueError("thread_id must use 1-128 letters, digits, dots, underscores, or hyphens")
    return thread_id


def _safe_session_name(thread_id: str) -> str:
    validated = validate_thread_id(thread_id)
    safe_name = Path(validated).name
    if safe_name != validated:
        raise ValueError("thread_id resolves outside session root")
    return f"session_{safe_name}"


def safe_session_dir(root: Path, thread_id: str) -> Path:
    resolved_root = os.path.realpath(root)
    session_name = _safe_session_name(thread_id)
    session_dir = os.path.realpath(os.path.join(resolved_root, session_name))
    if os.path.commonpath([resolved_root, session_dir]) != resolved_root:
        raise ValueError("thread_id resolves outside session root")
    return Path(session_dir)


def ensure_session_dir(root: Path, thread_id: str) -> Path:
    resolved_root = os.path.realpath(root)
    session_name = _safe_session_name(thread_id)
    session_dir = os.path.realpath(os.path.join(resolved_root, session_name))
    if os.path.commonpath([resolved_root, session_dir]) != resolved_root:
        raise ValueError("thread_id resolves outside session root")
    os.makedirs(session_dir, exist_ok=True)
    return Path(session_dir)


def save_session_file(
    root: Path,
    thread_id: str,
    filename: str,
    source: BinaryIO,
) -> str:
    resolved_root = os.path.realpath(root)
    session_name = _safe_session_name(thread_id)
    session_dir = os.path.realpath(os.path.join(resolved_root, session_name))
    if os.path.commonpath([resolved_root, session_dir]) != resolved_root:
        raise ValueError("thread_id resolves outside session root")
    os.makedirs(session_dir, exist_ok=True)

    parts = _safe_relative_parts(filename)
    if len(parts) != 1:
        raise ValueError("path resolves outside root")
    file_path = os.path.realpath(os.path.join(session_dir, *parts))
    if os.path.commonpath([session_dir, file_path]) != session_dir:
        raise ValueError("path resolves outside root")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(source, buffer)
    return parts[0]


def copy_session_files(
    *,
    source_root: Path,
    destination_root: Path,
    thread_id: str,
) -> list[str]:
    source_root_real = os.path.realpath(source_root)
    destination_root_real = os.path.realpath(destination_root)
    session_name = _safe_session_name(thread_id)
    source_dir = os.path.realpath(os.path.join(source_root_real, session_name))
    destination_dir = os.path.realpath(os.path.join(destination_root_real, session_name))
    if os.path.commonpath([source_root_real, source_dir]) != source_root_real:
        raise ValueError("thread_id resolves outside source root")
    if os.path.commonpath([destination_root_real, destination_dir]) != destination_root_real:
        raise ValueError("thread_id resolves outside destination root")
    os.makedirs(destination_dir, exist_ok=True)

    if not os.path.isdir(source_dir):
        return []

    copied = []
    for filename in sorted(os.listdir(source_dir)):
        parts = _safe_relative_parts(filename)
        if len(parts) != 1:
            continue
        source_path = os.path.realpath(os.path.join(source_dir, parts[0]))
        destination_path = os.path.realpath(os.path.join(destination_dir, parts[0]))
        if os.path.commonpath([source_dir, source_path]) != source_dir:
            continue
        if os.path.commonpath([destination_dir, destination_path]) != destination_dir:
            continue
        if not os.path.isfile(source_path):
            continue
        shutil.copy2(source_path, destination_path)
        copied.append(parts[0])
    return copied


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
