import discord
from redbot.core import commands, checks, data_manager
from redbot.core.config import Config
from redbot.core.utils import mod

import aiohttp, asyncio
from bs4 import BeautifulSoup
import re
import json


class wiki(commands.Cog):
    """ MTA:SA Wiki Cog """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self,
            identifier=1001,
            force_registration=True,
        )
        self.url = "https://wiki.multitheftauto.com/wiki/"

        default_guild = {
            "channels": []
        }

        self.config.register_guild(**default_guild)

        with open(data_manager.bundled_data_path(self) / "list.json", "r") as f:
            self.list = json.load(f)

        self.junk = [
            "[[{{{image}}}|link=]]"
        ]

        self.types = [
            "Server-only function",
            "Server-side function",
            "Server-side event",
            "Client-only function",
            "Client-side function",
            "Client-side event",
            "Shared function",
            "Useful Function"
        ]


    def sanitize(self, string):
        for v in self.junk:
            string = string.replace(v, "")
        return string

    async def fetch(self, ctx, target, part):
        # async with ctx.typing():
        async with aiohttp.ClientSession() as session:
            target = target[0].upper() + target[1:]
            async with session.get(self.url+target) as response:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                data_type = soup.find('meta', attrs={'name': 'headingclass'})
                if data_type:
                    for v in self.types:
                        if v == data_type["data-subcaption"]:
                            return await self.respond(ctx, target, part, soup, data_type["data-subcaption"])

                    return await ctx.channel.send("No result!")
                else:
                    return await ctx.channel.send("No result!")

    def parse(self, obj):
        result = []
        if obj:
            for v in obj:
                result.append(v.text)
            return self.sanitize("\n".join(result))

    async def respond(self, ctx, target, part, soup, data):
        if data in ["Server-only function", "Server-side function", "Client-only function", "Client-side function", "Shared function", "Useful Function"]:
            body = list(soup.find(class_="mw-parser-output").findChildren(recursive=False))
            hits = {}

            hits["description"] = []

            result = soup.find(class_="mw-headline", id="Syntax")
            if result:
                hits["syntax"] = result.parent.find_next_siblings()


            result = soup.find('a', attrs={'title': 'OOP Introduction'})
            if result:
                hits["oop"] = result.parent.parent.find_next_siblings()

            result = soup.find(class_="mw-headline", id="Required_Arguments")
            if result:
                hits["rArgs"] = result.parent.find_next_siblings()

            result = soup.find(class_="mw-headline", id="Optional_Arguments")
            if result:
                hits["oArgs"] = result.parent.find_next_siblings()

            result = soup.find(class_="mw-headline", id="Returns")
            if result:
                hits["returns"] = result.parent.find_next_siblings()

            result = soup.find(class_="mw-headline", id="Issues")
            if result:
                hits["issues"] = result.parent.find_next_siblings()

            result = soup.find(class_="mw-headline", id="Example")
            if result:
                hits["example"] = result.parent.find_next_siblings()

            result = soup.find(class_="mw-headline", id="Changelog")
            if result:
                hits["changelog"] = result.parent.find_next_siblings()

            result = soup.find(class_="mw-headline", id="See_Also")
            if result:
                hits["seealso"] = result.parent.find_next_siblings()

            hits["footer"] = soup.find(class_="printfooter").find_next_siblings()

        elif data in ["Server-side event", "Client-side event"]:
            body = list(soup.find(class_="mw-parser-output").findChildren(recursive=False))
            hits = {}

            hits["description"] = []

            result = soup.find(class_="mw-headline", id="Parameters")
            if result:
                hits["parameters"] = result.parent.find_next_siblings()

            result = soup.find(class_="mw-headline", id="Source")
            if result:
                hits["source"] = result.parent.find_next_siblings()

            result = soup.find(class_="mw-headline", id="Cancel_effect")
            if result:
                hits["cancel"] = result.parent.find_next_siblings()

            result = soup.find(class_="mw-headline", id="Issues")
            if result:
                hits["issues"] = result.parent.find_next_siblings()

            result = soup.find(class_="mw-headline", id="Example")
            if result:
                hits["example"] = result.parent.find_next_siblings()

            result = soup.find(class_="mw-headline", id="Changelog")
            if result:
                hits["changelog"] = result.parent.find_next_siblings()

            result = soup.find(class_="mw-headline", id="See_Also")
            if result:
                hits["seealso"] = result.parent.find_next_siblings()

            hits["footer"] = soup.find(class_="printfooter").find_next_siblings()

        result = {}
        for i, v in hits.items():
            if v:
                count = len(body) - len(v) - 1
                result[p] = self.parse(body[:count])
                body = body[count+1:]
            p = i

        if result:
            if data == "Client-side event":
                name = "Client Event"
                colour = discord.Colour(0xff0000)
                title_url = "https://wiki.multitheftauto.com/wiki/Client_Scripting_Events"
                r_type = "event"
            elif data == "Server-side event":
                name = "Server Event"
                colour = discord.Colour(0xe67e22)
                title_url = "https://wiki.multitheftauto.com/wiki/Server_Scripting_Events"
                r_type = "event"
            elif data == "Client-only function" or data == "Client-side function":
                name = "Client Function"
                colour = discord.Colour(0xff0000)
                title_url = "https://wiki.multitheftauto.com/wiki/Client_Scripting_Functions"
                r_type = "function"
            elif data == "Server-only function" or data == "Server-side function":
                name = "Server Function"
                colour = discord.Colour(0xe67e22)
                title_url = "https://wiki.multitheftauto.com/wiki/Server_Scripting_Functions"
                r_type = "function"
            elif data == "Shared function":
                name = "Shared Function"
                colour = discord.Colour(0x3498db)
                title_url = "https://wiki.multitheftauto.com/wiki/Shared_Scripting_Functions"
                r_type = "function"
            elif data == "Useful Function":
                name = "Useful Function"
                colour = discord.Colour(0x2ecc71)
                title_url = "https://wiki.multitheftauto.com/wiki/Useful_Functions"
                r_type = "function"
            
            embed = discord.Embed(title=target, colour=colour, url=self.url+target)
            embed.set_author(name=name, url=title_url)
            embed.set_footer(text="@"+ctx.author.name+"#"+ctx.author.discriminator, icon_url=ctx.author.avatar_url)

            if part in ["description", "syntax", "example", "source", "parameters", "returns", "oArgs", "rArgs", "changelog", "seealso", "oop", "cancel"]:
                part_name = part[0].upper() + part[1:]
                embed.add_field(name=part_name, value=result[part], inline=False)
            else:
                if r_type == "function":
                    # embed.add_field(name="Description", value=result["description"], inline=False)
                    embed.add_field(name="Syntax", value=result["syntax"], inline=False)
                else:
                    embed.add_field(name="Parameters", value=result["parameters"], inline=False)
                    embed.add_field(name="Source", value=result["source"], inline=False)

            await ctx.channel.send(embed=embed)


    def intersection(self, lst1, lst2):
        return list(set(lst1) & set(lst2))

    @commands.command()
    async def wiki(self, ctx, target, part=None):
        if target == "allow":
            if not await ctx.bot.is_mod(ctx.author):
                return
            channels = await self.config.guild(ctx.guild).channels()
            if ctx.channel.id in channels:
                return await ctx.channel.send("Wiki is already allowed in this channel.")
            channels.append(ctx.channel.id)
            await self.config.guild(ctx.guild).channels.set(channels)
            await ctx.channel.send("Wiki is now allowed in this channel.")
        elif target == "deny":
            if not await ctx.bot.is_mod(ctx.author):
                return
            channels = await self.config.guild(ctx.guild).channels()
            if ctx.channel.id not in channels:
                return await ctx.channel.send("Wiki is not allowed in here already.")
            channels.remove(ctx.channel.id)
            await self.config.guild(ctx.guild).channels.set(channels)
            await ctx.channel.send("Wiki is no longer available in this channel.")
        elif ctx.channel.id in await self.config.guild(ctx.guild).channels():
            await self.fetch(ctx, target, part)
        else:
            await ctx.channel.send("Wiki command is not allowed in this channel.")

    @commands.Cog.listener()
    async def on_message_without_command(self, ctx):
        if ctx.author.bot:
            return
        guild = ctx.guild
        if guild is None:
            return
        channels = await self.config.guild(ctx.guild).channels()
        if ctx.channel.id not in channels:
            return

        ticks = re.findall(r'\`\`(.*?)\`\`', ctx.content)

        while("" in ticks):
            ticks.remove("")

        if ticks:
            matches = self.intersection(ticks, self.list)
            if matches:
                for v in matches:
                    await self.fetch(ctx, v, None)
