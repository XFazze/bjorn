from discord.ext import commands
import discord
from typing import Optional

import lib.persmissions as permissions
from lib.event import Database, Event


class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(bot)

    @commands.hybrid_group(name="event", description="Event commands")
    async def event(self, ctx: commands.Context): pass

    @event.command(name="create", description="Creates an event")
    async def create(self, ctx: commands.Context, name: str, description: str, date: str, time: str, location: str):
        event = Event(self.bot, name, description, date, time, location)
