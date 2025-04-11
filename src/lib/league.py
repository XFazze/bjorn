import os
import datetime
import random
import discord
import logging
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
    ):
        self.db = Database(bot)
        self.bot = bot
        self.user_exists = False  # If the user has not been deleted

        if discord_id != None:
            self.discord_id = discord_id
            user = self.bot.get_user(discord_id)
            if user != None:  # In case user doesnt exists
                self.discord_name = user.name
                self.user_exists = True
            else:
                return
        elif discord_name != None:
            discord_member_object = next(
                (m for m in self.bot.get_all_members() if m.name == discord_name), None
            )
            if discord_member_object is None:
                raise Exception(f"No user with discord name{discord_name}")

            discord_id = discord_member_object.id
            self.discord_name = discord_name

        existing_player = self.db.cursor.execute(
            f"SELECT discord_id, mmr, wins, losses FROM player WHERE discord_id = {discord_id}"
        ).fetchone()

        self.discord_id = discord_id

        self.mmr = math.ceil(existing_player[1]) if existing_player else 1000
        self.wins = existing_player[2] if existing_player else 0
        self.losses = existing_player[3] if existing_player else 0
        self.win_rate = (
            self.wins / (self.wins + self.losses) * 100
            if self.wins + self.losses > 0
            else 0
        )

        if not existing_player:
            self.db.insert_player(self)

    def set_mmr(self, mmr):
        self.db.cursor.execute(
            f"UPDATE player SET mmr = {mmr} WHERE discord_id = {self.discord_id}"
        )
        self.db.connection.commit()
        self.mmr = mmr

    def update(self):
        self.db.cursor.execute(
            f"UPDATE player SET mmr = {self.mmr}, wins = {self.wins}, losses = {self.losses} WHERE discord_id = {self.discord_id}"
        )
        self.db.connection.commit()

        insertion = (
            f"INSERT INTO mmr_history (discord_id, mmr, timestamp) VALUES (?, ?, ?)"
        )
        self.db.cursor.execute(
            insertion, (self.discord_id, self.mmr, datetime.datetime.now())
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
        return next(
            (m for m in self.bot.get_all_members() if m.id == self.discord_id), None
        )

    def get_matches(self):
        return self.db.get_matches(self.discord_id)


class Match:
    def __init__(
        self,
        match_id: int,
        team1: list[Player],
        team2: list[Player],
        winner: int,  # 1 or 2
        mmr_diff: int,
        timestamp: datetime.datetime,
    ):
        self.match_id = match_id
        self.team1 = team1
        self.team2 = team2
        self.winner = winner
        self.mmr_diff = mmr_diff
        self.timestamp = timestamp


class Database(general.Database):
    def __init__(self, bot: commands.Bot):
        super().__init__(os.environ["LEAGUE_DB_NAME"])
        self.create_tables(
            {
                "player": ["discord_id", "mmr", "wins", "losses", "discord_name"],
                "match": [
                    "match_id",
                    "team1",
                    "team2",
                    "winner",
                    "mmr_diff",
                    "timestamp",
                ],
                "mmr_history": ["discord_id", "mmr", "timestamp"],
                "guild_options": ["guild_id", "customs_channel"],
            }
        )
        self.bot = bot

    def get_all_guild_options(self):
        try:
            res = self.cursor.execute(
                "SELECT guild_id, customs_channel FROM guild_options"
            ).fetchall()
            return res
        except Exception as e:
            logger.error(f"Error fetching guild options: {e}")
            return []

    def get_all_matches(self):
        try:
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
                    matches.append(Match(i[0], team1, team2, i[3], i[4], i[5]))
                except Exception as e:
                    logger.error(f"Error processing match {i[0]}: {e}")
            return matches
        except Exception as e:
            logger.error(f"Error fetching matches: {e}")
            return []

    def get_matches(self, discord_id: int):
        try:
            res = self.cursor.execute(
                "SELECT match_id, team1, team2, winner, mmr_diff, timestamp FROM match"
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
                        matches.append(Match(i[0], team1, team2, i[3], i[4], i[5]))
                except Exception as e:
                    logger.error(
                        f"Error processing match {i[0]} for player {discord_id}: {e}"
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
            insertion = "INSERT INTO match (match_id, team1, team2, winner, mmr_diff, timestamp) VALUES (?, ?, ?, ?, ?, ?)"
            self.cursor.execute(
                insertion,
                (
                    match.match_id,
                    team1_string,
                    team2_string,
                    match.winner,
                    match.mmr_diff,
                    match.timestamp,
                ),
            )
            self.connection.commit()
        except Exception as e:
            logger.error(f"Error inserting match {match.match_id}: {e}")

    def insert_player(self, player: Player):
        try:
            self.cursor.execute(
                "INSERT INTO player (discord_id, mmr, wins, losses, discord_name) VALUES (?, ?, ?, ?, ?)",
                (
                    player.discord_id,
                    player.mmr,
                    player.wins,
                    player.losses,
                    player.discord_name,
                ),
            )
            self.connection.commit()
        except Exception as e:
            logger.error(f"Error inserting player {player.discord_id}: {e}")

    def remove_player(self, player: Member):
        try:
            self.cursor.execute("DELETE FROM player WHERE discord_id = ?", (player.id,))
            self.connection.commit()
        except Exception as e:
            logger.error(f"Error removing player {player.id}: {e}")

    def remove_match(self, match_id: int):
        try:
            self.cursor.execute("DELETE FROM match WHERE match_id = ?", (match_id,))
            self.connection.commit()
        except Exception as e:
            logger.error(f"Error removing match {match_id}: {e}")


class StatisticsGeneralEmbed(Embed):
    def __init__(self, players: list[Player], match_counts_cache=None):
        super().__init__(title=f"Players", color=0x00FF42)

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
        self.set_footer(text="Normal")


class StatisticsGeneralExtEmbed(Embed):
    def __init__(self, players: list[Player]):
        super().__init__(title=f"Players", color=0x00FF42)

        self.add_field(name="Name", value="\n".join([p.discord_name for p in players]))

        self.add_field(name="MMR", value="\n".join([f"{p.mmr}" for p in players]))

        self.add_field(
            name="Rank",
            value="\n".join([f"{p.get_rank()} | {p.get_lp()}%" for p in players]),
        )
        self.set_footer(text="Extended")


class StatisticsGeneralView(View):
    def __init__(self, players: list[Player], match_counts_cache=None):
        super().__init__(timeout=7200)
        self.current_embed_index = 0
        self.current_sort_embed_index = 1
        self.current_embed = None
        self.players = players
        
        # Initialize the match counts cache if provided
        self.match_counts_cache = match_counts_cache or {}
        
        self.view_button = Button(label="Extended", style=ButtonStyle.blurple)
        self.view_button.callback = self._view_callback
        self.add_item(self.view_button)
        
        self.sort_button = Button(label="Sort", style=ButtonStyle.blurple)
        self.sort_button.callback = self._sort_callback
        self.add_item(self.sort_button)
    
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
            self.current_embed = StatisticsGeneralExtEmbed(self.players)
            self.current_embed_index = 1
            self.current_sort_embed_index = 0
            self.view_button.label = "Normal"
            self.sort_button.label = "Name"
        else:
            self.players = sorted(self.players, key=lambda p: p.discord_name)
            self.current_embed = StatisticsGeneralEmbed(self.players)
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
        
        # Precompute match counts if not already cached
        if not self.match_counts_cache:
                self.match_counts_cache = {}
                for p in self.players:
                    self.match_counts_cache[p.discord_id] = len(p.get_matches())
        
        # Use cached match counts for sorting
        normal_list = [
            sorted(self.players, key=lambda p: p.discord_name),
            sorted(self.players, key=lambda p: -p.win_rate),
            sorted(self.players, key=lambda p: -self.match_counts_cache.get(p.discord_id, 0)),
        ]
        extended_list = [
            sorted(self.players, key=lambda p: -p.mmr),
            sorted(self.players, key=lambda p: p.discord_name),
        ]
        
        # Handle different sort states
        if self.current_embed_index == 1 and self.current_sort_embed_index == 0:
            self.sort_button.label = "MMR"
            self.players = extended_list[0]
            self.current_embed = StatisticsGeneralExtEmbed(self.players)
            self.current_embed_index = 1
            self.current_sort_embed_index = 1
        elif self.current_embed_index == 1 and self.current_sort_embed_index == 1:
            self.sort_button.label = "Name"
            self.players = extended_list[1]
            self.current_embed = StatisticsGeneralExtEmbed(self.players)
            self.current_embed_index = 1
            self.current_sort_embed_index = 0
        elif self.current_embed_index == 0 and self.current_sort_embed_index == 1:
            self.sort_button.label = "Name"
            self.players = normal_list[0]
            self.current_embed = StatisticsGeneralEmbed(self.players, self.match_counts_cache)
            self.current_embed_index = 0
            self.current_sort_embed_index = 2
        elif self.current_embed_index == 0 and self.current_sort_embed_index == 2:
            self.sort_button.label = "Winrate"
            self.players = normal_list[1]
            self.current_embed = StatisticsGeneralEmbed(self.players, self.match_counts_cache)
            self.current_embed_index = 0
            self.current_sort_embed_index = 3
        elif self.current_embed_index == 0 and self.current_sort_embed_index == 3:
            self.sort_button.label = "Matches"
            self.players = normal_list[2]
            self.current_embed = StatisticsGeneralEmbed(self.players, self.match_counts_cache)
            self.current_embed_index = 0
            self.current_sort_embed_index = 1
        
        # Reset button state but with the new label
        self.sort_button.disabled = False
        
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
        self.mmr_gains_min = 100
        self.min_mmr_gains = 10
        self.winner = None
        (
            self.mmr_diff,
            self.mmr_diff_scaled,
        ) = self._calc_mmr_diff()
        self.timestamp = datetime.datetime.now()
        self.match_id = self._gen_match_id()

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
        res = self.db.cursor.execute("SELECT match_id FROM match")

        match_ids = [i[0] for i in res.fetchall()]
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
            if (player in self.team1 and winner == 1) or (
                player in self.team2 and winner == 2
            ):
                player.mmr += mmr_gains
                player.wins += 1
            else:
                player.mmr -= mmr_gains
                player.losses += 1

            player.update()

        self.db.insert_match(
            Match(
                self.match_id,
                self.team1,
                self.team2,
                winner,
                self.mmr_diff,
                self.timestamp,
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
    ):
        super().__init__(timeout=7200)

        self.current_embed = None
        self.bot = bot
        self.match = match
        self.match_message = match_message
        self.match_embed = match_embed
        self.ingame_ping_message = ingame_ping_message
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
        await interaction.response.defer()
        try:
            await self.remove_ingame_role(interaction)
            await self.match_message.delete()
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
        rematch_button = Button(label="Rematch", style=ButtonStyle.blurple)
        rematch_button.callback = self._rematch_callback
        self.add_item(rematch_button)

    async def _rematch_callback(self, interaction: Interaction):
        await interaction.response.defer()
        await start_match(
            self.match.team1,
            self.match.team2,
            self.bot,
            interaction.guild,
            self.match.creator,
            interaction.channel,
            interaction,
        )


class QueueEmbed(Embed):
    def __init__(
        self, queue: list[Player], vc_members_names: list[str], creator: Member
    ):
        super().__init__(title=f"Queue {len(queue)}p", color=0x00FF42)
        self.creator = creator
        self.add_field(name="Players", value="\n".join([p.discord_name for p in queue]))
        self.add_field(
            name="VC",
            value="\n".join(
                [
                    m
                    for m in vc_members_names
                    if m not in [p.discord_name for p in queue]
                ]
            ),
        )
        self.set_footer(text=f"Creator: {creator.name}")


class QueueView(View):
    def __init__(self, bot, voice_channel: VoiceChannel | None):
        super().__init__(timeout=10800)  # I think 3 hours
        self.db = Database(bot)
        self.bot = bot
        self.voice_channel = voice_channel

        self.queue: list[Member] = []

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

        await interaction.message.edit(
            embed=QueueEmbed(
                [Player(self.bot, p.id, False) for p in self.queue],
                vc_members_names,
                Player(
                    self.bot,
                    discord_name=interaction.message.embeds[0].footer.text[9:],
                ).get_discord_object(),
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

        await self.queue_message.edit(
            embed=QueueEmbed(
                [Player(self.bot, p.id, False) for p in self.queue_view.queue],
                vc_members_names,
                Player(
                    self.bot,
                    discord_name=self.queue_message.embeds[0].footer.text[9:],
                ).get_discord_object(),
            )
        )
        await interaction.response.edit_message(
            view=QueueControlView(
                self.bot,
                self.queue_message,
                self.queue_view,
                voice=self.voice,
            )
        )


class QueueControlView(View):
    def __init__(
        self,
        bot: commands.Bot,
        queue_message: Message,
        queue_view: QueueView,
        voice: VoiceChannel | None = None,
        creator: Member | None = None,
    ):
        super().__init__(timeout=10800)  # I think 3 hours
        self.db = Database(bot)
        self.bot = bot
        self.queue_message = queue_message
        self.queue_view = queue_view
        self.voice = voice
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
        
        move_players_button = Button(
            label=f"Toggle Voice Split: Off",
            style=ButtonStyle.secondary,
            row=1,
        )
        move_players_button.callback = self._toggle_move_players
        self.add_item(move_players_button)

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
        await interaction.response.edit_message(view=self)
        
        team1, team2 = generate_teams(
            [Player(self.bot, p.id, False) for p in self.queue_view.queue]
        )
        await start_match(
            team1,
            team2,
            self.bot,
            interaction.guild,
            interaction.user,
            interaction.channel,
            interaction,
            move_players_setting=self.move_players,
        )
        # Reset the button after generating teams
        for item in self.children:
            if isinstance(item, Button) and item.callback == self._start_callback:
                item.label = "Start match"
                item.disabled = False
                break
        await interaction.edit_original_response(view=self)

    async def _discard_callback(self, interaction: Interaction):
        await interaction.response.defer()
        await self.queue_message.delete()

    async def _update_remove_list_callback(self, interaction: Interaction):
        await interaction.response.defer()
        message = await interaction.original_response()
        await message.edit(
            view=QueueControlView(
                self.bot,
                self.queue_message,
                self.queue_view,
                voice=self.voice,
            )
        )


async def start_match(
    team1: list[Player],
    team2: list[Player],
    bot: commands.Bot,
    guild: Guild,
    creator: Member,
    channel: TextChannel,
    interaction: Interaction,
    move_players_setting=False,
):
    match = CustomMatch(bot, creator, team1, team2)

    embed = MatchEmbed(team1, team2, creator)
    config = ConfigDatabase(bot)
    ingame_role = config.get_items_by(ConfigTables.INGAMEROLE, guild.id)
    logger.info(ingame_role)
    if len(ingame_role) > 0:
        ingame_role = guild.get_role(ingame_role[0])
        for player in team1 + team2:
            player_discord_object = player.get_discord_object()
            if ingame_role not in player_discord_object.roles:
                await player_discord_object.add_roles(ingame_role)
        ingame_ping_message = await interaction.channel.send(f"<@&{ingame_role.id}>")
    else:
        ingame_ping_message = None
    match_message = await channel.send(embed=embed)
    view = MatchControlView(
        bot, guild, match, match_message, embed, ingame_ping_message
    )
    await interaction.followup.send("Match Control", view=view, ephemeral=True)
    categories = config.get_items_by(ConfigTables.BETTERVC, guild.id)
    if len(categories) != 0 and move_players_setting:
        bettervc_category_obj = bot.get_channel(int(categories[0]))
        bettervc_channels = bettervc_category_obj.channels
        for voice_channel in bettervc_channels:
            if len(voice_channel.members) == 0 and voice_channel.name[0] != "|":
                for p in team1:
                    if p.get_discord_object().voice:
                        await p.get_discord_object().move_to(voice_channel)
                break

    # draftlol
    if os.environ["DEV"] != "True":
        draftlolws = draftlol.DraftLolWebSocket()
        draftlolws.run()

        retries = 0
        while not draftlolws.closed and retries < 10:
            time.sleep(0.5)
            retries += 1

        draftlolws.force_close()
        draft_message = draftlolws.message
    else:
        draft_message = "League draft links \n Not showed when in dev"
        # ifall den timear ut, så e failed message preset i draftlolws classen.
    await channel.send(draft_message)


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
            embed=FreeEmbed(
                self.team1,
                self.team2,
                self.creator,
            ),
            view=self,
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
            interaction.user,
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

        previous_button = Button(label="Previous", style=ButtonStyle.blurple)
        previous_button.callback = self._previous_callback
        self.add_item(previous_button)

        next_button = Button(label="Next", style=ButtonStyle.blurple)
        next_button.callback = self._next_callback
        self.add_item(next_button)

    async def _previous_callback(self, interaction: Interaction):
        await interaction.response.defer()
        self.current_embed = interaction.message.embeds[0]
        self.current_embed = self.embeds[self.embeds.index(self.current_embed) - 1]
        message = await interaction.original_response()
        await message.edit(embed=self.current_embed, view=self)

    async def _next_callback(self, interaction: Interaction):
        await interaction.response.defer()
        self.current_embed = interaction.message.embeds[0]
        self.current_embed = self.embeds[self.embeds.index(self.current_embed) + 1]
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

    if num_players > 10:
        raise ValueError("numplayers > 10")

    team_size = num_players // 2
    best_teams = None
    best_diff = float("inf")
    combination_list=list(combinations(range(num_players), team_size))
    random.shuffle(combination_list)
    for team1_indices in combination_list:
        team1 = [players[i] for i in team1_indices]
        team2 = [players[i] for i in range(num_players) if i not in team1_indices]

        team1_mmr = sum(player.mmr for player in team1)
        team2_mmr = sum(player.mmr for player in team2)
        diff = abs(team1_mmr - team2_mmr)

        if diff < 100:
            return (team1, team2)
        if diff < best_diff:
            best_diff = diff
            best_teams = (team1, team2)

    return best_teams
