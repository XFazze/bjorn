import random
import math
from typing import Literal
import discord
from discord.ext import commands
from discord import Role

import lib.persmissions as permissions
from lib.league import (
    Database,
    Player,
    generate_teams,
    mmr_graph,
    ranks_mmr,
    ranks_type,
    QueueView,
    QueueEmbed,
    QueueControlView,
    PlayerMatchesView,
    Match,
    FreeEmbed,
    FreeView,
    PlayersEmbed,
    PlayersView,
    start_match,
    MmrGraphEmbed,
)

from lib.config import (
    ConfigTables,
    show_roles,
    set_value,
    remove_value,
    show_roles,
)


class league_cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database(bot)

    @commands.hybrid_group(name="league", description="League commands")
    async def league(self, ctx: commands.Context):
        pass


    @league.command(
        name="queue",
        description="Creates a customs queue to automatically be placed in fair teams",
    )
    async def queue(self, ctx: commands.Context):
        vc_members_names = []
        if ctx.author.voice:
            vc_members_names = [
                member.name for member in ctx.author.voice.channel.members
            ]
        role = discord.utils.get(ctx.guild.roles, name="ingame")
        for member in ctx.guild.members:
            if role in member.roles:
                await member.remove_roles(role)

        embed = QueueEmbed([], vc_members_names, ctx.author)
        if ctx.author.voice:
            voice = ctx.author.voice.channel
        else:
            voice = None
        view = QueueView(self.bot, voice)
        message = await ctx.reply(embed=embed, view=view)

        view = QueueControlView(self.bot, message, view, voice=voice)
        await ctx.interaction.followup.send("Queue control", view=view, ephemeral=True)

    @league.command(name="free_teams", description="Create your own teams.")
    async def free_teams(self, ctx: commands.Context):
        embed = FreeEmbed([], [], ctx.author)
        view = FreeView(self.bot, ctx.author)
        await ctx.reply(embed=embed, view=view)

    @league.command(
        name="arena",
        description="Creates arena with teams from the current voice channel.",
    )
    @permissions.voice()
    async def arena(
        self,
        ctx: commands.Context,
        toggle_player_1: discord.Member | None = None,
        toggle_player_2: discord.Member | None = None,
        toggle_player_3: discord.Member | None = None,
        toggle_player_4: discord.Member | None = None,
        toggle_player_5: discord.Member | None = None,
        toggle_player_6: discord.Member | None = None,
        toggle_player_7: discord.Member | None = None,
        toggle_player_8: discord.Member | None = None,
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

    @league.group(name="rating", description="Various mmr related commands")
    async def rating(self, ctx: commands.Context):
        pass

    @rating.command(
        name="set", description="Sets a player's rank to a given rank or mmr"
    )
    @permissions.admin()
    async def mmr_set(
        self,
        ctx: commands.Context,
        member: discord.Member,
        rank: ranks_type = None,
        mmr: int = None,
    ):
        if rank is not None:
            mmr = ranks_mmr[rank]
        elif mmr is not None:
            mmr = int(mmr)

        player = Player(self.bot, member.id)
        player.mmr = mmr
        player.update()

        await ctx.interaction.response.send_message(
            embed=discord.Embed(
                title=f"{member.name}'s mmr has been set to {rank if rank is not None else mmr}: {mmr}",
                color=0x00FF42,
            )
        )

    @rating.command(name="get", description="Get rank or mmr")
    async def mmr_get(
        self,
        ctx: commands.Context,
        member: discord.Member,
        rating_type: Literal["Rank", "MMR"],
    ):
        player = Player(self.bot, member.id)

        if rating_type == "Rank":
            for i, j in ranks_mmr.items():
                if player.mmr < j:
                    rank = i
                    break

            await ctx.reply(
                embed=discord.Embed(
                    title=f"{member.name}'s current rank is close to {rank}",
                    color=0x00FF42,
                )
            )

        elif rating_type == "MMR":
            await ctx.interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{member.name}'s mmr is {player.mmr}", color=0x00FF42
                )
            )

    @rating.command(name="list", description="Get all ranks and equivalent MMRs")
    async def mmr_list(self, ctx: commands.Context):
        embed = discord.Embed(title="League ranks")
        embed.add_field(name="Rank", value="\n".join([i for i in ranks_mmr.keys()]))
        embed.add_field(
            name="MMR", value="\n".join([str(i) for i in ranks_mmr.values()])
        )

        await ctx.reply(embed=embed)

    @rating.command(
        name="graph", description="Get a users league customs mmr graph over time"
    )
    async def mmr_graph(self, ctx: commands.Context, player: discord.Member = None):
        if player is None:
            player = ctx.author
        file = mmr_graph(self.bot, player)
        embed = MmrGraphEmbed(self.bot, player)
        await ctx.reply(file=file, embed=embed)

    @league.command(name="players", description=f"Displays all players.")
    async def players(self, ctx: commands.Context):
        await ctx.interaction.response.send_message(
            "League player statistics loading", ephemeral=True
        )
        players = self.db.get_all_players()
        players = sorted(players, key=lambda p: -len(p.get_matches()))

        embed = PlayersEmbed(players)
        view = PlayersView(players)
        message = await ctx.interaction.original_response()
        await message.edit(embed=embed, view=view)

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
    async def matches(self, ctx: commands.Context, member: discord.Member = None):
        await ctx.interaction.response.send_message(
            "League matches loading", ephemeral=True
        )
        if member is None:
            member = ctx.author
        player = Player(self.bot, member.id) if member else None
        embeds = []
        matches = player.get_matches() if player else self.db.get_all_matches()

        if len(matches) == 0:
            message = await ctx.interaction.original_response()
            await message.edit(
                embed=discord.Embed(title=f"No matches found", color=0xFF0000)
            )
            return

        for i, match in enumerate(matches):
            match: Match
            embed = discord.Embed(
                title=f"{match.match_id}\t({i+1}/{len(matches)})", color=0x00FF42
            )

            embed.add_field(
                name=f"Team 1",
                value=f"\n".join([f"{p.discord_name}" for p in match.team1]),
            )
            embed.add_field(name=f"{math.ceil(match.mmr_diff)}", value="")
            embed.add_field(
                name=f"Team 2",
                value=f"\n".join([f"{p.discord_name}" for p in match.team2]),
            )
            embed.add_field(name=f"Date", value=f"{match.timestamp[:10]}", inline=False)
            embed.add_field(name=f"Result", value=f"Team {match.winner}")
            embeds.append(embed)

        if not embeds:
            message = await ctx.interaction.original_response()
            await message.edit(
                embed=discord.Embed(
                    title=f"{member.name} has no matches!", color=0xFF0000
                )
            )
            return

        view = PlayerMatchesView(embeds)

        message = await ctx.interaction.original_response()
        await message.edit(embed=embeds[0], view=view)

    @commands.hybrid_group(description="ingame role manage commands")
    async def ingame_role_manage(self, ctx: commands.Context):
        pass

    @ingame_role_manage.command(description="Show the ingame_role for the server.")
    @permissions.admin()
    async def show_ingame_role(self, ctx: commands.Context):
        await show_roles(self.bot, ctx, ConfigTables.INGAMEROLE, ctx.guild.id)

    @ingame_role_manage.command(description="Set a ingame_role for the server.")
    @permissions.admin()
    async def set_ingame_role(self, ctx: commands.Context, role: Role):
        await set_value(self.bot, ctx, ConfigTables.INGAMEROLE, ctx.guild.id, role.id)

    @ingame_role_manage.command(description="Remove a ingame_role for the server.")
    @permissions.admin()
    async def remove_ingame_role(self, ctx: commands.Context, role: Role):
        await remove_value(
            self.bot, ctx, ConfigTables.INGAMEROLE, ctx.guild.id, role.id
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(league_cog(bot))
