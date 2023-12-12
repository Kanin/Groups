import asyncio
from aioconsole import ainput
import threading

import discord
from discord.ext import commands

from bot import Bot


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    async def cog_load(self):
        # await self.command_handler()
        threading.Thread(target=self.run_command_handler, daemon=True).start()

    def run_command_handler(self):
        asyncio.run_coroutine_threadsafe(self.command_handler(), self.bot.loop)

    async def command_handler(self):
        while True:
            command = await ainput()
            match command:
                case "kill":
                    await self.bot.close()
                    break
                case "hello":
                    print(f"Hello, world! {self.bot.user}")
                case "help":
                    print("Available commands: hello, help, kill")
                case _:
                    print("Unknown command")

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        self.bot.log.info(f"{ctx.author} in #{ctx.channel} ({ctx.guild}): {ctx.message.content}")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            location = f"#{interaction.channel} ({interaction.guild})" if interaction.guild else "Private Messages"
            data = interaction.data
            parent_command = ""
            parent = interaction.command.parent
            while parent:
                parent_command = f"{parent.name} {parent_command}"
                parent = parent.parent
            command = f"/{parent_command} {interaction.command.name}"
            if "options" in data and "options" in data["options"][0]:
                for option in data["options"][0]["options"]:
                    command += f" {option['name']}: {option['value']}"
            self.bot.log.info(f"{interaction.user} in {location}: {command}")
