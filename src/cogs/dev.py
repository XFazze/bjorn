from discord.ext import commands
import discord
import sqlite3


class dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self,ctx, err ):
        print("error made", err)
        if isinstance(err, commands.CommandOnCooldown):
            await ctx.send(f":stopwatch: Command is on Cooldown for **{err.retry_after:.2f}** seconds.")
            ' Missing Permissions '
        elif isinstance(err, commands.MissingPermissions):
            await ctx.send(f":x: You can't use that command.")
            ' Missing Arguments '
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f":x: Required arguments aren't passed.")
            ' Command not found '
        elif isinstance(err, commands.CommandNotFound):
            pass
            ' Any Other Error '


async def setup(bot):
    await bot.add_cog(dev(bot))
