from .spam import spam

async def setup(bot):
    cog = spam(bot)
    await bot.add_cog(cog)