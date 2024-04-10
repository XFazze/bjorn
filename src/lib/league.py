import os
import sqlite3
import datetime
import random
import discord
from discord.ext import commands
from typing import Optional, Literal
import math
import plotly.express as px
import pandas as pd
from itertools import combinations

import lib.general as general


ranks_mmr = {
    "Iron+" : 0,
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
    "Emerald 4": 1500,
    "Emerald 3": 1550,
    "Emerald 2": 1600,
    "Emerald 1": 1650,
    "Diamond 4": 1700,
    "Diamond 3": 1750,
    "Diamond 2": 1800,
    "Diamond 1": 1850,
    "Master+": 1900,
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


class StartMenuEmbed(discord.Embed):
    def __init__(self):
        pass


class StartMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=7200)

        self.buttons = {
            discord.ui.Button(label="", custom_id=""),
            discord.ui.Button(label="", custom_id=""),
            discord.ui.Button(label="", custom_id=""),
            discord.ui.Button(label="", custom_id=""),
            discord.ui.Button(label="", custom_id=""),
            discord.ui.Button(label="", custom_id=""),
        }


class Player:
    def __init__(
        self,
        bot: commands.Bot,
        discord_id: int = None,
        discord_name: str = None,
        get_matches=True,
    ):
        self.db = Database(bot, "data/league.sqlite")
        self.bot = bot

        if discord_id == None:
            if discord_name == None:
                return None
            discord_member_object = next(
                (m for m in self.bot.get_all_members() if m.name == discord_name), None
            )
            if discord_member_object is None:
                return None
            discord_id = discord_member_object.id

        existing_player = self.db.cursor.execute(
            f"SELECT discord_id, mmr, wins, losses FROM player WHERE discord_id = {discord_id}"
        ).fetchone()

        self.discord_id = discord_id
        self.discord_member_object = next(
            (m for m in self.bot.get_all_members() if m.id == discord_id), None
        )
        self.discord_name = self.bot.get_user(discord_id).name
        self.mmr = existing_player[1] if existing_player else 1000
        self.wins = existing_player[2] if existing_player else 0
        self.losses = existing_player[3] if existing_player else 0
        self.win_rate = (
            self.wins / (self.wins + self.losses) * 100
            if self.wins + self.losses > 0
            else 0
        )
        self.matches: list[Match] = (
            self.db.get_matches(discord_id) if get_matches else []
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
            return 100 - (ranks_mmr["Master+"]-self.mmr)*2
        
        elif rank is None:
            rank = "Master+"
        lp = ranks_mmr[rank]+(100) - self.mmr # 100 taken from  -> ranks_mmr["Bronze 1"]-ranks_mmr["Bronze 2"]
        
        if lp < 0 and self.mmr < ranks_mmr["Bronze 3"]:
            lp = ((self.mmr/ranks_mmr["Bronze 3"]) * 100)
            return int(lp//1)

        return int(100 - lp)*2


class Match:
    def __init__(
        self,
        match_id: int,
        team1: list[Player],
        team2: list[Player],
        winner: int,
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
    def __init__(self, bot, db_name):
        super().__init__(db_name)
        self.create_tables(
            {
                "player": ["discord_id", "mmr", "wins", "losses"],
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
        res = self.cursor.execute(
            f"SELECT guild_id, customs_channel FROM guild_options"
        ).fetchall()

    def get_all_matches(self):
        res = self.cursor.execute(
            f"SELECT match_id, team1, team2, winner, mmr_diff, timestamp FROM match"
        ).fetchall()

        matches = []
        for i in res:
            team1 = [
                Player(self.bot, int(i), get_matches=False)
                for i in i[1].split(" ")[0:-1]
            ]
            team2 = [
                Player(self.bot, int(i), get_matches=False)
                for i in i[2].split(" ")[0:-1]
            ]

            matches.append(Match(i[0], team1, team2, i[3], i[4], i[5]))

        return matches

    def get_matches(self, discord_id: int):
        res = self.cursor.execute(
            f"SELECT match_id, team1, team2, winner, mmr_diff, timestamp FROM match"
        ).fetchall()

        matches = []
        for i in res:
            if (
                str(discord_id) in i[1].split(" ")[0:-1]
                or str(discord_id) in i[2].split(" ")[0:-1]
            ):
                team1 = []
                team2 = []

                team1 = [
                    Player(self.bot, int(i), get_matches=False)
                    for i in i[1].split(" ")[0:-1]
                ]
                team2 = [
                    Player(self.bot, int(i), get_matches=False)
                    for i in i[2].split(" ")[0:-1]
                ]

                matches.append(Match(i[0], team1, team2, i[3], i[4], i[5]))
        return matches

    def get_all_players(self):
        res = self.cursor.execute(f"SELECT discord_id FROM player").fetchall()
        return [Player(self.bot, i[0]) for i in res]

    def insert_match(self, match: Match):
        team1_string = "".join([str(player.discord_id) + " " for player in match.team1])
        team2_string = "".join([str(player.discord_id) + " " for player in match.team2])

        insertion = f"INSERT INTO match (match_id, team1, team2, winner, mmr_diff, timestamp) VALUES (?, ?, ?, ?, ?, ?)"
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

    def insert_player(self, player: Player):
        self.cursor.execute(
            f"INSERT INTO player (discord_id, mmr, wins, losses) VALUES ({player.discord_id}, {player.mmr}, {player.wins}, {player.losses})"
        )
        self.connection.commit()

    def remove_player(self, player: discord.Member):
        self.cursor.execute(f"DELETE FROM player WHERE discord_id = {player.id}")
        self.connection.commit()

    def remove_match(self, match_id: int):
        self.cursor.execute(f"DELETE FROM match WHERE match_id = {match_id}")
        self.connection.commit()


class PlayersEmbed(discord.Embed):
    def __init__(self, players: list[Player]):
        super().__init__(title=f"Players", color=0x00FF42)

        self.add_field(name="Name", value="\n".join([p.discord_name for p in players]))
        self.add_field(
            name="Win rate", value="\n".join([f"{p.win_rate:.1f}%" for p in players])
        )
        self.add_field(
            name="Matches", value="\n".join([f"{len(p.matches)}" for p in players])
        )
        self.set_footer(text="Normal")


class PlayersExtEmbed(discord.Embed):
    def __init__(self, players: list[Player]):
        super().__init__(title=f"Players", color=0x00FF42)

        self.add_field(name="Name", value="\n".join([p.discord_name for p in players]))

        self.add_field(name="MMR", value="\n".join([f"{p.mmr}" for p in players]))

        self.add_field(
            name="Rank",
            value="\n".join([f"{p.get_rank()} | {p.get_lp()}%" for p in players]),
        )
        self.set_footer(text="Extended")


class PlayersView(discord.ui.View):
    def __init__(self, players):
        super().__init__(timeout=7200)

        self.current_embed_index = 0
        self.current_sort_embed_index = 1
        self.current_embed = None
        self.players = players
        self.view_button = discord.ui.Button(
            label="Extended", style=discord.ButtonStyle.blurple, custom_id="view"
        )
        self.sort_button = discord.ui.Button(
            label="Sort", style=discord.ButtonStyle.blurple, custom_id="sort"
        )
        normal_list = [
            sorted(self.players, key=lambda p: p.discord_name),
            sorted(self.players, key=lambda p: -p.win_rate),
            sorted(self.players, key=lambda p: -len(p.matches)),
        ]
        extended_list = [
            sorted(self.players, key=lambda p: -p.mmr),
            sorted(self.players, key=lambda p: p.discord_name),
        ]

        async def view_callback(interaction: discord.Interaction):
            if interaction.data["custom_id"] == "view":
                if self.current_embed_index == 0:
                    self.players = sorted(self.players, key=lambda p: p.discord_name)
                    self.current_embed = PlayersExtEmbed(self.players)
                    self.current_embed_index = 1
                    self.current_sort_embed_index = 0
                    self.view_button.label = "Normal"
                    self.sort_button.label = "Name"

                else:
                    self.players = sorted(self.players, key=lambda p: p.discord_name)
                    self.current_embed = PlayersEmbed(self.players)
                    self.current_embed_index = 0
                    self.current_sort_embed_index = 1
                    self.view_button.label = "Extended"
                await interaction.message.edit(embed=self.current_embed, view=self)
                await interaction.response.defer()
                return

            if interaction.data["custom_id"] == "sort":
                if self.current_embed_index == 1 and self.current_sort_embed_index == 0:
                    self.sort_button.label = "MMR"
                    self.players = extended_list[0]
                    self.current_embed = PlayersExtEmbed(self.players)
                    self.current_embed_index = 1
                    self.current_sort_embed_index = 1

                elif (
                    self.current_embed_index == 1 and self.current_sort_embed_index == 1
                ):
                    self.sort_button.label = "Name"
                    self.players = extended_list[1]
                    self.current_embed = PlayersExtEmbed(self.players)
                    self.current_embed_index = 1
                    self.current_sort_embed_index = 0

                elif (
                    self.current_embed_index == 0 and self.current_sort_embed_index == 1
                ):
                    self.sort_button.label = "Name"
                    self.players = normal_list[0]
                    self.current_embed = PlayersEmbed(self.players)
                    self.current_embed_index = 0
                    self.current_sort_embed_index = 2

                elif (
                    self.current_embed_index == 0 and self.current_sort_embed_index == 2
                ):
                    self.sort_button.label = "Winrate"
                    self.players = normal_list[1]
                    self.current_embed = PlayersEmbed(self.players)
                    self.current_embed_index = 0
                    self.current_sort_embed_index = 3

                elif (
                    self.current_embed_index == 0 and self.current_sort_embed_index == 3
                ):
                    self.sort_button.label = "Matches"
                    self.players = normal_list[2]
                    self.current_embed = PlayersEmbed(self.players)
                    self.current_embed_index = 0
                    self.current_sort_embed_index = 1

                await interaction.message.edit(embed=self.current_embed, view=self)
                await interaction.response.defer()
                return

        self.view_button.callback = view_callback
        self.sort_button.callback = view_callback
        self.add_item(self.view_button)
        self.add_item(self.sort_button)


class CustomMatch:
    def __init__(
        self, bot, creator: discord.Member, team1: list[Player], team2: list[Player]
    ):
        self.db = Database(bot, "data/league.sqlite")
        self.bot = bot
        self.creator = creator
        self.team1 = team1
        self.team2 = team2
        self.winner = None
        (
            self.mmr_diff,
            self.mmr_diff_maxed,
            self.mmr_diff_powed,
            self.mmr_diff_scaled,
        ) = self.calc_mmr_diff()
        self.timestamp = datetime.datetime.now()
        self.match_id = self.gen_match_id()

    def calc_mmr_diff(self) -> list[int, int, int, int]:
        mmr_diff = abs(
            sum([player.mmr for player in self.team1])
            - sum([player.mmr for player in self.team2])
        )

        # 0.1 to 1
        mmr_diff_maxed = max(min(abs(mmr_diff), 100), 10) / 100

        # 0.01 to 1
        mmr_diff_powed = mmr_diff_maxed**2

        # 0 to 2. over 1 when left is higher mmr
        mmr_diff_scaled = 1 + (
            0 if mmr_diff == 0 else (mmr_diff / abs(mmr_diff)) * mmr_diff_powed
        )

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
                player.mmr += 20 * self.mmr_diff_scaled
                player.mmr = math.ceil(player.mmr)
                player.wins += 1

            for player in self.team2:
                player.mmr -= 20 * self.mmr_diff_scaled
                player.mmr = math.ceil(player.mmr)
                player.losses += 1

        elif winner == 2:

            for player in self.team1:
                player.mmr -= 20 * self.mmr_diff_scaled
                player.mmr = math.ceil(player.mmr)
                player.losses += 1

            for player in self.team2:
                player.mmr += 20 * self.mmr_diff_scaled
                player.mmr = math.ceil(player.mmr)
                player.wins += 1

        [player.update() for player in self.team1 + self.team2]

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


class MatchEmbed(discord.Embed):
    def __init__(
        self, team1: list[Player], team2: list[Player], match_creator: discord.Member
    ):
        super().__init__(title="Match in progress", color=0x00FF42)

        self.add_field(
            name=f"Left Team ({int(sum([p.mmr for p in team1]))})",
            value="\n".join([p.discord_name for p in team1]),
        )
        self.add_field(
            name=f"Right Team ({int(sum([p.mmr for p in team2]))})",
            value="\n".join([p.discord_name for p in team2]),
        )
        self.set_footer(text=f"Creator: {match_creator.name}")


class MatchControlView(discord.ui.View):  # ändra till playersembed
    def __init__(
        self,
        bot,
        match: CustomMatch,
        match_message: discord.Message,
        match_embed: discord.Embed,
    ):
        super().__init__(timeout=7200)

        self.current_embed = None
        self.bot = bot
        self.match_message = match_message
        self.match_embed = match_embed

        self.buttons = [
            discord.ui.Button(
                label="Left Win", style=discord.ButtonStyle.green, custom_id="left_win"
            ),
            discord.ui.Button(
                label="Right Win",
                style=discord.ButtonStyle.green,
                custom_id="right_win",
            ),
            discord.ui.Button(
                label="Discard",
                style=discord.ButtonStyle.red,
                custom_id="discard",
                row=2,
            ),
        ]

        async def win_callback(interaction: discord.Interaction):
            role = discord.utils.get(interaction.guild.roles, name="ingame")
            player_ids = [player.discord_id for player in match.team1 + match.team2]

            if interaction.user != match.creator:
                return

            if interaction.data["custom_id"] == "discard":
                for player_id in player_ids:
                    user = interaction.guild.get_member(player_id)
                    if role in user.roles:
                            await user.remove_roles(role)
                await self.match_message.delete()

            if interaction.data["custom_id"] == "left_win":
                for player_id in player_ids:
                    user = interaction.guild.get_member(player_id)
                    if role in user.roles:
                            await user.remove_roles(role)
                        
                match.finish_match(1)
                match_embed.title = f"Winner: Left Team"
                await match_message.edit(embed=match_embed)
                await interaction.response.edit_message(
                    view=MatchViewDone(self.bot, match),
                )


            if interaction.data["custom_id"] == "right_win":
                for player_id in player_ids:
                    user = interaction.guild.get_member(player_id)
                    if role in user.roles:
                            await user.remove_roles(role)
                match.finish_match(2)
                match_embed.title = f"Winner: Right Team"
                await match_message.edit(embed=match_embed)
                await interaction.response.edit_message(
                    view=MatchViewDone(self.bot, match),
                )

        for button in self.buttons:
            button.callback = win_callback
            self.add_item(button)


class MatchViewDone(discord.ui.View):
    def __init__(self, bot, match: CustomMatch):
        super().__init__(timeout=7200)

        self.current_embed = None
        self.bot = bot
        self.match = match

        self.buttons = [
            discord.ui.Button(
                label="Rematch",
                style=discord.ButtonStyle.blurple,
                custom_id="rematch",
                row=2,
            )
        ]

        async def win_callback(interaction: discord.Interaction):
            if interaction.user != match.creator:
                return

            if interaction.data["custom_id"] == "rematch":
                await start_match(
                    match.team1,
                    match.team2,
                    bot,
                    match.creator,
                    interaction.channel,
                    interaction,
                )

                return

        for button in self.buttons:
            button.callback = win_callback
            self.add_item(button)


class QueueEmbed(discord.Embed):
    def __init__(
        self, queue: list[Player], vc_members_names: list[str], creator: discord.Member
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


class QueueView(discord.ui.View):
    def __init__(self, bot, voice_channel: discord.VoiceChannel,role:discord.Role):
        super().__init__(timeout=10800)  # I think 3 hours
        self.db = Database(bot, "data/league.sqlite")
        self.bot = bot
        self.voice_channel = voice_channel

        self.buttons = [
            discord.ui.Button(
                label="Join Queue",
                style=discord.ButtonStyle.green,
                custom_id="join_queue",
            ),
            discord.ui.Button(
                label="Leave Queue",
                style=discord.ButtonStyle.red,
                custom_id="leave_queue",
            ),
        ]

        self.queue: list[discord.abc.User | discord.abc.Member] = []

        async def queue_callback(interaction: discord.Interaction):
            if interaction.data["custom_id"] == "join_queue":
                if interaction.user not in self.queue:
                    self.queue.append(interaction.user)

                vc_members_names = [m.name for m in self.voice_channel.members]

                await interaction.message.edit(
                    embed=QueueEmbed(
                        [Player(self.bot, p.id, False) for p in self.queue],
                        vc_members_names,
                        Player(
                            self.bot,
                            discord_name=interaction.message.embeds[0].footer.text[9:],
                        ).discord_member_object,
                    ),
                )

            if interaction.data["custom_id"] == "leave_queue":
                if interaction.user in self.queue:
                    self.queue.remove(interaction.user)

                vc_members_names = [m.name for m in self.voice_channel.members]
                await interaction.message.edit(
                    embed=QueueEmbed(
                        [Player(self.bot, p.id, False) for p in self.queue],
                        vc_members_names,
                        Player(
                            self.bot,
                            discord_name=interaction.message.embeds[0].footer.text[9:],
                        ).discord_member_object,
                    ),
                )
            await interaction.response.defer()

        for button in self.buttons:
            button.callback = queue_callback
            self.add_item(button)


class RemovePlayerFromQueueSelect(discord.ui.Select):
    def __init__(self, players: list[discord.User]):
        options = [discord.SelectOption(label="Noone", description="Remove Noone")] + [
            discord.SelectOption(label=p.name) for p in players
        ]
        super().__init__(
            placeholder="Select player to remove",
            custom_id="remove_queue_select",
            max_values=1,
            min_values=1,
            options=options,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            content=f"Your choice is {self.values[0]}!", ephemeral=True
        )


class QueueControlView(discord.ui.View):
    def __init__(
        self,
        bot,
        queue_message: discord.Message,
        queue_view: QueueView,
        players=[],
        voice: discord.VoiceChannel = None,
    ):
        super().__init__(timeout=10800)  # I think 3 hours
        self.db = Database(bot, "data/league.sqlite")
        self.bot = bot
        self.queue_message = queue_message
        self.queue_view = queue_view
        self.voice = voice
        self.buttons = [
            discord.ui.Button(
                label="Start match",
                style=discord.ButtonStyle.green,
                custom_id="start",
                row=0,
            ),
            discord.ui.Button(
                label="Discard",
                style=discord.ButtonStyle.red,
                custom_id="discard",
                row=0,
            ),
            discord.ui.Button(
                label="Update remove list",
                style=discord.ButtonStyle.blurple,
                custom_id="update_remove",
                row=3,
            ),
        ]
        if len(players) > 0:
            self.buttons.append(RemovePlayerFromQueueSelect(players))

        async def queue_callback(interaction: discord.Interaction):
            if interaction.data["custom_id"] == "discard":
                await self.queue_message.delete()
                await interaction.response.defer()
                return

            if interaction.data["custom_id"] == "start" or len(queue_view.queue) == 10:
                role = discord.utils.get(interaction.guild.roles, name="ingame")
                if len(queue_view.queue) < 2:
                    await interaction.response.send_message(
                        "Not enough players in queue", ephemeral=True
                    )
                    return
                await interaction.response.defer()
                
                for user in queue_view.queue:
                    if role  not in user.roles:
                            await user.add_roles(role)
                        
                await interaction.channel.send(f"<@&{role.id}>")

                team1, team2 = generate_teams(
                    [Player(self.bot, p.id, False) for p in queue_view.queue]
                )
                print("g",interaction, interaction.response.is_done())
                await start_match(
                    team1,
                    team2,
                    self.bot,
                    interaction.user,
                    interaction.channel,
                    interaction,
                )
            if interaction.data["custom_id"] == "remove_queue_select":
                queue_view.queue = [
                    p
                    for p in queue_view.queue
                    if p.name != interaction.data["values"][0]
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
                        ).discord_member_object,
                    )
                )
                await interaction.response.edit_message(
                    view=QueueControlView(
                        self.bot,
                        self.queue_message,
                        self.queue_view,
                        queue_view.queue,
                        voice=self.voice,
                    )
                )

            if interaction.data["custom_id"] == "update_remove":
                self.add_item(RemovePlayerFromQueueSelect(queue_view.queue))
                await interaction.response.edit_message(
                    view=QueueControlView(
                        self.bot,
                        self.queue_message,
                        self.queue_view,
                        queue_view.queue,
                        voice=self.voice,
                    )
                )

        for button in self.buttons:
            button.callback = queue_callback
            self.add_item(button)


async def start_match(
    team1: list[Player],
    team2: list[Player],
    bot,
    creator: discord.Member,
    channel: discord.TextChannel,
    interaction: discord.Interaction,
):
    match = CustomMatch(bot, creator, team1, team2)

    embed = MatchEmbed(team1, team2, creator)

    #await channel.send(
        #"".join([p.discord_member_object.mention for p in team1 + team2])
    #)
    match_message = await channel.send(embed=embed)

    view = MatchControlView(bot, match, match_message, embed)
    await interaction.followup.send("Match Control", view=view, ephemeral=True)

    bettervc_category_obj: discord.CategoryChannel = bot.get_channel(
        int(os.getenv("BETTERVC_CATEGORY_ID"))
    )
    if bettervc_category_obj:
        bettervc_channels = bettervc_category_obj.channels
        for channel in bettervc_channels:
            if len(channel.members) == 0 and channel.name[0] != "|":
                for p in team1:
                    if p.discord_member_object.voice:
                        await p.discord_member_object.move_to(channel)
                break


class FreeEmbed(discord.Embed):
    def __init__(
        self, team1: list[Player], team2: list[Player], creator: discord.Member
    ):
        super().__init__(title="Create teams", color=0x00FF42)

        self.add_field(name="Team 1", value="\n".join([p.discord_name for p in team1]))
        self.add_field(name="Team 2", value="\n".join([p.discord_name for p in team2]))
        self.set_footer(text=f"Creator: {creator.name}")


class FreeView(discord.ui.View):
    def __init__(self, bot, creator: discord.Member):
        super().__init__(timeout=10800)
        self.bot = bot

        self.buttons = [
            discord.ui.Button(
                label="Join team 1",
                style=discord.ButtonStyle.blurple,
                custom_id="join_team_1",
            ),
            discord.ui.Button(
                label="Join team 2",
                style=discord.ButtonStyle.blurple,
                custom_id="join_team_2",
            ),
            discord.ui.Button(
                label="Start match",
                style=discord.ButtonStyle.green,
                custom_id="start",
                row=2,
            ),
            discord.ui.Button(
                label="Discard",
                style=discord.ButtonStyle.red,
                custom_id="discard",
                row=2,
            ),
        ]

        self.team1 = []
        self.team2 = []

        async def free_callback(interaction: discord.Interaction):
            if interaction.data["custom_id"] == "join_team_1":
                if interaction.user in self.team1:
                    self.team1.remove(interaction.user)
                elif interaction.user in self.team2:
                    self.team2.remove(interaction.user)
                    self.team1.append(interaction.user)
                else:
                    self.team1.append(interaction.user)

                await interaction.message.edit(
                    embed=FreeEmbed(
                        [Player(self.bot, p.id, False) for p in self.team1],
                        [Player(self.bot, p.id, False) for p in self.team2],
                        creator,
                    ),
                    view=self,
                )
                await interaction.response.defer()
                return

            if interaction.data["custom_id"] == "join_team_2":
                if interaction.user in self.team2:
                    self.team2.remove(interaction.user)
                elif interaction.user in self.team1:
                    self.team1.remove(interaction.user)
                    self.team2.append(interaction.user)
                else:
                    self.team2.append(interaction.user)

                await interaction.message.edit(
                    embed=FreeEmbed(
                        [Player(self.bot, p.id, False) for p in self.team1],
                        [Player(self.bot, p.id, False) for p in self.team2],
                        creator,
                    ),
                    view=self,
                )
                await interaction.response.defer()
                return

            if interaction.data["custom_id"] == "start":
                if len(self.team1) < 1 or len(self.team2) < 1:
                    await interaction.response.send_message(
                        "Not enough players in queue", ephemeral=True
                    )
                    return
                player_team_1 = [Player(self.bot, p.id, False) for p in self.team1]
                player_team_2 = [Player(self.bot, p.id, False) for p in self.team2]

                await start_match(
                    player_team_1,
                    player_team_2,
                    self.bot,
                    interaction.user,
                    interaction.channel,
                    interaction,
                )
                await interaction.message.delete()
                return

            if interaction.data["custom_id"] == "discard":
                await interaction.message.delete()
                return

        for button in self.buttons:
            button.callback = free_callback
            self.add_item(button)


class PlayerMatchesView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=7200)

        self.embeds = embeds
        self.current_embed = None

        self.buttons = [
            discord.ui.Button(
                label="Previous",
                style=discord.ButtonStyle.blurple,
                custom_id="prev",
                row=1,
            ),
            discord.ui.Button(
                label="Next", style=discord.ButtonStyle.blurple, custom_id="next", row=1
            ),
            discord.ui.Button(
                label="Discard",
                style=discord.ButtonStyle.red,
                custom_id="discard",
                row=2,
            ),
        ]

        async def callback(interaction: discord.Interaction):
            self.current_embed = interaction.message.embeds[0]

            if interaction.data["custom_id"] == "discard":
                await interaction.message.delete()
                return

            if interaction.data["custom_id"] == "prev":
                self.current_embed = self.embeds[
                    self.embeds.index(self.current_embed) - 1
                ]
                await interaction.response.defer()
            elif interaction.data["custom_id"] == "next":
                self.current_embed = self.embeds[
                    self.embeds.index(self.current_embed) + 1
                ]
                await interaction.response.defer()

            await interaction.message.edit(embed=self.current_embed, view=self)

        for button in self.buttons:
            button.callback = callback
            self.add_item(button)


class MmrGraphEmbed(discord.Embed):
    def __init__(self, player: discord.Member):
        super().__init__(title="MMR Graph", color=0x00FF42)
        self.set_image(url=f"attachment://{os.getenv('LEAGUE_GRAPH_FILENAME')}")
        self.set_footer(text=f"Player: {player.name}")


def mmr_graph(bot, player: discord.Member):
    db = Database(bot, "data/league.sqlite")
    res = db.cursor.execute(
        f"SELECT mmr, timestamp FROM mmr_history WHERE discord_id = {player.id}"
    ).fetchall()
    df = pd.DataFrame(res)
    fig = px.line(df, x=1, y=0)
    fig.write_image(os.getenv("LEAGUE_GRAPH_DIR") + os.getenv("LEAGUE_GRAPH_FILENAME"))
    file = discord.File(
        os.getenv("LEAGUE_GRAPH_DIR") + os.getenv("LEAGUE_GRAPH_FILENAME"),
        os.getenv("LEAGUE_GRAPH_FILENAME"),
    )
    return file


def generate_teams(players: list[Player]) -> tuple[list[Player], list[Player]]:
    num_players = len(players)
    
    if num_players > 10:
        raise ValueError("numplayers > 10")

    team_size = num_players // 2
    best_teams = None
    best_diff = float('inf')

    for team1_indices in combinations(range(num_players), team_size):
        team1 = [players[i] for i in team1_indices]
        team2 = [players[i] for i in range(num_players) if i not in team1_indices]

        team1_mmr = sum(player.mmr for player in team1)
        team2_mmr = sum(player.mmr for player in team2)
        diff = abs(team1_mmr - team2_mmr)

        if diff < best_diff:
            best_diff = diff
            best_teams = (team1, team2)

    return best_teams
