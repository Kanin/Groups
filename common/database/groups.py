import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, List, Optional


@dataclass
class Group:
    db: Any
    creator: str
    name: str
    description: str
    _id: str = field(default=str(uuid.uuid4()))
    guild_id: Optional[str] = None
    members: List[str] = field(default_factory=list)

    @classmethod
    def create(cls, db, creator: str, name: str, description: str) -> "Group":
        giveaway = cls(db=db, creator=creator, name=name, description=description)
        return giveaway

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
