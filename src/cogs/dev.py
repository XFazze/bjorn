import os
from discord.ext import commands
import discord

import src.lib.persmissions as permissions


class dev(commands.Cog):
    def __init__(self, bot):
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
        category_search = [
            category
            for category in ctx.guild.categories
            if category.name == os.getenv("DEV_TEST_CATEGORY_NAME")
        ]
        if len(category_search) == 0:
            category = await ctx.guild.create_category(
                os.getenv("DEV_TEST_CATEGORY_NAME"),
                overwrites={
                    ctx.guild.default_role: discord.PermissionOverwrite(
                        read_messages=False
                    )
                },
            )
        else:
            category = category_search[0]
        channel = await ctx.guild.create_text_channel(
            os.getenv("DEV_TEST_CHANNEL_NAME") + str(len(category.text_channels)),
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


async def setup(bot):
    await bot.add_cog(dev(bot))
