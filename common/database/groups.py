import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, List, Optional

import discord


@dataclass
class Group:
    db: Any
    _id: str
    creator: str
    name: str
    description: str
    guild_id: Optional[str] = None
    members: List[str] = field(default_factory=list)

    @property
    def id(self):
        return self._id

    def to_dict(self):
        return {
            "_id": self._id,
            "creator": self.creator,
            "name": self.name,
            "description": self.description,
            "members": self.members
        }

    @classmethod
    def create(cls, db, creator: str, name: str, description: str) -> "Group":
        new_id = str(uuid.uuid4())
        group = cls(db=db, _id=new_id, creator=creator, name=name, description=description)
        return group

    async def save(self):
        group_dict = asdict(self)
        group_dict.pop('db')
        group_dict.pop('guild_id')
        await self.db.guilds.update_one(
            {"_id": self.guild_id},
            {"$push": {"groups": group_dict}}
        )

    @classmethod
    async def from_existing(cls, db, guild_id: str, data: dict) -> "Group":
        return cls(db=db, guild_id=guild_id, **data)

    async def update_fields(self, **kwargs):
        allowed_fields = set(self.__annotations__.keys()) - {'guild_id', 'db'}
        update_data = {f'groups.$.{key}': value for key, value in kwargs.items() if key in allowed_fields}
        await self.db.guilds.update_one(
            {"_id": self.guild_id, "groups._id": self._id},
            {"$set": update_data}
        )

    async def add_member(self, member: str):
        self.members.append(member)
        await self.update_fields(members=self.members)

    async def remove_member(self, member: str):
        self.members.remove(member)
        await self.update_fields(members=self.members)

    def get_members(self, guild: discord.Guild):
        members = guild.members
        available = [member for member in members if str(member.id) in self.members]
        return available
