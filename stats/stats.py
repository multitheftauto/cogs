from redbot.core import commands, checks
from .ase import MTAServerlist

import discord, aiohttp, asyncio, time, re

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
                if not server["version"].endswith("n"):
                    total += server["players"]
            await ctx.channel.send("There are currently "+str(total)+" players online!")

    @stats.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.guild_only()
    async def top(self, ctx):
        """Shows the servers with most players."""
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    ase = MTAServerlist()
                    await ase.parse(await response.read())
            top = sorted(ase.servers, key=lambda k: k['players'], reverse=True)[:10]
            embed = discord.Embed(colour=discord.Colour(0xf5a623), description="Multi Theft Auto Top Servers")
            for v in top:
                if not v["version"].endswith("n"):
                    embed.add_field(name="**"+v["name"]+"**", value=str(v["players"])+"/"+str(v["maxplayers"]), inline=False)
            await ctx.channel.send(embed=embed)

    @stats.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.guild_only()
    async def server(self, ctx, host):
        """Shows the provided server stats."""
        async with ctx.typing():
            host_ip = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", host)
            host_port = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\:(\d+)", host)
            if not host_ip:
                embed = discord.Embed(colour=discord.Colour(0xf5a623), description="**Invalid ip address.**")
                return await ctx.channel.send(embed=embed)
            else:
                host_ip = host_ip[0]
            if not host_port:
                host_port = "22003"
            else:
                host_port = host_port[0]
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    ase = MTAServerlist()
                    await ase.parse(await response.read())
            for v in ase.servers:
                if str(v["ip"]) == str(host_ip) and str(v["port"]) == str(host_port):
                    embed = discord.Embed(colour=discord.Colour(0xf5a623), description="**"+v["name"]+"**\n"+str(v["players"])+"/"+str(v["maxplayers"]))
                    return await ctx.channel.send(embed=embed)
            embed = discord.Embed(colour=discord.Colour(0xf5a623), description="**No result.**")
            return await ctx.channel.send(embed=embed)