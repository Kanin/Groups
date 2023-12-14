from .groups import Groups


async def setup(bot):
    await bot.add_cog(Groups(bot))
