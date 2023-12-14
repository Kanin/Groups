import re

import discord

from common.database import Database


class GroupLeave(discord.ui.DynamicItem[discord.ui.Button], template=r"groups:leave:(?P<id>[0-9a-f-]+)"):
    def __init__(self, database: Database, group_id: str) -> None:
        super().__init__(
            discord.ui.Button(
                label="Leave",
                style=discord.ButtonStyle.red,
                custom_id=f"groups:leave:{group_id}"
            )
        )
        self.db = database
        self.group_id = group_id

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, _item: discord.ui.Button, match: re.Match[str], /):
        await interaction.response.defer(thinking=True, ephemeral=True)
        return cls(database=interaction.client.db, group_id=match["id"])

    async def callback(self, interaction: discord.Interaction) -> None:
        group = await interaction.client.db.get_group(str(interaction.guild_id), self.group_id)
        members = group.get_members(interaction.guild)
        if interaction.user not in members:
            return await interaction.followup.send(f"You're not in `{group.name}`!", ephemeral=True)
        await group.remove_member(str(interaction.user.id))
        await interaction.followup.send(f"You've left `{group.name}`!", ephemeral=True)
