from discord.ext import commands
import discord
import os

def admin():
    async def predicate(ctx):
        return int(os.getenv("LOADING_ADMIN_ROLE_ID")) in [role.id for role in ctx.author.roles]
    return commands.check(predicate)


def voice():
    async def predicate(ctx):
        if not ctx.author.voice:
            await ctx.reply(embed=discord.Embed(title=f"You must be in a voice channel to use this command!", color=0xFF0000))
        return ctx.author.voice
    return commands.check(predicate)


def remove_original():
    async def predicate(ctx: commands.Context):
        await ctx.message.delete(delay=1)
        return True
    return commands.check(predicate)
