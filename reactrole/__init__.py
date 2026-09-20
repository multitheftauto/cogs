from .reactrole import ReactRole

async def setup(bot):
    await bot.add_cog(ReactRole(bot))
