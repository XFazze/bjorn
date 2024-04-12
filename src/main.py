from dotenv import load_dotenv
import os
import asyncio
import logging
import discord
from discord.ext import commands

# import logging


def setup_logging():
    discord.utils.setup_logging(level=logging.INFO, root=False)


# if os.getenv("DEV") != "TRUE":
# else:
#    handler = logging.FileHandler(
#        filename="data/discord.log", encoding="utf-8", mode="w"
#    )
#    discord.utils.setup_logging(level=logging.INFO, root=False, handler=handler)


async def load_extensions(bot: commands.Bot, extensions=None):
    if extensions is None:
        extensions = ["info", "betterVC", "autoPublic", "league", "dev"]
    print(f"Extensions loaded: {', '.join(extensions)}")
    for extension in extensions:
        await bot.load_extension(f"extensions.{extension}")


async def setup():
    setup_logging()
    load_dotenv(".env")
    load_dotenv(".env.secret")

    if not os.path.exists("data"):
        os.makedirs("data")

    bot = commands.Bot(
        intents=discord.Intents.all(), command_prefix=os.getenv("PREFIX")
    )

    @bot.event
    async def on_ready():
        print(f"We have logged in as {bot.user} with prefix '{os.getenv('PREFIX')}'")

    @bot.command()
    async def alive(ctx):
        await ctx.send("Is alive!")

    if os.getenv("DEV") == "True":
        print("Dev mode enabled")
        await load_extensions(bot, ["dev", os.getenv("TEST_EXTENSION")])
    else:
        await load_extensions(bot)
    return bot


async def start_bot(bot: commands.Bot):
    await bot.start(os.getenv("TOKEN"))


if __name__ == "__main__":
    bot = asyncio.run(setup())
    asyncio.run(start_bot(bot))
