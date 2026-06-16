from pathlib import Path

import pytest

from io import BytesIO

from api.thread_ids import (
    copy_session_files,
    ensure_session_dir,
    safe_child_path,
    safe_output_path,
    safe_session_dir,
    save_session_file,
    validate_thread_id,
)


def test_validate_thread_id_rejects_path_traversal():
    with pytest.raises(ValueError, match="thread_id"):
        validate_thread_id("../../../../../../tmp/escape")


def test_safe_session_dir_stays_inside_root(tmp_path):
    session_dir = safe_session_dir(tmp_path, "thread-001")

    assert session_dir == Path(tmp_path, "session_thread-001")
    assert session_dir.resolve().is_relative_to(tmp_path.resolve())


def test_safe_child_path_rejects_nested_path_components(tmp_path):
    with pytest.raises(ValueError, match="path"):
        safe_child_path(tmp_path, "../escape.txt")


def test_safe_child_path_accepts_sanitized_filename(tmp_path):
    child = safe_child_path(tmp_path, "report.md")

    assert child == (tmp_path / "report.md").resolve()
    assert child.is_relative_to(tmp_path.resolve())


def test_safe_output_path_rejects_absolute_path_outside_root(tmp_path):
    outside = tmp_path.parent / "outside.md"

    with pytest.raises(ValueError, match="path"):
        safe_output_path(tmp_path, str(outside))


def test_safe_output_path_accepts_output_prefixed_relative_path(tmp_path):
    child = safe_output_path(tmp_path, "output/session-1/report.md")

    assert child == (tmp_path / "session-1" / "report.md").resolve()
    assert child.is_relative_to(tmp_path.resolve())


def test_ensure_session_dir_creates_directory_inside_root(tmp_path):
    session_dir = ensure_session_dir(tmp_path, "thread-001")

    assert session_dir == (tmp_path / "session_thread-001").resolve()
    assert session_dir.is_dir()


def test_save_session_file_writes_inside_session_dir(tmp_path):
    saved = save_session_file(
        tmp_path,
        "thread-001",
        "notes.txt",
        BytesIO(b"hello"),
    )

    assert saved == "notes.txt"
    assert (tmp_path / "session_thread-001" / "notes.txt").read_bytes() == b"hello"


def test_copy_session_files_copies_only_files(tmp_path):
    upload_dir = ensure_session_dir(tmp_path / "updated", "thread-001")
    upload_dir.joinpath("notes.txt").write_text("hello", encoding="utf-8")
    upload_dir.joinpath("nested").mkdir()

    copied = copy_session_files(
        source_root=tmp_path / "updated",
        destination_root=tmp_path / "output",
        thread_id="thread-001",
    )

    assert copied == ["notes.txt"]
    assert (
        tmp_path / "output" / "session_thread-001" / "notes.txt"
    ).read_text(encoding="utf-8") == "hello"
