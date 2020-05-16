from redbot.core import commands, checks
from .ase import fetch_data

class Stats(commands.Cog):
    """My custom cog"""

    @commands.group()
    async def stats(self, ctx):
        """MTA:SA Stats!"""
        pass
    @stats.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def online(self, ctx):
        """Shows MTA's online players count"""
        total = 0
        servers = fetch_data()
        for server in servers:
            total += server.playersCount
        await ctx.channel.send("There are currently "+str(total)+" online!")
