from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from bot import Bot


class Dev(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command(name="synctree", hidden=True)
    @commands.is_owner()
    async def sync_tree(self, ctx: commands.Context, guilds: Optional[str] = None):
        await ctx.defer()
        if not guilds:
            synced = await ctx.bot.tree.sync()
            return await ctx.send(f"Synced {len(synced)} commands globally.")

        ret = 0
        for guild in guilds.split(","):
            try:
                await ctx.bot.tree.sync(guild=ctx.bot.get_guild(int(guild)))
            except discord.HTTPException:
                pass
            else:
                ret += 1
        await ctx.send(f"Synced the tree to {ret}/{len(guilds.split(','))}")

    @app_commands.command()
    async def test(self, interaction: discord.Interaction, example: Optional[str]):
        command = interaction.command.name
        data = interaction.data
        extras = interaction.extras
        await interaction.response.send_message(f"{command}\n{data}\n{extras}\n{example}", ephemeral=True)

    testing = app_commands.Group(name="testing", description="Testing commands")

    @testing.command()
    async def testone(self, interaction: discord.Interaction, example: Optional[str]):
        command = interaction.command.name
        data = interaction.data
        extras = interaction.extras
        await interaction.response.send_message(f"{command}\n{data}\n{extras}\n{example}", ephemeral=True)