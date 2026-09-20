from .helper import Helper


async def setup(bot):
    cog = Helper(bot)
    await bot.add_cog(cog)
