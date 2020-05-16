from redbot.core import commands, checks
from .ase import MTAServerlist

import aiohttp, asyncio, time

class Stats(commands.Cog):
    """My custom cog"""
    def __init__(self):
        self.url = 'https://master.multitheftauto.com/ase/mta/'

    @commands.group()
    async def stats(self, ctx):
        """MTA:SA Stats!"""
        pass

    @stats.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.guild_only()
    async def online(self, ctx):
        """Shows MTA's online players count"""
        async with ctx.typing():
            total = 0
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    ase = MTAServerlist()
                    await ase.parse(await response.read())

            for server in ase.servers:
                total += server["players"]
            await ctx.channel.send("There are currently "+str(total)+" players online!")

    @stats.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.guild_only()
    async def top(self, ctx):
        """Shows the servers with most players."""
        async with ctx.typing():
            top = ""
            peak = 0
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    ase = MTAServerlist()
                    await ase.parse(await response.read())
            for server in ase.servers:
                if peak < server.playersCount:
                    peak = server["players"]
                    top = server["name"]
            await ctx.channel.send("`"+top+"` with "+str(peak)+" players!")
