def test_database_path_uses_only_canonical_env(monkeypatch, tmp_path):
    from api.database import application_db_path

    canonical = tmp_path / "decision_research_agent.db"
    monkeypatch.setenv("DECISION_RESEARCH_AGENT_DB_PATH", str(canonical))
    monkeypatch.setenv("TASKS_DB_PATH", str(tmp_path / "ignored.db"))

    assert application_db_path() == canonical.resolve()


def test_old_env_alone_is_not_read(monkeypatch, tmp_path):
    from api.database import application_db_path

    old = tmp_path / "old.db"
    monkeypatch.delenv("DECISION_RESEARCH_AGENT_DB_PATH", raising=False)
    monkeypatch.setenv("TASKS_DB_PATH", str(old))

    path = application_db_path()

    assert path.name == "decision_research_agent.db"
    assert path.parent.name == "data"
    assert path != old.resolve()
