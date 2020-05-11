from .wiki import wiki

def setup(bot):
    cog = wiki(bot)
    bot.add_cog(cog)