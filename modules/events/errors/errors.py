import os
import traceback
from datetime import datetime, timedelta

import discord
import sentry_sdk
from discord import app_commands
from discord.ext import commands

from bot import Bot
from common.functions.text import pagify


def init_sentry(bot: Bot):
    sentry_sdk.init(
        os.getenv("SENTRY_URL"),
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        environment="Development" if bot.debug else "Production",
        max_breadcrumbs=50,
        release=bot.version["bot"],
    )


class Errors(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self._old_tree_error = None

    def cog_load(self):
        tree = self.bot.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.on_app_command_error

    def cog_unload(self):
        tree = self.bot.tree
        tree.on_error = self._old_tree_error

    @staticmethod
    def float_to_discord_timestamp(seconds):
        now = datetime.utcnow()
        off = now + timedelta(seconds=seconds)
        return f"<t:{int(off.timestamp())}:R>"

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            timestamp = self.float_to_discord_timestamp(error.retry_after)
            return await interaction.response.send_message(f"You're on cooldown! Try again {timestamp}", ephemeral=True)
        if isinstance(error, app_commands.CheckFailure):
            return await interaction.response.send_message(f"You don't have permission to use this command!",
                                                           ephemeral=True)
        sentry_sdk.capture_exception(error)
        webhook = discord.Webhook.from_url(os.getenv("ERROR_WEBHOOK"), session=self.bot.session)

        long = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        self.bot.log.error(long)

        data = interaction.data
        parent_command = ""
        parent = interaction.command.parent
        while parent:
            parent_command = f"{parent.name} {parent_command}"
            parent = parent.parent
        command = f"/{parent_command} {interaction.command.name}"
        if "options" in data:
            if "options" in data["options"][0]:
                for option in data["options"][0]["options"]:
                    command += f" `{option['name']}: {option['value']}`"

        em = discord.Embed(
            color=self.bot.config.colors["error"],
            description=f"`{type(error).__name__}: {str(error)}`",
            title="Error:"
        )
        em.add_field(name="Content:", value=command)
        em.add_field(name="Invoker:", value=f"{interaction.user.mention}\n({interaction.user})")
        if not isinstance(interaction.channel, discord.DMChannel):
            em.add_field(
                name="Location:",
                value=f"**Guild:** {interaction.guild.name}\n"
                      f"**Channel:** {interaction.channel.mention} ({interaction.channel.name})"
            )
        else:
            em.add_field(name="Location:", value="Private messages-")

        await webhook.send(embed=em)
        if pages := pagify(long):
            for page in pages:
                await webhook.send(f"```py\n{page}\n```")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        if cog := ctx.cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound,)

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return
        if isinstance(error, commands.CommandOnCooldown):
            timestamp = self.float_to_discord_timestamp(error.retry_after)
            error = f"You're on cooldown! Try again {timestamp}"
            return await ctx.reply(error)
        ctx.command.reset_cooldown(ctx)
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.reply(str(error))

        sentry_sdk.capture_exception(error)
        webhook = discord.Webhook.from_url(os.getenv("ERROR_WEBHOOK"), session=self.bot.session)

        long = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        self.bot.log.error(long)

        em = discord.Embed(
            color=self.bot.config.colors["error"],
            description=f"`{type(error).__name__}: {str(error)}`",
            title="Error:"
        )
        em.add_field(name="Content:", value=ctx.message.content)
        em.add_field(name="Invoker:", value=f"{ctx.author.mention}\n({ctx.author})")
        if not isinstance(ctx.channel, discord.DMChannel):
            em.add_field(
                name="Location:",
                value=f"**Guild:** {ctx.guild.name}\n**Channel:** {ctx.channel.mention} ({ctx.channel.name})"
            )
        else:
            em.add_field(name="Location:", value="Private messages-")

        await webhook.send(embed=em)

        if pages := pagify(long):
            for page in pages:
                await webhook.send(f"```py\n{page}\n```")
