from discord.ext import commands
import discord


def admin():
    async def predicate(ctx):
        return 802299956299169845 in [role.id for role in ctx.author.roles]
    return commands.check(predicate)


def voice():
    async def predicate(ctx):
        if not ctx.author.voice:
            await ctx.reply(embed=discord.Embed(title=f"You must be in a voice channel to use this command!", color=0xFF0000))
        return ctx.author.voice
    return commands.check(predicate)
