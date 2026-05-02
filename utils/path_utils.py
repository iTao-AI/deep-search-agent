import os
from pathlib import Path
from typing import Optional


def resolve_path(filename: str, session_dir: Optional[str] = None) -> str:
    """
    Resolve a file path relative to session_dir with safety checks.

    - Strips virtual path prefixes (/workspace, /mnt/data, /home/user)
    - Detects updated/ directory and resolves relative to CWD
    - Combines with session_dir for path isolation
    - Prevents nested session_id duplication
    """
    path = Path(filename)
    path_str = filename.replace("\\", "/")

    # Strip virtual path prefixes
    virtual_prefixes = ["/workspace", "/mnt/data", "/home/user"]
    for prefix in virtual_prefixes:
        if path_str.startswith(prefix):
            cleaned = path_str[len(prefix):].lstrip("/")
            path = Path(cleaned)
            path_str = str(path).replace("\\", "/")
            break

    # Special handling: updated/ (uploaded files)
    if "updated/" in path_str:
        idx = path_str.find("updated/")
        relative_part = path_str[idx:]
        return str(Path(relative_part).resolve())

    if not session_dir:
        return str(path.resolve())

    session_path = Path(session_dir).resolve()
    session_name = session_path.name

    is_unix_abs = path_str.startswith("/")

    if path.is_absolute() or (os.name == 'nt' and is_unix_abs):
        if os.name == 'nt' and is_unix_abs and not path.drive:
            full_path = session_path / path_str.lstrip("/")
        else:
            full_path = path.resolve()

        try:
            if session_path in full_path.parents or full_path == session_path:
                # Prevent nested session dirs
                parts = full_path.parts
                for i in range(len(parts) - 1):
                    if parts[i] == session_name and parts[i + 1] == session_name:
                        return str(session_path / full_path.name)
                return str(full_path)
        except Exception:
            pass

        return str(full_path)

    else:
        parts = path.parts

        if session_name in parts:
            return str(session_path / path.name)

        if parts and parts[0] == "output":
            return str(session_path / path.name)

        return str(session_path / path)
