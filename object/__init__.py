from .object import Object


async def setup(bot):
    cog = Object(bot)
    await bot.add_cog(cog)
