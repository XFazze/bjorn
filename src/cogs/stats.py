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
        # Check if user has database entries
        self.db.ensure_user_entry(member.id)
        self.db.ensure_guild_entry(member.guild.id)
        self.db.ensure_voice_channel_entry(after.channel.id)
        print("test")

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

        # If the player joined a channel regardless of if they were in a channel
        if after.channel is not None:
            for i in joined_users:
                if int(i[0]) == member.id:
                    break
            else:
                self.db.insert_joined_user(member.id, datetime.now())
                vc_joins += 1

        # If the player left a channel
        if after.channel is None:
            for i in joined_users:
                if int(i[0]) == member.id:
                    vc_leaves += 1
                    vc_time += datetime.now() - i[1]
                    print(vc_time)
                    self.db.remove_joined_user(member.id)
                    break

        # If the player muted themselves
        if after.self_mute:
            for i in muted_users:
                if int(i[0]) == member.id:
                    break
            else:
                self.db.insert_muted_user(member.id, datetime.now())

        # If the player unmuted themselves
        if not after.self_mute:
            for i in muted_users:
                if int(i[0]) == member.id:
                    vc_time_muted += datetime.now() - i[1]
                    self.db.remove_muted_user(member.id)
                    break

        # If the player deafened themselves
        if after.self_deaf:
            for i in deafened_users:
                if int(i[0]) == member.id:
                    break
            else:
                self.db.insert_deafened_user(member.id, datetime.now())

        # If the player undeafened themselves
        if not after.self_deaf:
            for i in deafened_users:
                if int(i[0]) == member.id:
                    vc_time_deafened += datetime.now() - i[1]
                    self.db.remove_deafened_user(member.id)
                    break

        # If the player started streaming
        if after.self_stream:
            for i in streaming_users:
                if int(i[0]) == member.id:
                    break
            else:
                self.db.insert_streaming_user(member.id, datetime.now())

        # If the player stopped streaming
        if not after.self_stream:
            for i in streaming_users:
                if int(i[0]) == member.id:
                    vc_time_streaming += datetime.now() - i[1]
                    self.db.remove_streaming_user(member.id)
                    break

        self.db.update_user(member.id, vc_time=vc_time, vc_joins=vc_joins, vc_leaves=vc_leaves,
                            vc_time_muted=vc_time_muted, vc_time_deafened=vc_time_deafened, vc_time_streaming=vc_time_streaming)
        self.db.update_guild_user(member.guild.id, member.id, vc_time=vc_time, vc_joins=vc_joins, vc_leaves=vc_leaves,
                                  vc_time_muted=vc_time_muted, vc_time_deafened=vc_time_deafened, vc_time_streaming=vc_time_streaming)
        self.db.update_voice_channel_user(member.id, after.channel.id, vc_time=vc_time, vc_joins=vc_joins, vc_leaves=vc_leaves,
                                          vc_time_muted=vc_time_muted, vc_time_deafened=vc_time_deafened, vc_time_streaming=vc_time_streaming)


async def setup(bot):
    await bot.add_cog(Stats(bot))
