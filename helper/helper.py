import contextlib
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from redbot.core import Config, checks, commands

DEFAULT_TIMEOUT = timedelta(hours=1)
MIN_TIMEOUT = timedelta(minutes=1)
MAX_TIMEOUT = timedelta(days=28)

_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}


def parse_duration(raw: str) -> Optional[timedelta]:
    """Read a duration like ``30m``, ``2h``, ``1d12h`` or a bare number of minutes."""
    if not raw:
        return None
    text = raw.strip().lower()
    if text.isdigit():
        return timedelta(minutes=int(text))
    parts = re.findall(r"(\d+)\s*([dhms])", text)
    if not parts:
        return None
    seconds = sum(int(amount) * _UNIT_SECONDS[unit] for amount, unit in parts)
    return timedelta(seconds=seconds) if seconds else None


def format_duration(delta: timedelta) -> str:
    """Short human form, e.g. ``1h 30m``."""
    total = int(delta.total_seconds())
    chunks = []
    for unit, size in (("d", 86400), ("h", 3600), ("m", 60)):
        amount, total = divmod(total, size)
        if amount:
            chunks.append("{}{}".format(amount, unit))
    return " ".join(chunks) or "0m"


class Helper(commands.Cog):
    """Helper role tools: native member timeouts with an audit feed."""

    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger("red.cogs.helper")
        self.config = Config.get_conf(self, identifier=707350954969792584)
        self.config.register_guild(role=None, feed=None, channel=None)

    async def _allowed(self, ctx):
        """Return (is_allowed_channel, is_helper) for the invoker."""
        conf = self.config.guild(ctx.guild)
        helpers_channel_id = await conf.channel()
        helper_role_id = await conf.role()
        helper_role = ctx.guild.get_role(helper_role_id) if helper_role_id else None

        in_helpers_channel = helpers_channel_id is None or ctx.channel.id == helpers_channel_id
        is_helper = helper_role is not None and helper_role in ctx.author.roles
        return in_helpers_channel, is_helper

    @commands.command()
    @commands.guild_only()
    async def timeout(
        self,
        ctx,
        member: discord.Member,
        duration: Optional[str] = None,
        *,
        reason: Optional[str] = None,
    ):
        """Time out a member with Discord's native timeout.

        Only the helper role can use this, and only in the helpers channel.
        Defaults to 1 hour. Duration accepts `30m`, `2h`, `1d`, `1d12h`, or a
        bare number of minutes. Max 28 days. Every use is logged to the feed.
        """
        in_helpers_channel, is_helper = await self._allowed(ctx)

        # Outside the helpers channel the command is invisible: no reply, no
        # deletion, nothing.
        if not in_helpers_channel:
            self.log.debug("timeout ignored outside the helpers channel: %s", ctx.channel.id)
            return

        if not is_helper:
            await ctx.send(
                "Only helpers can use this command.", delete_after=10, allowed_mentions=discord.AllowedMentions.none()
            )
            return

        guild = ctx.guild

        if member.id == ctx.author.id:
            return await ctx.send("You cannot time yourself out.", delete_after=10)
        if member.bot:
            return await ctx.send("Bots cannot be timed out.", delete_after=10)
        if member.id == guild.owner_id:
            return await ctx.send("The server owner cannot be timed out.", delete_after=10)
        if not guild.me.guild_permissions.moderate_members:
            return await ctx.send(
                "I need the **Moderate Members** permission to time someone out.", delete_after=10
            )
        if member.top_role >= guild.me.top_role:
            return await ctx.send(
                "{} has a role above mine, so I cannot time them out.".format(member.display_name),
                delete_after=10,
            )
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(
                "{} has a role above yours, so you cannot time them out.".format(member.display_name),
                delete_after=10,
            )

        if duration is None:
            delta = DEFAULT_TIMEOUT
        else:
            delta = parse_duration(duration)
            if delta is None:
                return await ctx.send(
                    "I could not read that duration. Try `30m`, `2h` or `1d`.", delete_after=10
                )
            if delta < MIN_TIMEOUT:
                return await ctx.send("The shortest timeout is 1 minute.", delete_after=10)
            if delta > MAX_TIMEOUT:
                return await ctx.send("The longest timeout is 28 days.", delete_after=10)

        until = datetime.now(timezone.utc) + delta
        audit_reason = "{}: {}".format(ctx.author, reason) if reason else str(ctx.author)

        try:
            await member.timeout(until, reason=audit_reason[:512])
        except discord.Forbidden:
            return await ctx.send("I do not have permission to time that member out.", delete_after=10)
        except discord.HTTPException as error:
            self.log.warning("timeout request rejected for %s: %s", member.id, error)
            return await ctx.send(
                "Discord rejected that timeout (`{}`).".format(error.status), delete_after=10
            )

        embed = discord.Embed(colour=discord.Colour(0xF5A623), timestamp=datetime.now(timezone.utc))
        embed.description = "{} timed out {} for **{}**".format(
            ctx.author.mention, member.mention, format_duration(delta)
        )
        if reason:
            embed.add_field(name="Reason", value=reason[:1024])
        embed.set_footer(text="Ends {}".format(until.strftime("%Y-%m-%d %H:%M UTC")))
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

        feed_id = await self.config.guild(ctx.guild).feed()
        if not feed_id:
            return
        feed = guild.get_channel(feed_id)
        if feed is None:
            try:
                feed = await self.bot.fetch_channel(feed_id)
            except discord.HTTPException:
                return
        log_embed = discord.Embed(colour=discord.Colour(0xF5A623), timestamp=datetime.now(timezone.utc))
        log_embed.description = "{} ({}) issued a timeout to {} ({})".format(
            ctx.author.mention, ctx.author.id, member.mention, member.id
        )
        log_embed.add_field(name="Duration", value=format_duration(delta), inline=True)
        log_embed.add_field(name="Reason", value=(reason or "No reason given")[:1024], inline=True)
        log_embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
        with contextlib.suppress(discord.HTTPException):
            await feed.send(embed=log_embed, allowed_mentions=discord.AllowedMentions.none())

    @checks.admin_or_permissions(manage_roles=True)
    @commands.group()
    async def helperset(self, ctx):
        """Configure the helper role, the helpers channel and the timeout feed."""

    @helperset.command(name="show")
    async def helperset_show(self, ctx):
        """Show the current helper settings."""
        conf = self.config.guild(ctx.guild)
        role_id = await conf.role()
        channel_id = await conf.channel()
        feed_id = await conf.feed()
        role = ctx.guild.get_role(role_id) if role_id else None
        channel = ctx.guild.get_channel(channel_id) if channel_id else None
        feed = ctx.guild.get_channel(feed_id) if feed_id else None
        embed = discord.Embed(title="Helper settings", colour=discord.Colour(0xF5A623))
        embed.add_field(name="Helper role", value=role.mention if role else "not set")
        embed.add_field(name="Helpers channel", value=channel.mention if channel else "any channel")
        embed.add_field(name="Timeout feed", value=feed.mention if feed else "not set")
        await ctx.send(embed=embed)

    @helperset.command(name="role")
    async def helperset_role(self, ctx, role: discord.Role):
        """Set the role that may use helper commands."""
        await self.config.guild(ctx.guild).role.set(role.id)
        await ctx.send("Helper role set to {}.".format(role.mention))

    @helperset.command(name="channel")
    async def helperset_channel(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Restrict helper commands to one channel. Leave empty to allow anywhere."""
        if channel is None:
            await self.config.guild(ctx.guild).channel.set(None)
            return await ctx.send("Helper commands are now allowed in any channel.")
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send("Helper commands are now restricted to {}.".format(channel.mention))

    @helperset.command(name="feed")
    async def helperset_feed(self, ctx, channel: discord.TextChannel):
        """Set the channel that timeout logs are posted to."""
        await self.config.guild(ctx.guild).feed.set(channel.id)
        await ctx.send("Helper feed set to {}.".format(channel.mention))
