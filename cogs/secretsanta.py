import asyncio
import os
import random
from collections import deque
from datetime import datetime

import discord
import jwt
from discord.ext import commands
from loguru import logger

from .utils.SecretSanta import SecretSantaModel
from .utils.EventType import EventTypeModel
from .utils.SecretSantaSettings import SecretSantaSettingsModel
from .utils.checks import mod_or_permissions
from .utils.chat_formatting import escape


class Draft:
    def __init__(self, guild, member):
        self.guild = guild.id
        self.member = member.id


class SecretSanta(commands.Cog):

    def __init__(self, bot):
        self.pending_tasks = {}
        self.bot = bot
        self.secret_santa = SecretSantaModel()
        self.secret_santa_settings = SecretSantaSettingsModel()
        self.event_type = EventTypeModel()

        self.key = os.environ["JWT_KEY"]
        self.drafts = []

    @commands.group()
    async def secretsanta(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="❌ That's not how you use this command",
                                  description=f"**{ctx.prefix}secretsanta new** => Starts the flow for creating a new Secret Santa event (Requires Manage Message Permissions)\n"
                                              f"**{ctx.prefix}secretsanta assign [id]** => Assigns pairs for the given Secret Santa event (Event Organizer Only)\n"
                                              f"**{ctx.prefix}secretsanta address edit [id] [your new address]** => Replaces your address with a new one (encrypted)\n"
                                              f"**{ctx.prefix}secretsanta note add [id] [note]** => Adds a note for whoever draws your name\n\n"
                                              f"`[id]` is provided by the bot, keep an eye out for some of the tips that it will leave at the bottom of its responses.\n"
                                              f"`Note:` the square brackets \"[]\" are placeholders you don\'t need to use them when you send commands",
                                  color=discord.Color.green())
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content == "cancel":
            key = Draft(message.guild, message.author)
            closed_task = False
            for k, v in self.pending_tasks.items():
                if k.guild == key.guild and k.member == key.member:
                    v.close()
                    closed_task = True
            if closed_task:
                return await message.add_reaction("✅")
            return await message.add_reaction("❌")

    @mod_or_permissions()
    @secretsanta.command(aliases=["start"])
    async def new(self, ctx):
        key = Draft(ctx.guild, ctx.author)
        for k, v in self.pending_tasks.items():
            if k.guild == key.guild and k.member == key.member:
                v.close()

        secret_santa_settings = {
            "created_at": datetime.now(),
            "guild": ctx.guild,
            "organizer": ctx.author
        }
        await ctx.send(
            ":santa: Ho Ho Ho! Lets setup your Secret Santa event! First what channel do you want this secret santa in? You can type `cancel` at anytime to quit this process \n\n `Enter a channel by typing # then the name of the channel name`")

        def check_channel(m):
            return m.author == ctx.message.author and len(m.channel_mentions) > 0

        def check_budget(m):
            return m.author == ctx.message.author and len(m.content) > 2

        def check_event_type(r, u):
            return u == ctx.message.author and (str(r.emoji) == "💻" or str(r.emoji) == "📦")

        try:
            self.pending_tasks[key] = self.bot.wait_for('message', timeout=300.0, check=check_channel)
            msg = await self.pending_tasks[key]
            del self.pending_tasks[key]
        except asyncio.TimeoutError:
            return await ctx.send(
                f'❌ Sorry, looks like we lost you there. Please restart this wizard by sending `{ctx.prefix}secretsanta start`')
        secret_santa_settings["channel"] = msg.channel_mentions[0]
        await ctx.send(
            f":santa: Great! The Secret Santa will be in {msg.channel_mentions[0].mention}. Now what would you like the budget to be set at? If you dont know yet you can say TBA and adjust this later.\n\n `Please enter the the maximum you want people to spend (i.e. $25.00)`")
        try:
            self.pending_tasks[key] = self.bot.wait_for('message', timeout=300.0, check=check_budget)
            budget = await self.pending_tasks[key]
            del self.pending_tasks[key]
        except asyncio.TimeoutError:
            return await ctx.send(
                f'❌ Sorry, looks like we lost you there. Please restart this wizard by sending `{ctx.prefix}secretsanta start`')

        secret_santa_settings["budget"] = budget.content
        type = await ctx.send(
            f":santa: Great! You\'ve set the budget to be **{budget.content}**. Finally would you like this gift exchange to be virtual (💻) or using shipping addresses (📦)\n\n `React with the coreesponding emoji to choose`")
        await type.add_reaction("💻")
        await type.add_reaction("📦")

        self.pending_tasks[key] = self.bot.wait_for('reaction_add', timeout=300.0, check=check_event_type)
        reaction, user = await self.pending_tasks[key]
        del self.pending_tasks[key]

        if str(reaction.emoji) == "💻":
            secret_santa_settings["event_type"] = 1
        elif str(reaction.emoji) == "📦":
            secret_santa_settings["event_type"] = 2
        else:
            await ctx.send("Invalid Gift Exchange Type. Exiting...")

        event_type = await self.event_type.get_by_id(secret_santa_settings["event_type"])
        notice = ""
        if event_type.address_required:
            notice = "__Please DM this bot your shipping address after you've enrolled.__\n\n"
        embed = discord.Embed(
            title=f":santa: {escape(ctx.guild.name, formatting=True)}'s Secret Santa Event",
            description=f"**Hosted By:** {ctx.author.mention}\n"
                        f"**Budget:** {secret_santa_settings['budget']}\n\n"
                        f"**Event Type:** {event_type.name}\n" +
                        notice +
                        f"React with :santa: to enroll!",
            color=discord.Color.green())
        secret_santa_settings["message"] = await secret_santa_settings["channel"].send(embed=embed)
        try:
            settings = await self.secret_santa_settings.add(secret_santa_settings)
        except Exception as e:
            return await ctx.send(
                f"Error saving your event! Please raise an issue on our github page with the following error\n\n```\n{str(e)}\n```")
        await secret_santa_settings["message"].add_reaction("🎅")
        await ctx.send(
            f":santa: Good Job! Your Secret Santa Event has been created! You can view it {secret_santa_settings['channel'].mention}\nTo draw pairs use this command:\n`{ctx.prefix}secretsanta assign {settings.id}`")

    @secretsanta.group(name="address")
    async def address(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("❌ Sorry, that's not how you use this command!")

    @secretsanta.group(name="note")
    async def note(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("❌ Sorry, that's not how you use this command!")

    @note.command(name="add")
    async def add_note(self, ctx, secret_santa_settings_id: int, *, note):
        if ctx.message.channel.type.name != "private":
            return await ctx.send("This command can only be used in DMs please DM the bot.")
        secret_santa_settings = await self.secret_santa_settings.get_by_id(secret_santa_settings_id)
        if secret_santa_settings is None or secret_santa_settings.ended:
            return await ctx.send(
                "Sorry, either that Secret Santa event does not exist or has already ended! If you feel this is a mistake please open an issue on our Github")
        participant = await self.secret_santa.get_by_user_id_and_settings_id(ctx.author.id, secret_santa_settings_id)
        if participant is None:
            return await ctx.send(
                "Sorry, I couldn't find a record of your enrollment to this Secret Santa event! If you feel this is a mistake please open an issue on our Github")
        participant.note = note
        await self.secret_santa.save()
        await ctx.send(
            f"✅ Note Saved successfully! \n\nIf you want to change your note at anytime use this command: `{ctx.prefix}secretsanta note add 3 [your note here]` ")

    @address.command(name="edit")
    async def _edit_address(self, ctx, secret_santa_settings_id: int, *, address):
        if ctx.message.channel.type.name != "private":
            return await ctx.send("This command can only be used in DMs please DM the bot.")
        secret_santa_settings = await self.secret_santa_settings.get_by_id(secret_santa_settings_id)
        if secret_santa_settings is None or secret_santa_settings.ended:
            return await ctx.send(
                "Sorry, either that Secret Santa event does not exist or has already ended! If you feel this is a mistake please open an issue on our Github")
        participant = await self.secret_santa.get_by_user_id_and_settings_id(ctx.author.id, secret_santa_settings_id)
        if participant is None:
            return await ctx.send(
                "Sorry, I couldn't find a record of your enrollment to this Secret Santa event! If you feel this is a mistake please open an issue on our Github")
        payload = {"address": address}
        encrypted_address = jwt.encode(payload, self.key, algorithm='HS256')
        participant.address = encrypted_address
        await self.secret_santa.save()
        await ctx.send(
            f"Perfect! Your address, **{address}**, has been encrypted and saved.\n\nIf you need to change your "
            f"address DM me again with this command\n\n`!secretsanta address edit {secret_santa_settings.id} [your "
            f"new address]`")

    # @secretsanta.command()
    # async def list(self, ctx):
    #     all_users = await self.secret_santa.get_all(ctx.guild.id)
    #     members = []
    #     for user in all_users:
    #         user = await self.bot.fetch_user(user.user_id)
    #         if user is not None:
    #             members.append(user.mention)
    #
    #     embed = discord.Embed(title=f"{ctx.guild.name} Secret Santa Participants",
    #                           description=f"Budget: **TBD**\nNumber of participants: {len(all_users)}\n\n {', '.join(members)}")
    #     await ctx.send(embed=embed)

    @mod_or_permissions()
    @secretsanta.command()
    async def assign(self, ctx, secret_santa_id: int):
        settings = await self.secret_santa_settings.get_by_id(secret_santa_id, ctx.guild.id)
        if settings is None or ctx.author.id != settings.organizer_id:
            return await ctx.send("❌ Sorry, that Secret Santa event does not exist or you are not the organizer")
        all_users = await self.secret_santa.get_all(secret_santa_id)
        # if len(all_users) % 2 != 0:
        #     return await ctx.send("There are an odd number of participants. Cant assign pairs.")

        def pair_up(people):
            """ Given a list of people, assign each one a secret santa partner
            from the list and return the pairings as a dict. Implemented to always
            create a perfect cycle"""
            random.shuffle(people)
            partners = deque(people)
            partners.rotate()
            user_ids = [user.user_id for user in people]
            return dict(zip(user_ids, partners))

        pairs = pair_up(all_users)
        for key, value in pairs.items():
            user = await self.bot.fetch_user(key)
            if user.bot or user is None:
                continue
            assigned_user = await self.bot.fetch_user(value.user_id)

            value.assigned_user_id = assigned_user.id
            await self.secret_santa.save()
            description = f"You have pulled {escape(assigned_user.name, formatting=True)}#{assigned_user.discriminator}\nYour budget is **{settings.budget}**\n"
            event = await self.event_type.get_by_id(settings.event_type_id)
            if event.address_required:
                decoded = jwt.decode(value.address, self.key, algorithms='HS256')
                description += f"\nPlease ship their gift to: \n`{decoded['address']}`"
            if len(value.note) > 0:
                description += f"\n\nThey left you a note which will hopefully help you pick an item:\n`{value.note}`"
            organizer = await self.bot.fetch_user(settings.organizer_id)
            description += f"\n\nIf you have any questions please reach out to {escape(organizer.name, formatting=True)}#{organizer.discriminator}"
            embed = discord.Embed(
                title=f":santa: {escape(ctx.guild.name, formatting=True)}'s Secret Santa Event Parings :santa:",
                description=description,
            color=discord.Color.green())
            await user.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        reaction = payload.emoji
        message_id = payload.message_id
        guild_id = payload.guild_id
        guild = discord.utils.find(lambda g: g.id == guild_id, self.bot.guilds)
        user = await guild.fetch_member(payload.user_id)
        channel = discord.utils.get(guild.channels, id=payload.channel_id)
        message = await channel.fetch_message(id=message_id)

        def check_address(m):
            return not m.author.bot and 10 < len(m.content) < 255

        if not user.bot:
            secret_santa_settings = await self.secret_santa_settings.get_by_ids(guild.id, channel.id, message.id)
            organizer = await guild.fetch_member(secret_santa_settings.organizer_id)

            if secret_santa_settings is not None:
                if str(reaction) == "🎅":
                    try:
                        secret_santa = await self.secret_santa.add(secret_santa_settings.id, user.id)
                    except Exception as e:
                        logger.error(f'Could not enroll user in event {secret_santa_settings.id}: {e}')
                        await reaction.message.remove_reaction(reaction, user)
                        return await user.send(
                            f"Failed to enroll you in {escape(guild.name, formatting=True)}'s Secret Santa Event organized by {escape(organizer.name, formatting=True)}. Please open an issue on our Github page with the error message: {str(e)}")
                    try:
                        await user.send(
                            f":santa: Ho Ho Ho! You've been enrolled in {escape(guild.name, formatting=True)}'s Secret Santa Event organized by {escape(organizer.name, formatting=True)}!")
                    except discord.Forbidden:
                        m = await channel.send(
                            f"❌ {user.mention} I could not enroll you because you have DMs disabled. Please right click this server and select Privacy Settings => Allow direct messages from server members ")
                        await message.remove_reaction(reaction, user)
                        await m.delete(delay=10)
                    event_type = await self.event_type.get_by_id(secret_santa_settings.event_type_id)
                    if event_type.address_required:
                        await user.send(
                            "Because this Secret Santa is a Shipped Gift Exchange who ever pulls your name will be shipping you your gift! Please Provide your address now:\n\n`(Don't worry it will be encrypted and no one besides your partner will have access to it.)`")
                        try:
                            message = await self.bot.wait_for('message', timeout=300.0, check=check_address)
                        except asyncio.TimeoutError:
                            await message.remove_reaction(reaction, user)
                            return await user.send(
                                f'❌ Sorry, looks like we lost you there. Please re-enroll by reacting to the embed here with :santa: \n\n https://discord.com/channels/{secret_santa_settings.guild_id}/{secret_santa_settings.channel_id}/{secret_santa_settings.message_id}')
                        payload = {"address": message.content}
                        address = jwt.encode(payload, self.key, algorithm='HS256')
                        secret_santa.address = address
                        await self.secret_santa.save()
                        await user.send(
                            f"Perfect! Your address, **{message.content}**, has been encrypted and saved.\n\nIf you need to change your address DM me again with this command\n\n`!secretsanta address edit {secret_santa_settings.id} [your new address]`\n\n If you would like to add a note to be sent to whoever pulls your name please use the following command\n`!secretsanta note add {secret_santa_settings.id} [your note here]`")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        reaction = payload.emoji
        message_id = payload.message_id
        guild_id = payload.guild_id
        guild = discord.utils.find(lambda g: g.id == guild_id, self.bot.guilds)
        user = await guild.fetch_member(payload.user_id)
        channel = discord.utils.get(guild.channels, id=payload.channel_id)
        message = await channel.fetch_message(id=message_id)

        if not user.bot:
            secret_santa_settings = await self.secret_santa_settings.get_by_ids(guild.id, channel.id, message.id)
            organizer = await guild.fetch_member(secret_santa_settings.organizer_id)

            if secret_santa_settings is not None:
                if str(reaction) == "🎅":
                    try:
                        participant = await self.secret_santa.get_by_user_id_and_settings_id(user.id,
                                                                                             secret_santa_settings.id)
                        self.secret_santa.delete(participant)
                    except Exception as e:
                        logger.error(f'Could not un-enroll user in event {secret_santa_settings.id}: {e}')
                        return await user.send(
                            f"Failed to un-enroll you in {escape(guild.name, formatting=True)}'s Secret Santa Event organized by {escape(organizer.name, formatting=True)}. Please open an issue on our Github page with the error message:\n\n ```{str(e)}```")
                    try:
                        await user.send(
                            f":white_check_mark: You've been successfully un-enrolled in {escape(guild.name, formatting=True)}'s Secret Santa Event organized by {escape(organizer.name, formatting=True)}!")
                    except discord.Forbidden:
                        m = await channel.send(
                            f"❌ {user.mention} I could not enroll you because you have DMs disabled. Please right click this server and select Privacy Settings => Allow direct messages from server members ")
                        await message.remove_reaction(reaction, user)
                        await m.delete(delay=10)


def setup(bot):
    bot.add_cog(SecretSanta(bot))
