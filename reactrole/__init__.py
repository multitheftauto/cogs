from .reactrole import ReactRole

async def setup(bot):
    bot.add_cog(ReactRole(bot))
