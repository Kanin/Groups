from dataclasses import dataclass, field, asdict
from typing import Any, List, Optional
from .groups import Group
from ..functions.text import normalize_text


@dataclass
class Guild:
    db: Any
    _id: str
    create_roles: List[str] = field(default_factory=list)
    groups: List[Group] = field(default_factory=list)

    def to_dict(self):
        return {
            "_id": self._id,
            "create_roles": self.create_roles,
            "groups": [group.to_dict() for group in self.groups]
        }

    @classmethod
    def create(cls, db, guild_id: str) -> "Guild":
        guild = cls(db=db, _id=guild_id)
        return guild

    async def save(self):
        guild_dict = self.to_dict()
        await self.db.guilds.insert_one(guild_dict)

    @classmethod
    def from_existing(cls, db, guild_id: str, data: dict) -> "Guild":
        groups = [Group(**group_data, guild_id=guild_id, db=db) for group_data in data.get('groups', [])]
        groups.sort(key=lambda group: group.name.lower())
        data.pop('groups')
        return cls(db=db, groups=groups, **data)

    async def update_fields(self):
        update_data = self.to_dict()
        await self.db.guilds.update_one(
            {"_id": self._id},
            {"$set": update_data}
        )

    async def create_group(self, creator: str, name: str, description: str) -> Group:
        existing = [normalize_text(group.name) for group in self.groups]
        if normalize_text(name) in existing:
            raise ValueError("Group with that name already exists!")
        group = Group.create(self.db, creator, name, description)
        self.groups.append(group)
        await self.update_fields()
        return group
