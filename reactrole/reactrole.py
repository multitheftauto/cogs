import discord
import unicodedata
import time
from redbot.core import Config, checks, commands
from typing import Optional, Union


class ReactRole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=95932766180343811, force_registration=True
        )
        defaultsguild = {"reacts": {}}
        defaults = {}
        self.config.register_guild(**defaultsguild)
        self.config.register_global(**defaults)
        self.stamps = {}
        self.period = 5

    @commands.group()
    async def reactrole(self, ctx):
        """MTA:SA Reactrole"""
        pass

    @reactrole.command()
    async def add(self, ctx, channel: discord.TextChannel, message: Union[discord.Message, str], emoji: Union[discord.Emoji, discord.PartialEmoji, str], role: discord.Role):
        """Adds an item to the list"""
        if type(message) == str:
            message = await channel.fetch_message(int(message))
        if type(emoji) != str:
            react = "{}_{}".format(message.id, emoji.id)
        else:
            part_two = "_".join(unicodedata.name(emoji[0]).split(' ')).lower()
            react = "{}_{}".format(message.id, part_two)
        async with self.config.guild(ctx.guild).reacts() as reacts:
            if react not in reacts:
                reacts[react] = role.id
                await ctx.maybe_send_embed("Reaction added.")
            else:
                await ctx.maybe_send_embed("This reaction exists already.")

    @reactrole.command()
    async def remove(self, ctx, channel: discord.TextChannel, message: Union[discord.Message, str], emoji: Union[discord.Emoji, discord.PartialEmoji, str], role: discord.Role):
        """Removes an item from the list"""
        if type(message) == str:
            message = await channel.fetch_message(int(message))
        if type(emoji) != str:
            react = "{}_{}".format(message.id, emoji.id)
        else:
            part_two = "_".join(unicodedata.name(emoji[0]).split(' ')).lower()
            react = "{}_{}".format(message.id, part_two)
        async with self.config.guild(ctx.guild).reacts() as reacts:
            if react in reacts:
                del reacts[react]
                await ctx.maybe_send_embed("Removed!")
            else:
                await ctx.maybe_send_embed("Doesn't exist.")

    @reactrole.command(name="list")
    async def _list(self, ctx):
        reacts = await self.config.guild(ctx.guild).reacts()
        msg = ""
        for key in reacts:
            keys = key.split("_")
            msg += "``{}`` > ``{}`` > ``{}``\n".format(keys[0], "_".join(keys[1:]), reacts[key])
        if msg:
            msg = "``Message`` > ``Emoji`` > ``Role``\n"+msg
        await ctx.maybe_send_embed(msg if msg else "List is empty.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        ts = time.time()
        if payload.user_id in self.stamps:
            diff = ts - self.stamps[payload.user_id]
            if diff < self.period:
                return

        self.stamps[payload.user_id] = ts

        user = payload.member
        if user.bot:
            return
        guild = user.guild
        if guild is None:
            return

        message_id = payload.message_id
        emoji = payload.emoji

        react = "{}_{}".format(message_id, emoji.id or "_".join(unicodedata.name(emoji.name[0]).split(' ')).lower())

        reacts = await self.config.guild(user.guild).reacts()
        if react in reacts:
            role = user.guild.get_role(reacts[react])
            await user.add_roles(role, reason="Reaction Role")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        ts = time.time()
        if payload.user_id in self.stamps:
            diff = ts - self.stamps[payload.user_id]
            if diff < self.period:
                return

        guild = await self.bot.fetch_guild(payload.guild_id)
        if guild is None:
            return
        user = await guild.fetch_member(payload.user_id)
        if user.bot:
            return
        guild = user.guild

        message_id = payload.message_id
        emoji = payload.emoji

        react = "{}_{}".format(message_id, emoji.id or "_".join(unicodedata.name(emoji.name[0]).split(' ')).lower())

        reacts = await self.config.guild(user.guild).reacts()
        if react in reacts:
            role = user.guild.get_role(reacts[react])
            await user.remove_roles(role, reason="Reaction Role")
