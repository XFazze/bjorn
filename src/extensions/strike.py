from discord.ext import commands
import discord
import time
import lib.persmissions as permissions
from lib.config import ConfigTables, show_roles, set_value, remove_value
from discord import Role
from lib.strike import Database

warnings_before_strike = 2


class strike(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database(bot, "strike.sqlite")

    @commands.hybrid_group(
        name="strike",
        description="Gives people in a server a chance before kicking/baning them",
    )
    async def strike(self, ctx: commands.Context):
        pass

    @strike.command(
        name="how_many_warnings",
        description="Shows how many warnings a specifik person has gotten",
    )
    @permissions.strike()
    async def contributions_from(
        self, ctx: commands.Context, user: discord.Member | None = None
    ):
        if user is None:
            user = ctx.message.author
        warnings = self.db.contributions_from(user.id)
        await ctx.reply(
            embed=discord.Embed(title=f"The person has gotten {warnings} warnings")
        )

    @strike.command(
        name="add_warning",
        description="Adds a warning to a specifik person",
    )
    @permissions.strike()
    async def add_to_jar(self, ctx: commands.Context, user: discord.Member):
        if ctx.author.id == user.id:
            await ctx.reply(
                embed=discord.Embed(title=f"You can't give yourself a warning")
            )
        else:
            warning = self.db.add_to_jar(user.id)
            await ctx.reply(
                embed=discord.Embed(title=f"{user.name} has gotten a warning")
            )
        if warning > warnings_before_strike:
            await ctx.reply(
                embed=discord.Embed(title=f"{user.name} has {warning} warnings!!!")
            )

    @strike.command(description="Show the Warning role for the server.")
    @permissions.admin()
    async def show_roles(self, ctx: commands.Context):
        await show_roles(self.bot, ctx, ConfigTables.STRIKEPERMISSIONS, ctx.guild.id)

    @strike.command(description="Set a Warning role for the server.")
    @permissions.admin()
    async def set_role(self, ctx: commands.Context, role: Role):
        await set_value(
            self.bot, ctx, ConfigTables.STRIKEPERMISSIONS, ctx.guild.id, role.id
        )

    @strike.command(description="Remove a Warning role for the server.")
    @permissions.admin()
    async def remove_role(self, ctx: commands.Context, role: Role):
        await remove_value(
            self.bot, ctx, ConfigTables.STRIKEPERMISSIONS, ctx.guild.id, role.id
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(strike(bot))
