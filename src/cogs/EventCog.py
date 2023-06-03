from discord.ext import commands
import discord
from typing import Optional

import lib.persmissions as permissions
from lib.event import Database, Event, gen_event_id


class EventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.hybrid_group(name="event", description="Event commands")
    async def event(self, ctx: commands.Context): pass

    @event.command(name="create", description="Creates an event")
    async def create(self, ctx: commands.Context, name: str, description: str, date: str, time: str, location: str):
        event_id = gen_event_id(self.db)
        event = Event(ctx.author.id, ctx.guild.id, name,
                      description, date, time, location, event_id)

        await ctx.send(f"{event.event_id}, {event.discord_id}, {event.guild_id}, {event.finished}, {event.name}, {event.description}, {event.date}, {event.time}, {event.location}")


async def setup(bot):
    await bot.add_cog(EventCog(bot))
