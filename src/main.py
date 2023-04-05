from dotenv import load_dotenv
import os
import asyncio

import discord
from discord.ext import commands
from cogwatch import Watcher

load_dotenv()
bot = commands.Bot(intents=discord.Intents.all(), command_prefix="¤")


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    if os.getenv("DEV") == "TRUE":
        print("DEV MODE ACTIVE")
        watcher = Watcher(bot, path="cogs", preload=True, debug=True)
        await watcher.start()


@bot.command()
async def alive(ctx):
    await ctx.send("Is alive!")


async def main():
    # await bot.load_extension("cogs.dev")
    await bot.load_extension("cogs.info")
    await bot.load_extension("cogs.betterVC")
    await bot.load_extension("cogs.autoPublic")
    # await bot.load_extension("cogs.leagueCustoms")
    async with bot:
        await bot.start(os.getenv("TOKEN"))


if os.getenv("DEV") == "TRUE":
    bot.run(os.getenv("TOKEN"))
else:
    asyncio.run(main())
