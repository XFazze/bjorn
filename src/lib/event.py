import datetime
import random
import discord
from discord.ext import commands
from typing import Optional, Literal, Union

import lib.general as general


def gen_event_id(db) -> int:
    res = db.cursor.execute("SELECT event_id FROM event")
    event_ids = [i[0] for i in res.fetchall()]
    event_id = random.randint(100000, 999999)
    while event_id in event_ids:
        event_id = random.randint(10000000, 99999999)

    return event_id


class Event:
    def __init__(self, discord_id: int, guild_id: int, name: str, description: str, date: str, time: str, location: str, event_id: int, finished: Optional[int] = 0):
        self.discord_id = discord_id
        self.guild_id = guild_id
        self.finished = finished
        self.name = name
        self.description = description
        self.date = date
        self.time = time
        self.location = location
        self.event_id = event_id


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

    def insert_event(self, event: Event):
        self.cursor.execute(
            "INSERT INTO event VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (event.event_id, event.discord_id, event.guild_id, event.finished,
             event.name, event.description, event.date, event.time, event.location)
        )
        self.connection.commit()

    def remove_event(self, event_id: int):
        self.cursor.execute(
            "DELETE FROM event WHERE event_id = ?",
            (event_id)
        )
        self.connection.commit()

    def get_all_events(self):
        events_db = self.cursor.execute("SELECT * FROM event")
        events = [Event(discord_id, guild_id, name, description, date, time, location, event_id, finished) for event_id,
                  discord_id, guild_id, finished, name, description, date, time, location in events_db.fetchall()]
        return events

    def get_event(self, event_id: int):
        event_db = self.cursor.execute(
            "SELECT * FROM event WHERE event_id = ?", (event_id,))
        event_id, discord_id, guild_id, finished, name, description, date, time, location = event_db.fetchone()
        event = Event(discord_id, guild_id, name, description,
                      date, time, location, event_id, finished)
        return event

    def update_event(self, event_id: int, name: str, description: str, date: str, time: str, location: str):
        self.cursor.execute(
            "UPDATE event SET name = ?, description = ?, date = ?, time = ?, location = ? WHERE event_id = ?",
            (name, description, date, time, location, event_id)
        )
