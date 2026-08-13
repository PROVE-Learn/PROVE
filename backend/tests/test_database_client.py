import pytest

from app.config import Settings
from app.db import client


class FailingAdmin:
    async def command(self, command: str) -> None:
        assert command == "ping"
        raise ConnectionError("MongoDB is unavailable")


class FailingMongoClient:
    def __init__(self, uri: str):
        self.uri = uri
        self.admin = FailingAdmin()
        self.closed = False

    def __getitem__(self, database_name: str):
        return {"name": database_name}

    def close(self) -> None:
        self.closed = True


def test_get_database_requires_a_connection():
    client._database = None

    with pytest.raises(RuntimeError, match="not connected"):
        client.get_database()


@pytest.mark.asyncio
async def test_connect_to_mongodb_surfaces_ping_failures(monkeypatch):
    created_clients = []

    def create_client(uri: str) -> FailingMongoClient:
        mongo_client = FailingMongoClient(uri)
        created_clients.append(mongo_client)
        return mongo_client

    monkeypatch.setattr(client, "AsyncIOMotorClient", create_client)
    settings = Settings(mongodb_uri="mongodb://unavailable:27017", mongodb_db_name="test_db")

    with pytest.raises(ConnectionError, match="unavailable"):
        await client.connect_to_mongodb(settings)

    assert created_clients[0].uri == "mongodb://unavailable:27017"
    assert client.get_database() == {"name": "test_db"}

    await client.close_mongodb_connection()
    assert created_clients[0].closed is True
