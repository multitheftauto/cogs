from .botmention import BotMention


async def setup(bot):
    cog = BotMention(bot)
    await bot.add_cog(cog)
    cog.init()