import discord
from redbot.core import Config, checks, commands
import aiohttp
from bs4 import BeautifulSoup

class Object(commands.Cog):
    """Object cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=707350954969792584)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.url = "https://dev.prineside.com/en/gtasa_samp_model_id/model/"
        self.image = "https://files.prineside.com/gtasa_samp_model_id/white/{}_w.jpg"

    @commands.command()
    async def object(self, ctx, id: int):
        """Get the object info"""
        # If not allowed channel return
        channels = await self.config.guild(ctx.guild).channels()
        if ctx.channel.id not in channels:
            return
        async with ctx.typing():
            # Get object info from webpage
            url = self.url + str(id)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.text()
            
            match = "[{}] - object of SA-MP and GTA San Andreas".format(id)
            # check if object exists
            if match not in data:
                return await ctx.send("Object not found")

            # scrape data
            soup = BeautifulSoup(data, "html.parser")
            # find the table by id "mp-model-info"
            table = soup.find("table", {"id": "mp-model-info"})
            # get first 8 rows
            rows = table.findAll("tr")[:8]
            # add embed
            embed = discord.Embed()
            # loop through rows
            for row in rows:
                # find children td
                cols = row.findAll("td")
                # get text
                index = cols[0].text.strip()
                # if next is input get value
                if cols[1].find("input"):
                    value = cols[1].find("input").get("value")
                else:
                    value = cols[1].text.strip()
                # add to embed
                embed.add_field(name=index, value=value, inline=True)
            
            # get image
            image = self.image.format(id)
            embed.set_image(url=image)
            embed.set_footer(text="Requested by: " + ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @checks.admin_or_permissions(manage_roles=True)
    @commands.group()
    async def objectset(self, ctx):
        pass

    @objectset.command()
    async def channel(self, ctx):
        channels = await self.config.guild(ctx.guild).channels()
        if ctx.channel.id in channels:
            channels.remove(ctx.channel.id)
            await self.config.guild(ctx.guild).channels.set(channels)
            await ctx.channel.send("Object command is no longer allowed in this channel.")
        else:
            channels.append(ctx.channel.id)
            await self.config.guild(ctx.guild).channels.set(channels)
            await ctx.channel.send("Object command is now allowed in this channel.")