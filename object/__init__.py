from .object import Object


def setup(bot):
    cog = Object(bot)
    bot.add_cog(cog)
