from tests.integration.test_durable_review_container import (
    _ensure_compose_env_file,
)


def test_compose_env_file_is_created_and_removed_when_missing(tmp_path):
    env_path = tmp_path / ".env"

    with _ensure_compose_env_file(tmp_path):
        assert env_path.read_text(encoding="utf-8").startswith(
            "# Created temporarily"
        )

    assert not env_path.exists()


def test_compose_env_file_preserves_existing_content(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("API_SECRET=existing\n", encoding="utf-8")

    with _ensure_compose_env_file(tmp_path):
        assert env_path.read_text(encoding="utf-8") == "API_SECRET=existing\n"

    assert env_path.read_text(encoding="utf-8") == "API_SECRET=existing\n"
