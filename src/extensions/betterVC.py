import os
from discord.ext import commands, tasks
from discord.utils import get
from discord import Member, VoiceState, Guild, CategoryChannel

import lib.permissions as permissions
from lib.config import (
    ConfigDatabase,
    ConfigTables,
    show_channel,
    set_value,
    remove_value,
)


class betterVC(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def cog_unload(self):
        self.hideChannels.cancel()

    def cog_load(self):
        self.hideChannels.start()

    @tasks.loop(seconds=60.0)
    async def hideChannels(self):
        try:
            db = ConfigDatabase(self.bot)
            bettervc_categories = db.get_items(ConfigTables.BETTERVC)
            for guild_id, category_id in bettervc_categories:
                guild_obj = self.bot.get_guild(int(guild_id))
                category_obj = self.bot.get_channel(int(category_id))

                await self._hide_channels(guild_obj, category_obj)

        except Exception as e:
            print("hidechannel error: ", e)
            pass

    async def _hide_channels(Self, guild_obj: Guild, category_obj: CategoryChannel):
        empty_channels = []
        for channel in category_obj.channels:
            if len(channel.members) == 0 and channel.name[0] != "|":
                empty_channels.append(channel)

        showchannel = empty_channels.pop(0)
        await showchannel.set_permissions(guild_obj.default_role, overwrite=None)

        for hiding_channel in empty_channels:
            await hiding_channel.set_permissions(
                guild_obj.default_role, read_messages=False
            )

    @hideChannels.before_loop
    async def before_hidechannels(self):
        print("Bettervc loop enabled")
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        if after.channel is None:
            return

        guild_object = member.guild

        db = ConfigDatabase(self.bot)
        bettervc_categories = db.get_items_by(ConfigTables.BETTERVC, guild_object.id)

        if (
            after.channel.category_id in bettervc_categories
            and len(after.channel.members) == 1
        ):
            category_object = guild_object.get_channel(after.channel.category_id)

            for empty_channel in category_object.channels:
                if len(empty_channel.members) == 0 and empty_channel.name[0] != "|":
                    await empty_channel.set_permissions(
                        guild_object.default_role, overwrite=None
                    )
                    return
            await category_object.create_voice_channel(
                "waowie", guild_object.default_role, read_messages=None
            )

    @commands.hybrid_group(description="bettervc manage commands")
    async def bettervc_manage(self, ctx: commands.Context):
        pass

    @bettervc_manage.command(description="Show the bettervc categories for the server.")
    @permissions.admin()
    async def show_category(self, ctx: commands.Context):
        await show_channel(self.bot, ctx, ConfigTables.BETTERVC, ctx.guild.id)

    @bettervc_manage.command(description="Set a bettervc category for the server.")
    @permissions.admin()
    async def set_category(self, ctx: commands.Context, category_id: int):
        await set_value(self.bot, ctx, ConfigTables.BETTERVC, ctx.guild.id, category_id)

    @bettervc_manage.command(description="Remove a bettervc category for the server.")
    @permissions.admin()
    async def remove_category(self, ctx: commands.Context, category_id: int):
        await remove_value(
            self.bot, ctx, ConfigTables.BETTERVC, ctx.guild.id, category_id
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(betterVC(bot))
