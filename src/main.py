from dotenv import load_dotenv, dotenv_values
import os
import asyncio

import discord
from discord.ext import commands
import logging


async def setup_bot(
    cogs: list[str] = ["info", "betterVC", "autoPublic", "league", "dev"],
    prefix: str = os.getenv("PREFIX"),
):
    if not os.path.exists("data"):
        os.makedirs("data")
    bot = commands.Bot(intents=discord.Intents.all(), command_prefix=prefix)

    for cog in cogs:
        await bot.load_extension(f"src.cogs.{cog}")
    print(bot)
    return bot


async def main():
    load_dotenv(".env")
    load_dotenv(".env.secret")

    if os.getenv("DEV") != "TRUE":
        discord.utils.setup_logging(level=logging.INFO, root=False)
    else:
        handler = logging.FileHandler(
            filename="data/discord.log", encoding="utf-8", mode="w"
        )
        discord.utils.setup_logging(level=logging.INFO, root=False, handler=handler)

    if os.getenv("DEV") == "False":
        bot = setup_bot()
    elif os.getenv("DEV") == "True":
        bot = setup_bot(["dev", os.getenv("TEST_COG")])

    @bot.event
    async def on_ready():
        print(f"We have logged in as {bot.user}")

    @bot.command()
    async def alive(ctx):
        await ctx.send("Is alive!")

    await bot.start(os.getenv("TOKEN"))

    asyncio.run(main())
