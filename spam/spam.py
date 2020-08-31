import discord
from redbot.core import commands, checks, data_manager
from redbot.core.config import Config
from redbot.core.utils import mod

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
    async def remove(self, ctx, name):
        async with self.config.guild(ctx.guild).strings() as strings:
            if name in strings:
                del strings[name]
                await ctx.maybe_send_embed("Removed ``{}`` from the list".format(name))
            else:
                await ctx.maybe_send_embed("Doesn't exist.")

    @spam.command(name="list")
    async def _list(self, ctx):
        strings = await self.config.guild(ctx.guild).strings()
        msg = ""
        for key in strings:
            msg += "``{}`` > ``{}``\n".format(key, strings[key])
        await ctx.maybe_send_embed(msg if msg else "List is empty.")
        pass

    @checks.admin_or_permissions(manage_roles=True)
    @spam.command()
    async def setfeed(self, ctx, channel_id):
        await self.config.guild(ctx.guild).feed.set(channel_id)
        await ctx.maybe_send_embed("The feed channel has been set to {}".format(channel_id))

    @commands.Cog.listener()
    async def on_message_without_command(self, ctx):
        if ctx.author.bot:
            return
        guild = ctx.guild
        if guild is None:
            return
        active = await self.config.guild(ctx.guild).active()
        if not active:
            return

        strings = await self.config.guild(ctx.guild).strings()
        for key in strings:
            if ctx.content.find(strings[key]) != -1:
                feed = await self.config.guild(ctx.guild).feed()
                if feed:
                    embed = discord.Embed(colour=discord.Colour(0xf5a623), description="Spam protection deleted a message in <#"+str(ctx.channel.id)+">")
                    embed.add_field(name="**Message:**", value=ctx.content, inline=False)
                    await self.bot.get_channel(int(await self.config.guild(ctx.guild).feed())).send(embed=embed)
                await ctx.delete()
                return
