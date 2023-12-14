import logging
import os
from typing import Optional

import motor.motor_asyncio
import pymongo.errors
from motor.core import AgnosticCollection, AgnosticDatabase

from common.database.groups import Group
from common.database.guilds import Guild


class Database:
    def __init__(self):
        self.log = logging.getLogger("database")
        db_user = os.getenv("DB_USER")
        db_pass = os.getenv("DB_PASS")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", 27017)
        db_name = os.getenv("DB_NAME", "groups")
        db_auth = os.getenv("DB_AUTH", db_name)
        self.uri = f"mongodb://{db_user}:{db_pass}@{db_host}:{db_port}?authSource={db_auth}"
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.uri)
        self.database: AgnosticDatabase = self.client[os.getenv("DB_NAME")]
        self.guilds: Optional[AgnosticCollection] = None

    #############################################
    # Core operations                           #
    #############################################

    @classmethod
    async def create(cls):
        db = Database()
        try:
            await db._init()
            db.log.info(f"Mongo connected to {db.database.name}!")
        except Exception as e:
            db.log.error(f"Failed to initialize database: {e}")
            raise
        return db

    async def _init(self):
        collections = ["guilds"]
        for collection_name in collections:
            try:
                await self.database.create_collection(collection_name)
                self.log.info(f"Created the {collection_name} collection")
            except pymongo.errors.CollectionInvalid:
                self.log.info(f"The {collection_name} collection already exists!")
            except Exception as e:
                self.log.error(f"Failed to create collection {collection_name}: {e}")
                raise
            setattr(self, collection_name, self.database[collection_name])

    #
    async def get_guild(self, guild_id: str) -> Guild:
        guild_data = await self.guilds.find_one({"_id": guild_id})
        if guild_data:
            return Guild.from_existing(self, guild_id, dict(guild_data))
        new_guild = Guild.create(self, guild_id)
        await new_guild.save()
        return new_guild

    async def get_group(self, guild_id: str, group_id: str) -> Optional[Group]:
        guild = await self.get_guild(guild_id)
        for group in guild.groups:
            if group.id == group_id:
                return group
        return None
