import discord
from discord.ext import commands, tasks
from datetime import timedelta, datetime

from lib.stats import Database


class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # check if user has database entries

        vc_time = 0
        vc_joins = 0
        vc_leaves = 0
        vc_time_muted = 0
        vc_time_deafened = 0
        vc_time_streaming = 0

        joined_users = self.db.get_joined_users()
        muted_users = self.db.get_muted_users()
        deafened_users = self.db.get_deafened_users()
        streaming_users = self.db.get_streaming_users()

        if after.channel is None:
            for i in joined_users:
                if i[0] == member.id:
                    vc_leaves = 1
                    vc_time = datetime.now() - i[1]
                    print(vc_time)
                    break

            for i in muted_users:
                if i[0] == member.id:
                    vc_time_muted = i[1]
                    break


async def setup(bot):
    await bot.add_cog(Stats(bot))
