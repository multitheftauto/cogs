import discord
from redbot.core import Config, checks, commands
from typing import Union, Dict
from datetime import timedelta

class Helper(commands.Cog):
    """Helper cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=707350954969792584)
        default_channel = {"role": None, "feed": None, "duration": None}
        self.config.register_channel(**default_channel)

    @commands.command()
    async def timeout(self, ctx, member: discord.Member):
        role_id = await self.config.guild(ctx.guild).role()
        role = discord.utils.find(lambda r: r.id == role_id, ctx.message.guild.roles)
        if role in ctx.author.roles:
            res: Dict[str, Union[timedelta, str, None]] = {}
            res["duration"] = timedelta(minutes=60)
            res["reason"] = "Helper timeout"
            await ctx.invoke(self.bot.get_command('mute'), users=[member], time_and_reason=res)
            feed_id = await self.config.guild(ctx.guild).feed()
            if feed_id:
                embed = discord.Embed(colour=discord.Colour(0xf5a623), description="{} issued a timeout to {}".format(ctx.author.mention, member.mention))
                await self.bot.get_channel(int(feed_id)).send(embed=embed)
        pass

    @checks.admin_or_permissions(manage_roles=True)
    @commands.group()
    async def helperset(self, ctx):
        pass

    @helperset.command()
    async def feed(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).feed.set(channel.id)
        await ctx.send("Helper feed set to {}".format(channel.mention))

    @helperset.command()
    async def role(self, ctx, role: discord.Role):
        await self.config.guild(ctx.guild).role.set(role.id)
        await ctx.send("Helper role set to {}".format(role.mention))