import datetime
import re

import discord
from redbot.core import commands, Config, checks


class BotMention(commands.Cog):
    """
    Feed bot mentions
    """

    def __init__(self, bot):
        self.bot = bot
        self.mention_pattern = None
        self.cooldowns = commands.CooldownMapping.from_cooldown(
            1, 300, commands.BucketType.channel
        )
        self.__config = Config.get_conf(
            self, identifier=707350954969792584, force_registration=True
        )
        defaultsguild = {"feed": None}
        defaults = {}
        self.__config.register_guild(**defaultsguild)
        self.__config.register_global(**defaults)

    def init(self):
        pass

    @checks.admin_or_permissions(manage_roles=True)
    @commands.command()
    async def setbotmentionfeed(self, ctx, channel_id):
        await self.__config.guild(ctx.guild).feed.set(channel_id)
        await ctx.send("The bot mention feed channel has been set to {}".format(channel_id))

    @commands.Cog.listener("on_message_without_command")
    async def help_handler(self, message: discord.Message):


        if '<@!'+str(self.bot.user.id)+'>' not in message.content:
            return
        
        channel = message.channel
        guild = message.guild

        if guild:
            assert isinstance(channel, discord.TextChannel)  # nosec
            if not channel.permissions_for(guild.me).send_messages:
                return
            if not (await self.bot.ignored_channel_or_guild(message)):
                return
                # This is *supposed* to only take a context object,
                # ducktyping is safe here though

        if not (await self.bot.allowed_by_whitelist_blacklist(message.author)):
            return

        bucket = self.cooldowns.get_bucket(message)
        current = message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()

        if bucket.update_rate_limit(current):
            return

        channel_id = await self.__config.guild(message.guild).feed()
        if not channel_id:
            return

        feed_channel = self.bot.get_channel(int(channel_id))
        if not feed_channel:
            return

        embed = discord.Embed(colour=discord.Colour(0xf5a623), description="<@"+str(message.author.id)+"> mentioned <@!"+str(self.bot.user.id)+"> in <#"+str(message.channel.id)+">\n**Message:**\n"+message.content+"\n[Go to message]("+message.jump_url+")")
        if not embed:
            return
        
        await feed_channel.send(embed=embed)
        