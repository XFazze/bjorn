import os
from discord.ext import commands, tasks
from discord.utils import get


class betterVC(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.hideChannels.start()

    def cog_unload(self):
        self.hideChannels.cancel()

    @tasks.loop(seconds=60.0)
    async def hideChannels(self):
        try:
            guild_object = self.bot.get_guild(int(os.environ["LOADING_ID"]))
            category_object = get(
                self.bot.get_all_channels(), id=int(os.environ["BETTERVC_CATEGORY_ID"])
            )

            empty_channels = []
            for channel in category_object.channels:
                if len(channel.members) == 0 and channel.name[0] != "|":
                    empty_channels.append(channel)

            showchannel = empty_channels.pop(0)
            await showchannel.set_permissions(guild_object.default_role, overwrite=None)

            for hiding_channel in empty_channels:
                await hiding_channel.set_permissions(
                    guild_object.default_role, read_messages=False
                )
        except Exception as e:
            print("hidechannel error: ", e)
            pass

    @hideChannels.before_loop
    async def before_hidechannels(self):
        print("Bettervc enabled")
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel is None:
            return
        guild_object = self.bot.get_guild(int(os.environ["LOADING_ID"]))
        if (
            after.channel.category_id == int(os.environ["BETTERVC_CATEGORY_ID"])
            and len(after.channel.members) == 1
        ):
            category_object = get(
                self.bot.get_all_channels(), id=after.channel.category_id
            )

            for empty_channel in category_object.channels:
                if len(empty_channel.members) == 0 and empty_channel.name[0] != "|":
                    # print("on_voice_state_update found empty channel(row 101)")
                    await empty_channel.set_permissions(
                        guild_object.default_role, overwrite=None
                    )
                    return
            await category_object.create_voice_channel(
                "waowie", guild_object.default_role, read_messages=None
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(betterVC(bot))
