from dataclasses import dataclass, field, asdict
from typing import Any, List, Optional
from .groups import Group


@dataclass
class Guild:
    db: Any
    _id: str
    create_roles: List[str] = field(default_factory=list)
    groups: List[Group] = field(default_factory=list)

    @classmethod
    def create(cls, db, guild_id: str) -> "Guild":
        guild = cls(db=db, _id=guild_id)
        return guild

    async def save(self):
        guild_dict = asdict(self)
        guild_dict.pop('db')
        groups = []
        for group in guild_dict["groups"]:
            group_dict = asdict(group)
            group_dict.pop('db')
            group_dict.pop('guild_id')
            groups.append(group_dict)
        guild_dict["groups"] = groups
        await self.db.guilds.insert_one(guild_dict)

    @classmethod
    async def from_existing(cls, db, guild_id: str, data: dict) -> "Guild":
        data['groups'] = [Group(**group_data, guild_id=guild_id, db=db) for group_data in data.get('groups', [])]
        return cls(db=db, _id=guild_id, **data)

    async def update_fields(self, **kwargs):
        allowed_fields = set(self.__annotations__.keys()) - {"db"}
        update_data = {key: value for key, value in kwargs.items() if key in allowed_fields}
        if 'groups' in update_data:
            groups = []
            for group in update_data['groups']:
                group_dict = asdict(group)
                group_dict.pop('db')
                group_dict.pop('guild_id')
                groups.append(group_dict)
            update_data['groups'] = groups
        await self.db.guilds.update_one(
            {"guild_id": self._id},
            {"$set": update_data}
        )
