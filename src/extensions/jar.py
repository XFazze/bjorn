from discord.ext import commands
import discord
import time
import lib.persmissions as permissions
from lib.config import ConfigTables, show_roles, set_value, remove_value
from discord import Role
from lib.jar import Database


class jar(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database(bot, "jar.sqlite")

    @commands.hybrid_group(name="jar", description="A pot of money for the server")
    async def jar(self, ctx: commands.Context):
        pass

    @jar.command(
        name="pot",
        description="Says how much in total there is in the pot",
    )
    async def pot(self, ctx: commands.Context):
        pot = self.db.pot_value()
        total = 0
        for value in pot:
            total += int(value[0])
        await ctx.reply(
            embed=discord.Embed(title=f"The total pot right now is {total}kr")
        )

    @jar.command(
        name="contributions_from",
        description="Shows how much a certain person has flamed",
    )
    async def contributions_from(
        self, ctx: commands.Context, user: discord.Member | None = None
    ):
        if user is None:
            user = ctx.message.author
        flamed = self.db.contributions_from(user.id)
        await ctx.reply(
            embed=discord.Embed(title=f"The person needs to pay {flamed}kr")
        )

    @jar.command(
        name="add_to_jar",
        description="Adds so that specifik person flamed",
    )
    @permissions.jar()
    async def add_to_jar(
        self, ctx: commands.Context, user: discord.Member | None = None
    ):
        if user is None:
            user = ctx.message.author.id
        if ctx.author.id == user.id:
            flamed = self.db.add_to_jar(user.id)
            await ctx.reply(
                embed=discord.Embed(title=f"{user.name} has contributed to the pot")
            )
        else:
            await ctx.reply(
                embed=discord.Embed(title=f"U don't have permission for this")
            )

    @jar.command(description="Show the Jar role for the server.")
    @permissions.admin()
    async def show_roles(self, ctx: commands.Context):
        await show_roles(self.bot, ctx, ConfigTables.JARPERMISSIONS, ctx.guild.id)

    @jar.command(description="Set a Jar role for the server.")
    @permissions.admin()
    async def set_role(self, ctx: commands.Context, role: Role):
        await set_value(
            self.bot, ctx, ConfigTables.JARPERMISSIONS, ctx.guild.id, role.id
        )

    @jar.command(description="Remove a Jar role for the server.")
    @permissions.admin()
    async def remove_role(self, ctx: commands.Context, role: Role):
        await remove_value(
            self.bot, ctx, ConfigTables.JARPERMISSIONS, ctx.guild.id, role.id
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(jar(bot))
