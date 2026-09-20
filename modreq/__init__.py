from .mod import ModReq

async def setup(bot):
    await bot.add_cog(ModReq(bot))
