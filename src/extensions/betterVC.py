import os
from discord.ext import commands, tasks
from discord.utils import get
from discord import Member, VoiceState, Guild, CategoryChannel
import logging

import lib.permissions as permissions
from lib.config import (
    ConfigDatabase,
    ConfigTables,
    show_channel,
    set_value,
    remove_value,
)

logger = logging.getLogger(__name__)


class betterVC(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("BetterVC extension initialized")

    def cog_unload(self):
        logger.info("Cancelling hideChannels loop on cog unload")
        self.hideChannels.cancel()

    def cog_load(self):
        logger.info("Starting hideChannels loop on cog load")
        self.hideChannels.start()

    @tasks.loop(seconds=60.0)
    async def hideChannels(self):
        try:
            logger.debug("Running hideChannels task loop")
            db = ConfigDatabase(self.bot)
            bettervc_categories = db.get_items(ConfigTables.BETTERVC)
            logger.debug(f"Found {len(bettervc_categories)} bettervc categories")

            for guild_id, category_id in bettervc_categories:
                guild_obj = self.bot.get_guild(int(guild_id))
                category_obj = self.bot.get_channel(int(category_id))

                if not guild_obj:
                    logger.warning(f"Guild {guild_id} not found, skipping")
                    continue

                if not category_obj:
                    logger.warning(
                        f"Category {category_id} not found in guild {guild_id}, skipping"
                    )
                    continue

                logger.debug(
                    f"Processing category {category_obj.name} in guild {guild_obj.name}"
                )
                await self._hide_channels(guild_obj, category_obj)

        except Exception as e:
            logger.error(f"Error in hideChannels task: {e}", exc_info=True)

    async def _hide_channels(self, guild_obj: Guild, category_obj: CategoryChannel):
        try:
            empty_channels = []
            for channel in category_obj.channels:
                if len(channel.members) == 0 and channel.name[0] != "|":
                    empty_channels.append(channel)

            logger.debug(
                f"Found {len(empty_channels)} empty channels in category {category_obj.name}"
            )

            if not empty_channels:
                logger.debug(
                    f"No empty channels to manage in category {category_obj.name}"
                )
                return

            showchannel = empty_channels.pop(0)
            logger.info(
                f"Setting {showchannel.name} as visible in category {category_obj.name}"
            )
            await showchannel.set_permissions(guild_obj.default_role, overwrite=None)

            for hiding_channel in empty_channels:
                logger.debug(
                    f"Hiding channel {hiding_channel.name} in category {category_obj.name}"
                )
                await hiding_channel.set_permissions(
                    guild_obj.default_role, read_messages=False
                )
        except Exception as e:
            logger.error(
                f"Error hiding channels in category {category_obj.name}: {e}",
                exc_info=True,
            )

    @hideChannels.before_loop
    async def before_hidechannels(self):
        logger.info("Waiting for bot to be ready before starting hideChannels loop")
        await self.bot.wait_until_ready()
        logger.info("BetterVC loop enabled")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        try:
            if after.channel is None:
                return

            guild_object = member.guild
            logger.debug(
                f"Voice state update: {member} joined {after.channel.name} in {guild_object.name}"
            )

            db = ConfigDatabase(self.bot)
            bettervc_categories = db.get_items_by(
                ConfigTables.BETTERVC, guild_object.id
            )

            if not bettervc_categories:
                logger.debug(
                    f"No betterVC categories found for guild {guild_object.name}"
                )
                return

            if (
                after.channel.category_id in bettervc_categories
                and len(after.channel.members) == 1
            ):
                logger.info(
                    f"User {member.name} joined empty betterVC channel {after.channel.name}"
                )
                category_object = guild_object.get_channel(after.channel.category_id)

                for empty_channel in category_object.channels:
                    if len(empty_channel.members) == 0 and empty_channel.name[0] != "|":
                        logger.info(
                            f"Making empty channel {empty_channel.name} visible"
                        )
                        await empty_channel.set_permissions(
                            guild_object.default_role, overwrite=None
                        )
                        return

                logger.info(
                    f"Creating new voice channel in category {category_object.name}"
                )
                await category_object.create_voice_channel(
                    "waowie", guild_object.default_role, read_messages=None
                )
        except Exception as e:
            logger.error(f"Error in voice state update handler: {e}", exc_info=True)

    @commands.hybrid_group(description="bettervc manage commands")
    async def bettervc_manage(self, ctx: commands.Context):
        pass

    @bettervc_manage.command(description="Show the bettervc categories for the server.")
    @permissions.admin()
    async def show_category(self, ctx: commands.Context):
        logger.debug(f"Show category command executed by {ctx.author} in {ctx.guild}")
        try:
            await show_channel(self.bot, ctx, ConfigTables.BETTERVC, ctx.guild.id)
            logger.info(f"Displayed betterVC categories for guild {ctx.guild.name}")
        except Exception as e:
            logger.error(f"Error showing betterVC categories: {e}", exc_info=True)
            await ctx.reply(f"An error occurred: {e}")

    @bettervc_manage.command(description="Set a bettervc category for the server.")
    @permissions.admin()
    async def set_category(self, ctx: commands.Context, category_id: int):
        logger.debug(f"Set category command executed by {ctx.author} in {ctx.guild}")
        try:
            category = ctx.guild.get_channel(category_id)
            if not category or not isinstance(category, CategoryChannel):
                logger.warning(f"Invalid category ID provided: {category_id}")
                await ctx.reply(
                    "Invalid category ID. Please provide a valid category ID."
                )
                return

            logger.info(
                f"Setting category {category.name} (ID: {category_id}) as betterVC category in {ctx.guild.name}"
            )
            await set_value(
                self.bot, ctx, ConfigTables.BETTERVC, ctx.guild.id, category_id
            )
        except Exception as e:
            logger.error(f"Error setting betterVC category: {e}", exc_info=True)
            await ctx.reply(f"An error occurred: {e}")

    @bettervc_manage.command(description="Remove a bettervc category for the server.")
    @permissions.admin()
    async def remove_category(self, ctx: commands.Context, category_id: int):
        logger.debug(f"Remove category command executed by {ctx.author} in {ctx.guild}")
        try:
            logger.info(
                f"Removing category ID {category_id} from betterVC in {ctx.guild.name}"
            )
            await remove_value(
                self.bot, ctx, ConfigTables.BETTERVC, ctx.guild.id, category_id
            )
        except Exception as e:
            logger.error(f"Error removing betterVC category: {e}", exc_info=True)
            await ctx.reply(f"An error occurred: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(betterVC(bot))
    logger.info("BetterVC cog loaded successfully")
