from discord.ext import commands
import os


class autoPublic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == int(os.environ["LOADING_ID"]):
            await member.add_roles(
                member.guild.get_role(int(os.environ["LOADING_PUBLIC_ROLE_ID"]))
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(autoPublic(bot))
