import pytest
import pytest_asyncio
import discord.ext.test as dpytest
import discord
import os

from ...src.main import setup_bot

from discord.ext import commands


@pytest_asyncio.fixture
async def info_bot():
    # Setup
    b = await setup_bot(["dev"], "info")
    await b._async_setup_hook()
    dpytest.configure(b)

    yield b

    # Teardown
    await dpytest.empty_queue()  # empty the global message queue as test teardown


@pytest.mark.asyncio
async def test_ping(info_bot):
    await dpytest.message("¤sync")
    print("A", bool(dpytest.verify().message().contains()))
    assert dpytest.verify().message().contains()
