import os
import discord
from discord.ext import commands
from discord import Role
#import sqlite3
#import logging
#logger = logging.getLogger(__name__)
import lib.persmissions as permissions
from lib.config import ConfigTables, show_roles, set_value, remove_value


class dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        print("error made", err)
        if isinstance(err, commands.CommandOnCooldown):
            await ctx.send(
                f":stopwatch: Command is on Cooldown for **{err.retry_after:.2f}** seconds."
            )
            " Missing Permissions "
        elif isinstance(err, commands.MissingPermissions):
            await ctx.send(f":x: You can't use that command.")
            " Missing Arguments "
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f":x: Required arguments aren't passed.")
            " Command not found "
        elif isinstance(err, commands.CommandNotFound):
            pass
            " Any Other Error "

    @commands.hybrid_command(
        name="sync", description="Syncs the discord slash commands"
    )
    @permissions.admin()
    async def sync(self, ctx: commands.Context):
        await self.bot.tree.sync()
        await ctx.reply(embed=discord.Embed(title=f"Synced!", color=0x00FF42))

    @commands.hybrid_command(name="devchannel", description="Creates a dev channel")
    @permissions.admin()
    async def devchannel(self, ctx: commands.Context):
        assert ctx.guild is not None
        category_search = [
            category
            for category in ctx.guild.categories
            if category.name == os.environ["DEV_TEST_CATEGORY_NAME"]
        ]
        if len(category_search) == 0:
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
        assert type(ctx.author) is discord.Member
        channel = await ctx.guild.create_text_channel(
            os.environ["DEV_TEST_CHANNEL_NAME"] + str(len(category.text_channels)),
            overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False
                ),
                ctx.author: discord.PermissionOverwrite(read_messages=True),
            },
            category=category,
        )
        await channel.send(
            embed=discord.Embed(title=f"Created dev channel!", color=0x00FF42)
        )

    @commands.hybrid_group(description="admin manage commands")
    async def adminmanage(self, ctx: commands.Context):
        pass

    @adminmanage.command(description="Show the admin roles for the server.")
    @permissions.admin()
    async def show_roles(self, ctx: commands.Context):
        await show_roles(self.bot, ctx, ConfigTables.ADMIN, ctx.guild.id)

    @adminmanage.command(description="Set a admin role for the server.")
    @permissions.admin()
    async def set_role(self, ctx: commands.Context, role: Role):
        await set_value(self.bot, ctx, ConfigTables.ADMIN, ctx.guild.id, role.id)

    @adminmanage.command(description="Remove a admin role for the server.")
    @permissions.admin()
    async def remove_role(self, ctx: commands.Context, role: Role):
        await remove_value(self.bot, ctx, ConfigTables.ADMIN, ctx.guild.id, role.id)

    #@commands.command()
    #async def add_player_names(self, ctx):
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
