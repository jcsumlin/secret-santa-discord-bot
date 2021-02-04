import aiohttp
from discord.ext import commands


#
# This is a modified version of checks.py, originally made by Rapptz
#
#                 https://github.com/Rapptz
#          https://github.com/Rapptz/RoboDanny/tree/async
#

def is_bot_owner_check():
    return commands.is_owner()


def is_owner():
    return commands.has_role('administrator')

# The permission system of the bot is based on a "just works" basis
# You have permissions and the bot has permissions. If you meet the permissions
# required to execute the command (and the bot does as well) then it goes through
# and you can execute the command.
# If these checks fail, then there are two fallbacks.
# A role with the name of Bot Mod and a role with the name of Bot Admin.
# Having these roles provides you access to certain commands without actually having
# the permissions required for them.
# Of course, the owner will always be able to execute commands.


def admin_or_permissions():
    return commands.has_permissions(administrator=True)

def mod_or_permissions():
    return commands.has_permissions(manage_messages=True)

def admin():
    return admin_or_permissions()

def mod_or_higher():
    return commands.has_permissions(manage_messages=True)

def is_in_guild(guild_id):
    async def predicate(ctx):
        return ctx.guild and ctx.guild.id == guild_id
    return commands.check(predicate)

def mod_or_higher():
    return commands.has_permissions(manage_messages=True)

async def hastebin(content):
    async with aiohttp.ClientSession() as session:
        async with session.post('https://hastebin.com/documents', data=content.encode('utf-8')) as r:
            if r.status == 200:
                result = await r.json()
                return "https://hastebin.com/" + result["key"]
            else:
                return "Error with creating Hastebin. Status: %s" % r.status
