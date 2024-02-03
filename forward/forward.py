from redbot.core import commands, checks, Config
# from googletrans import Translator
import discord
import uuid
from .converters import MuteTime
from datetime import datetime, timezone
import asyncio
import logging

from typing import Optional, Dict

# trans = Translator()

log = logging.getLogger("red.cogs.forward")

class Forward(commands.Cog):
    """Forward messages sent to the bot to the bot owner or in a specified channel."""

    __version__ = "1.2.5"

    def format_help_for_context(self, ctx):
        """Thanks Sinbad."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot

        self.config = Config.get_conf(
            self, 1398467138478, force_registration=True)
        default_global = {"toggles": {"botmessages": False},
                          "destination": None, "reply": {}, "blocked": {}, "modlog": None, "response": "Hi there, this is an automated reply."}
        self.config.register_global(**default_global)

        self.welcome = {}

        self._unblock_task = asyncio.create_task(self._handle_automatic_unblock())

    def cog_unload(self):
        self._unblock_task.cancel()

    async def _handle_automatic_unblock(self):
        """This is the core task creator and loop
        for automatic unblocks
        """
        await self.bot.wait_until_red_ready()
        while True:
            try:
                await self._process_expired_blocks()
            except Exception:
                log.error("Error checking bot unblocks", exc_info=True)
            await asyncio.sleep(60) # 60 seconds

    async def _process_expired_blocks(self):
        async with self.config.blocked() as blocked:
            for userid, until in blocked:
                if datetime.now(timezone.utc).timestamp() > until:
                    del blocked[userid]

    async def _destination(self, msg: str = None, embed: discord.Embed = None):
        await self.bot.wait_until_ready()
        channel = await self.config.destination()
        channel = self.bot.get_channel(channel)
        if channel is None:
            await self.bot.send_to_owners(msg, embed=embed)
        else:
            await channel.send(msg, embed=embed)

    @staticmethod
    def _append_attachements(message: discord.Message, embeds: list):
        attachments_urls = []
        for attachment in message.attachments:
            if any(attachment.filename.endswith(imageext) for imageext in ["jpg", "png", "gif"]):
                if embeds[0].image:
                    embed = discord.Embed()
                    embed.set_image(url=attachment.url)
                    embeds.append(embed)
                else:
                    embeds[0].set_image(url=attachment.url)
            else:
                attachments_urls.append(
                    f"[{attachment.filename}]({attachment.url})")
        if attachments_urls:
            embeds[0].add_field(name="Attachments",
                                value="\n".join(attachments_urls))
        return embeds

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        if message.guild is not None:
            return
        if message.channel.recipient.id in self.bot.owner_ids:
            return
        userid = str(message.author.id)
        async with self.config.blocked() as blocked:
            if userid in blocked:
                return
        if message.author == self.bot.user:
            async with self.config.toggles() as toggle:
                if not toggle["botmessages"]:
                    return
            msg = f"Sent PM to {message.channel.recipient} (`{message.channel.recipient.id}`)"
            if message.embeds:
                embed = discord.Embed.from_dict(
                    {**message.embeds[0].to_dict(),
                     "timestamp": str(message.created_at)}
                )
            else:
                embed = discord.Embed(
                    description=message.content, timestamp=message.created_at)
            await self._destination(msg, embed)
        else:
            embeds = []
            embeds.append(discord.Embed(description=message.content))
            embeds[0].set_author(
                name=f"{message.author} | {message.author.id}", icon_url=message.author.avatar_url
            )

            if userid not in self.welcome:
                self.welcome[userid] = True
                response = await self.config.response()
                embeds[0].add_field(name="Auto Replied:", value=response)
                await message.channel.send(response)
            # result = trans.detect(message.content)
            # if result.lang != "en":
            #     translated = trans.translate(message.content)
            #     embeds[0].add_field(name="Language", value=result.lang)
            #     embeds[0].add_field(name="Translation", value=translated.text)
            embeds = self._append_attachements(message, embeds)
            embeds[-1].timestamp = message.created_at
            for embed in embeds:
                await self._destination(msg=None, embed=embed)

    @checks.is_owner()
    @commands.group()
    async def forwardset(self, ctx):
        """Forwarding commands."""

    @forwardset.command(aliases=["botmessage"])
    async def botmsg(self, ctx, type: bool = None):
        """Set whether to send notifications when the bot sends a message.

        Type must be a valid bool.
        """
        async with self.config.toggles() as toggles:
            type = not toggles.get("botmessages")
            if type:
                toggles["botmessages"] = True
                await ctx.send("Bot message notifications have been enabled.")
            else:
                toggles["botmessages"] = False
                await ctx.send("Bot message notifications have been disabled.")

    @forwardset.command()
    async def channel(self, ctx, channel: discord.TextChannel = None):
        """Set if you want to receive notifications in a channel instead of your DMs.

        Leave blank if you want to set back to your DMs.
        """
        data = (
            {"msg": "Notifications will be sent in your DMs.", "config": None}
            if channel is None
            else {"msg": f"Notifications will be sent in {channel.mention}.", "config": channel.id}
        )
        await self.config.destination.set(data["config"])
        await ctx.send(data["msg"])

    @forwardset.command()
    async def modlog(self, ctx, channel: discord.TextChannel = None):
        """Set modlog channel
        """
        data = (
            {"msg": "Modlog will not be sent.", "config": None}
            if channel is None
            else {"msg": f"Modlog will be sent in {channel.mention}.", "config": channel.id}
        )
        await self.config.modlog.set(data["config"])
        await ctx.send(data["msg"])

    @forwardset.command()
    async def response(self, ctx, *, message: str):
        """Set auto response message
        """
        await self.config.response.set(message)
        await ctx.send('Done!')

    @commands.command()
    @commands.guild_only()
    @checks.guildowner()
    async def pm(self, ctx, user: discord.Member, *, message: str):
        """PMs a person.

        Separate version of [p]dm but allows for guild owners. This only works for users in the
        guild.
        """
        em = discord.Embed(colour=discord.Colour.red(), description=message)

        # if ctx.bot.user.avatar_url:
        #     em.set_author(
        #         name=f"Message from {ctx.author} | {ctx.author.id}",
        #         icon_url=ctx.bot.user.avatar_url,
        #     )
        # else:
        #     em.set_author(name=f"Message from {ctx.author} | {ctx.author.id}")

        em.set_author(name=f"Message from MTA Staff")

        random_hash = uuid.uuid4().hex
        em.set_footer(text=random_hash)

        try:
            await user.send(embed=em)
        except discord.Forbidden:
            await ctx.send(
                "Oops. I couldn't deliver your message to {}. They most likely have me blocked or DMs closed!".format(
                    user)
            )
        em = discord.Embed(colour=discord.Colour.green(
        ), description="Message delivered to {}".format(user)+"\n**"+message+"**")
        em.set_footer(text="@"+ctx.author.name+"#"+ctx.author.discriminator +
                      " | "+random_hash, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=em)
        async with self.config.reply() as reply:
            reply[str(ctx.author.id)] = user.id

    @commands.command()
    @commands.guild_only()
    @checks.guildowner()
    async def tpm(self, ctx, language, user: discord.Member, *, message: str):
        """Translated PMs a person.

        Separate version of [p]dm but allows for guild owners. This only works for users in the
        guild.
        """
        return await ctx.maybe_send_embed("This command is currently disabled.")
        # translated = trans.translate(message, dest=language)
        # em = discord.Embed(colour=discord.Colour.red(),
        #                    description="**Translation:**\n"+translated.text)
        # em.add_field(name="Source:", value=message)

        # # if ctx.bot.user.avatar_url:
        # #     em.set_author(
        # #         name=f"Message from {ctx.author} | {ctx.author.id}",
        # #         icon_url=ctx.bot.user.avatar_url,
        # #     )
        # # else:
        # #     em.set_author(name=f"Message from {ctx.author} | {ctx.author.id}")

        # em.set_author(name=f"Message from MTA Staff")

        # random_hash = uuid.uuid4().hex
        # em.set_footer(text=random_hash)

        # try:
        #     await user.send(embed=em)
        # except discord.Forbidden:
        #     await ctx.send(
        #         "Oops. I couldn't deliver your message to {}. They most likely have me blocked or DMs closed!".format(
        #             user)
        #     )
        # em = discord.Embed(colour=discord.Colour.green(), description="Message delivered to {}".format(
        #     user)+"\n**Translation:**\n"+translated.text+"")
        # em.set_footer(text="@"+ctx.author.name+"#"+ctx.author.discriminator +
        #               " | "+random_hash, icon_url=ctx.author.avatar_url)
        # em.add_field(name="Source:", value=message)
        # await ctx.send(embed=em)
        # async with self.config.reply() as reply:
        #     reply[str(ctx.author.id)] = user.id

    @commands.command()
    @commands.guild_only()
    @checks.guildowner()
    async def tblock(self, ctx, user: discord.Member, time: Optional[MuteTime] = None):
        """Blocks a member from sending dms to the bot
        """
        async with self.config.blocked() as blocked:
            userid = str(user.id)
            if userid not in blocked:
                duration = time.get("duration") if time else MuteTime().convert(ctx, "5d").get("duration")
                blocked[userid] = (datetime.now(timezone.utc) + duration).timestamp() # until
                await ctx.maybe_send_embed("Blocked <@{id}> from send messages to the bot until {until}.".format(id=userid, until=datetime.fromtimestamp(blocked[userid])))
            else:
                await ctx.maybe_send_embed("This user is already blocked until {}.".format(datetime.fromtimestamp(blocked[userid])))

    @commands.command()
    @commands.guild_only()
    @checks.guildowner()
    async def tunblock(self, ctx, user: discord.Member):
        """Unblocks a member from sending dms
        """
        async with self.config.blocked() as blocked:
            userid = str(user.id)
            if userid in blocked:
                del blocked[userid]
                await ctx.maybe_send_embed("Unblocked <@{}> from sending messages to the bot.".format(userid))
            else:
                await ctx.maybe_send_embed("This user is not blocked.")

    @commands.command()
    @commands.guild_only()
    @checks.guildowner()
    async def tcheckblock(self, ctx, user: discord.Member):
        """Checks if a member is blocked from sending dms to the bot
        """
        async with self.config.blocked() as blocked:
            userid = str(user.id)
            if userid in blocked:
                await ctx.maybe_send_embed("User <@{id}> is blocked until {until}.".format(id=userid, until=datetime.fromtimestamp(blocked[userid])))
            else:
                await ctx.maybe_send_embed("This user is not blocked.")

    @commands.command(name="r")
    @commands.guild_only()
    @checks.guildowner()
    async def reply(self, ctx, *, message: str):
        """Reply your last pm recipient
        """
        reply = await self.config.reply()
        if reply[str(ctx.author.id)] is None:
            return await ctx.send("You have no recipient yet!")

        user_id = reply[str(ctx.author.id)]
        user = await self.bot.fetch_user(user_id)

        em = discord.Embed(colour=discord.Colour.red(), description=message)

        # if ctx.bot.user.avatar_url:
        #     em.set_author(
        #         name=f"Message from {ctx.author} | {ctx.author.id}",
        #         icon_url=ctx.bot.user.avatar_url,
        #     )
        # else:
        #     em.set_author(name=f"Message from {ctx.author} | {ctx.author.id}")

        em.set_author(name=f"Message from MTA Staff")

        random_hash = uuid.uuid4().hex
        em.set_footer(text=random_hash)

        try:
            await user.send(embed=em)
        except discord.Forbidden:
            await ctx.send(
                "Oops. I couldn't deliver your message to {}. They most likely have me blocked or DMs closed!".format(
                    user)
            )
        em = discord.Embed(colour=discord.Colour.green(
        ), description="Message delivered to {}".format(user)+"\n``"+message+"``")
        em.set_footer(text="@"+ctx.author.name+"#"+ctx.author.discriminator +
                      " | "+random_hash, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=em)

    @commands.guild_only()
    @checks.mod_or_permissions(manage_roles=True)
    @commands.command()
    async def talk(self, ctx, channel: discord.TextChannel, *, message: str):
        """Send message in a channel
        """
        msg = await channel.send(message)
        channel = await self.config.modlog()
        if channel:
            channel = self.bot.get_channel(channel)
            random_hash = uuid.uuid4().hex
            em = discord.Embed(colour=discord.Colour.green(
            ), description="Message delivered to <#{}".format(msg.channel.id)+">\n``"+message+"``\n[Goto]({})".format(msg.jump_url))
            em.set_footer(text="@"+ctx.author.name+"#"+ctx.author.discriminator +
                          " | "+random_hash, icon_url=ctx.author.avatar_url)
            await channel.send(embed=em)
