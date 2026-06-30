from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_legacy_vue_frontend_assets_are_retired():
    assert not (ROOT / "frontend" / "vue.config.js").exists()
    assert not (ROOT / "frontend" / "src" / "main.js").exists()
    assert not (ROOT / "Dockerfile.frontend").exists()
    assert not (ROOT / "nginx.conf").exists()


def test_compose_is_backend_only():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())

    assert "frontend" not in compose["services"]
    assert compose["services"]["backend"]["build"]["dockerfile"] == "Dockerfile.backend"


def test_ci_has_frontend_demo_console_job():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())

    frontend = workflow["jobs"]["frontend"]
    assert frontend["name"] == "Frontend Demo Console"

    serialized = yaml.safe_dump(frontend, sort_keys=False)
    assert "actions/setup-node" in serialized
    assert "frontend/package-lock.json" in serialized
    assert "npm ci" in serialized
    assert "npm run test" in serialized
    assert "npm run lint" in serialized
    assert "npm run build" in serialized


def test_dependabot_tracks_frontend_npm():
    config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text())

    updates = config["updates"]
    frontend_npm = [
        entry for entry in updates
        if entry.get("package-ecosystem") == "npm"
        and entry.get("directory") == "/frontend"
    ]

    assert frontend_npm == [
        {
            "package-ecosystem": "npm",
            "directory": "/frontend",
            "schedule": {"interval": "weekly"},
            "open-pull-requests-limit": 2,
        }
    ]
