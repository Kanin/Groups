import discord
from discord.ext import commands

# Discord Intents are necessary to receive certain events.
# For instance, the 'guilds' intent is needed to access the 'on_guild_join' event.
# More about intents can be found in the Discord.py documentation: https://discordpy.readthedocs.io/en/latest/intents.html
intents = discord.Intents.none()
intents.guilds = True
intents.members = True

# The prefix is the character(s) used to invoke a command. For example, '!help'.
# The 'commands.when_mentioned_or' function allows the bot to respond when mentioned or when a specific character is used.
# Multiple prefixes can be used, for example: commands.when_mentioned_or("!", "?")
# If intents.messages is False, the bot will not respond to commands invoked by a prefix. Only mentions will work.
prefix = commands.when_mentioned_or("!")

# 'home_guild' is the ID of the guild (server) that the bot will use for specific operations.
home_guild = 123

# 'colors' is a dictionary that stores colors for use in embed messages.
# 'main' is the primary color of the bot.
# 'error' is the color used for error messages.
# 'success' is the color used for success messages.
colors = {"main": discord.Color.blue(), "error": discord.Color.red(), "success": discord.Color.green()}