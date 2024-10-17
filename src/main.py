from dotenv import load_dotenv
import os
import asyncio
import logging
import discord
from discord.ext import commands

# import logging


def setup_logging() -> None:
    discord.utils.setup_logging(level=logging.INFO, root=False)


async def load_extensions(bot: commands.Bot, extensions=None) -> None:
    if extensions is None:
        extensions = [
            "info",
            "betterVC",
            "roleOnJoin",
            "league",
            "dev",
            "reactionRoles",
            "strike",
        ]
    print(f"Loading extensions: {', '.join(extensions)}")
    for extension in extensions:
        try:
            await bot.load_extension(f"extensions.{extension}")
        except:
            print(f'Could not load extension: "{extension}"')
            extensions.remove(extension)
    print(f"Loaded extensions: {', '.join(extensions)}")


def check_enviroment_variables() -> list[str]:
    enviromental_variables = [
        "DEV",
        "PREFIX",
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
        raise Exception(f"Missing enviroment variables: {missing_variables}")

    if not os.path.exists("data"):
        os.makedirs("data")

    bot = commands.Bot(
        intents=discord.Intents.all(), command_prefix=os.environ["PREFIX"]
    )

    @bot.event
    async def on_ready():
        print(f"We have logged in as {bot.user} with prefix '{os.environ['PREFIX']}'")

    if os.environ["DEV"] == "True":
        print("DEV MODE ENABLED")
        await load_extensions(bot, ["dev", os.environ["TEST_EXTENSION"]])
    else:
        await load_extensions(bot)
    return bot


async def start_bot():
    bot = await setup()
    await bot.start(os.environ["TOKEN"])


if __name__ == "__main__":
    asyncio.run(start_bot())
