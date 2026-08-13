import httpx
import pytest

from app.main import create_app


class ConnectedDatabase:
    async def command(self, command: str) -> None:
        assert command == "ping"


class FailingDatabase:
    async def command(self, command: str) -> None:
        raise ConnectionError("MongoDB is unavailable")


async def request_health() -> httpx.Response:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/health")


@pytest.mark.asyncio
async def test_health_reports_disconnected_when_database_is_not_initialized(monkeypatch):
    def unavailable_database():
        raise RuntimeError("Database is not connected")

    monkeypatch.setattr("app.api.routes.health.get_database", unavailable_database)

    response = await request_health()

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "app_name": "PROVE",
        "database": "disconnected",
    }


@pytest.mark.asyncio
async def test_health_reports_connected_database(monkeypatch):
    monkeypatch.setattr("app.api.routes.health.get_database", lambda: ConnectedDatabase())

    response = await request_health()

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "connected"


@pytest.mark.asyncio
async def test_health_reports_database_error(monkeypatch):
    monkeypatch.setattr("app.api.routes.health.get_database", lambda: FailingDatabase())

    response = await request_health()

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["database"] == "error"
