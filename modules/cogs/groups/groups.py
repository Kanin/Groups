import discord
from discord import app_commands
from discord.ext import commands

from bot import Bot
from common.functions.paginator import IndexedGroupPages
from common.functions.text import pagify


class Groups(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    group = app_commands.Group(name="group", description="Commands for managing groups.")

    @group.command(name="list", description="List all groups.")
    async def group_list(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        guild = await self.bot.db.get_guild(str(interaction.guild_id))
        if not guild.groups:
            return await interaction.followup.send("No groups", ephemeral=True)
        em = discord.Embed(color=self.bot.config.colors["main"], title="Groups")
        em.set_thumbnail(url=interaction.guild.icon.with_static_format("png").with_size(512).url)
        pages = IndexedGroupPages(entries=guild.groups, interaction=interaction, embed=em)
        await pages.start()

    @group.command(name="ping", description="Ping a group.")
    @app_commands.describe(group="The group to ping")
    async def group_ping(self, interaction: discord.Interaction, group: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        group = await self.bot.db.get_group(str(interaction.guild_id), group)
        if not group:
            return await interaction.followup.send("Group not found!", ephemeral=True)
        members = group.get_members(interaction.guild)
        if not members:
            return await interaction.followup.send("No members to ping!", ephemeral=True)
        content = f"**@{interaction.user.mention}:** **@{group.name}:** "
        content += ", ".join(x.mention for x in members)
        if pages := pagify(content, delims=[", "]):
            for page in pages:
                await interaction.channel.send(
                    page,
                    allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False)
                )
        await interaction.followup.send("Done!")

    @group.command(name="info", description="Get info about a group.")
    @app_commands.describe(group="The name of the group")
    async def group_info(self, interaction: discord.Interaction, group: str):
        await interaction.response.defer(thinking=True)
        group = await self.bot.db.get_group(str(interaction.guild_id), group)
        if not group:
            return await interaction.followup.send("Group not found!", ephemeral=True)
        from common.functions.groups import build_group_info
        em, view = await build_group_info(interaction, group)
        await interaction.followup.send(embed=em, view=view)

    @group.command(name="create", description="Create a group.")
    @app_commands.describe(name="The name of the group", description="The description of the group")
    async def group_create(self, interaction: discord.Interaction, name: str, description: str):
        await interaction.response.defer(thinking=True)
        guild = await self.bot.db.get_guild(str(interaction.guild_id))
        try:
            await guild.create_group(str(interaction.user.id), name, description)
        except ValueError as e:
            return await interaction.followup.send(str(e), ephemeral=True)
        await interaction.followup.send("Done!")

    @group.command(name="delete", description="Delete a group.")
    @app_commands.describe(group="The name of the group")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def group_delete(self, interaction: discord.Interaction, group: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        guild = await self.bot.db.get_guild(str(interaction.guild_id))
        await guild.delete_group(group)
        await interaction.followup.send("Done!")

    @group_info.autocomplete("group")
    @group_ping.autocomplete("group")
    @group_delete.autocomplete("group")
    async def group_info_autocomplete(self, interaction: discord.Interaction, current: str):
        current = current.lower()
        data = await self.bot.db.get_guild(str(interaction.guild_id))
        groups = []
        for group in data.groups:
            if not current or current in group.name.lower():
                groups.append(app_commands.Choice(name=group.name, value=group.id))
        return groups
