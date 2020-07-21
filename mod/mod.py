import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import discord
from redbot.cogs.mod import Mod as ModClass
from redbot.core import Config, checks, commands, modlog
from redbot.core.commands.converter import TimedeltaConverter
from redbot.core.utils.chat_formatting import humanize_list, humanize_timedelta, inline
from redbot.core.utils.mod import is_allowed_by_hierarchy
from redbot.core.utils.predicates import MessagePredicate

log = logging.getLogger("red.flarecogs.mod")


class Mod(ModClass):
    """Mod with timed mute."""

    __version__ = "1.1.5"

    def format_help_for_context(self, ctx):
        """Thanks Sinbad."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.__config = Config.get_conf(
            self, identifier=95932766180343808, force_registration=True
        )
        defaultsguild = {"muterole": None, "respect_hierarchy": True}
        defaults = {"muted": {}}
        self.__config.register_guild(**defaultsguild)
        self.__config.register_global(**defaults)
        self.loop = bot.loop.create_task(self.unmute_loop())

    # Removes main mods mute commands.
    voice_mute = None
    channel_mute = None
    guild_mute = None
    unmute_voice = None
    unmute_channel = None
    unmute_guild = None
    ban = None
    unban = None
    hackban = None
    tempban = None
    softban = None

    def cog_unload(self):
        self.loop.cancel()

    async def unmute_loop(self):
        while True:
            muted = await self.__config.muted()
            for guild in muted:
                for user in muted[guild]:
                    if datetime.fromtimestamp(muted[guild][user]["expiry"]) < datetime.now():
                        await self.unmute(user, guild)
            await asyncio.sleep(15)

    async def unmute(self, user, guildid, *, moderator: discord.Member = None):
        guild = self.bot.get_guild(int(guildid))
        if guild is None:
            return
        mutedroleid = await self.__config.guild(guild).muterole()
        muterole = guild.get_role(mutedroleid)
        member = guild.get_member(int(user))
        if member is not None:
            if moderator is None:
                await member.remove_roles(muterole, reason="Mute expired.")
                log.info("Unmuted {} in {}.".format(member, guild))
            else:
                await member.remove_roles(muterole, reason="Unmuted by {}.".format(moderator))
                log.info("Unmuted {} in {} by {}.".format(member, guild, moderator))
            await modlog.create_case(
                self.bot,
                guild,
                datetime.utcnow(),
                "sunmute",
                member,
                moderator,
                "Automatic Unmute" if moderator is None else None,
            )
        else:
            log.info("{} is no longer in {}, removing from muted list.".format(user, guild))
        async with self.__config.muted() as muted:
            if user in muted[guildid]:
                del muted[guildid][user]

    async def create_muted_role(self, guild):
        muted_role = await guild.create_role(
            name="Muted", reason="Muted role created for timed mutes."
        )
        await self.__config.guild(guild).muterole.set(muted_role.id)
        o = discord.PermissionOverwrite(send_messages=False, add_reactions=False, connect=False)
        for channel in guild.channels:
            mr_overwrite = channel.overwrites.get(muted_role)
            if not mr_overwrite or o != mr_overwrite:
                await channel.set_permissions(
                    muted_role,
                    overwrite=o,
                    reason="Ensures that Muted users won't be able to talk here.",
                )

    @checks.mod_or_permissions(manage_roles=True)
    @checks.bot_has_permissions(manage_roles=True)
    @commands.group(invoke_without_command=True)
    async def mute(
        self,
        ctx,
        users: commands.Greedy[discord.Member],
        duration: Optional[TimedeltaConverter] = None,
        *,
        reason: str = None,
    ):
        """Mute users."""
        if not users:
            return await ctx.send_help()
        if duration is None:
            duration = timedelta(minutes=10)
        duration_seconds = duration.total_seconds()
        guild = ctx.guild
        roleid = await self.__config.guild(guild).muterole()
        if roleid is None:
            await ctx.send(
                "There is currently no mute role set for this server. If you would like one to be automatically setup then type yes, otherwise type no then one can be set via {}mute roleset <role>".format(
                    ctx.prefix
                )
            )
            try:
                pred = MessagePredicate.yes_or_no(ctx, user=ctx.author)
                msg = await ctx.bot.wait_for("message", check=pred, timeout=60)
            except asyncio.TimeoutError:
                return await ctx.send("Alright, cancelling the operation.")

            if pred.result:
                await msg.add_reaction("\N{WHITE HEAVY CHECK MARK}")
                await self.create_muted_role(guild)
                roleid = await self.__config.guild(guild).muterole()
            else:
                await msg.add_reaction("\N{WHITE HEAVY CHECK MARK}")
                return
        mutedrole = guild.get_role(roleid)
        if mutedrole is None:
            return await ctx.send(
                f"The mute role for this server is invalid. Please set one up using {ctx.prefix}mute roleset <role>."
            )
        completed = []
        failed = []
        async with self.__config.muted() as muted:
            if str(ctx.guild.id) not in muted:
                muted[str(ctx.guild.id)] = {}
            for user in users:
                if user == ctx.author:
                    failed.append(f"{user} - Self harm is bad.")
                    continue
                if not await is_allowed_by_hierarchy(
                    self.bot, self.__config, guild, ctx.author, user
                ):
                    failed.append(
                        f"{user} - You are not higher than this user in the role hierarchy"
                    )
                    continue
                if guild.me.top_role <= user.top_role or user == guild.owner:
                    failed.append(
                        f"{user} - Discord hierarcy rules prevent you from muting this user."
                    )
                    continue
                await user.add_roles(
                    mutedrole,
                    reason="Muted by {} for {}{}".format(
                        ctx.author,
                        humanize_timedelta(timedelta=duration),
                        f" | Reason: {reason}" if reason is not None else "",
                    ),
                )
                expiry = datetime.now() + timedelta(seconds=duration_seconds)
                muted[str(ctx.guild.id)][str(user.id)] = {
                    "time": datetime.now().timestamp(),
                    "expiry": expiry.timestamp(),
                }
                await modlog.create_case(
                    ctx.bot,
                    ctx.guild,
                    ctx.message.created_at,
                    "smute",
                    user,
                    ctx.author,
                    reason,
                    expiry,
                )
                log.info(
                    f"{user} muted by {ctx.author} in {ctx.guild} for {humanize_timedelta(timedelta=duration)}"
                )
                completed.append(user)
        msg = "{}".format("\n**Reason**: {}".format(reason) if reason is not None else "")
        if completed:
            await ctx.send(
                f"`{humanize_list(list(map(inline, [str(x) for x in completed])))}` has been muted for {humanize_timedelta(timedelta=duration)}.{msg}"
            )
        if failed:
            failemsg = "\n{}".format("\n".join(failed))
            await ctx.send(
                f"{len(failed)} user{'s' if len(failed) > 1 else ''} failed to be muted for the following reasons.{failemsg}"
            )

    @checks.admin_or_permissions(manage_roles=True)
    @mute.command()
    async def roleset(self, ctx, role: discord.Role):
        """Set a mute role."""
        await self.__config.guild(ctx.guild).muterole.set(role.id)
        await ctx.send("The muted role has been set to {}".format(role.name))

    @checks.mod_or_permissions(manage_roles=True)
    @checks.bot_has_permissions(manage_roles=True)
    @commands.group(invoke_without_command=True, name="unmute")
    async def _unmute(self, ctx, users: commands.Greedy[discord.Member]):
        """Unmute users."""
        muted = await self.__config.muted()
        for user in users:
            if str(ctx.guild.id) not in muted:
                return await ctx.send("There is nobody currently muted in this server.")
            await self.unmute(str(user.id), str(ctx.guild.id), moderator=ctx.author)
            await ctx.tick()

    @checks.mod_or_permissions(manage_roles=True)
    @mute.command(name="list")
    async def _list(self, ctx):
        """List those who are muted."""
        muted = await self.__config.muted()
        guildmuted = muted.get(str(ctx.guild.id))
        if guildmuted is None:
            return await ctx.send("There is currently nobody muted in {}".format(ctx.guild))
        msg = ""
        for user in guildmuted:
            expiry = datetime.fromtimestamp(guildmuted[user]["expiry"]) - datetime.now()
            msg += f"{self.bot.get_user(int(user)).mention} is muted for {humanize_timedelta(timedelta=expiry)}\n"
        await ctx.maybe_send_embed(msg if msg else "Nobody is currently muted.")

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @checks.admin_or_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        user_id: int,
        duration: Optional[commands.TimedeltaConverter] = None,
        days: Optional[int] = None,
        *,
        reason: str = None,
    ):
        """Ban a user from this server and optionally temporary or delete days of messages.
        If days is not a number, it's treated as the first word of the reason.
        Minimum 0 days, maximum 7. If not specified, defaultdays setting will be used instead."""
        guild = ctx.guild
        author = ctx.author
        if duration:
            unban_time = datetime.utcnow() + duration

        user = self.bot.get_user(user_id)

        if not user:
            await ctx.send(
                ("User not found!")
            )
            return

        if author == user:
            await ctx.send(
                ("I cannot let you do that. Self-harm is bad {}").format("\N{PENSIVE FACE}")
            )
            return
        elif not await is_allowed_by_hierarchy(self.bot, self.config, guild, author, user):
            await ctx.send(
                (
                    "I cannot let you do that. You are "
                    "not higher than the user in the role "
                    "hierarchy."
                )
            )
            return
        elif guild.me.top_role <= user.top_role or user == guild.owner:
            await ctx.send(("I cannot do that due to discord hierarchy rules"))
            return

        if days is None:
            days = await self.config.guild(guild).default_days()

        if not unban_time:
            if days is None:
                days = await self.config.guild(guild).default_days()

            result = await self.ban_user(
                user=user, ctx=ctx, days=days, reason=reason, create_modlog_case=True
            )

            if result is True:
                await ctx.send(("Done. It was about time."))
            elif isinstance(result, str):
                await ctx.send(result)
        else:
            if not (0 <= days <= 7):
                await ctx.send(("Invalid days. Must be between 0 and 7."))
                return
            invite = await self.get_invite_for_reinvite(ctx, int(duration.total_seconds() + 86400))
            if invite is None:
                invite = ""

            queue_entry = (guild.id, user.id)
            await self.config.member(user).banned_until.set(unban_time.timestamp())
            async with self.config.guild(guild).current_tempbans() as current_tempbans:
                current_tempbans.append(user.id)

            with contextlib.suppress(discord.HTTPException):
                # We don't want blocked DMs preventing us from banning
                msg = ("You have been temporarily banned from {server_name} until {date}.").format(
                    server_name=guild.name, date=unban_time.strftime("%m-%d-%Y %H:%M:%S")
                )
                if invite:
                    msg += (" Here is an invite for when your ban expires: {invite_link}").format(
                        invite_link=invite
                    )
                await user.send(msg)
            try:
                await guild.ban(user, reason=reason, delete_message_days=days)
            except discord.Forbidden:
                await ctx.send(("I can't do that for some reason."))
            except discord.HTTPException:
                await ctx.send(("Something went wrong while banning."))
            else:
                try:
                    await modlog.create_case(
                        self.bot,
                        guild,
                        ctx.message.created_at,
                        "tempban",
                        user,
                        author,
                        reason,
                        unban_time,
                    )
                except RuntimeError as e:
                    await ctx.send(e)
                await ctx.send(("Done. Enough chaos for now."))
