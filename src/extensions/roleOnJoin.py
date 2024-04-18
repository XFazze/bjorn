from discord.ext import commands
from discord import Member, app_commands, Role, Embed
from lib.general import ConfigDatabase, ConfigTables


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
            await member.add_roles(member.guild.get_role(int(role[1])))

    @commands.hybrid_group(description="roleonjoin commands")
    async def roleonjoin(self, ctx: commands.Context):
        pass

    @roleonjoin.command(description="Set a roleOnJoin role for the server.")
    async def show_roles(self, ctx: commands.Context):
        db = ConfigDatabase(self.bot)
        roles = db.get_items_by(ConfigTables.ROLEONJOIN, ctx.guild.id)
        print("roles", roles)
        embed = Embed(title=f"Role on join", color=0x00FF42)
        embed.add_field(
            name="Roles",
            value="\n".join([ctx.guild.get_role(int(r[1])).name for r in roles]),
        )
        await ctx.send(
            embed=embed,
            ephemeral=True,
        )

    @roleonjoin.command(description="Set a roleOnJoin role for the server.")
    async def set_role(self, ctx: commands.Context, role: Role):
        db = ConfigDatabase(self.bot)
        roles = db.get_items_by(ConfigTables.ROLEONJOIN, ctx.guild.id)
        if role.id in [r[1] for r in roles]:
            await ctx.send(
                embed=Embed(title=f"{role.name} already is roleOnJoin", color=0xFF0000),
                ephemeral=True,
            )
            return

        db.insert_item(ConfigTables.ROLEONJOIN, ctx.guild.id, role.id)
        await ctx.send(
            embed=Embed(title=f"Set {role.name} as roleonjoin role", color=0x00FF42),
            ephemeral=True,
        )

    @roleonjoin.command(description="Remove a roleOnJoin role for the server.")
    async def remove_role(self, ctx: commands.Context, role: Role):
        db = ConfigDatabase(self.bot)
        roles = db.get_items_by(ConfigTables.ROLEONJOIN, ctx.guild.id)
        if role.id not in [r[1] for r in roles]:
            await ctx.send(
                embed=Embed(title=f"{role.name} is not a roleOnJoin", color=0xFF0000),
                ephemeral=True,
            )
            return
        db.delete_item(ConfigTables.ROLEONJOIN, ctx.guild.id, role.id)
        await ctx.send(
            embed=Embed(title=f"Removed {role.name} as roleOnJoin", color=0x00FF42),
            ephemeral=True,
        )

    @roleonjoin.command(description="Remove all roleOnJoin roles for the server.")
    async def remove_all_roles(self, ctx: commands.Context):
        db = ConfigDatabase(self.bot)
        roles = db.get_items_by(ConfigTables.ROLEONJOIN, ctx.guild.id)
        print()
        if len(roles) == 0:
            await ctx.send(
                embed=Embed(title=f"No role is a roleOnJoin", color=0xFF0000),
                ephemeral=True,
            )
            return
        db.delete_item(ConfigTables.ROLEONJOIN, ctx.guild.id)
        await ctx.send(
            embed=Embed(title=f"Removed all roles", color=0x00FF42),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(role_on_join(bot))
