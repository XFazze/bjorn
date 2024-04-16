from dotenv import load_dotenv
import os
import asyncio
import logging
import discord
from discord.ext import commands

# import logging


def setup_logging():
    discord.utils.setup_logging(level=logging.INFO, root=False)


async def load_extensions(bot: commands.Bot, extensions=None):
    if extensions is None:
        extensions = ["info", "betterVC", "autoPublic", "league", "dev"]
    print(f"Extensions loaded: {', '.join(extensions)}")
    for extension in extensions:
        await bot.load_extension(f"extensions.{extension}")


def check_enviroment_variables():
    enviromental_variables = [
        "DEV",
        "PREFIX",
        "LOADING_ID",
        "BETTERVC_CATEGORY_ID",
        "LOADING_ADMIN_ROLE_ID",
        "LOADING_ACTIVE_ROLE_ID",
        "LOADING_INACTIVE_ROLE_ID",
        "LOADING_INACTIVE_ROLE_ID",
        "LOADING_PUBLIC_ROLE_ID",
        "DEV_TEST_CATEGORY_NAME",
        "DEV_TEST_CHANNEL_NAME",
        "LEAGUE_GRAPH_DIR",
        "LEAGUE_GRAPH_FILENAME",
    ]
    missing_varaibles = []
    for var in enviromental_variables:
        if os.getenv(var) is None:
            missing_varaibles.append(var)
    return missing_varaibles


async def setup():
    setup_logging()
    load_dotenv(".env")
    load_dotenv(".env.secret")

    missing_variables = check_enviroment_variables()
    if len(missing_variables) != 0:
        raise Exception(f"Missing enviroment variables{missing_variables}")

    if not os.path.exists("data"):
        os.makedirs("data")

    bot = commands.Bot(
        intents=discord.Intents.all(), command_prefix=os.environ["PREFIX"]
    )

    @bot.event
    async def on_ready():
        print(f"We have logged in as {bot.user} with prefix '{os.environ['PREFIX']}'")

    @bot.command()
    async def alive(ctx):
        await ctx.send("Is alive!")

    if os.environ["DEV"] == "True":
        print("Dev mode enabled")
        await load_extensions(bot, ["dev", os.environ["TEST_EXTENSION"]])
    else:
        await load_extensions(bot)
    return bot


async def start_bot(bot: commands.Bot):
    await bot.start(os.environ["TOKEN"])


if __name__ == "__main__":
    bot = asyncio.run(setup())
    asyncio.run(start_bot(bot))
