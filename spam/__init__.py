from .spam import spam

def setup(bot):
    cog = spam(bot)
    bot.add_cog(cog)