"""Small script to inspect saved weekly plans in the local MongoDB used by the app.

Usage:
    python -m scripts.inspect_plans

This script uses the same `app.config.get_settings` and `app.db.client` helpers as the app.
"""
from pprint import pprint
from app.config import get_settings
from app.db.client import AsyncIOMotorClient, get_database

# Use a quick async runner since motor needs an event loop
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    cursor = db["learning_sessions"].find({})
    docs = []
    async for d in cursor:
        docs.append(d)
    pprint(docs)
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
