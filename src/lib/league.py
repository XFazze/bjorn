import os
import datetime
import random
import discord
import logging
import asyncio
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
    Guild,
)
from discord.ui import Button, View, Select
from discord.ext import commands
from typing import Literal
import math
import plotly.express as px
import pandas as pd
from itertools import combinations
import time

from lib.config import ConfigDatabase, ConfigTables
import lib.draftlolws as draftlol
import lib.general as general


logger = logging.getLogger(__name__)

ranks_mmr = {
    "Iron+": 0,
    "Bronze 3": 700,
    "Bronze 2": 800,
    "Bronze 1": 900,
    "Silver 4": 1000,
    "Silver 3": 1100,
    "Silver 2": 1200,
    "Silver 1": 1300,
    "Gold 4": 1400,
    "Gold 3": 1500,
    "Gold 2": 1600,
    "Gold 1": 1700,
    "Platinum 4": 1800,
    "Platinum 3": 1900,
    "Platinum 2": 2000,
    "Platinum 1": 2100,
    "Emerald 4": 2200,
    "Emerald 3": 2300,
    "Emerald 2": 2400,
    "Emerald 1": 2500,
    "Diamond 4": 2600,
    "Diamond 3": 2700,
    "Diamond 2": 2800,
    "Diamond 1": 2900,
    "Master+": 3000,
}

ranks_type = Literal[
    "Iron+",
    "Bronze 3",
    "Bronze 2",
    "Bronze 1",
    "Silver 4",
    "Silver 3",
    "Silver 2",
    "Silver 1",
    "Gold 4",
    "Gold 3",
    "Gold 2",
    "Gold 1",
    "Platinum 4",
    "Platinum 3",
    "Platinum 2",
    "Platinum 1",
    "Emerald 4",
    "Emerald 3",
    "Emerald 2",
    "Emerald 1",
    "Diamond 4",
    "Diamond 3",
    "Diamond 2",
    "Diamond 1",
    "Master+",
]


class Tournament:
    pass


class GuildOptions:
    def __init__(self):
        pass


class StartMenuEmbed(Embed):
    def __init__(self):
        pass


class StartMenuView(View):
    def __init__(self):
        super().__init__(timeout=7200)

        self.buttons = {
            Button(label="", custom_id=""),
            Button(label="", custom_id=""),
            Button(label="", custom_id=""),
            Button(label="", custom_id=""),
            Button(label="", custom_id=""),
            Button(label="", custom_id=""),
        }


class Player:
    def __init__(
        self,
        bot: commands.Bot,
        discord_id: int = None,
        discord_name: str = None,
        queue_type: str = "summoners_rift",
    ):
        self.db = Database(bot)
        self.bot = bot
        self.user_exists = False  # If the user has not been deleted
        self.discord_name = "Unknown Player"  # Default fallback name
        self.queue_type = queue_type
        # Check if it's a fake player
        if discord_id and discord_id < 0:
            fake_player = self.db.cursor.execute(
                f"SELECT discord_id, sr_mmr, sr_wins, sr_losses, aram_mmr, aram_wins, aram_losses, discord_name FROM fake_player WHERE discord_id = {discord_id}"
            ).fetchone()

            if fake_player:
                self.discord_id = discord_id
                self.sr_mmr = math.ceil(fake_player[1])
                self.sr_wins = fake_player[2]
                self.sr_losses = fake_player[3]
                self.aram_mmr = math.ceil(fake_player[4]) if fake_player[4] else 1000
                self.aram_wins = fake_player[5] if fake_player[5] else 0
                self.aram_losses = fake_player[6] if fake_player[6] else 0
                self.discord_name = fake_player[7]
                self.is_fake = True

                # Set the active stats based on queue type
                if queue_type == "summoners_rift":
                    self.mmr = self.sr_mmr
                    self.wins = self.sr_wins
                    self.losses = self.sr_losses
                else:  # aram
                    self.mmr = self.aram_mmr
                    self.wins = self.aram_wins
                    self.losses = self.aram_losses

                self.win_rate = (
                    self.wins / (self.wins + self.losses) * 100
                    if self.wins + self.losses > 0
                    else 0
                )
                return

        if discord_id != None:
            self.discord_id = discord_id
            user = self.bot.get_user(discord_id)
            if user != None:  # In case user doesnt exists
                self.discord_name = user.name
                self.user_exists = True
            else:
                # Try to get the name from the database as fallback
                try:
                    player_data = self.db.cursor.execute(
                        f"SELECT discord_name FROM player WHERE discord_id = {discord_id}"
                    ).fetchone()
                    if player_data and player_data[0]:
                        self.discord_name = player_data[0]
                    else:
                        self.discord_name = f"User_{discord_id}"
                except:
                    self.discord_name = f"User_{discord_id}"
                return
        elif discord_name != None:
            discord_member_object = next(
                (m for m in self.bot.get_all_members() if m.name == discord_name), None
            )
            if discord_member_object is None:
                # Improved error message that properly separates the discord_name from any additional info
                raise Exception(f"No user with discord name: {discord_name}")

            discord_id = discord_member_object.id
            self.discord_name = discord_name

        existing_player = self.db.cursor.execute(
            f"SELECT discord_id, sr_mmr, sr_wins, sr_losses, aram_mmr, aram_wins, aram_losses FROM player WHERE discord_id = {discord_id}"
        ).fetchone()

        self.discord_id = discord_id

        if existing_player:
            self.sr_mmr = math.ceil(existing_player[1]) if existing_player[1] else 1000
            self.sr_wins = existing_player[2] if existing_player[2] else 0
            self.sr_losses = existing_player[3] if existing_player[3] else 0
            self.aram_mmr = math.ceil(existing_player[4]) if existing_player[4] else 1000
            self.aram_wins = existing_player[5] if existing_player[5] else 0
            self.aram_losses = existing_player[6] if existing_player[6] else 0
        else:
            self.sr_mmr = 1000
            self.sr_wins = 0
            self.sr_losses = 0
            self.aram_mmr = 1000
            self.aram_wins = 0
            self.aram_losses = 0

        # Set the active stats based on queue type
        if queue_type == "summoners_rift":
            self.mmr = self.sr_mmr
            self.wins = self.sr_wins
            self.losses = self.sr_losses
        else:  # aram
            self.mmr = self.aram_mmr
            self.wins = self.aram_wins
            self.losses = self.aram_losses

        self.win_rate = (
            self.wins / (self.wins + self.losses) * 100
            if self.wins + self.losses > 0
            else 0
        )

        if not existing_player:
            self.db.insert_player(self)

    def set_mmr(self, mmr):
        if self.queue_type == "summoners_rift":
            self.db.cursor.execute(
                f"UPDATE player SET sr_mmr = {mmr} WHERE discord_id = {self.discord_id}"
            )
            self.sr_mmr = mmr
        else:  # aram
            self.db.cursor.execute(
                f"UPDATE player SET aram_mmr = {mmr} WHERE discord_id = {self.discord_id}"
            )
            self.aram_mmr = mmr
        self.db.connection.commit()
        self.mmr = mmr

    def update(self):
        if hasattr(self, "is_fake") and self.is_fake:
            # Update fake player
            if self.queue_type == "summoners_rift":
                self.db.cursor.execute(
                    f"UPDATE fake_player SET sr_mmr = {self.sr_mmr}, sr_wins = {self.sr_wins}, sr_losses = {self.sr_losses} WHERE discord_id = {self.discord_id}"
                )
            else:  # aram
                self.db.cursor.execute(
                    f"UPDATE fake_player SET aram_mmr = {self.aram_mmr}, aram_wins = {self.aram_wins}, aram_losses = {self.aram_losses} WHERE discord_id = {self.discord_id}"
                )
            self.db.connection.commit()

            # Also update MMR history
            insertion = (
                f"INSERT INTO mmr_history (discord_id, mmr, timestamp, queue_type) VALUES (?, ?, ?, ?)"
            )
            self.db.cursor.execute(
                insertion,
                (
                    self.discord_id,
                    self.mmr,
                    datetime.datetime.now(),
                    self.queue_type,
                ),
            )
            self.db.connection.commit()
            return

        # Original implementation for real players
        if self.queue_type == "summoners_rift":
            self.db.cursor.execute(
                f"UPDATE player SET sr_mmr = {self.sr_mmr}, sr_wins = {self.sr_wins}, sr_losses = {self.sr_losses} WHERE discord_id = {self.discord_id}"
            )
        else:  # aram
            self.db.cursor.execute(
                f"UPDATE player SET aram_mmr = {self.aram_mmr}, aram_wins = {self.aram_wins}, aram_losses = {self.aram_losses} WHERE discord_id = {self.discord_id}"
            )
        self.db.connection.commit()

        insertion = (
            f"INSERT INTO mmr_history (discord_id, mmr, timestamp, queue_type) VALUES (?, ?, ?, ?)"
        )
        self.db.cursor.execute(
            insertion,
            (
                self.discord_id,
                self.mmr,
                datetime.datetime.now(),
                self.queue_type,
            ),
        )
        self.db.connection.commit()

    def get_rank(self):
        rank = None
        for i in ranks_mmr:
            if self.mmr >= ranks_mmr[i]:
                rank = i
            else:
                break
        if self.mmr >= ranks_mmr["Master+"]:
            return "Master+"
        return rank

    def get_lp(self):
        rank = self.get_rank()
        if self.mmr >= ranks_mmr["Master+"]:
            return 100 - (ranks_mmr["Master+"] - self.mmr)

        elif rank is None:
            rank = "Master+"
        lp = (
            ranks_mmr[rank] + (100) - self.mmr
        )  # 100 taken from  -> ranks_mmr["Bronze 1"]-ranks_mmr["Bronze 2"]

        if lp < 0 and self.mmr < ranks_mmr["Bronze 3"]:
            lp = (self.mmr / ranks_mmr["Bronze 3"]) * 100
            return int(lp // 1)

        return int(100 - lp)

    def get_discord_object(self):
        if hasattr(self, "is_fake") and self.is_fake:
            # Return a Mock object for fake players
            class FakeUser:
                def __init__(self, id, name):
                    self.id = id
                    self.name = name
                    self.display_name = name
                    self.roles = []
                    self.voice = None

                async def add_roles(self, *args, **kwargs):
                    pass

                async def remove_roles(self, *args, **kwargs):
                    pass

                async def move_to(self, *args, **kwargs):
                    pass

            return FakeUser(self.discord_id, self.discord_name)

        # Original implementation for real players
        return next(
            (m for m in self.bot.get_all_members() if m.id == self.discord_id), None
        )

    def get_matches(self, include_fake=False):
        return self.db.get_matches(self.discord_id, include_fake=include_fake)


class Match:
    def __init__(
        self,
        match_id: int,
        team1: list[Player],
        team2: list[Player],
        winner: int,  # 1 or 2
        mmr_diff: int,
        timestamp: datetime.datetime,
        is_fake: bool = False,
        queue_type: str = "summoners_rift",
    ):
        self.match_id = match_id
        self.team1 = team1
        self.team2 = team2
        self.winner = winner
        self.mmr_diff = mmr_diff
        self.timestamp = timestamp
        self.is_fake = is_fake
        self.queue_type = queue_type


class Database(general.Database):
    def __init__(self, bot: commands.Bot):
        super().__init__(os.environ["LEAGUE_DB_NAME"])
        self.create_tables(
            {
                "player": [
                    "discord_id",
                    "sr_mmr",
                    "sr_wins",
                    "sr_losses",
                    "aram_mmr",
                    "aram_wins",
                    "aram_losses",
                    "discord_name",
                ],
                "match": [
                    "match_id",
                    "team1",
                    "team2",
                    "winner",
                    "mmr_diff",
                    "timestamp",
                ],
                "mmr_history": ["discord_id", "mmr", "timestamp", "queue_type"],
                "guild_options": ["guild_id", "customs_channel"],
            }
        )
        self.bot = bot

        # Create fake players table if it doesn't exist
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS fake_player (
            fake_id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER UNIQUE,
            discord_name TEXT,
            sr_mmr INTEGER,
            sr_wins INTEGER,
            sr_losses INTEGER,
            aram_mmr INTEGER,
            aram_wins INTEGER,
            aram_losses INTEGER
        )
        """
        )

        # Create fake match table if it doesn't exist - same structure as regular match table
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS fake_match (
            match_id INTEGER PRIMARY KEY,
            team1 TEXT,
            team2 TEXT,
            winner INTEGER,
            mmr_diff INTEGER,
            timestamp TEXT
        )
        """
        )
        self.connection.commit()

    def get_all_guild_options(self):
        try:
            res = self.cursor.execute(
                "SELECT guild_id, customs_channel FROM guild_options"
            ).fetchall()
            return res
        except Exception as e:
            logger.error(f"Error fetching guild options: {e}")
            return []

    def get_all_matches(self, include_fake=False):
        try:
            # Get real matches
            res = self.cursor.execute(
                "SELECT match_id, team1, team2, winner, mmr_diff, timestamp FROM match"
            ).fetchall()
            matches = []

            for i in res:
                try:
                    team1 = [
                        Player(self.bot, int(player_id)) for player_id in i[1].split()
                    ]
                    team2 = [
                        Player(self.bot, int(player_id)) for player_id in i[2].split()
                    ]
                    matches.append(
                        Match(i[0], team1, team2, i[3], i[4], i[5], is_fake=False)
                    )
                except Exception as e:
                    logger.error(f"Error processing match {i[0]}: {e}")

            # Get fake matches if requested
            if include_fake:
                fake_res = self.cursor.execute(
                    "SELECT match_id, team1, team2, winner, mmr_diff, timestamp FROM fake_match"
                ).fetchall()

                for i in fake_res:
                    try:
                        team1 = [
                            Player(self.bot, int(player_id))
                            for player_id in i[1].split()
                        ]
                        team2 = [
                            Player(self.bot, int(player_id)) for player_id in i[2].split()
                        ]
                        matches.append(
                            Match(i[0], team1, team2, i[3], i[4], i[5], is_fake=True)
                        )
                    except Exception as e:
                        logger.error(f"Error processing fake match {i[0]}: {e}")

            return matches
        except Exception as e:
            logger.error(f"Error fetching matches: {e}")
            return []

    def get_matches(self, discord_id: int, include_fake=False):
        try:
            # Get real matches
            res = self.cursor.execute(
                "SELECT match_id, team1, team2, winner, mmr_diff, timestamp, queue_type FROM match"
            ).fetchall()
            matches = []

            for i in res:
                try:
                    if (
                        str(discord_id) in i[1].split()
                        or str(discord_id) in i[2].split()
                    ):
                        team1 = [
                            Player(self.bot, int(player_id))
                            for player_id in i[1].split()
                        ]
                        team2 = [
                            Player(self.bot, int(player_id))
                            for player_id in i[2].split()
                        ]
                        # Use the queue_type from the database or default to summoners_rift if NULL
                        queue_type = i[6] if len(i) > 6 and i[6] else "summoners_rift"
                        matches.append(
                            Match(i[0], team1, team2, i[3], i[4], i[5], is_fake=False, queue_type=queue_type)
                        )
                except Exception as e:
                    logger.error(
                        f"Error processing match {i[0]} for player {discord_id}: {e}"
                    )

            # Get fake matches if requested or if discord_id is negative (fake player)
            if include_fake or discord_id < 0:
                fake_res = self.cursor.execute(
                    "SELECT match_id, team1, team2, winner, mmr_diff, timestamp, queue_type FROM fake_match"
                ).fetchall()

                for i in fake_res:
                    try:
                        if (
                            str(discord_id) in i[1].split()
                            or str(discord_id) in i[2].split()
                        ):
                            team1 = [
                                Player(self.bot, int(player_id))
                                for player_id in i[1].split()
                            ]
                            team2 = [
                                Player(self.bot, int(player_id))
                                for player_id in i[2].split()
                            ]
                            # Use the queue_type from the database or default to summoners_rift if NULL
                            queue_type = i[6] if len(i) > 6 and i[6] else "summoners_rift"
                            matches.append(
                                Match(
                                    i[0], team1, team2, i[3], i[4], i[5], is_fake=True, queue_type=queue_type
                                )
                            )
                    except Exception as e:
                        logger.error(
                            f"Error processing fake match {i[0]} for player {discord_id}: {e}"
                        )

            return matches
        except Exception as e:
            logger.error(f"Error fetching matches for player {discord_id}: {e}")
            return []

    def get_all_players(self):
        try:
            res = self.cursor.execute("SELECT discord_id FROM player").fetchall()
            players = [Player(self.bot, discord_id=i[0]) for i in res]
            players = [player for player in players if player.user_exists]
            return players
        except Exception as e:
            logger.error(f"Error fetching all players: {e}")
            return []

    def insert_match(self, match: Match):
        try:
            team1_string = " ".join([str(player.discord_id) for player in match.team1])
            team2_string = " ".join([str(player.discord_id) for player in match.team2])

            # Enhanced fake match detection
            # Double-check by looking at player IDs - any negative ID means a fake player
            is_fake = match.is_fake
            if not is_fake:
                for player in match.team1 + match.team2:
                    if player.discord_id < 0:
                        is_fake = True
                        logger.info(
                            f"Found fake player in match {match.match_id}, will store in fake_match table"
                        )
                        break

            # For consistency with the flag on the match object
            match.is_fake = is_fake

            # Choose the appropriate table
            table_name = "fake_match" if is_fake else "match"

            # Log which table we're using for debugging
            logger.info(
                f"Inserting match {match.match_id} into {table_name} table (is_fake: {is_fake})"
            )

            # Get queue type from the first player (all players in a match will have the same queue type)
            queue_type = match.team1[0].queue_type if match.team1 else "summoners_rift"

            insertion = f"INSERT INTO {table_name} (match_id, team1, team2, winner, mmr_diff, timestamp, queue_type) VALUES (?, ?, ?, ?, ?, ?, ?)"
            self.cursor.execute(
                insertion,
                (
                    match.match_id,
                    team1_string,
                    team2_string,
                    match.winner,
                    match.mmr_diff,
                    match.timestamp,
                    queue_type,
                ),
            )
            self.connection.commit()
            logger.info(
                f"Successfully inserted match {match.match_id} into {table_name}"
            )
        except Exception as e:
            logger.error(f"Error inserting match {match.match_id}: {e}")

    def insert_player(self, player: Player):
        try:
            self.cursor.execute(
                "INSERT INTO player (discord_id, sr_mmr, sr_wins, sr_losses, aram_mmr, aram_wins, aram_losses, discord_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    player.discord_id,
                    player.sr_mmr,
                    player.sr_wins,
                    player.sr_losses,
                    player.aram_mmr,
                    player.aram_wins,
                    player.aram_losses,
                    player.discord_name,
                ),
            )
            self.connection.commit()
            logger.info(f"Successfully inserted player {player.discord_id}")
        except Exception as e:
            logger.error(f"Error inserting player {player.discord_id}: {e}")

    def remove_player(self, player: Member):
        try:
            self.cursor.execute("DELETE FROM player WHERE discord_id = ?", (player.id,))
            self.connection.commit()
        except Exception as e:
            logger.error(f"Error removing player {player.id}: {e}")

    def remove_match(self, match_id: int, is_fake=False):
        try:
            table_name = "fake_match" if is_fake else "match"
            self.cursor.execute(
                f"DELETE FROM {table_name} WHERE match_id = ?", (match_id,)
            )
            self.connection.commit()
            logger.info(f"Removed match {match_id} from {table_name}")
        except Exception as e:
            logger.error(f"Error removing match {match_id}: {e}")

            # Try the other table if not found
            try:
                other_table = "match" if is_fake else "fake_match"
                self.cursor.execute(
                    f"DELETE FROM {other_table} WHERE match_id = ?", (match_id,)
                )
                if self.cursor.rowcount > 0:
                    self.connection.commit()
                    logger.info(
                        f"Removed match {match_id} from {other_table} after failed attempt in {table_name}"
                    )
            except Exception as e2:
                logger.error(
                    f"Error removing match {match_id} from {other_table}: {e2}"
                )

    def add_fake_player(
        self, name: str, sr_mmr: int = 1000, sr_wins: int = 0, sr_losses: int = 0, aram_mmr: int = 1000, aram_wins: int = 0, aram_losses: int = 0
    ):
        """Add a fake player to the database"""
        try:
            # Generate a unique negative ID for fake players
            fake_discord_id = -random.randint(100000, 999999)
            while self.cursor.execute(
                "SELECT discord_id FROM fake_player WHERE discord_id = ?",
                (fake_discord_id,),
            ).fetchone():
                fake_discord_id = -random.randint(100000, 999999)

            self.cursor.execute(
                "INSERT INTO fake_player (discord_id, discord_name, sr_mmr, sr_wins, sr_losses, aram_mmr, aram_wins, aram_losses) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (fake_discord_id, name, sr_mmr, sr_wins, sr_losses, aram_mmr, aram_wins, aram_losses),
            )
            self.connection.commit()
            return fake_discord_id
        except Exception as e:
            logger.error(f"Error adding fake player {name}: {e}")
            return None

    def get_fake_players(self):
        """Get all fake players"""
        try:
            return self.cursor.execute("SELECT * FROM fake_player").fetchall()
        except Exception as e:
            logger.error(f"Error fetching fake players: {e}")
            return []

    def remove_fake_player(self, discord_id: int):
        """Remove a fake player by ID"""
        try:
            self.cursor.execute(
                "DELETE FROM fake_player WHERE discord_id = ?", (discord_id,)
            )
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error removing fake player {discord_id}: {e}")
            return False

    def get_fake_matches(self):
        """Get matches directly from the fake_match table"""
        try:
            fake_res = self.cursor.execute(
                "SELECT match_id, team1, team2, winner, mmr_diff, timestamp FROM fake_match"
            ).fetchall()
            matches = []
            for i in fake_res:
                try:
                    team1 = [
                        Player(self.bot, int(player_id)) for player_id in i[1].split()
                    ]
                    team2 = [
                        Player(self.bot, int(player_id)) for player_id in i[2].split()
                    ]
                    matches.append(
                        Match(i[0], team1, team2, i[3], i[4], i[5], is_fake=True)
                    )
                except Exception as e:
                    logger.error(f"Error processing fake match {i[0]}: {e}")
            return matches
        except Exception as e:
            logger.error(f"Error fetching fake matches: {e}")
            return []


class StatisticsGeneralEmbed(Embed):
    def __init__(self, players: list[Player], match_counts_cache=None, queue_type="summoners_rift"):
        queue_type_str = "ARAM" if queue_type == "aram" else "Summoner's Rift"
        super().__init__(title=f"Players - {queue_type_str}", color=0x00FF42)

        # Use provided cache or create empty dict
        match_counts_cache = match_counts_cache or {}
        
        self.add_field(name="Name", value="\n".join([p.discord_name for p in players]))
        self.add_field(
            name="Win rate", value="\n".join([f"{p.win_rate:.1f}%" for p in players])
        )
        self.add_field(
            name="Matches",
            value="\n".join([f"{match_counts_cache.get(p.discord_id, 0)}" for p in players]),
        )
        self.set_footer(text=f"Normal | Queue Type: {queue_type_str}")


class StatisticsGeneralExtEmbed(Embed):
    def __init__(self, players: list[Player], queue_type="summoners_rift"):
        queue_type_str = "ARAM" if queue_type == "aram" else "Summoner's Rift"
        super().__init__(title=f"Players - {queue_type_str}", color=0x00FF42)

        self.add_field(name="Name", value="\n".join([p.discord_name for p in players]))
        self.add_field(name="MMR", value="\n".join([f"{p.mmr}" for p in players]))
        self.add_field(
            name="Rank",
            value="\n".join([f"{p.get_rank()} | {p.get_lp()}%" for p in players]),
        )
        self.set_footer(text=f"Extended | Queue Type: {queue_type_str}")


class StatisticsGeneralView(View):
    def __init__(self, players: list[Player], match_counts_cache=None, aram_match_counts_cache=None):
        super().__init__(timeout=7200)
        self.current_embed_index = 0
        self.current_sort_embed_index = 1
        self.current_embed = None
        self.players = players
        self.queue_type = "summoners_rift"  # Default to Summoner's Rift
        
        # Initialize the match counts caches if provided
        self.match_counts_cache = match_counts_cache or {}
        self.aram_match_counts_cache = aram_match_counts_cache or {}
        
        # Create the initial embed with the appropriate match count cache
        self.current_embed = StatisticsGeneralEmbed(self.players, self.match_counts_cache, queue_type=self.queue_type)
        
        self.view_button = Button(label="Extended", style=ButtonStyle.blurple)
        self.view_button.callback = self._view_callback
        self.add_item(self.view_button)
        
        self.sort_button = Button(label="Sort", style=ButtonStyle.blurple)
        self.sort_button.callback = self._sort_callback
        self.add_item(self.sort_button)
        
        # Add queue type toggle button
        self.queue_button = Button(label="Toggle ARAM Stats", style=ButtonStyle.secondary, row=1)
        self.queue_button.callback = self._toggle_queue_callback
        self.add_item(self.queue_button)
    
    async def _view_callback(self, interaction: Interaction):
        # Show loading animation
        self.view_button.label = "Loading..."
        self.view_button.disabled = True
        await interaction.response.defer()
        
        if not self.match_counts_cache:
                for p in self.players:
                    self.match_counts_cache[p.discord_id] = len(p.get_matches())
        
        if self.current_embed_index == 0:
            self.players = sorted(self.players, key=lambda p: p.discord_name)
            self.current_embed = StatisticsGeneralExtEmbed(self.players, queue_type=self.queue_type)
            self.current_embed_index = 1
            self.current_sort_embed_index = 0
            self.view_button.label = "Normal"
            self.sort_button.label = "Name"
        else:
            self.players = sorted(self.players, key=lambda p: p.discord_name)
            self.current_embed = StatisticsGeneralEmbed(self.players, queue_type=self.queue_type)
            self.current_embed_index = 0
            self.current_sort_embed_index = 1
            self.view_button.label = "Extended"
        # Reset button state
        self.view_button.disabled = False
        
        message = await interaction.original_response()
        await message.edit(embed=self.current_embed, view=self)

    async def _sort_callback(self, interaction: Interaction):
        # First update button to show loading state
        self.sort_button.label = "Sorting..."
        self.sort_button.disabled = True
        await interaction.response.edit_message(view=self)
        
        # Determine the current match counts based on queue type
        current_match_counts = self.aram_match_counts_cache if self.queue_type == "aram" else self.match_counts_cache
        
        # If we don't have match counts for the current queue type, load them
        if not current_match_counts:
            if self.queue_type == "aram":
                self.aram_match_counts_cache = {}
                for p in self.players:
                    # Get matches with queue_type filter for ARAM
                    aram_matches = [m for m in p.get_matches() if getattr(m, "queue_type", "summoners_rift") == "aram"]
                    self.aram_match_counts_cache[p.discord_id] = len(aram_matches)
                current_match_counts = self.aram_match_counts_cache
            else:
                self.match_counts_cache = {}
                for p in self.players:
                    # Get matches with queue_type filter for SR
                    sr_matches = [m for m in p.get_matches() if getattr(m, "queue_type", "summoners_rift") == "summoners_rift"]
                    self.match_counts_cache[p.discord_id] = len(sr_matches)
                current_match_counts = self.match_counts_cache
        
        # Use cached match counts for sorting
        normal_list = [
            sorted(self.players, key=lambda p: p.discord_name),
            sorted(self.players, key=lambda p: -p.win_rate),
            sorted(self.players, key=lambda p: -current_match_counts.get(p.discord_id, 0)),
        ]
        extended_list = [
            sorted(self.players, key=lambda p: -p.mmr),
            sorted(self.players, key=lambda p: p.discord_name),
        ]
        
        # Handle different sort states
        if self.current_embed_index == 1 and self.current_sort_embed_index == 0:
            self.sort_button.label = "MMR"
            self.players = extended_list[0]
            self.current_embed = StatisticsGeneralExtEmbed(self.players, queue_type=self.queue_type)
            self.current_embed_index = 1
            self.current_sort_embed_index = 1
        elif self.current_embed_index == 1 and self.current_sort_embed_index == 1:
            self.sort_button.label = "Name"
            self.players = extended_list[1]
            self.current_embed = StatisticsGeneralExtEmbed(self.players, queue_type=self.queue_type)
            self.current_embed_index = 1
            self.current_sort_embed_index = 0
        elif self.current_embed_index == 0 and self.current_sort_embed_index == 1:
            self.sort_button.label = "Name"
            self.players = normal_list[0]
            self.current_embed = StatisticsGeneralEmbed(self.players, current_match_counts, queue_type=self.queue_type)
            self.current_embed_index = 0
            self.current_sort_embed_index = 2
        elif self.current_embed_index == 0 and self.current_sort_embed_index == 2:
            self.sort_button.label = "Winrate"
            self.players = normal_list[1]
            self.current_embed = StatisticsGeneralEmbed(self.players, current_match_counts, queue_type=self.queue_type)
            self.current_embed_index = 0
            self.current_sort_embed_index = 3
        elif self.current_embed_index == 0 and self.current_sort_embed_index == 3:
            self.sort_button.label = "Matches"
            self.players = normal_list[2]
            self.current_embed = StatisticsGeneralEmbed(self.players, current_match_counts, queue_type=self.queue_type)
            self.current_embed_index = 0
            self.current_sort_embed_index = 1
        
        # Reset button state but with the new label
        self.sort_button.disabled = False
        
        message = await interaction.original_response()
        await message.edit(embed=self.current_embed, view=self)
    
    async def _toggle_queue_callback(self, interaction: Interaction):
        # Show loading state
        self.queue_button.label = "Loading..."
        self.queue_button.disabled = True
        await interaction.response.defer()
        
        # Toggle between Summoner's Rift and ARAM stats
        self.queue_type = "aram" if self.queue_type == "summoners_rift" else "summoners_rift"
        
        # Update players to use the correct queue type stats
        for player in self.players:
            # Update player's queue_type to match the current view
            player.queue_type = self.queue_type
            
            # Reset MMR and win/loss stats to the right queue type values
            if self.queue_type == "aram":
                player.mmr = player.aram_mmr
                player.wins = player.aram_wins
                player.losses = player.aram_losses
            else:  # summoners_rift
                player.mmr = player.sr_mmr
                player.wins = player.sr_wins
                player.losses = player.sr_losses
            
            # Recalculate win rate
            player.win_rate = (
                player.wins / (player.wins + player.losses) * 100
                if player.wins + player.losses > 0
                else 0
            )
        
        # Determine which match count cache to use based on queue type
        current_match_counts = self.aram_match_counts_cache if self.queue_type == "aram" else self.match_counts_cache
        
        # If we don't have match counts for the current queue type, load them
        if not current_match_counts:
            if self.queue_type == "aram":
                self.aram_match_counts_cache = {}
                for p in self.players:
                    # Get matches with queue_type filter for ARAM
                    aram_matches = [m for m in p.get_matches() if getattr(m, "queue_type", "summoners_rift") == "aram"]
                    self.aram_match_counts_cache[p.discord_id] = len(aram_matches)
                current_match_counts = self.aram_match_counts_cache
            else:
                self.match_counts_cache = {}
                for p in self.players:
                    # Get matches with queue_type filter for SR
                    sr_matches = [m for m in p.get_matches() if getattr(m, "queue_type", "summoners_rift") == "summoners_rift"]
                    self.match_counts_cache[p.discord_id] = len(sr_matches)
                current_match_counts = self.match_counts_cache
        
        # Reset the UI state
        self.queue_button.label = "Toggle SR Stats" if self.queue_type == "aram" else "Toggle ARAM Stats"
        self.queue_button.disabled = False
        
        # Sort players by name as default
        self.players = sorted(self.players, key=lambda p: p.discord_name)
        
        # Create the appropriate embed (normal or extended) with the current queue type
        if self.current_embed_index == 0:
            self.current_embed = StatisticsGeneralEmbed(self.players, current_match_counts, queue_type=self.queue_type)
        else:
            self.current_embed = StatisticsGeneralExtEmbed(self.players, queue_type=self.queue_type)
        
        # Update the UI
        message = await interaction.original_response()
        await message.edit(embed=self.current_embed, view=self)


class StatisticsTeamatesEnemiesEmbed(Embed):
    def __init__(
        self,
        player_winrate: int,
        title: str,
        player_stats: list[dict[str, str]],
    ):
        super().__init__(title=title, color=0x00FF42)
        self.add_field(
            name="Name", value="\n".join([player["name"] for player in player_stats])
        )
        self.add_field(
            name="Win rate",
            value="\n".join(
                [
                    f"{((player['wins'] /(1 if player['losses'] + player['wins'] == 0 else player['losses'] + player['wins']))*100):.1f}%"
                    for player in player_stats
                ]
            ),
        )
        self.add_field(
            name="Matches",
            value="\n".join(
                [str(player["losses"] + player["wins"]) for player in player_stats]
            ),
        )
        self.set_footer(text="Average winrate: " + str(round(player_winrate)) + "%")


class StatisticsTeamatesEnemiesView(View):
    def __init__(
        self,
        player_winrate: int,
        teamates: list[dict[str, str]],
        enemies: list[dict[str, str]],
        target_player_name: str,
    ):
        super().__init__(timeout=7200)
        self.player_winrate = player_winrate
        self.teamates = teamates
        self.enemies = enemies
        self.target_player_name = target_player_name
        self.sort_button = Button(label="Enemies", style=ButtonStyle.blurple)
        self.sort_button.callback = self._change_callback
        self.add_item(self.sort_button)

    async def _change_callback(self, interaction: Interaction):
        await interaction.response.defer()
        message = await interaction.original_response()
        if self.sort_button.label == "Enemies":
            self.sort_button.label = "Teamates"
            await message.edit(
                content="",
                embed=StatisticsTeamatesEnemiesEmbed(
                    self.player_winrate,
                    self.target_player_name + " Enemies statistics",
                    self.enemies,
                ),
                view=self,
            )
        else:
            self.sort_button.label = "Enemies"
            await message.edit(
                content="",
                embed=StatisticsTeamatesEnemiesEmbed(
                    self.player_winrate,
                    self.target_player_name + " Teamates statistics",
                    self.teamates,
                ),
                view=self,
            )


class CustomMatch:
    def __init__(self, bot, creator: Member, team1: list[Player], team2: list[Player]):
        self.db = Database(bot)
        self.bot = bot
        self.creator = creator
        self.team1 = team1
        self.team2 = team2
        self.team1_mmr = sum(p.mmr for p in team1)
        self.team2_mmr = sum(p.mmr for p in team2)
        self.average_mmr_gains = 30
        self.mmr_gains_maxed = 1000
        self.mmr_gains_min = 10
        self.min_mmr_gains = 10
        self.winner = None
        self.mmr_diff, self.mmr_diff_scaled = self._calc_mmr_diff()
        self.timestamp = datetime.datetime.now()
        self.match_id = self._gen_match_id()
        # Store the queue_type from the first team player (all players in a team should have same queue_type)
        self.queue_type = getattr(team1[0], "queue_type", "summoners_rift") if team1 else "summoners_rift"

        # Improved detection of fake players - check if any player is a fake player
        # Check both for the is_fake attribute and for negative discord_ids
        self.is_fake = False
        for player in team1 + team2:
            if hasattr(player, "is_fake") and player.is_fake:
                self.is_fake = True
                break
            if player.discord_id < 0:  # Fake players have negative IDs
                self.is_fake = True
                break

        logger.info(f"Created match {self.match_id} (is_fake: {self.is_fake}, queue_type: {self.queue_type})")

    def _calc_mmr_diff(self) -> list[int, int]:
        mmr_diff = self.team1_mmr - self.team2_mmr
        # 0.1 to 1
        mmr_diff_maxed = (
            max(min(abs(mmr_diff), self.mmr_gains_maxed), self.mmr_gains_min)
            / self.mmr_gains_maxed
        )
        # 0.01 to 1
        mmr_diff_powed = mmr_diff_maxed**2
        mmr_diff_scaled = math.ceil((mmr_diff_powed + 1) * self.average_mmr_gains)
        return [mmr_diff, mmr_diff_scaled]

    def _gen_match_id(self) -> int:
        # Query both real and fake match tables
        real_matches = self.db.cursor.execute("SELECT match_id FROM match").fetchall()
        fake_matches = self.db.cursor.execute(
            "SELECT match_id FROM fake_match"
        ).fetchall()
        match_ids = [i[0] for i in real_matches + fake_matches]
        match_id = random.randint(100000, 999999)
        while match_id in match_ids:
            match_id = random.randint(10000000, 99999999)
        return match_id

    def finish_match(self, winner: int):
        #   Predicted team wins -> small mmr gains/losses
        #   Predicted team loses -> Large mmr gains/losses
        if (self.team1_mmr > self.team2_mmr and winner == 1) or (
            self.team1_mmr < self.team2_mmr and winner == 2
        ):
            mmr_gains = (
                self.average_mmr_gains * 2 - self.mmr_diff_scaled + self.min_mmr_gains
            )
        else:
            mmr_gains = self.mmr_diff_scaled + self.min_mmr_gains

        for player in self.team1 + self.team2:
            # Skip MMR updates for real players in fake matches
            if self.is_fake and not (hasattr(player, "is_fake") and player.is_fake):
                logger.info(
                    f"Skipping MMR update for real player {player.discord_name} in fake match"
                )
                continue

            if (player in self.team1 and winner == 1) or (
                player in self.team2 and winner == 2
            ):
                player.mmr += mmr_gains
                player.wins += 1
                # Update the specific MMR field based on queue type
                if player.queue_type == "aram":
                    player.aram_mmr = player.mmr
                    player.aram_wins = player.wins
                else:
                    player.sr_mmr = player.mmr
                    player.sr_wins = player.wins
            else:
                player.mmr -= mmr_gains
                player.losses += 1
                # Update the specific MMR field based on queue type
                if player.queue_type == "aram":
                    player.aram_mmr = player.mmr
                    player.aram_losses = player.losses
                else:
                    player.sr_mmr = player.mmr
                    player.sr_losses = player.losses
            player.update()

        self.db.insert_match(
            Match(
                self.match_id,
                self.team1,
                self.team2,
                winner,
                self.mmr_diff,
                self.timestamp,
                is_fake=self.is_fake,
                queue_type=self.team1[0].queue_type if self.team1 else "summoners_rift"
            )
        )
        return mmr_gains


class MatchEmbed(Embed):
    def __init__(self, team1: list[Player], team2: list[Player], match_creator: Member):
        super().__init__(title="Match in progress", color=0x00FF42)

        self.add_field(
            name=f"Blue Team ({int(sum([p.mmr for p in team1]))})",
            value="\n".join([p.discord_name for p in team1]),
        )
        self.add_field(
            name=f"Red Team ({int(sum([p.mmr for p in team2]))})",
            value="\n".join([p.discord_name for p in team2]),
        )
        self.set_footer(text=f"Creator: {match_creator.name}")


class MatchControlView(View):  # ändra till playersembed
    def __init__(
        self,
        bot: discord.client.Client,
        guild: Guild,
        match: CustomMatch,
        match_message: Message,
        match_embed: Embed,
        ingame_ping_message: Message | None,
        creator: Member = None,
    ):
        super().__init__(timeout=7200)
        self.current_embed = None
        self.bot = bot
        self.match = match
        self.match_message = match_message
        self.match_embed = match_embed
        self.ingame_ping_message = ingame_ping_message
        self.creator = creator
        config = ConfigDatabase(bot)
        try:
            ingame_role = config.get_items_by(ConfigTables.INGAMEROLE, guild.id)
            if len(ingame_role) > 0:
                self.ingame_role = guild.get_role(ingame_role[0])
            else:
                self.ingame_role = None
        except Exception as e:
            logger.error(f"Error setting up ingame role: {e}")
            self.ingame_role = None

        blue_win_button = Button(label="Blue Win", style=ButtonStyle.green)
        blue_win_button.callback = self._blue_win_callback
        self.add_item(blue_win_button)

        red_win_button = Button(label="Red Win", style=ButtonStyle.green)
        red_win_button.callback = self._red_win_callback
        self.add_item(red_win_button)

        discard_button = Button(label="Discard", style=ButtonStyle.red, row=2)
        discard_button.callback = self._discard_callback
        self.add_item(discard_button)

    async def _blue_win_callback(self, interaction: Interaction):
        if interaction.user != self.creator:
            await interaction.response.send_message(
                "You are not authorized to use this button.", ephemeral=True
            )
            return
        await interaction.response.defer()
        try:
            await self.remove_ingame_role(interaction)
            mmr_gains = self.match.finish_match(1)
            self.match_embed.title = f"Winner: Blue Team(+/- {mmr_gains})"
            await self.match_message.edit(embed=self.match_embed)

            message = await interaction.original_response()
            await message.edit(
                view=MatchViewDone(self.bot, self.match),
            )
        except Exception as e:
            logger.error(f"Error in blue win callback: {e}")
            try:
                await interaction.followup.send(
                    f"An error occurred while processing the blue team win: {e}",
                    ephemeral=True,
                )
            except Exception:
                pass

    async def _red_win_callback(self, interaction: Interaction):
        if interaction.user != self.creator:
            await interaction.response.send_message(
                "You are not authorized to use this button.", ephemeral=True
            )
            return
        await interaction.response.defer()
        try:
            await self.remove_ingame_role(interaction)
            mmr_gains = self.match.finish_match(2)
            self.match_embed.title = f"Winner: Red Team(+/- {mmr_gains})"
            await self.match_message.edit(embed=self.match_embed)

            message = await interaction.original_response()
            await message.edit(
                view=MatchViewDone(self.bot, self.match),
            )
        except Exception as e:
            logger.error(f"Error in red win callback: {e}")
            try:
                await interaction.followup.send(
                    f"An error occurred while processing the red team win: {e}",
                    ephemeral=True,
                )
            except Exception:
                pass

    async def _discard_callback(self, interaction: Interaction):
        if interaction.user != self.creator:
            await interaction.response.send_message(
                "You are not authorized to use this button.", ephemeral=True
            )
            return
        await interaction.response.defer()
        try:
            await self.remove_ingame_role(interaction)
            # Delete the match message
            await self.match_message.delete()
            
            # Delete the control panel message as well
            message = await interaction.original_response()
            await message.delete()
        except Exception as e:
            logger.error(f"Error in discard callback: {e}")
            try:
                await interaction.followup.send(
                    f"An error occurred while discarding the match: {e}", ephemeral=True
                )
            except Exception:
                pass

    async def remove_ingame_role(self, interaction: Interaction):
        if not self.ingame_role:
            return
        try:
            player_ids = [
                player.discord_id for player in self.match.team1 + self.match.team2
            ]
            for player_id in player_ids:
                try:
                    user = interaction.guild.get_member(player_id)
                    if user and self.ingame_role in user.roles:
                        await user.remove_roles(self.ingame_role)
                except Exception as e:
                    logger.error(f"Error removing role from user {player_id}: {e}")
        except Exception as e:
            logger.error(f"Error removing ingame roles: {e}")


class MatchViewDone(View):
    def __init__(self, bot: commands.Bot, match: CustomMatch):
        super().__init__(timeout=7200)
        self.current_embed = None
        self.bot = bot
        self.match = match
        self.keep_same_teams = False  # Default to generating new teams

        rematch_button = Button(label="Rematch", style=ButtonStyle.green)
        rematch_button.callback = self._rematch_callback
        self.add_item(rematch_button)
        
        # Toggle button for keeping same teams
        toggle_teams_button = Button(
            label="Same Teams: Off", 
            style=ButtonStyle.secondary, 
            row=1
        )
        toggle_teams_button.callback = self._toggle_teams_callback
        self.add_item(toggle_teams_button)

    async def _rematch_callback(self, interaction: Interaction):
        await interaction.response.defer()
        
        # Get the queue type from the match object's team1 first player
        # Make sure to use queue_type from the match object, not just the player
        queue_type = self.match.queue_type
        
        # If queue_type is not available in the match object, try to get it from first player
        if not queue_type and self.match.team1:
            queue_type = getattr(self.match.team1[0], "queue_type", "summoners_rift")
        
        if self.keep_same_teams:
            # Use the exact same teams
            await start_match(
                self.match.team1,
                self.match.team2,
                self.bot,
                interaction.guild,
                self.match.creator,
                interaction.channel,
                interaction,
                queue_type=queue_type
            )
        else:
            # Combine all players from both teams
            all_players = self.match.team1 + self.match.team2
            
            # Generate fresh teams
            team1, team2 = generate_teams(all_players)
            
            # Start match with new teams, passing the queue_type
            await start_match(
                team1,
                team2,
                self.bot,
                interaction.guild,
                self.match.creator,
                interaction.channel,
                interaction,
                queue_type=queue_type
            )
    
    async def _toggle_teams_callback(self, interaction: Interaction):
        self.keep_same_teams = not self.keep_same_teams
        status = "On" if self.keep_same_teams else "Off"
        style = ButtonStyle.primary if self.keep_same_teams else ButtonStyle.secondary
        
        # Update button label and style
        for item in self.children:
            if isinstance(item, Button) and item.callback == self._toggle_teams_callback:
                item.label = f"Same Teams: {status}"
                item.style = style
                break
                
        await interaction.response.edit_message(view=self)


class QueueEmbed(Embed):
    def __init__(
        self, queue: list[Player], vc_members_names: list[str], creator: Member, queue_type: str = "summoners_rift"
    ):
        title_prefix = "ARAM" if queue_type == "aram" else "SR"
        super().__init__(title=f"{title_prefix} Queue {len(queue)}p", color=0x00FF42)
        self.creator = creator
        self.queue_type = queue_type

        # Format player names - highlight fake players with [BOT] tag
        players_formatted = []
        for p in queue:
            if hasattr(p, "is_fake") and p.is_fake:
                players_formatted.append(f"{p.discord_name} [BOT]")
            else:
                players_formatted.append(p.discord_name)

        self.add_field(
            name="Players",
            value=(
                "\n".join(players_formatted)
                if players_formatted
                else "No players in queue"
            ),
        )

        # Filter out both real and fake players from VC list
        vc_players_not_in_queue = [
            m
            for m in vc_members_names
            if m not in [p.discord_name for p in queue] and m not in players_formatted
        ]

        self.add_field(
            name="VC",
            value=(
                "\n".join(vc_players_not_in_queue)
                if vc_players_not_in_queue
                else "No one in VC"
            ),
        )
        queue_type_str = "ARAM" if queue_type == "aram" else "Summoner's Rift"
        self.set_footer(text=f"Creator: {creator.name} | Queue Type: {queue_type_str}")


class QueueView(View):
    def __init__(self, bot, voice_channel: VoiceChannel | None, queue_type: str = "summoners_rift"):
        super().__init__(timeout=10800)  # I think 3 hours
        self.db = Database(bot)
        self.bot = bot
        self.voice_channel = voice_channel
        self.queue: list[Member] = []
        self.queue_type = queue_type

        join_queue_button = Button(label="Join Queue", style=ButtonStyle.green)
        join_queue_button.callback = self._join_queue_callback
        self.add_item(join_queue_button)

        leave_queue_button = Button(label="Leave Queue", style=ButtonStyle.red)
        leave_queue_button.callback = self._leave_queue_callback
        self.add_item(leave_queue_button)

    async def _update_queue_embed(self, interaction: Interaction):
        vc_members_names = (
            [m.name for m in self.voice_channel.members]
            if self.voice_channel != None
            else []
        )

        # Extract the creator name from the footer text
        footer_text = interaction.message.embeds[0].footer.text
        creator_name = footer_text.split('|')[0].replace('Creator:', '').strip()

        # Convert queue member list to Player objects with proper queue_type
        queue_players = []
        for member in self.queue:
            if hasattr(member, "is_fake") and hasattr(member, "_player"):
                # For fake players, use the stored Player object
                queue_players.append(member._player)
            else:
                # For real players, create a new Player object with the correct queue_type
                queue_players.append(Player(self.bot, member.id, queue_type=self.queue_type))

        await interaction.message.edit(
            embed=QueueEmbed(
                queue_players,
                vc_members_names,
                Player(
                    self.bot,
                    discord_name=creator_name,
                ).get_discord_object(),
                queue_type=self.queue_type,
            ),
        )

    async def _leave_queue_callback(self, interaction: Interaction):
        await interaction.response.defer()
        if interaction.user in self.queue:
            self.queue.remove(interaction.user)
        await self._update_queue_embed(interaction)

    async def _join_queue_callback(self, interaction: Interaction):
        await interaction.response.defer()
        if interaction.user not in self.queue:
            self.queue.append(interaction.user)
        await self._update_queue_embed(interaction)


class RemovePlayerFromQueueSelect(Select):
    def __init__(
        self,
        bot: commands.Bot,
        players: list[Member],
        queue_message: Message,
        queue_view: QueueView,
        voice: VoiceChannel = None,
    ):
        options = [SelectOption(label="Noone", description="Remove Noone")] + [
            SelectOption(label=p.name) for p in players
        ]
        super().__init__(
            placeholder="Select player to remove",
            custom_id="remove_queue_select",
            max_values=1,
            min_values=1,
            options=options,
            row=2,
        )
        self.bot = bot
        self.queue_message = queue_message
        self.queue_view = queue_view
        self.voice = voice

    async def callback(self, interaction: Interaction):
        self.queue_view.queue = [
            p for p in self.queue_view.queue if p.name != interaction.data["values"][0]
        ]
        if self.voice:
            vc_members_names = [m.name for m in self.voice.members]
        else:
            vc_members_names = []
            
        # Extract just the creator name and queue_type from footer text
        footer_text = self.queue_message.embeds[0].footer.text
        creator_name = footer_text.split('|')[0].replace('Creator:', '').strip()
        queue_type = "aram" if "ARAM" in footer_text else "summoners_rift"
        
        # Create Player objects with proper queue type
        queue_players = []
        for member in self.queue_view.queue:
            if hasattr(member, "is_fake") and hasattr(member, "_player"):
                queue_players.append(member._player)
            else:
                try:
                    queue_players.append(Player(self.bot, member.id, queue_type=queue_type))
                except:
                    continue
        
        creator = Player(self.bot, discord_name=creator_name).get_discord_object()
        
        await self.queue_message.edit(
            embed=QueueEmbed(
                queue_players,
                vc_members_names,
                creator,
                queue_type=queue_type
            )
        )
        
        await interaction.response.edit_message(
            view=QueueControlView(
                self.bot,
                self.queue_message,
                self.queue_view,
                voice=self.voice,
                creator=creator,
            )
        )


class QueueControlView(View):
    def __init__(
        self,
        bot: commands.Bot,
        queue_message: Message,
        queue_view: QueueView,
        voice: VoiceChannel | None = None,
        creator: Member = None,
    ):
        super().__init__(timeout=10800)  # I think 3 hours
        self.db = Database(bot)
        self.bot = bot
        self.queue_message = queue_message
        self.queue_view = queue_view
        self.voice = voice
        self.creator = creator
        self.move_players = False

        start_button = Button(
            label="Start match",
            style=ButtonStyle.green,
            row=0,
        )
        start_button.callback = self._start_callback
        self.add_item(start_button)

        discard_button = Button(
            label="Discard",
            style=ButtonStyle.red,
            row=0,
        )
        discard_button.callback = self._discard_callback
        self.add_item(discard_button)
        
        # Add a button to toggle the move players setting
        move_players_button = Button(
            label="Toggle Voice Split: Off",
            style=ButtonStyle.secondary,
            row=1,
        )
        move_players_button.callback = self._toggle_move_players
        self.add_item(move_players_button)
        
        # Add a clear queue button
        clear_queue_button = Button(
            label="Clear Queue",
            style=ButtonStyle.danger,
            row=1,
        )
        clear_queue_button.callback = self._clear_queue_callback
        self.add_item(clear_queue_button)
        
        update_remove_list_button = Button(
            label="Update remove list",
            style=ButtonStyle.blurple,
            row=3,
        )
        update_remove_list_button.callback = self._update_remove_list_callback
        self.add_item(update_remove_list_button)

        if len(self.queue_view.queue) > 0:
            self.add_item(
                RemovePlayerFromQueueSelect(
                    self.bot,
                    self.queue_view.queue,
                    self.queue_message,
                    self.queue_view,
                    self.voice,
                )
            )
    async def _toggle_move_players(self, interaction: Interaction):
        self.move_players = not self.move_players
        status = "On" if self.move_players else "Off"
        style = ButtonStyle.primary if self.move_players else ButtonStyle.secondary
        
        # Update button label and style
        for item in self.children:
            if isinstance(item, Button) and item.callback == self._toggle_move_players:
                item.label = f"Toggle Voice Split: {status}"
                item.style = style
                break
                
        await interaction.response.edit_message(view=self)
    
    async def _start_callback(self, interaction: Interaction):
        if interaction.user != self.creator:
            await interaction.response.send_message(
                "You are not authorized to use this button.", ephemeral=True
            )
            return
        if len(self.queue_view.queue) < 2:
            await interaction.response.send_message(
                "Not enough players in queue", ephemeral=True
            )
            return
        
        # Update button to show loading state
        for item in self.children:
            if isinstance(item, Button) and item.callback == self._start_callback:
                item.label = "Creating teams..."
                item.disabled = True
                break
        
        # Show the updated button immediately
        await interaction.response.edit_message(view=self)
        
        # Extract queue type from the footer text
        footer_text = self.queue_message.embeds[0].footer.text
        queue_type = "aram" if "ARAM" in footer_text else "summoners_rift"
        
        # Convert queue members to Players, handling both real and fake players
        queue_players = []
        for member in self.queue_view.queue:
            if hasattr(member, "is_fake") and hasattr(member, "_player"):
                # For fake players, use the stored Player object
                queue_players.append(member._player)
            else:
                # For real players, create a new Player object with the correct queue_type
                queue_players.append(Player(self.bot, member.id, queue_type=queue_type))

        team1, team2 = generate_teams(queue_players)
        
        await start_match(
            team1,
            team2,
            self.bot,
            interaction.guild,
            interaction.user,
            interaction.channel,
            interaction,
            move_players_setting=self.move_players,
            queue_type=queue_type
        )
        # Reset the button after generating teams
        for item in self.children:
            if isinstance(item, Button) and item.callback == self._start_callback:
                item.label = "Start match"
                item.disabled = False
                break
        # Update the UI with reset button
        await interaction.edit_original_response(view=self)

    async def _discard_callback(self, interaction: Interaction):
        if interaction.user != self.creator:
            await interaction.response.send_message(
                "You are not authorized to use this button.", ephemeral=True
            )
            return
        await interaction.response.defer()
        await self.queue_message.delete()

    async def _clear_queue_callback(self, interaction: Interaction):
        if interaction.user != self.creator:
            await interaction.response.send_message(
                "You are not authorized to use this button.", ephemeral=True
            )
            return
        await interaction.response.defer()
        
        # Clear the queue
        self.queue_view.queue.clear()
        
        # Get current voice channel members if available
        vc_members_names = (
            [m.name for m in self.voice.members] if self.voice else []
        )
        
        # Extract creator name and queue type from footer
        footer_text = self.queue_message.embeds[0].footer.text
        creator_name = footer_text.split('|')[0].replace('Creator:', '').strip()
        queue_type = "aram" if "ARAM" in footer_text else "summoners_rift"
        
        # Get creator discord object
        creator = Player(self.bot, discord_name=creator_name).get_discord_object()
        
        # Update the queue message with empty player list
        await self.queue_message.edit(
            embed=QueueEmbed([], vc_members_names, creator, queue_type=queue_type)
        )
        
        # Create a new control view with updated (empty) select menu
        new_view = QueueControlView(
            self.bot,
            self.queue_message,
            self.queue_view,
            voice=self.voice,
            creator=self.creator,
        )
        
        # Update the control panel with the new view
        await interaction.edit_original_response(view=new_view)

    async def _update_remove_list_callback(self, interaction: Interaction):
        if interaction.user != self.creator:
            await interaction.response.send_message(
                "You are not authorized to use this button.", ephemeral=True
            )
            return
        await interaction.response.defer()
        
        # Create new options for the remove player select
        new_view = QueueControlView(
            self.bot,
            self.queue_message,
            self.queue_view,
            voice=self.voice,
            creator=self.creator,
        )
        
        # Only update the interaction response, not the queue message itself
        await interaction.edit_original_response(view=new_view)


async def start_match(
    team1: list[Player],
    team2: list[Player],
    bot: commands.Bot,
    guild: Guild,
    creator: Member,
    channel: TextChannel,
    interaction: Interaction,
    move_players_setting=False,
    queue_type="summoners_rift",
):
    # First, clean up old match controls and winner messages, but only for the same queue type
    try:
        async for message in channel.history(limit=50):
            if message.author == bot.user:
                # Check if it's a match control message
                if message.content == "Match Control":
                    # Need to check the associated match message to determine the queue type
                    # Search for a match message that was posted right before this control message
                    async for potential_match_message in channel.history(limit=5, before=message):
                        if (potential_match_message.author == bot.user and 
                            potential_match_message.embeds and 
                            potential_match_message.embeds[0].title):
                            
                            # Check for match queue type
                            match_type = "aram" if "ARAM" in potential_match_message.embeds[0].footer.text else "summoners_rift"
                            
                            # Only delete if it's the same queue type
                            if match_type == queue_type:
                                await message.delete()
                                logger.info(f"Deleted old {queue_type} match control message")
                            break
                    
                # Check if it's a match result message (with "Winner:" in the title)
                elif message.embeds and message.embeds[0].title and "Winner:" in message.embeds[0].title:
                    # Determine if this is from the same queue type
                    match_type = "aram" if "ARAM" in message.embeds[0].footer.text else "summoners_rift"
                    
                    # Only delete if it's the same queue type
                    if match_type == queue_type:
                        await message.delete()
                        logger.info(f"Deleted old {queue_type} match result message")
    except Exception as e:
        logger.error(f"Error cleaning up old match messages: {e}")

    # Ensure all players have the correct queue_type
    for player in team1 + team2:
        player.queue_type = queue_type
    
    match = CustomMatch(bot, creator, team1, team2)
    config = ConfigDatabase(bot)

    # Add players to ingame role if configured
    ingame_role = config.get_items_by(ConfigTables.INGAMEROLE, guild.id)
    logger.info(ingame_role)
    if len(ingame_role) > 0:
        ingame_role = guild.get_role(ingame_role[0])
        
        # First add the ingame role to each player BEFORE sending the ping
        for player in team1 + team2:
            player_discord_object = player.get_discord_object()
            try:
                if ingame_role not in player_discord_object.roles:
                    await player_discord_object.add_roles(ingame_role)
            except discord.errors.Forbidden:
                logger.warning(
                    f"Missing permissions to add ingame role to {player_discord_object.display_name}. "
                    f"Please ensure the bot has 'Manage Roles' permission and its role is higher than {ingame_role.name}."
                )
            except Exception as e:
                logger.error(f"Error adding ingame role to player: {e}")
        
        # Now send the ping message after roles are assigned
        ingame_ping_message = await channel.send(f"<@&{ingame_role.id}>")
        
        # Delete the ping message after delay
        try:
            await ingame_ping_message.delete()
            # Since we're deleting the message, set it to None
            ingame_ping_message = None
        except Exception as e:
            logger.error(f"Error deleting ingame ping message: {e}")
    else:
        ingame_ping_message = None

    # Send the match embed
    embed = MatchEmbed(team1, team2, creator)
    
    # Add queue type to the footer
    queue_type_display = "ARAM" if queue_type == "aram" else "Summoner's Rift"
    embed.set_footer(text=f"Creator: {creator.name} | Mode: {queue_type_display}")
    
    match_message = await channel.send(embed=embed)

    # Create the match control view
    view = MatchControlView(
        bot, guild, match, match_message, embed, ingame_ping_message, creator=creator
    )

    # Send the control panel to the creator as a normal message
    try:
        await channel.send("Match Control", view=view)
    except Exception as e:
        logger.error(f"Couldn't send match control to channel: {e}")

    # Move players to voice channels if configured
    categories = config.get_items_by(ConfigTables.BETTERVC, guild.id)
    if len(categories) != 0 and move_players_setting:
        try:
            bettervc_category_obj = bot.get_channel(int(categories[0]))
            if bettervc_category_obj:
                bettervc_channels = bettervc_category_obj.channels
                for voice_channel in bettervc_channels:
                    if len(voice_channel.members) == 0 and voice_channel.name[0] != "|":
                        for p in team1:
                            discord_obj = p.get_discord_object()
                            if discord_obj and discord_obj.voice:
                                await discord_obj.move_to(voice_channel)
                        break
        except Exception as e:
            logger.error(f"Error moving players to voice channels: {e}")

    # Generate and send draft links ONLY for Summoner's Rift matches
    if queue_type == "summoners_rift":
        draft_message = "League draft links \n Not showed when in dev"
        try:
            if os.environ["DEV"] != "True":
                draftlolws = draftlol.DraftLolWebSocket()
                draftlolws.run()

                retries = 0
                while not draftlolws.closed and retries < 10:
                    time.sleep(0.5)
                    retries += 1

                draftlolws.force_close()
                draft_message = draftlolws.message
                
                # Send the draft links
                await channel.send(draft_message)
        except Exception as e:
            logger.error(f"Error generating draft links: {e}")
            await channel.send(f"League draft links \nError: {str(e)}")
    
    return match_message


class FreeEmbed(Embed):
    def __init__(self, team1: list[Member], team2: list[Member], creator: Member):
        super().__init__(title="Create teams", color=0x00FF42)

        self.add_field(name="Team 1", value="\n".join([p.name for p in team1]))
        self.add_field(name="Team 2", value="\n".join([p.name for p in team2]))
        self.set_footer(text=f"Creator: {creator.name}")


class FreeView(View):
    def __init__(self, bot: commands.Bot, creator: Member):
        super().__init__(timeout=10800)
        self.bot = bot
        self.creator = creator
        self.team1: list[Member] = []
        self.team2: list[Member] = []

        join_team1_button = Button(label="Join team 1", style=ButtonStyle.blurple)
        join_team1_button.callback = self._join_team1_callback
        self.add_item(join_team1_button)

        join_team2_button = Button(label="Join team 2", style=ButtonStyle.blurple)
        join_team2_button.callback = self._join_team2_callback
        self.add_item(join_team2_button)

        start_button = Button(label="Start match", style=ButtonStyle.green, row=2)
        start_button.callback = self._start_callback
        self.add_item(start_button)

        discard_button = Button(label="Discard", style=ButtonStyle.red, row=2)
        discard_button.callback = self._discard_callback
        self.add_item(discard_button)

    async def _update_teams(self, interaction: Interaction):
        message = await interaction.original_response()
        await message.edit(
            embed=FreeEmbed(self.team1, self.team2, self.creator), view=self
        )

    async def _join_team1_callback(self, interaction: Interaction):
        await interaction.response.defer()
        if interaction.user in self.team1:
            self.team1.remove(interaction.user)
        elif interaction.user in self.team2:
            self.team2.remove(interaction.user)
            self.team1.append(interaction.user)
        else:
            self.team1.append(interaction.user)
        await self._update_teams(interaction)

    async def _join_team2_callback(self, interaction: Interaction):
        await interaction.response.defer()
        if interaction.user in self.team2:
            self.team2.remove(interaction.user)
        elif interaction.user in self.team1:
            self.team1.remove(interaction.user)
            self.team2.append(interaction.user)
        else:
            self.team2.append(interaction.user)
        await self._update_teams(interaction)

    async def _start_callback(self, interaction: Interaction):
        await interaction.response.defer()
        if len(self.team1) < 1 or len(self.team2) < 1:
            await interaction.followup.send(
                "Not enough players in queue", ephemeral=True
            )
            return
        player_team1 = [Player(self.bot, p.id, False) for p in self.team1]
        player_team2 = [Player(self.bot, p.id, False) for p in self.team2]

        await start_match(
            player_team1,
            player_team2,
            self.bot,
            interaction.guild,
            self.creator,
            interaction.channel,
            interaction,
        )
        await interaction.message.delete()

    async def _discard_callback(self, interaction: Interaction):
        await interaction.message.delete()


class PlayerMatchesView(View):
    def __init__(self, embeds):
        super().__init__(timeout=7200)
        self.embeds = embeds
        self.current_embed = None
        self.current_index = 0

        self.previous_button = Button(label="Previous", style=ButtonStyle.blurple)
        self.previous_button.callback = self._previous_callback
        self.add_item(self.previous_button)

        self.next_button = Button(label="Next", style=ButtonStyle.blurple)
        self.next_button.callback = self._next_callback
        self.add_item(self.next_button)

        # Disable previous button initially if we start at the first embed
        if len(embeds) <= 1:
            self.previous_button.disabled = True
            self.next_button.disabled = True
        else:
            self.previous_button.disabled = True
            self.current_embed = self.embeds[self.current_index]

    async def _previous_callback(self, interaction: Interaction):
        await interaction.response.defer()
        self.next_button.disabled = False
        if self.current_embed is None:
            self.current_embed = interaction.message.embeds[0]
            self.current_index = self.embeds.index(self.current_embed)
        # Check if we can go to the previous embed
        if self.current_index > 0:
            self.current_index -= 1
            self.current_embed = self.embeds[self.current_index]

            # Enable next button since we can now go forward
            self.next_button.disabled = False

            # Disable previous button if we reached the first embed
            if self.current_index == 0:
                self.previous_button.disabled = True

            message = await interaction.original_response()
            await message.edit(embed=self.current_embed, view=self)

    async def _next_callback(self, interaction: Interaction):
        await interaction.response.defer()
        self.previous_button.disabled = False
        if self.current_embed is None:
            self.current_embed = interaction.message.embeds[0]
            self.current_index = self.embeds.index(self.current_embed)
        # Check if we can go to the next embed
        if self.current_index < len(self.embeds) - 1:
            self.current_index += 1
            self.current_embed = self.embeds[self.current_index]

            # Enable previous button since we can now go back
            self.previous_button.disabled = False

            # Disable next button if we reached the last embed
            if self.current_index == len(self.embeds) - 1:
                self.next_button.disabled = True

            message = await interaction.original_response()
            await message.edit(embed=self.current_embed, view=self)


class MmrGraphEmbed(Embed):
    def __init__(self, bot: commands.Bot, player: Member):
        super().__init__(title=f"MMR Graph for {player.name}", color=0x00FF42)
        self.set_image(url=f"attachment://{os.environ['LEAGUE_GRAPH_FILENAME']}")
        self.set_footer(text=f"Current mmr {Player(bot, discord_id=player.id).mmr} ")


def mmr_graph(bot, player: Member):
    db = Database(bot)
    res = db.cursor.execute(
        f"SELECT mmr, timestamp FROM mmr_history WHERE discord_id = {player.id}"
    ).fetchall()
    df = pd.DataFrame(res)
    fig = px.line(df, x=1, y=0)
    fig.write_image(
        os.environ["LEAGUE_GRAPH_DIR"] + os.environ["LEAGUE_GRAPH_FILENAME"]
    )
    file = discord.File(
        os.environ["LEAGUE_GRAPH_DIR"] + os.environ["LEAGUE_GRAPH_FILENAME"],
        os.environ["LEAGUE_GRAPH_FILENAME"],
    )
    return file


def generate_teams(players: list[Player]) -> tuple[list[Player], list[Player]]:
    num_players = len(players)
    team_size = num_players // 2
    if num_players > 10:
        raise ValueError("numplayers > 10")
    combination_list = list(combinations(range(num_players), team_size))
    random.shuffle(combination_list)
    best_diff = float("inf")
    best_teams = None

    for team1_indices in combination_list:
        team1 = [players[i] for i in team1_indices]
        team2 = [players[i] for i in range(num_players) if i not in team1_indices]
        team1_mmr = sum(player.mmr for player in team1)
        team2_mmr = sum(player.mmr for player in team2)
        diff = abs(team1_mmr - team2_mmr)
        if diff < best_diff:
            best_teams = (team1, team2)
            best_diff = diff
        if diff < 100:
            return (team1, team2)

    return best_teams
