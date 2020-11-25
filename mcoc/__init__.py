from redbot.core.bot import Red
from .mcoc import Mcoc

__red_end_user_data_statement__ = (
    "This cog does not persistently store data or metadata about users."
)


def setup(bot: Red):
    cog = Mcoc(bot)
    bot.add_cog(cog)
