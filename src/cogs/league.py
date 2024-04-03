from discord.ext import commands
import discord
import random
from typing import Optional, List, Union, Literal

import lib.persmissions as permissions
from lib.league import (
    Database,
    Player,
    CustomMatch,
    Tournament,
    CustomMatch,
    generate_teams,
    MatchEmbed,
    MatchView,
    ranks_mmr,
    ranks_type,
    QueueView,
    QueueEmbed,
    PlayerMatchesView,
    Match,
)


class league(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(bot, "data/league.sqlite")

    @commands.hybrid_group(name="league", description="League commands")
    async def league(self, ctx: commands.Context):
        pass

    @league.command(
        name="customs",
        description="Creates a league custom match instance with teams from the current voice channel.",
    )
    @permissions.admin()
    @permissions.voice()
    async def customs(
        self,
        ctx: commands.Context,
        toggle_player_1: Optional[discord.Member],
        toggle_player_2: Optional[discord.Member],
        toggle_player_3: Optional[discord.Member],
        toggle_player_4: Optional[discord.Member],
        toggle_player_5: Optional[discord.Member],
        toggle_player_6: Optional[discord.Member],
        toggle_player_7: Optional[discord.Member],
        toggle_player_8: Optional[discord.Member],
    ):
        member_players = ctx.author.voice.channel.members

        toggle_additional_players = [
            toggle_player_1,
            toggle_player_2,
            toggle_player_3,
            toggle_player_4,
            toggle_player_5,
            toggle_player_6,
            toggle_player_7,
            toggle_player_8,
        ]
        toggle_additional_players = [
            i for i in toggle_additional_players if i is not None
        ]

        for player in toggle_additional_players:
            removed = False
            for toggle_player in member_players:
                if toggle_player.id == player.id:
                    member_players.remove(toggle_player)
                    removed = True
            if not removed:
                if player not in member_players:
                    member_players.append(player)

        if len(member_players) < 2:
            await ctx.reply(
                embed=discord.Embed(
                    title=f"Not enough players in voice channel!", color=0xFF0000
                )
            )
            return

        players = [Player(self.bot, i.id) for i in member_players]
        team1, team2 = generate_teams(players)
        custom_match = CustomMatch(self.bot, ctx.author, team1, team2)

        embed = MatchEmbed(team1, team2)
        view = MatchView(self.bot, custom_match, embed)

        await ctx.reply(embed=embed, view=view)

    @league.command(
        name="queue",
        description="Creates a customs queue to automatically be placed in fair teams",
    )
    async def queue(self, ctx: commands.Context):
        embed = QueueEmbed([])
        view = QueueView(self.bot)
        await ctx.reply(embed=embed, view=view)

    @league.command(
        name="arena",
        description="Creates arena with teams from the current voice channel.",
    )
    @permissions.admin()
    @permissions.voice()
    async def arena(
        self,
        ctx: commands.Context,
        toggle_player_1: Optional[discord.Member],
        toggle_player_2: Optional[discord.Member],
        toggle_player_3: Optional[discord.Member],
        toggle_player_4: Optional[discord.Member],
        toggle_player_5: Optional[discord.Member],
        toggle_player_6: Optional[discord.Member],
        toggle_player_7: Optional[discord.Member],
        toggle_player_8: Optional[discord.Member],
    ):
        voice_players = ctx.author.voice.channel.members

        toggle_additional_players = [
            toggle_player_1,
            toggle_player_2,
            toggle_player_3,
            toggle_player_4,
            toggle_player_5,
            toggle_player_6,
            toggle_player_7,
            toggle_player_8,
        ]
        toggle_additional_player_ids = [
            i.id for i in toggle_additional_players if i is not None
        ]
        players = [
            player
            for player in voice_players
            if player.id not in toggle_additional_player_ids
        ]

        if len(players) > 8:
            await ctx.reply(
                embed=discord.Embed(
                    title=f"Too many players in voice channel!", color=0xFF0000
                )
            )
            return

        random.shuffle(players)
        embed = discord.Embed(
            title="Arena teams", description=self.bot.description, color=0x00FF42
        )
        for i in range(len(players) // 2):
            embed.add_field(
                name=f"Team {i*2}",
                value=f"'{players[i*2].name}' and '{players[i*2+1].name}'",
            )

        await ctx.reply(embed=embed)

    @league.command(
        name="setrank", description=f"Sets a player's rank to a given rank or mmr"
    )
    @permissions.admin()
    async def set_rank(
        self,
        ctx: commands.Context,
        member: discord.Member,
        rank: Optional[ranks_type],
        mmr: Optional[int],
    ):
        if rank is not None:
            mmr = ranks_mmr[rank]
        elif mmr is not None:
            mmr = int(mmr)

        player = Player(self.bot, member.id)
        player.mmr = mmr
        player.update()

        await ctx.reply(
            embed=discord.Embed(
                title=f"{member.name}'s mmr has been set to {rank if rank is not None else mmr}: {mmr}",
                color=0x00FF42,
            )
        )

    @league.command(name="getmmr", description=f"Gets a player's mmr")
    @permissions.admin()
    async def get_mmr(self, ctx: commands.Context, member: discord.Member):
        player = Player(self.bot, member.id)
        await ctx.reply(
            embed=discord.Embed(
                title=f"{member.name}'s mmr is {player.mmr}", color=0x00FF42
            )
        )

    @league.command(name="players", description=f"Displays all players.")
    async def players(self, ctx: commands.Context):
        players = self.db.get_all_players()

        embed = discord.Embed(title=f"Players", color=0x00FF42)
        embed.add_field(name="Name", value="\n".join([p.discord_name for p in players]))
        embed.add_field(
            name="Win rate", value="\n".join([f"{p.win_rate:.1f}%" for p in players])
        )
        embed.add_field(
            name="Matches", value="\n".join([f"{len(p.matches)}" for p in players])
        )

        await ctx.reply(embed=embed)

    @league.group(name="remove", description=f"Remove commands")
    async def remove(self, ctx: commands.Context):
        pass

    @remove.command(
        name="player", description=f"Removes a player record from the database."
    )
    @permissions.admin()
    async def player(self, ctx: commands.Context, member: discord.Member):
        self.db.remove_player(member)
        await ctx.reply(
            embed=discord.Embed(
                title=f"{member.name}'s record has been removed from the database",
                color=0x00FF42,
            )
        )

    @remove.command(
        name="match", description=f"Removes a match record from the database."
    )
    @permissions.admin()
    async def match(self, ctx: commands.Context, match_id: int):
        self.db.remove_match(match_id)
        await ctx.reply(
            embed=discord.Embed(
                title=f"Match {match_id} has been removed from the database",
                color=0x00FF42,
            )
        )

    @league.command(name="matches", description=f"Displays a players matches")
    async def matches(self, ctx: commands.Context, member: Optional[discord.Member]):
        player = Player(self.bot, member.id) if member else None
        embeds = []
        matches = player.matches if player else self.db.get_all_matches()

        if len(matches) == 0:
            await ctx.reply(
                embed=discord.Embed(title=f"No matches found", color=0xFF0000)
            )
            return

        for i, match in enumerate(matches):
            match: Match
            if player:
                embed = discord.Embed(
                    title=f"{player.discord_name}\t({i+1}/{len(matches)})",
                    color=0x00FF42,
                )
            else:
                embed = discord.Embed(
                    title=f"{match.match_id}\t({i+1}/{len(matches)})", color=0x00FF42
                )

            embed.add_field(
                name=f"Team 1",
                value=f"\n".join([f"{p.discord_name}" for p in match.team1]),
            )
            embed.add_field(
                name=f"Team 2",
                value=f"\n".join([f"{p.discord_name}" for p in match.team2]),
            )
            embed.add_field(name=f"Date", value=f"{match.timestamp[:10]}", inline=False)
            embed.add_field(name=f"Result", value=f"Team {match.winner}")
            embeds.append(embed)

        if not embeds:
            await ctx.reply(
                embed=discord.Embed(
                    title=f"{member.name} has no matches!", color=0xFF0000
                )
            )
            return

        view = PlayerMatchesView(embeds)

        await ctx.reply(embed=embeds[0], view=view)


async def setup(bot):
    await bot.add_cog(league(bot))
