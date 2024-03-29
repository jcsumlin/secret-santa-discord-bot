import glob
import os
import re
import time
from configparser import *
import platform

import discord
from discord.ext import commands
from loguru import logger

from cogs.utils.checks import is_bot_owner_check

from cogs.utils.GuildSettings import GuildSettingsModel

ServerSettings = GuildSettingsModel()

# initiate logger test
logger.add(f"file_{str(time.strftime('%Y%m%d-%H%M%S'))}.log", rotation="500 MB")

"""	
Setup bot intents (events restrictions)
For more information about intents, please go to the following websites:
https://discordpy.readthedocs.io/en/latest/intents.html
https://discordpy.readthedocs.io/en/latest/intents.html#privileged-intents
"""
intents = discord.Intents().default()
intents.messages = True
intents.reactions = True
intents.presences = True
intents.members = True
intents.guilds = True
intents.emojis = True
intents.bans = True
intents.guild_typing = False
intents.typing = False
intents.dm_messages = True
intents.dm_reactions = True
intents.dm_typing = False
intents.guild_messages = True
intents.guild_reactions = True
intents.integrations = True
intents.invites = True
intents.voice_states = False
intents.webhooks = False

if "TOKEN" not in os.environ or "PREFIX" not in os.environ:
    logger.error("Missing required parameters (TOKEN and PREFIX) check your environment variables")
    exit(0)


def load_cogs(folder):
    os.chdir(folder)
    files = []
    for file in glob.glob("*.py"):
        file = re.search('^([A-Za-z1-9]{1,})(?:.py)$', file).group(1)
        files.append(file)
    return files


bot = commands.Bot(command_prefix=os.environ["PREFIX"], intents=intents)


@bot.event
async def on_ready():
    """
    When bot is ready and online it prints that its online
    :return:
    """
    # bot.timer_manager = timers.TimerManager(bot)
    logger.debug(f"Logged in as {bot.user.name}")
    logger.debug(f"Discord.py API version: {discord.__version__}")
    logger.debug(f"Python version: {platform.python_version()}")
    logger.debug(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    logger.success("===== Bot is ready! =====")


@bot.event
async def on_guild_join(guild):
    guild_settings = GuildSettingsModel()
    return await guild_settings.add(guild_id=guild.id, server_name=guild.name, region=guild.region,
                                    owner_id=guild.owner.id)


@bot.command()
@is_bot_owner_check()
async def load(ctx, extension):
    try:
        bot.load_extension('cogs.' + extension)
        logger.success(f'Loaded {extension}')
        await ctx.send(f'Loaded {extension}')
    except Exception as error:
        logger.exception(f"Extension {extension} could not be loaded. [{error}]")


@bot.command()
@is_bot_owner_check()
async def reload(ctx, extension):
    try:
        bot.unload_extension('cogs.' + extension)
        bot.load_extension('cogs.' + extension)
        logger.success(f'Reloaded {extension}')
        await ctx.send(f'Reloaded {extension}')
    except Exception as error:
        logger.exception(f"Extension {extension} could not be reloaded. [{error}]")


@bot.command()
@is_bot_owner_check()
async def unload(ctx, extension):
    try:
        bot.unload_extension('cogs.' + extension)
        logger.success(f'Unloaded {extension}')
        await ctx.send(f'{extension} successfully unloaded')
    except Exception as error:
        logger.exception(f"Extension {extension} could not be unloaded. [{error}]")


# The code in this event is executed every time a command has been *successfully* executed
@bot.event
async def on_command_completion(ctx):
    fullCommandName = ctx.command.qualified_name
    guild_name = "DMs"
    if ctx.guild is not None:
        guild_name = ctx.guild.name
    logger.debug(
        f"Executed '{fullCommandName}' command in {guild_name} by {ctx.message.author} (ID: {ctx.message.author.id})")


if "SENTRY_URL" in os.environ:
    logger.debug("Initializing Sentry error logging")
    from discord_sentry_reporting import use_sentry

    use_sentry(bot, dsn=os.environ["SENTRY_URL"])



if __name__ == "__main__":
    extensions = load_cogs('cogs')
    for extension in extensions:
        try:
            bot.load_extension('cogs.' + extension)
            logger.success(f'Loaded {extension} cog.')
        except Exception as error:
            logger.exception(f"Extension {extension} could not be loaded. [{error}]")

    bot.run(os.environ["TOKEN"])
