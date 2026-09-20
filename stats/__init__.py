from .stats import Stats

async def setup(bot):
    await bot.add_cog(Stats())
