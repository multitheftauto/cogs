import discord
import re
from redbot.core import commands, checks, data_manager
from redbot.core.config import Config
from redbot.core.utils import mod
from typing import Union, Pattern


INVITE_RE: Pattern = re.compile(
    r"(?:https?\:\/\/)?discord(?:\.gg|(?:app)?\.com\/invite)\/([a-zA-Z0-9]+)", re.I
)


class spam(commands.Cog):
    """ MTA:SA Spam Cog """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self,
            identifier=7073509549697925843,
            force_registration=True,
        )

        default_guild = {
            "strings": {},
            "invites": {},
            "channels": {},
            "active": False,
            "feed": None
        }

        self.config.register_guild(**default_guild)

    @checks.mod_or_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.group()
    async def spam(self, ctx):
        pass

    @spam.command()
    async def toggle(self, ctx):
        active = await self.config.guild(ctx.guild).active()
        if active:
            await self.config.guild(ctx.guild).active.set(False)
            await ctx.maybe_send_embed("Spam protection disabled.")
        else:
            await self.config.guild(ctx.guild).active.set(True)
            await ctx.maybe_send_embed("Spam protection enabled.")

    @spam.command()
    async def add(self, ctx, name, *, string):
        async with self.config.guild(ctx.guild).strings() as strings:
            if name not in strings:
                strings[name] = string
                await ctx.maybe_send_embed("Added ``{}`` to the list".format(name))
            else:
                await ctx.maybe_send_embed("This name is already taken.")

    @spam.command()
    async def invite(self, ctx, invite: discord.Invite):
        if invite.guild:
            guild_id = str(invite.guild.id)
            guild_name = invite.guild.name
            async with self.config.guild(ctx.guild).invites() as invites:
                if guild_id not in invites:
                    invites[guild_id] = guild_name
                    await ctx.maybe_send_embed("Added {}: ``{}`` to the list".format(guild_name, guild_id))
                else:
                    del invites[guild_id]
                    await ctx.maybe_send_embed("Removed {}: ``{}`` from the list".format(guild_name, guild_id))
        else:
            await ctx.maybe_send_embed("Couldn't resolve the invite.")

    @spam.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        if channel:
            channel_id = str(channel.id)
            channel_name = channel.name
            async with self.config.guild(ctx.guild).channels() as channels:
                if channel_id not in channels:
                    channels[channel_id] = channel_name
                    await ctx.maybe_send_embed("Added {}: ``{}`` to the whitelist".format(channel_name, channel_id))
                else:
                    del channels[channel_id]
                    await ctx.maybe_send_embed("Removed {}: ``{}`` from the whitelist".format(channel_name, channel_id))
        else:
            await ctx.maybe_send_embed("Couldn't find channel.")

    @spam.command()
    async def remove(self, ctx, name):
        async with self.config.guild(ctx.guild).strings() as strings:
            if name in strings:
                del strings[name]
                await ctx.maybe_send_embed("Removed ``{}`` from the list".format(name))
            else:
                await ctx.maybe_send_embed("Doesn't exist.")

    @spam.command(name="list")
    async def _list(self, ctx):
        invites = await self.config.guild(ctx.guild).invites()
        channels = await self.config.guild(ctx.guild).channels()
        strings = await self.config.guild(ctx.guild).strings()
        msg = ""
        for key in channels:
            msg += "``Allowed Channel: {}`` > ``{}``\n".format(channels[key], key)
        for key in invites:
            msg += "``Blocked Server: {}`` > ``{}``\n".format(invites[key], key)
        for key in strings:
            msg += "``{}`` > ``{}``\n".format(key, strings[key])
        await ctx.maybe_send_embed(msg if msg else "List is empty.")

    @checks.admin_or_permissions(manage_roles=True)
    @spam.command()
    async def setfeed(self, ctx, channel_id):
        await self.config.guild(ctx.guild).feed.set(channel_id)
        await ctx.maybe_send_embed("The feed channel has been set to {}".format(channel_id))

    @commands.Cog.listener()
    async def on_message(self, ctx):
        # if ctx.author.bot:
        #     return
        guild = ctx.guild
        if guild is None:
            return
        active = await self.config.guild(ctx.guild).active()
        if not active:
            return

        find = INVITE_RE.findall(ctx.clean_content)
        # print(find)
        if find:
            channels = await self.config.guild(ctx.guild).channels()
            if str(ctx.channel.id) not in channels:
                feed = await self.config.guild(ctx.guild).feed()
                if feed:
                    embed = discord.Embed(colour=discord.Colour(0xf5a623), description="Spam protection deleted an invite (Whitelist) in <#"+str(ctx.channel.id)+">")
                    embed.add_field(name="**Author:**", value="<@"+str(ctx.author.id)+">", inline=False)
                    embed.add_field(name="**Message:**", value=ctx.content, inline=False)
                    await self.bot.get_channel(int(await self.config.guild(ctx.guild).feed())).send(embed=embed)
                return await ctx.delete()

            invites = await self.config.guild(ctx.guild).invites()
            for i in find:
                invite = await self.bot.fetch_invite(i)
                if str(invite.guild.id) in invites:
                    feed = await self.config.guild(ctx.guild).feed()
                    if feed:
                        embed = discord.Embed(colour=discord.Colour(0xf5a623), description="Spam protection deleted an invite (Blocked) in <#"+str(ctx.channel.id)+">")
                        embed.add_field(name="**Author:**", value="<@"+str(ctx.author.id)+">", inline=False)
                        embed.add_field(name="**Message:**", value=ctx.content, inline=False)
                        await self.bot.get_channel(int(await self.config.guild(ctx.guild).feed())).send(embed=embed)
                    return await ctx.delete()

        strings = await self.config.guild(ctx.guild).strings()
        for key in strings:
            if ctx.content.find(strings[key]) != -1:
                feed = await self.config.guild(ctx.guild).feed()
                if feed:
                    embed = discord.Embed(colour=discord.Colour(0xf5a623), description="Spam protection deleted a message in <#"+str(ctx.channel.id)+">")
                    embed.add_field(name="**Author:**", value="<@"+str(ctx.author.id)+">", inline=False)
                    embed.add_field(name="**Message:**", value=ctx.content, inline=False)
                    await self.bot.get_channel(int(await self.config.guild(ctx.guild).feed())).send(embed=embed)
                await ctx.delete()
                return

    @commands.Cog.listener()
    async def on_message_edit(self, _prior, ctx):
        await self.on_message(ctx)
