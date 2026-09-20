from redbot.core.bot import Red
from .mutes import Mutes


async def setup(bot: Red):
    cog = Mutes(bot)
    await bot.add_cog(cog)
