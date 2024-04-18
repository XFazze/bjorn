import discord
from discord.ext import commands

from lib.config import ConfigDatabase, ConfigTables


def admin():
    async def predicate(ctx: commands.Context):
        db = ConfigDatabase(ctx.bot)
        admin_roles = db.get_items_by(ConfigTables.ADMIN, ctx.guild.id)
        admin_roles_ids = set([r[1] for r in admin_roles])
        user_roles = set([r.id for r in ctx.author.roles])

        return (
            len(admin_roles_ids.intersection(user_roles)) != 0
            or len(admin_roles_ids) == 0
        )

    return commands.check(predicate)


def voice():
    async def predicate(ctx: commands.Context):
        if not ctx.author.voice:
            await ctx.reply(
                embed=discord.Embed(
                    title=f"You must be in a voice channel to use this command!",
                    color=0xFF0000,
                )
            )
        return ctx.author.voice

    return commands.check(predicate)


def remove_original():
    async def predicate(ctx: commands.Context):
        await ctx.message.delete(delay=1)
        return True

    return commands.check(predicate)
