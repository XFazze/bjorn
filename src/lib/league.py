import sqlite3
import datetime
import random
import discord
from discord.ext import commands
from typing import Optional, Literal

import lib.general as general


ranks_mmr = {
    "Iron 4": 500,
    "Iron 3": 550,
    "Iron 2": 600,
    "Iron 1": 650,
    "Bronze 4": 700,
    "Bronze 3": 750,
    "Bronze 2": 800,
    "Bronze 1": 850,
    "Silver 4": 900,
    "Silver 3": 950,
    "Silver 2": 1000,
    "Silver 1": 1050,
    "Gold 4": 1100,
    "Gold 3": 1150,
    "Gold 2": 1200,
    "Gold 1": 1250,
    "Platinum 4": 1300,
    "Platinum 3": 1350,
    "Platinum 2": 1400,
    "Platinum 1": 1450,
    "Diamond 4": 1500,
    "Diamond 3": 1550,
    "Diamond 2": 1600,
    "Diamond 1": 1650,
    "Master": 1700,
    "Grandmaster": 1850,
    "Challenger": 2300
}

ranks_type = Literal["Iron 2", "Iron 1", "Bronze 4", "Bronze 3", "Bronze 2", "Bronze 1", "Silver 4", "Silver 3", "Silver 2", "Silver 1", "Gold 4", "Gold 3",
                     "Gold 2", "Gold 1", "Platinum 4", "Platinum 3", "Platinum 2", "Platinum 1", "Diamond 4", "Diamond 3", "Diamond 2", "Diamond 1", "Master", "Grandmaster", "Challenger"]


class Tournament:
    pass


class Player:
    def __init__(self, bot, discord_id: int, get_matches=True):
        self.db = Database(bot, "data/league.sqlite")
        self.bot = bot

        existing_player = self.db.cursor.execute(
            f"SELECT discord_id, mmr, wins, losses FROM player WHERE discord_id = {discord_id}").fetchone()

        self.discord_id = discord_id
        self.discord_name = self.bot.get_user(discord_id).name
        self.mmr = existing_player[1] if existing_player else 1000
        self.wins = existing_player[2] if existing_player else 0
        self.losses = existing_player[3] if existing_player else 0
        self.win_rate = self.wins / (self.wins + self.losses) * \
            100 if self.wins + self.losses > 0 else 0
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


class Database(general.Database):
    def __init__(self, bot, db_name):
        super().__init__(db_name)
        self.create_tables(
            {
                "player": [
                    "discord_id",
                    "mmr",
                    "wins",
                    "losses"
                ],
                "match": [
                    "match_id",
                    "team1",
                    "team2",
                    "winner",
                    "mmr_diff",
                    "timestamp"
                ],
                "mmr_history": [
                    "discord_id",
                    "mmr",
                    "timestamp"
                ]
            }
        )
        self.bot = bot

    def get_all_matches(self):
        res = self.cursor.execute(
            f"SELECT match_id, team1, team2, winner, mmr_diff, timestamp FROM match").fetchall()

        matches = []
        for i in res:
            team1 = [Player(self.bot, int(i), get_matches=False)
                     for i in i[1].split(" ")[0:-1]]
            team2 = [Player(self.bot, int(i), get_matches=False)
                     for i in i[2].split(" ")[0:-1]]

            matches.append(Match(i[0], team1, team2, i[3], i[4], i[5]))

        return matches

    def get_matches(self, discord_id: int):
        res = self.cursor.execute(
            f"SELECT match_id, team1, team2, winner, mmr_diff, timestamp FROM match").fetchall()

        matches = []
        for i in res:
            if str(discord_id) in i[1].split(" ")[0:-1] or str(discord_id) in i[2].split(" ")[0:-1]:
                team1 = []
                team2 = []

                team1 = [Player(self.bot, int(i), get_matches=False)
                         for i in i[1].split(" ")[0:-1]]
                team2 = [Player(self.bot, int(i), get_matches=False)
                         for i in i[2].split(" ")[0:-1]]

                matches.append(Match(i[0], team1, team2, i[3], i[4], i[5]))
        return matches

    def get_all_players(self):
        res = self.cursor.execute(f"SELECT discord_id FROM player").fetchall()
        return [Player(self.bot, i[0]) for i in res]

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

    def remove_player(self, player: discord.Member):
        self.cursor.execute(
            f"DELETE FROM player WHERE discord_id = {player.id}")
        self.connection.commit()

    def remove_match(self, match_id: int):
        self.cursor.execute(
            f"DELETE FROM match WHERE match_id = {match_id}")
        self.connection.commit()


class CustomMatch:
    def __init__(self, bot, creator: discord.Member, team1: list[Player], team2: list[Player]):
        self.db = Database(bot, "data/league.sqlite")
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
                player.mmr += 10 * self.mmr_diff_scaled
                player.wins += 1

            for player in self.team2:
                player.mmr -= 10 * self.mmr_diff_scaled
                player.losses += 1

        elif winner == 2:

            for player in self.team1:
                player.mmr -= 10 * self.mmr_diff_scaled
                player.losses += 1

            for player in self.team2:
                player.mmr += 10 * self.mmr_diff_scaled
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
    def __init__(self, match: CustomMatch, base_embed: discord.Embed):
        super().__init__(timeout=7200)

        self.current_embed = None
        self.base_embed = base_embed

        self.buttons = [
            discord.ui.Button(
                label="Left Win", style=discord.ButtonStyle.green, custom_id="left"),
            discord.ui.Button(
                label="Right Win", style=discord.ButtonStyle.green, custom_id="right"),
            discord.ui.Button(
                label="Players", style=discord.ButtonStyle.blurple, custom_id="players", row=1),
            discord.ui.Button(
                label="Discard", style=discord.ButtonStyle.red, custom_id="discard", row=2)
        ]

        async def win_callback(interaction: discord.Interaction):
            self.current_embed = interaction.message.embeds[0]
            if interaction.data["custom_id"] == "players":
                if self.current_embed.title == "Players":
                    embed = base_embed
                    self.buttons[2].label = "Players"
                else:
                    players = [i for i in match.db.get_all_players(
                    ) if i.discord_id in [i.discord_id for i in match.team1 + match.team2]]

                    embed = discord.Embed(title=f"Players", color=0x228888)
                    embed.add_field(name="Name", value="\n".join(
                        [p.discord_name for p in players]))
                    embed.add_field(name="Win rate", value="\n".join(
                        [f"{p.win_rate:.1f}%" for p in players]))
                    embed.add_field(name="Matches", value="\n".join(
                        [f"{len(p.matches)}" for p in players]))

                    self.buttons[2].label = "Teams"

                await interaction.message.edit(embed=embed, view=self)
                await interaction.response.defer()
                return

            if interaction.user != match.creator:
                return

            if interaction.data["custom_id"] == "discard":
                self.current_embed.title = "Match Discarded"
                self.current_embed.color = 0xFF0000
                await interaction.message.edit(embed=self.current_embed, view=None)
                return
            elif interaction.data["custom_id"] == "left":
                match.finish_match(1)
                await interaction.response.defer()
            elif interaction.data["custom_id"] == "right":
                match.finish_match(2)
                await interaction.response.defer()

            self.current_embed.title = f"Winner: {'Left' if interaction.data['custom_id'] == 'left' else 'Right'} Team"
            await interaction.message.edit(embed=self.current_embed, view=None)

        for button in self.buttons:
            button.callback = win_callback
            self.add_item(button)


class QueueEmbed(discord.Embed):
    def __init__(self, queue: list[Player]):
        super().__init__(title="Queue", color=0x00FF42)

        self.add_field(name="Players", value='\n'.join(
            [p.discord_name for p in queue]))


class QueueView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=10800)  # I think 3 hours
        self.db = Database(bot, "data/league.sqlite")
        self.bot = bot

        self.buttons = [
            discord.ui.Button(
                label="Queue", style=discord.ButtonStyle.green, custom_id="queue"),
            discord.ui.Button(
                label="Start match", style=discord.ButtonStyle.green, custom_id="start"),
            discord.ui.Button(
                label="Discard", style=discord.ButtonStyle.red, custom_id="discard", row=2)
        ]

        self.queue = []

        async def queue_callback(interaction: discord.Interaction):
            if interaction.data["custom_id"] == "queue":
                if interaction.user in self.queue:
                    self.queue.remove(interaction.user)
                else:
                    self.queue.append(interaction.user)

                await interaction.message.edit(embed=QueueEmbed([Player(self.bot, p.id, False) for p in self.queue]), view=self)
                await interaction.response.defer()
                return

            if interaction.data["custom_id"] == "discard":
                await interaction.message.delete()
                return

            if interaction.data["custom_id"] == "start":
                if len(self.queue) < 2:
                    await interaction.response.send_message("Not enough players in queue", ephemeral=True)
                    await interaction.response.defer()
                    return

                team1, team2 = generate_teams(
                    [Player(self.bot, p.id, False) for p in self.queue])
                match = CustomMatch(self.bot, interaction.user, team1, team2)

                embed = MatchEmbed(team1, team2)
                view = MatchView(match, embed)

                await interaction.channel.send(embed=embed, view=view)
                await interaction.message.delete()
                await interaction.response.defer()
                return

        for button in self.buttons:
            button.callback = queue_callback
            self.add_item(button)


class PlayerMatchesView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=7200)

        self.embeds = embeds
        self.current_embed = None

        self.buttons = [
            discord.ui.Button(
                label="Previous", style=discord.ButtonStyle.blurple, custom_id="prev", row=1),
            discord.ui.Button(
                label="Next", style=discord.ButtonStyle.blurple, custom_id="next", row=1),
            discord.ui.Button(
                label="Discard", style=discord.ButtonStyle.red, custom_id="discard", row=2)
        ]

        async def callback(interaction: discord.Interaction):
            self.current_embed = interaction.message.embeds[0]

            if interaction.data["custom_id"] == "discard":
                await interaction.message.delete()
                return

            if interaction.data["custom_id"] == "prev":
                self.current_embed = self.embeds[self.embeds.index(
                    self.current_embed) - 1]
                await interaction.response.defer()
            elif interaction.data["custom_id"] == "next":
                self.current_embed = self.embeds[self.embeds.index(
                    self.current_embed) + 1]
                await interaction.response.defer()

            await interaction.message.edit(embed=self.current_embed, view=self)
            await interaction.response.defer()

        for button in self.buttons:
            button.callback = callback
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
