import pytest
import pytest_asyncio
import discord.ext.test as dpytest
from discord.ext.test import backend, get_config
from discord.ext.test import message

import discord
import os
import functools

from ...src.main import setup_bot

from discord.ext import commands


@pytest_asyncio.fixture
async def dev_bot():
    # Setup
    b = await setup_bot(["dev"], "dev")
    await b._async_setup_hook()
    dpytest.configure(b)
    global admin, admess
    guild = get_config().guilds[0]
    admin = backend.make_member(
        backend.make_user("AdminUser", "0001"),
        guild,
        roles=[
            backend.make_role(
                "Admin",
                guild,
                permissions=8,
                id_num=int(os.getenv("LOADING_ADMIN_ROLE_ID")),
            )
        ],
    )

    admess = functools.partial(message, member=admin)

    # config = dpytest.runner.get_config()
    # print("a", type(config.guilds[0].roles[0]))
    # print("a", type(config.members))
    # dpytest.add_role(
    #    config.members[0],
    #    HOW do i get role obj?
    # )

    yield b

    # Teardown
    await dpytest.empty_queue()  # empty the global message queue as test teardown


@pytest.mark.asyncio
async def test_sync(dev_bot):
    await message("¤sync")
    embed = discord.Embed(title=f"Synced!", color=0x00FF42)
    assert dpytest.verify().message().contains().embed(embed)


# def pytest_sessionfinish(session, exitstatus):
#    """Code to execute after all tests."""

#    # dat files are created when using attachements
#    print("\n-------------------------\nClean dpytest_*.dat fies")
#    fileList = glob.glob("./dpytest_*.dat")
#    for filePath in fileList:
#        try:
#            os.remove(filePath)
#        except Exception:
#            print("Error while deleting file : ", filePath)
