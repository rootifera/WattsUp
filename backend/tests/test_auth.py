from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from wattsup.core.auth import hash_password
from wattsup.core.config import get_settings
from wattsup.main import create_app
from wattsup.models.configuration import Administrator


def test_protected_endpoint_requires_authentication(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SSH_KEY_PATH", str(tmp_path / "id_ed25519"))
    get_settings.cache_clear()
    with TestClient(create_app()) as client:
        response = client.get("/api/status")

    assert response.status_code == 401
    get_settings.cache_clear()


def test_admin_can_log_in(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-at-least-32-characters")
    monkeypatch.setenv("SSH_KEY_PATH", str(tmp_path / "id_ed25519"))
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as client:

        async def create_administrator() -> None:
            async with app.state.database.sessions() as session:
                session.add(
                    Administrator(
                        username="admin",
                        password_hash=hash_password("a-secure-test-password"),
                    )
                )
                await session.commit()

        client.portal.call(create_administrator)
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "a-secure-test-password"},
        )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]
    get_settings.cache_clear()
