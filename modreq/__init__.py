from .mod import ModReq

async def setup(bot):
    bot.add_cog(ModReq(bot))
