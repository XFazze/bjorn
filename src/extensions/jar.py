from discord.ext import commands
import discord
import random
import math
from typing import Literal
import time

#import lib.persmissions as permissions
from lib.jar import Database

import sqlite3

def connect():
    conn = sqlite3.connect('data/league.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT discord_id, money, timestamp FROM 2024")
    rows = cursor.fetchall()
    
    conn.commit()
    cursor.close()
    conn.close()
    return rows


class jar():
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database(bot, "data/jar.sqlite")
    
    @commands.hybrid_group(name="jar", description="A pot of money for the server")
    async def jar(self, ctx: commands.Context):
        pass
    
    @jar.command(
        name="Pot",
        description="Says how much in total there is in the pot",
    )
    async def pot():
        rows = connect()
        for money in rows:
            pot += money[1]
        print(pot)

    @jar.command(
        name="How Tilted",
        description="Shows how much a certain person has tilted",
    )
    async def how_tilted():
        rows = connect()
        