# import os
# import datetime
# import random
# import discord
from discord import (
    ButtonStyle,
    Interaction,
    Member,
    Embed,
    Message,
    VoiceChannel,
    TextChannel,
    CategoryChannel,
    SelectOption,
)

from discord.ext import commands


import time

import lib.general as general

pot_value = "1"


class Database(general.Database):
    def __init__(self, bot: commands.Bot, db_name: str):
        super().__init__(db_name)
        self.create_tables({"pot": ["discord_id", "money", "timestamp"]})
        self.bot = bot

    def pot_value(self):
        res = self.cursor.execute(f"SELECT money, timestamp FROM pot").fetchall()
        return res

    def contributions_from(self, discord_id: int):
        res = self.cursor.execute(
            f"SELECT discord_id, money, timestamp FROM pot"
        ).fetchall()
        pot = 0
        for i in res:
            if str(discord_id) == str(i[0]):
                pot += int(i[1])
        return pot

    def add_to_jar(self, discord_id: int):
        tiden = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        discord_id = str(discord_id)
        self.cursor.execute(
            f"INSERT INTO pot (discord_id, money, timestamp) VALUES (?, ?, ?)",
            (discord_id, pot_value, tiden),
        )
        self.connection.commit()

    """
    def top_tilted(self, antal: int):
        res = self.cursor.execute(f"SELECT discord_id,money,timestamp FROM pot")
    """
    """        
    def remove_tilt(self,timestamp: str):
        self.cursor.executre(f"DELETE FROM pot WHERE timestamp = {timestamp}")
    """
