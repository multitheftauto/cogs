from collections import defaultdict, deque

from redbot.core import commands, i18n, checks
from redbot.core.utils.chat_formatting import box

from .abc import MixinMeta

_ = i18n.Translator("Mod", __file__)


class ModSettings(MixinMeta):
    """
    This is a mixin for the mod cog containing all settings commands.
    """

    @commands.group()
    @commands.guild_only()
    @checks.guildowner_or_permissions(administrator=True)
    async def modset(self, ctx: commands.Context):
        """Manage server administration settings."""

    @modset.command(name="showsettings")
    async def modset_showsettings(self, ctx: commands.Context):
        """Show the current server administration settings."""
        guild = ctx.guild
        data = await self.config.guild(guild).all()
        delete_repeats = data["delete_repeats"]
        ban_mention_spam = data["ban_mention_spam"]
        respect_hierarchy = data["respect_hierarchy"]
        delete_delay = data["delete_delay"]
        reinvite_on_unban = data["reinvite_on_unban"]
        dm_on_kickban = data["dm_on_kickban"]
        default_days = data["default_days"]
        msg = ""
        msg += _("Delete repeats: {num_repeats}\n").format(
            num_repeats=_("after {num} repeats").format(num=delete_repeats)
            if delete_repeats != -1
            else _("No")
        )
        msg += _("Ban mention spam: {num_mentions}\n").format(
            num_mentions=_("{num} mentions").format(num=ban_mention_spam)
            if ban_mention_spam
            else _("No")
        )
        msg += _("Respects hierarchy: {yes_or_no}\n").format(
            yes_or_no=_("Yes") if respect_hierarchy else _("No")
        )
        msg += _("Delete delay: {num_seconds}\n").format(
            num_seconds=_("{num} seconds").format(num=delete_delay)
            if delete_delay != -1
            else _("None")
        )
        msg += _("Reinvite on unban: {yes_or_no}\n").format(
            yes_or_no=_("Yes") if reinvite_on_unban else _("No")
        )
        msg += _("Send message to users on kick/ban: {yes_or_no}\n").format(
            yes_or_no=_("Yes") if dm_on_kickban else _("No")
        )
        if default_days:
            msg += _("Default message history delete on ban: Previous {num_days} days\n").format(
                num_days=default_days
            )
        else:
            msg += _("Default message history delete on ban: Don't delete any\n")
        await ctx.send(box(msg))

    @modset.command()
    @commands.guild_only()
    async def hierarchy(self, ctx: commands.Context):
        """Toggle role hierarchy check for mods and admins.

        **WARNING**: Disabling this setting will allow mods to take
        actions on users above them in the role hierarchy!

        This is enabled by default.
        """
        guild = ctx.guild
        toggled = await self.config.guild(guild).respect_hierarchy()
        if not toggled:
            await self.config.guild(guild).respect_hierarchy.set(True)
            await ctx.send(
                _("Role hierarchy will be checked when moderation commands are issued.")
            )
        else:
            await self.config.guild(guild).respect_hierarchy.set(False)
            await ctx.send(
                _("Role hierarchy will be ignored when moderation commands are issued.")
            )

    @modset.command()
    @commands.guild_only()
    async def banmentionspam(self, ctx: commands.Context, max_mentions: int = 0):
        """Set the autoban conditions for mention spam.

        Users will be banned if they send any message which contains more than
        `<max_mentions>` mentions.

        `<max_mentions>` must be at least 5. Set to 0 to disable.
        """
        guild = ctx.guild
        if max_mentions:
            if max_mentions < 5:
                max_mentions = 5
            await self.config.guild(guild).ban_mention_spam.set(max_mentions)
            await ctx.send(
                _(
                    "Autoban for mention spam enabled. "
                    "Anyone mentioning {max_mentions} or more different people "
                    "in a single message will be autobanned."
                ).format(max_mentions=max_mentions)
            )
        else:
            cur_setting = await self.config.guild(guild).ban_mention_spam()
            if not cur_setting:
                await ctx.send(_("Autoban for mention spam is already disabled."))
                return
            await self.config.guild(guild).ban_mention_spam.set(False)
            await ctx.send(_("Autoban for mention spam disabled."))

    @modset.command()
    @commands.guild_only()
    async def deleterepeats(self, ctx: commands.Context, repeats: int = None):
        """Enable auto-deletion of repeated messages.

        Must be between 2 and 20.

        Set to -1 to disable this feature.
        """
        guild = ctx.guild
        if repeats is not None:
            if repeats == -1:
                await self.config.guild(guild).delete_repeats.set(repeats)
                self.cache.pop(guild.id, None)  # remove cache with old repeat limits
                await ctx.send(_("Repeated messages will be ignored."))
            elif 2 <= repeats <= 20:
                await self.config.guild(guild).delete_repeats.set(repeats)
                # purge and update cache to new repeat limits
                self.cache[guild.id] = defaultdict(lambda: deque(maxlen=repeats))
                await ctx.send(
                    _("Messages repeated up to {num} times will be deleted.").format(num=repeats)
                )
            else:
                await ctx.send(
                    _(
                        "Number of repeats must be between 2 and 20"
                        " or equal to -1 if you want to disable this feature!"
                    )
                )
        else:
            repeats = await self.config.guild(guild).delete_repeats()
            if repeats != -1:
                await ctx.send(
                    _(
                        "Bot will delete repeated messages after"
                        " {num} repeats. Set this value to -1 to"
                        " ignore repeated messages"
                    ).format(num=repeats)
                )
            else:
                await ctx.send(_("Repeated messages will be ignored."))

    @modset.command()
    @commands.guild_only()
    async def reinvite(self, ctx: commands.Context):
        """Toggle whether an invite will be sent to a user when unbanned.

        If this is True, the bot will attempt to create and send a single-use invite
        to the newly-unbanned user.
        """
        guild = ctx.guild
        cur_setting = await self.config.guild(guild).reinvite_on_unban()
        if not cur_setting:
            await self.config.guild(guild).reinvite_on_unban.set(True)
            await ctx.send(
                _("Users unbanned with `{command}` will be reinvited.").format(
                    command=f"{ctx.clean_prefix}unban"
                )
            )
        else:
            await self.config.guild(guild).reinvite_on_unban.set(False)
            await ctx.send(
                _("Users unbanned with `{command}` will not be reinvited.").format(
                    command=f"{ctx.clean_prefix}unban"
                )
            )

    @modset.command()
    @commands.guild_only()
    async def dm(self, ctx: commands.Context, enabled: bool = None):
        """Toggle whether a message should be sent to a user when they are kicked/banned.

        If this option is enabled, the bot will attempt to DM the user with the guild name
        and reason as to why they were kicked/banned.
        """
        guild = ctx.guild
        if enabled is None:
            setting = await self.config.guild(guild).dm_on_kickban()
            await ctx.send(
                _("DM when kicked/banned is currently set to: {setting}").format(setting=setting)
            )
            return
        await self.config.guild(guild).dm_on_kickban.set(enabled)
        if enabled:
            await ctx.send(_("Bot will now attempt to send a DM to user before kick and ban."))
        else:
            await ctx.send(
                _("Bot will no longer attempt to send a DM to user before kick and ban.")
            )

    @modset.command()
    @commands.guild_only()
    async def defaultdays(self, ctx: commands.Context, days: int = 0):
        """Set the default number of days worth of messages to be deleted when a user is banned.

        The number of days must be between 0 and 7.
        """
        guild = ctx.guild
        if not (0 <= days <= 7):
            return await ctx.send(_("Invalid number of days. Must be between 0 and 7."))
        await self.config.guild(guild).default_days.set(days)
        await ctx.send(
            _("{days} days worth of messages will be deleted when a user is banned.").format(
                days=days
            )
        )
