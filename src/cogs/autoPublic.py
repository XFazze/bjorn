from discord.ext import commands
import os


class autoPublic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == int(os.getenv("LOADING_ID")):
            await member.add_roles(member.guild.get_role(int(os.getenv("LOADING_PUBLIC_ROLE_ID"))))


async def setup(bot):
    await bot.add_cog(autoPublic(bot))
