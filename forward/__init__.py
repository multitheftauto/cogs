from .forward import Forward


async def setup(bot):
    n = Forward(bot)
    await bot.add_cog(n)
