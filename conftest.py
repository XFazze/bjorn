# import pytest_asyncio
# import discord.ext.test as dpytest

# import sys

# sys.path.append(".")
# from src.main import setup_bot

# from discord.ext import commands


# @pytest_asyncio.fixture
# async def bot_fixture():
#    # Setup
#    b = setup_bot()

#    dpytest.configure(b)

#    yield b

#    # Teardown
#    await dpytest.empty_queue()  # empty the global message queue as test teardown


## def pytest_sessionfinish(session, exitstatus):
##    """Code to execute after all tests."""

##    # dat files are created when using attachements
##    print("\n-------------------------\nClean dpytest_*.dat fies")
##    fileList = glob.glob("./dpytest_*.dat")
##    for filePath in fileList:
##        try:
##            os.remove(filePath)
##        except Exception:
##            print("Error while deleting file : ", filePath)
