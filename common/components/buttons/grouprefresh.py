import re

import discord

from common.database import Database


class GroupRefresh(discord.ui.DynamicItem[discord.ui.Button], template=r"groups:refresh:(?P<id>[0-9a-f-]+)"):
    def __init__(self, database: Database, group_id: str) -> None:
        super().__init__(
            discord.ui.Button(
                emoji="<:Refresh:1288239757645709352>",
                style=discord.ButtonStyle.grey,
                custom_id=f"groups:refresh:{group_id}"
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
        if not group:
            return await interaction.message.delete()
        from common.functions.groups import build_group_info
        em, view = await build_group_info(interaction, group)
        await interaction.response.edit_message(embed=em, view=view)
