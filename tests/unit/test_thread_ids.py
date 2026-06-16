from pathlib import Path

import pytest

from api.thread_ids import safe_child_path, safe_output_path, safe_session_dir, validate_thread_id


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
