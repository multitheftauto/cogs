from .botmention import BotMention


def setup(bot):
    cog = BotMention(bot)
    bot.add_cog(cog)
    cog.init()