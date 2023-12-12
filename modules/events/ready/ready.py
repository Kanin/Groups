import os
import re

import discord.utils
from discord.ext import commands

from bot import Bot


class Ready(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot
        self.init = True

    @commands.Cog.listener()
    async def on_ready(self):
        avatar = self.bot.user.avatar or self.bot.user.default_avatar
        invite = discord.utils.oauth_url(self.bot.user.id)
        info = f"\n**Connected** ⚡\n" \
               f"\n**Logged in** 📡\n" \
               f"**User:** {self.bot.user} ({self.bot.user.id})\n" \
               f"**Avatar:** {avatar.with_size(512).with_format('png')}\n" \
               f"**Invite:** {invite}\n" \
               f"\n**Information** ℹ\n" \
               f"**Bot version:** {self.bot.version['bot']}\n" \
               f"**Lib version:** {self.bot.version['discord.py']}\n" \
               f"**Python version:** {self.bot.version['python']}"
        self.bot.log.info(re.sub(r"\*", "", info))
        if self.init is True:
            self.init = False
            await self.start_modules()

    async def start_modules(self):
        paths = ["modules/events", "modules/cogs"]
        blacklist = [
            "modules/events/ready"
        ]
        if self.bot.debug:
            blacklist.extend([])
        for path in paths:
            loaded, failed = 0, 0
            name = path.split("/")[-1]
            for file in os.listdir(path):
                try:
                    if not file.startswith("_"):
                        to_load = f"{path}/{file}"
                        if to_load not in blacklist:
                            self.bot.log.info(f"Loading {name}/{file}...")
                            await self.bot.load_extension(to_load.replace("/", "."))
                            loaded += 1
                except Exception as e:
                    failed += 1
                    self.bot.log.error(f"Failed to load {path}/{file}: {repr(e)}")
            message = f"Loaded {loaded} {name}"
            if failed > 0:
                message += f" | Failed to load {failed} {name}"
            self.bot.log.info(message)
        await self.bot.tree.sync()
