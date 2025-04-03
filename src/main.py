from dotenv import load_dotenv
import os
import asyncio
import logging
import discord
from discord.ext import commands
import traceback

# Setup logging
logging_level = (
    logging.DEBUG if os.environ.get("DEV", "False") == "True" else logging.INFO
)
logging.basicConfig(
    level=logging_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("bjorn.log")],
)


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
        logging.info(f"Loading extensions: {', '.join(extensions)}")

    successful_extensions = []
    for extension in extensions:
        try:
            await bot.load_extension(f"extensions.{extension}")
            logging.info(f'Successfully loaded extension: "{extension}"')
            successful_extensions.append(extension)
        except Exception as e:
            logging.error(
                f'Could not load extension: "{extension}". Error: {e}\n{traceback.format_exc()}'
            )

    logging.info(f"Loaded extensions: {', '.join(successful_extensions)}")


def check_environment_variables() -> list[str]:
    environmental_variables = [
        "DEV",
        "PREFIX",
        "DEV_TEST_CATEGORY_NAME",
        "DEV_TEST_CHANNEL_NAME",
        "LEAGUE_GRAPH_DIR",
        "LEAGUE_GRAPH_FILENAME",
    ]
    missing_variables = []
    for var in environmental_variables:
        if os.getenv(var) is None:
            missing_variables.append(var)
    return missing_variables


class CustomBot(commands.Bot):
    async def setup_hook(self):
        if os.environ["DEV"] == "True":
            logging.info("DEV MODE ENABLED")
            await load_extensions(self, ["dev", os.environ["TEST_EXTENSION"]])
        else:
            await load_extensions(self)

        await self.tree.sync()
        logging.info("Slash commands synced")


async def setup():
    setup_logging()
    load_dotenv(".env")
    load_dotenv(".env.secret")

    missing_variables = check_environment_variables()
    if len(missing_variables) != 0:
        raise Exception(f"Missing environment variables: {missing_variables}")

    if not os.path.exists("data"):
        os.makedirs("data")
        logging.info("Created 'data' directory")

    bot = CustomBot(intents=discord.Intents.all(), command_prefix=os.environ["PREFIX"])

    @bot.event
    async def on_ready():
        logging.info(f"Logged in as {bot.user} with prefix '{os.environ['PREFIX']}'")

    logging.info("Bot instance created")
    return bot


async def start_bot():
    try:
        bot = await setup()
        logging.info("Starting bot...")
        await bot.start(os.environ["TOKEN"])
    except KeyError as e:
        logging.critical(f"Missing environment variable: {e}")
    except discord.LoginFailure:
        logging.critical(
            "Invalid Discord token. Please check your TOKEN environment variable."
        )
    except Exception as e:
        logging.critical(f"Failed to start bot: {e}")
        logging.debug(traceback.format_exc())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)  # Fixed from logging.info
    logger = logging.getLogger("discord")
    asyncio.run(start_bot())
