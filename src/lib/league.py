import sqlite3
import datetime
import random
import discord
from discord.ext import commands
from typing import Optional


ranks_mmr = {
    "i4": 500,
    "i3": 550,
    "i2": 600,
    "i1": 650,
    "b4": 700,
    "b3": 750,
    "b2": 800,
    "b1": 850,
    "s4": 900,
    "s3": 950,
    "s2": 1000,
    "s1": 1050,
    "g4": 1100,
    "g3": 1150,
    "g2": 1200,
    "g1": 1250,
    "p4": 1300,
    "p3": 1350,
    "p2": 1400,
    "p1": 1450,
    "d4": 1500,
    "d3": 1550,
    "d2": 1600,
    "d1": 1650,
    "master": 1700,
    "grandmaster": 1850,
    "challenger": 2300
}


class Tournament:
    pass


class Player:
    def __init__(self, bot, discord_id: int, get_matches=True):
        self.db = Database(bot, "data/data.sqlite")
        self.bot = bot

        existing_player = self.db.cursor.execute(
            f"SELECT discord_id, mmr, wins, losses FROM player WHERE discord_id = {discord_id}").fetchone()

        self.discord_id = discord_id
        self.discord_name = self.bot.get_user(discord_id).name
        self.mmr = existing_player[1] if existing_player else 1000
        self.wins = existing_player[2] if existing_player else 0
        self.losses = existing_player[3] if existing_player else 0
        self.matches = self.db.get_matches(discord_id) if get_matches else []

        if not existing_player:
            self.db.insert_player(self)

    def set_mmr(self, mmr):
        self.db.cursor.execute(
            f"UPDATE player SET mmr = {mmr} WHERE discord_id = {self.discord_id}")
        self.db.connection.commit()
        self.mmr = mmr

    def update(self):
        self.db.cursor.execute(
            f"UPDATE player SET mmr = {self.mmr}, wins = {self.wins}, losses = {self.losses} WHERE discord_id = {self.discord_id}")
        self.db.connection.commit()

        insertion = f"INSERT INTO mmr_history (discord_id, mmr, timestamp) VALUES (?, ?, ?)"
        self.db.cursor.execute(
            insertion, (self.discord_id, self.mmr, datetime.datetime.now()))
        self.db.connection.commit()


class Match:
    def __init__(self, match_id: int, team1: list[Player], team2: list[Player], winner: int, mmr_diff: int, timestamp: datetime.datetime):
        self.match_id = match_id
        self.team1 = team1
        self.team2 = team2
        self.winner = winner
        self.mmr_diff = mmr_diff
        self.timestamp = timestamp


class Database:
    def __init__(self, bot, db_name):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.bot = bot

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS player(discord_id, mmr, wins, losses)"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS match(match_id, team1, team2, winner, mmr_diff, timestamp)"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS mmr_history(discord_id, mmr, timestamp)"
        )

    def get_matches(self, discord_id: int):
        res = self.cursor.execute(
            f"SELECT match_id, team1, team2, winner, mmr_diff, timestamp FROM match").fetchall()

        matches = []
        for i in res:
            if str(discord_id) in i[1].split(" ")[0:-1] or str(discord_id) in i[2].split(" ")[0:-1]:
                team1 = []
                team2 = []

                team1 = [Player(self.bot, int(i), False)
                         for i in i[1].split(" ")[0:-1]]
                team2 = [Player(self.bot, int(i), False)
                         for i in i[2].split(" ")[0:-1]]

                matches.append(Match(i[0], team1, team2, i[3], i[4], i[5]))
        return matches

    def insert_match(self, match: Match):
        team1_string = "".join(
            [str(player.discord_id) + " " for player in match.team1])
        team2_string = "".join(
            [str(player.discord_id) + " " for player in match.team2])

        insertion = f"INSERT INTO match (match_id, team1, team2, winner, mmr_diff, timestamp) VALUES (?, ?, ?, ?, ?, ?)"
        self.cursor.execute(insertion, (match.match_id, team1_string,
                            team2_string, match.winner, match.mmr_diff, match.timestamp))
        self.connection.commit()

    def insert_player(self, player: Player):
        self.cursor.execute(
            f"INSERT INTO player (discord_id, mmr, wins, losses) VALUES ({player.discord_id}, {player.mmr}, {player.wins}, {player.losses})")
        self.connection.commit()


class CustomMatch:
    def __init__(self, bot, creator: discord.Member, team1: list[Player], team2: list[Player]):
        self.db = Database(bot, "data/data.sqlite")
        self.bot = bot
        self.creator = creator
        self.team1 = team1
        self.team2 = team2
        self.winner = None
        self.mmr_diff, self.mmr_diff_maxed, self.mmr_diff_powed, self.mmr_diff_scaled = self.calc_mmr_diff()
        self.timestamp = datetime.datetime.now()
        self.match_id = self.gen_match_id()

    def calc_mmr_diff(self) -> list[int, int, int, int]:
        mmr_diff = abs(sum(
            [player.mmr for player in self.team1]) - sum([player.mmr for player in self.team2]))

        # 0.1 to 1
        mmr_diff_maxed = max(
            min(abs(mmr_diff), 100), 10)/100

        # 0.01 to 1
        mmr_diff_powed = mmr_diff_maxed**2

        # 0 to 2. over 1 when left is higher mmr
        mmr_diff_scaled = 1 + \
            (0 if mmr_diff == 0 else (mmr_diff/abs(mmr_diff))*mmr_diff_powed)

        return [mmr_diff, mmr_diff_maxed, mmr_diff_powed, mmr_diff_scaled]

    def gen_match_id(self) -> int:
        res = self.db.cursor.execute("SELECT match_id FROM match")

        match_ids = [i[0] for i in res.fetchall()]
        match_id = random.randint(100000, 999999)
        while match_id in match_ids:
            match_id = random.randint(10000000, 99999999)

        return match_id

    def finish_match(self, winner: int):
        if winner == 1:
            for player in self.team1:
                player.mmr += 10 * (2 - self.mmr_diff_scaled)
                player.wins += 1

            for player in self.team2:
                player.mmr += 10 * self.mmr_diff_scaled
                player.losses += 1

        elif winner == 2:
            for player in self.team1:
                player.mmr += 10 * self.mmr_diff_scaled
                player.losses += 1

            for player in self.team2:
                player.mmr += 10 * (2 - self.mmr_diff_scaled)
                player.wins += 1

        [player.update() for player in self.team1 + self.team2]

        self.db.insert_match(Match(self.match_id, self.team1,
                             self.team2, winner, self.mmr_diff, self.timestamp))


class MatchEmbed(discord.Embed):
    def __init__(self, team1: list[Player], team2: list[Player]):
        super().__init__(title="Teams",  color=0x00FF42)

        self.add_field(name="Left Team", value='\n'.join(
            [p.discord_name for p in team1]))
        self.add_field(name="Right Team", value='\n'.join(
            [p.discord_name for p in team2]))


class MatchView(discord.ui.View):
    def __init__(self, match: CustomMatch):
        super().__init__(timeout=7200)

        buttons = [
            discord.ui.Button(
                label="Left Win", style=discord.ButtonStyle.green, custom_id="left"),
            discord.ui.Button(
                label="Right Win", style=discord.ButtonStyle.green, custom_id="right"),
            discord.ui.Button(
                label="Discard", style=discord.ButtonStyle.red, custom_id="discard", row=1)
        ]

        async def win_callback(interaction: discord.Interaction):
            if interaction.user != match.creator:
                return

            if interaction.data["custom_id"] == "discard":
                interaction.message.embeds[0].title = "Match Discarded"
                interaction.message.embeds[0].color = 0xFF0000
                await interaction.message.edit(embed=interaction.message.embeds[0], view=None)
                return

            if interaction.data["custom_id"] == "left":
                match.finish_match(1)
            elif interaction.data["custom_id"] == "right":
                match.finish_match(2)

            interaction.message.embeds[0].title = f"Winner: {'Left' if interaction.data['custom_id'] == 'left' else 'Right'} Team"
            await interaction.message.edit(embed=interaction.message.embeds[0], view=None)

        for button in buttons:
            button.callback = win_callback
            self.add_item(button)


def generate_teams(players: list[Player]) -> tuple[list[Player], list[Player]]:
    team1 = []
    team2 = []

    while len(players) != 0:
        if sum([p.mmr for p in team1]) > sum([p.mmr for p in team2]):
            team2.append(players.pop())
        else:
            team1.append(players.pop())

    random.shuffle(team1)
    random.shuffle(team2)

    return (team1, team2)
