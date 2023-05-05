from discord.ext import commands


def admin():
    async def predicate(ctx):
        return 802299956299169845 in [role.id for role in ctx.author.roles]
    return commands.check(predicate)
