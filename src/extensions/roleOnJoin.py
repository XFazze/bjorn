from discord.ext import commands
from discord import Member, Role

from lib.config import (
    ConfigDatabase,
    ConfigTables,
    show_values,
    set_value,
    remove_value,
    remove_all_values,
)


class role_on_join(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        db = ConfigDatabase(self.bot)
        roles = db.get_items_by(ConfigTables.ROLEONJOIN, member.guild.id)
        if roles is None:
            return  # No roleonjoin for this server
        for role in roles:
            role_obj = member.guild.get_role(int(role[1]))
            await member.add_roles(role_obj)

    @commands.hybrid_group(description="roleonjoin commands")
    async def roleonjoin(self, ctx: commands.Context):
        pass

    @roleonjoin.command(description="Show all roleOnJoin roles for the server.")
    async def show_roles(self, ctx: commands.Context):
        await show_values(self.bot, ctx, ConfigTables.ROLEONJOIN, ctx.guild.id)

    @roleonjoin.command(description="Set a roleOnJoin role for the server.")
    async def set_role(self, ctx: commands.Context, role: Role):
        await set_value(self.bot, ctx, ConfigTables.ROLEONJOIN, ctx.guild.id, role.id)

    @roleonjoin.command(description="Remove a roleOnJoin role for the server.")
    async def remove_role(self, ctx: commands.Context, role: Role):
        await remove_value(
            self.bot, ctx, ConfigTables.ROLEONJOIN, ctx.guild.id, role.id
        )

    @roleonjoin.command(description="Remove all roleOnJoin roles for the server.")
    async def remove_all_roles(self, ctx: commands.Context):
        await remove_all_values(self.bot, ctx, ConfigTables.ROLEONJOIN, ctx.guild.id)


async def setup(bot: commands.Bot):
    await bot.add_cog(role_on_join(bot))
