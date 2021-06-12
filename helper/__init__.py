from .helper import Helper


def setup(bot):
    cog = Helper(bot)
    bot.add_cog(cog)
