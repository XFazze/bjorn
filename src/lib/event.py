import datetime
import random
import discord
from discord.ext import commands
from typing import Optional, Literal, Union

import lib.general as general


class Database(general.Database):
    def __init__(self):
        super().__init__("data/events.sqlite")

        self.create_tables(
            {
                "event": [
                    "event_id",
                    "discord_id",
                    "guild_id",
                    "finished",
                    "name",
                    "description",
                    "date",
                    "time",
                    "location"
                ],

            }
        )

    def insert_event(self, event_id: int, discord_id: int, guild_id: int, name: str, description: str, date: str, time: str, location: str):
        pass

    def remove_event(self, event_id: int):
        pass

    def get_all_events(self):
        pass

    def update_event(self, event_id: int, name: str, description: str, date: str, time: str, location: str):
        pass


db = Database()


class Event:
    def __init__(self, bot: commands.Bot, name: str, description: str, date: str, time: str, location: str):
        self.bot = bot
        self.name = name
        self.description = description
        self.date = date
        self.time = time
        self.location = location
        self.event_id = self.gen_event_id()

    def gen_event_id(self) -> int:
        res = self.db.cursor.execute("SELECT event_id FROM event")

        event_ids = [i[0] for i in res.fetchall()]
        event_id = random.randint(100000, 999999)
        while event_id in event_ids:
            event_id = random.randint(10000000, 99999999)

        return event_id
