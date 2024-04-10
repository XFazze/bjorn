from dotenv import load_dotenv, dotenv_values
import os
import asyncio

import discord
from discord.ext import commands
from cogwatch import Watcher
import logging

load_dotenv(".env")
load_dotenv(".env.secret")

if not os.path.exists("data"):
    os.makedirs("data")

if os.getenv("DEV") != "TRUE":
    discord.utils.setup_logging(level=logging.INFO, root=False)
else:
    handler = logging.FileHandler(
        filename="data/discord.log", encoding="utf-8", mode="w"
    )
    discord.utils.setup_logging(level=logging.INFO, root=False, handler=handler)

bot = commands.Bot(intents=discord.Intents.all(), command_prefix=os.getenv("PREFIX"))


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.command()
async def alive(ctx):
    await ctx.send("Is alive!")


async def main():
    cogs = ["info", "betterVC", "autoPublic", "league", "dev"]
    if os.getenv("DEV") != "True":
        for cog in cogs:
            await bot.load_extension(f"cogs.{cog}")
    else:
        print("Dev mode enabled")
        await bot.load_extension(f"cogs.dev")
        await bot.load_extension(f"cogs.{os.getenv('TEST_COG')}")
    await bot.start(os.getenv("TOKEN"))


asyncio.run(main())
