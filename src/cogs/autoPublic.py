from datetime import timedelta, datetime
from discord.ext import commands
import discord
import typing


class autoPublic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != 802298523214938153:
            return
        await member.add_roles(member.guild.get_role(802305915491319838))


async def setup(bot):
    await bot.add_cog(autoPublic(bot))
