import discord
from redbot.core import Config, checks, commands


class ModReq(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.__config = Config.get_conf(
            self, identifier=95932766180343809, force_registration=True
        )
        defaultsguild = {"feed": None}
        defaults = {}
        self.__config.register_guild(**defaultsguild)
        self.__config.register_global(**defaults)

    @commands.command(name="mod", alias="mod")
    async def mod_request(self, ctx, *message):
        await ctx.message.delete()
        embed = discord.Embed(colour=discord.Colour(0xf5a623), description="<@"+str(ctx.author.id)+"> requested a moderator in <#"+str(ctx.channel.id)+"> here: "+ctx.message.jump_url)
        embed.add_field(name="**Reason:**", value=" ".join(message), inline=False)
        await self.bot.get_channel(int(await self.__config.guild(ctx.guild).feed())).send(embed=embed)
        embed = discord.Embed(colour=discord.Colour(0xf5a623), description="Your request was received <@"+str(ctx.author.id)+">, a moderator will review and report back soon.")
        await ctx.author.send(embed=embed)

    @checks.admin_or_permissions(manage_roles=True)
    @commands.command()
    async def setfeed(self, ctx, channel_id):
        await self.__config.guild(ctx.guild).feed.set(channel_id)
        await ctx.send("The feed channel has been set to {}".format(channel_id))
