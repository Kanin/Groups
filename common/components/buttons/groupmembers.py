import re

import discord

from common.database import Database
from common.functions.paginator import IndexedPagesInteraction


class GroupMembers(discord.ui.DynamicItem[discord.ui.Button], template=r"groups:members:(?P<id>[0-9a-f-]+)"):
    def __init__(self, database: Database, group_id: str) -> None:
        super().__init__(
            discord.ui.Button(
                emoji="<:Silhouette:1176360845295489024>",
                label="Members",
                style=discord.ButtonStyle.grey,
                custom_id=f"groups:members:{group_id}"
            )
        )
        self.db = database
        self.group_id = group_id

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, _item: discord.ui.Button, match: re.Match[str], /):
        await interaction.response.defer(thinking=True, ephemeral=True)
        return cls(database=interaction.client.db, group_id=match["id"])

    async def callback(self, interaction: discord.Interaction) -> None:
        group = await self.db.get_group(str(interaction.guild.id), self.group_id)
        entries = [f"<@{x.id}> `[{x}]`" for x in group.get_members(interaction.guild)]
        if not entries:
            em = discord.Embed(color=interaction.client.config.colors["error"])
            em.description = "Nobody has joined this group!"
            return await interaction.followup.send(embed=em)
        em = discord.Embed(color=interaction.client.config.colors["main"])
        em.set_author(name=f"{group.name} Members")
        pages = IndexedPagesInteraction(entries=entries, interaction=interaction, embed=em)
        await pages.start()
