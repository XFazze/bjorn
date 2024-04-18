import os
from discord.ext import commands
from discord import Member


class autoPublic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        if member.guild.id == member.guild:
            await member.add_roles(
                member.guild.get_role(int(os.environ["LOADING_PUBLIC_ROLE_ID"]))
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(autoPublic(bot))
