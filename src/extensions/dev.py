import os
import discord
from discord.ext import commands
from discord import Role
import logging

import lib.permissions as permissions
from lib.config import ConfigTables, show_roles, set_value, remove_value


logger = logging.getLogger(__name__)


class dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("Dev extension initialized")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        logger.error(f"Command error: {err}", exc_info=True)
        if isinstance(err, commands.CommandOnCooldown):
            await ctx.send(
                f":stopwatch: Command is on Cooldown for **{err.retry_after:.2f}** seconds."
            )
            logger.debug(
                f"Command on cooldown: {ctx.command} for {err.retry_after:.2f} seconds"
            )
            " Missing Permissions "
        elif isinstance(err, commands.MissingPermissions):
            await ctx.send(f":x: You can't use that command.")
            logger.debug(
                f"Missing permissions: {ctx.author} tried to use {ctx.command}"
            )
            " Missing Arguments "
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f":x: Required arguments aren't passed.")
            logger.debug(f"Missing required argument for {ctx.command}: {err.param}")
            " Command not found "
        elif isinstance(err, commands.CommandNotFound):
            logger.debug(f"Command not found: {ctx.message.content}")
            pass
            " Any Other Error "
        else:
            logger.warning(f"Unhandled command error: {type(err).__name__}: {err}")

    @commands.hybrid_command(
        name="sync", description="Syncs the discord slash commands"
    )
    @permissions.admin()
    async def sync(self, ctx: commands.Context):
        logger.info(f"Syncing commands initiated by {ctx.author} in {ctx.guild}")
        await self.bot.tree.sync()
        logger.info("Command tree sync completed successfully")
        await ctx.reply(embed=discord.Embed(title=f"Synced!", color=0x00FF42))

    @commands.hybrid_command(name="devchannel", description="Creates a dev channel")
    @permissions.admin()
    async def devchannel(self, ctx: commands.Context):
        logger.info(f"Dev channel creation requested by {ctx.author} in {ctx.guild}")
        assert ctx.guild is not None
        category_search = [
            category
            for category in ctx.guild.categories
            if category.name == os.environ["DEV_TEST_CATEGORY_NAME"]
        ]
        if len(category_search) == 0:
            logger.debug(
                f"Creating new dev category: {os.environ['DEV_TEST_CATEGORY_NAME']}"
            )
            category = await ctx.guild.create_category(
                os.environ["DEV_TEST_CATEGORY_NAME"],
                overwrites={
                    ctx.guild.default_role: discord.PermissionOverwrite(
                        read_messages=False
                    )
                },
            )
        else:
            category = category_search[0]
            logger.debug(f"Using existing dev category: {category.name}")
        assert type(ctx.author) is discord.Member

        channel_name = os.environ["DEV_TEST_CHANNEL_NAME"] + str(
            len(category.text_channels)
        )
        logger.debug(f"Creating dev channel: {channel_name}")
        channel = await ctx.guild.create_text_channel(
            channel_name,
            overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False
                ),
                ctx.author: discord.PermissionOverwrite(read_messages=True),
            },
            category=category,
        )
        logger.info(f"Dev channel created: {channel.name} (ID: {channel.id})")
        await channel.send(
            embed=discord.Embed(title=f"Created dev channel!", color=0x00FF42)
        )

    @commands.hybrid_group(description="admin manage commands")
    async def adminmanage(self, ctx: commands.Context):
        pass

    @adminmanage.command(description="Show the admin roles for the server.")
    @permissions.admin()
    async def show_roles(self, ctx: commands.Context):
        logger.debug(f"Showing admin roles for guild {ctx.guild.id}")
        await show_roles(self.bot, ctx, ConfigTables.ADMIN, ctx.guild.id)

    @adminmanage.command(description="Set a admin role for the server.")
    @permissions.admin()
    async def set_role(self, ctx: commands.Context, role: Role):
        logger.info(
            f"Setting admin role {role.name} (ID: {role.id}) in guild {ctx.guild.id}"
        )
        await set_value(self.bot, ctx, ConfigTables.ADMIN, ctx.guild.id, role.id)

    @adminmanage.command(description="Remove a admin role for the server.")
    @permissions.admin()
    async def remove_role(self, ctx: commands.Context, role: Role):
        logger.info(
            f"Removing admin role {role.name} (ID: {role.id}) in guild {ctx.guild.id}"
        )
        await remove_value(self.bot, ctx, ConfigTables.ADMIN, ctx.guild.id, role.id)

    # @commands.command()
    # async def add_player_names(self, ctx):
    #    conn = sqlite3.connect("data/league.sqlite")
    #    cursor = conn.cursor()

    #    cursor.execute("SELECT discord_id FROM player")
    #    players = cursor.fetchall()
    #    for player in players:

    #        user = self.bot.get_user(player[0])
    #        logger.warning(player[0])
    #        if user is None:
    #            name = "Unknown"
    #        else:
    #            name = user.name
    #        logger.warning(name)

    #        cursor.execute(
    #            "UPDATE player SET discord_name = ? WHERE discord_id = ? ",
    #            (name, player[0])
    #        )
    #        conn.commit()
    #    cursor.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(dev(bot))
    logger.info("Dev cog loaded successfully")
