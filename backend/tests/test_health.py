from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from wattsup.core.config import get_settings
from wattsup.main import create_app


def test_health(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SSH_KEY_PATH", str(tmp_path / "id_ed25519"))
    get_settings.cache_clear()
    with TestClient(create_app()) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    get_settings.cache_clear()
