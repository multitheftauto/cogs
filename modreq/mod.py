import discord
from redbot.core import Config, checks, commands

class ModReq(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=735865928033501194)
        default_global = {
            "category_moderator_roles": {},
            "feed_channel_id": None
        }
        self.config.register_global(**default_global)

    @commands.command()
    async def mod(self, ctx, *, message: str):
        """
        Moderator help request.
        """
        jump_link = f"[Jump]({ctx.message.jump_url})"
        
        # Send PM to user
        embed = discord.Embed(title="New help request", description=f"Your help request has been sent. {jump_link}", color=discord.Color.green())
        await ctx.author.send(embed=embed)

        channel_category = ctx.channel.category
        
        category_moderator_roles = await self.config.category_moderator_roles()
        moderator_role_id = None
        if str(channel_category.id) in category_moderator_roles:
            moderator_role_id = category_moderator_roles[str(channel_category.id)]

        feed_channel_id = await self.config.feed_channel_id()
        feed_channel = self.bot.get_channel(feed_channel_id) if feed_channel_id else None
        
        if feed_channel:
            if moderator_role_id:
                moderator_role = discord.utils.get(ctx.guild.roles, id=moderator_role_id)
                if moderator_role:
                    description = f"{message}"
                    embed = discord.Embed(title="New help request", description=description, color=discord.Color.green())
                    embed.add_field(name="Category", value=f"{channel_category.name}")
                    embed.add_field(name="Channel", value=f"{ctx.channel.mention} {jump_link}")
                    await feed_channel.send(f"{moderator_role.mention}", embed=embed)
            else:
                description = f"{message}"
                embed = discord.Embed(title="New help request",description=description, color=discord.Color.green())
                embed.add_field(name="Category", value=f"{channel_category.name}")
                embed.add_field(name="Channel", value=f"{ctx.channel.mention} {jump_link}")
                await feed_channel.send("@here", embed=embed)
        else:
            await ctx.send("Feed channel not set.")

    @commands.group()
    async def modreqset(self, ctx):
        """
        Settings for modreq command
        """
        pass

    @modreqset.command()
    async def feedchannel(self, ctx, channel: discord.TextChannel):
        """
        Set the feed channel where the modreq messages will be sent.
        """
        await self.config.feed_channel_id.set(channel.id)
        await ctx.send(f"Feed channel set to {channel.name}.")

    @modreqset.command()
    async def modrole(self, ctx, category: discord.CategoryChannel, role: discord.Role):
        """
        Set the moderator role for a specific category.
        """
        category_moderator_roles = await self.config.category_moderator_roles()
        category_moderator_roles[str(category.id)] = role.id
        await self.config.category_moderator_roles.set(category_moderator_roles)
        await ctx.send(f"Moderator role for {category.name} category set to {role.name}.")