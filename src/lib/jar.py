import os
import datetime
import random
import discord
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
from discord.ui import Button, View, Select
from discord.ext import commands
from typing import Literal
import math
import plotly.express as px
import pandas as pd
from itertools import combinations
import time

import lib.draftlolws as draftlol
import lib.general as general

class Database(general.Database):
    def __init__(self, bot: commands.Bot, db_name: str):
        super().__init__(db_name)
        self.create_tables(
            {
                "Pot" : ["discord_id", "money", "timestamp"]
            }
        )
        self.bot = bot
        def pot_value(self):
            res = self.cursor.execute(
                
            )