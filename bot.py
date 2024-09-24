import logging
import sys
from typing import Optional

import aiohttp
import discord
import yaml
from dictor import dictor
from discord.ext.commands import AutoShardedBot as DiscordBot

from common.components.buttons.groupjoin import GroupJoin
from common.components.buttons.groupleave import GroupLeave
from common.components.buttons.groupmembers import GroupMembers
from common.components.buttons.grouprefresh import GroupRefresh
from common.database import Database
from config import config


def get_banner():
    banner = open("common/assets/banner.txt")
    return banner.read()


class Bot(DiscordBot):
    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        self.db: Database = await Database.create()
        self.add_dynamic_items(GroupJoin, GroupLeave, GroupMembers, GroupRefresh)
        for ext in self.initial_extensions:
            await self.load_extension(ext)

    async def close(self, signum=None, frame=None):
        logging.info("Cleaning up and logging out...")
        await super().close()
        await self.session.close()

    def emoji(self, emoji: str):
        with open("config/emojis.yml", "r") as emojis:
            emojis = yaml.safe_load(emojis)
        return self.get_emoji(dictor(emojis, emoji))

    def __init__(self):
        super().__init__(intents=config.intents, command_prefix=config.prefix)

        # Argument Handling
        self.session = None
        self.db: Optional[Database] = None
        self.debug: bool = any("debug" in arg.lower() for arg in sys.argv)

        # Commands/extensions
        self.initial_extensions = ["modules.events.ready"]

        # Logging
        discord_log = logging.getLogger("discord")
        discord_log.setLevel(logging.INFO if self.debug else logging.CRITICAL)
        self.log: logging.Logger = logging.getLogger("bot")
        self.log.info(f"\n{get_banner()}\nLoading....")

        # Config
        self.config = config
        self.version = {"bot": "v1.0.0", "python": sys.version.split(" ")[0], "discord.py": discord.__version__}
