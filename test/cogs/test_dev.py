import pytest
import pytest_asyncio
import discord.ext.test as dpytest
import os

from ...src.main import setup_bot

from discord.ext import commands


@pytest_asyncio.fixture
async def dev_bot():
    # Setup
    b = await setup_bot(["dev"], os.getenv("TEST_PREFIX"))
    await b._async_setup_hook()
    dpytest.configure(b)

    yield b

    # Teardown
    await dpytest.empty_queue()  # empty the global message queue as test teardown


@pytest.mark.asyncio
async def test_sync(dev_bot):
    await dpytest.message("¤sync")
    assert dpytest.verify().message().content("Synced!")


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
