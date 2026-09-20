from .wiki import wiki

async def setup(bot):
    cog = wiki(bot)
    await bot.add_cog(cog)