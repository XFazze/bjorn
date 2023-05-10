import discord
from discord.ext import commands, tasks

from lib.stats import Database


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("data/stats.db")

    @tasks.loop(hours=24)
    async def daily(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            for member in guild.members:
                # self.db.insert_daily_user(member.id, guild.id...)
                pass
