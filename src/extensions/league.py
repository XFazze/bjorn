import random
import math
import logging
from typing import Literal, List, Optional, Union, Sequence
import discord
from discord.ext import commands
from discord import Role, Member

import lib.permissions as permissions
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
    StatisticsGeneralEmbed,
    StatisticsGeneralView,
    StatisticsTeamatesEnemiesEmbed,
    StatisticsTeamatesEnemiesView,
    start_match,
    MmrGraphEmbed,
)

from lib.config import (
    ConfigTables,
    show_roles,
    set_value,
    remove_value,
)


logger = logging.getLogger(__name__)


class league_cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database(bot)
        self.MAX_PLAYERS = 10
        logger.info("League cog initialized")

    async def _filter_voice_channel_players(
        self, ctx: commands.Context, toggle_players: Sequence[discord.Member]
    ) -> list[discord.Member]:
        """Helper method to filter players in a voice channel."""
        voice_players = ctx.author.voice.channel.members
        toggle_player_ids = [p.id for p in toggle_players]
        return [p for p in voice_players if p.id not in toggle_player_ids]

    @commands.hybrid_group(name="league", description="League commands")
    async def league(self, ctx: commands.Context):
        pass

    @league.command(
        name="queue",
        description="Creates a customs queue to automatically be placed in fair teams",
    )
    async def queue(self, ctx: commands.Context):
        try:
            if not ctx.author.voice:
                await ctx.reply(
                    embed=discord.Embed(
                        title="You must be in a voice channel to use this command!",
                        color=0xFF0000,
                    )
                )
                logger.debug(
                    f"User {ctx.author.name} tried to use queue without being in a voice channel"
                )
                return

            vc_members_names = [
                member.name for member in ctx.author.voice.channel.members
            ]
            role = discord.utils.get(ctx.guild.roles, name="ingame")
            for member in ctx.guild.members:
                if role in member.roles:
                    await member.remove_roles(role)

            embed = QueueEmbed([], vc_members_names, ctx.author)
            voice = ctx.author.voice.channel
            view = QueueView(self.bot, voice)
            message = await ctx.reply(embed=embed, view=view)

            view = QueueControlView(self.bot, message, view, voice=voice)
            await ctx.interaction.followup.send(
                "Queue control", view=view, ephemeral=True
            )
            logger.info(f"Queue created by {ctx.author.name} in {ctx.guild.name}")
        except Exception as e:
            logger.error(f"Error creating queue: {str(e)}", exc_info=True)
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while creating the queue.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @league.command(name="free_teams", description="Create your own teams.")
    async def free_teams(self, ctx: commands.Context):
        try:
            embed = FreeEmbed([], [], ctx.author)
            view = FreeView(self.bot, ctx.author)
            await ctx.reply(embed=embed, view=view)
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while creating free teams.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @league.command(
        name="arena",
        description="Creates arena with teams from the current voice channel.",
    )
    @permissions.voice()
    async def arena(
        self,
        ctx: commands.Context,
        toggle_players: commands.Greedy[discord.Member] = None,
    ):
        if toggle_players is None:
            toggle_players = []
        try:
            if not ctx.author.voice:
                await ctx.reply(
                    embed=discord.Embed(
                        title="You must be in a voice channel to use this command!",
                        color=0xFF0000,
                    )
                )
                return

            players = await self._filter_voice_channel_players(ctx, toggle_players)

            if len(players) > self.MAX_PLAYERS:
                await ctx.reply(
                    embed=discord.Embed(
                        title="Too many players in the voice channel!",
                        color=0xFF0000,
                    )
                )
                return

            random.shuffle(players)
            embed = discord.Embed(
                title="Arena Teams",
                description="Teams generated from the voice channel.",
                color=0x00FF42,
            )
            for i in range(0, len(players), 2):
                embed.add_field(
                    name=f"Team {i // 2 + 1}",
                    value=f"{players[i].name} and {players[i + 1].name}",
                    inline=False,
                )

            await ctx.reply(embed=embed)
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while creating the arena.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

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
        rank: Optional[ranks_type] = None,
        mmr: Optional[int] = None,
    ):
        try:
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
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while setting the MMR.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @rating.command(name="get", description="Get rank or mmr")
    async def mmr_get(
        self,
        ctx: commands.Context,
        member: discord.Member,
        rating_type: Literal["Rank", "MMR"],
    ):
        try:
            player = Player(self.bot, member.id)

            if rating_type == "Rank":
                rank = None
                for i, j in ranks_mmr.items():
                    if player.mmr < j:
                        break
                    rank = i

                await ctx.reply(
                    embed=discord.Embed(
                        title=f"{member.name}'s current rank is {rank}",
                        color=0x00FF42,
                    )
                )

            elif rating_type == "MMR":
                await ctx.interaction.response.send_message(
                    embed=discord.Embed(
                        title=f"{member.name}'s mmr is {player.mmr}", color=0x00FF42
                    )
                )
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while getting the MMR.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @rating.command(name="list", description="Get all ranks and equivalent MMRs")
    async def mmr_list(self, ctx: commands.Context):
        try:
            embed = discord.Embed(title="League ranks")
            embed.add_field(name="Rank", value="\n".join([i for i in ranks_mmr.keys()]))
            embed.add_field(
                name="MMR", value="\n".join([str(i) for i in ranks_mmr.values()])
            )

            await ctx.reply(embed=embed)
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while listing the MMRs.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @rating.command(
        name="graph", description="Get a users league customs mmr graph over time"
    )
    async def mmr_graph(self, ctx: commands.Context, player: discord.Member = None):
        try:
            if player is None:
                player = ctx.author
            file = mmr_graph(self.bot, player)
            embed = MmrGraphEmbed(self.bot, player)
            await ctx.reply(file=file, embed=embed)
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while generating the MMR graph.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @league.group(name="statistics", description="Various statistics related commands")
    async def statistics(self, ctx: commands.Context):
        pass

    @statistics.command(name="general", description=f"Displays all players.")
    async def general(self, ctx: commands.Context):
        try:
            # Create a loading embed instead of just text
            loading_embed = discord.Embed(
                title="League Statistics Loading...",
                description="Please wait while we gather player statistics",
                color=0xFFA500  # Orange color for loading state
            )
            loading_embed.set_footer(text="This may take a few moments")
            
            # Send the loading embed
            await ctx.interaction.response.send_message(embed=loading_embed, ephemeral=True)
            
            # Fetch and process the data
            players = self.db.get_all_players()
            
            match_counts_cache = {}
            for p in players:
                match_counts_cache[p.discord_id] = len(p.get_matches())
            
            players = sorted(players, key=lambda p: -match_counts_cache.get(p.discord_id, 0))

            # Create and display the actual data with the match_counts_cache
            embed = StatisticsGeneralEmbed(players, match_counts_cache)
            view = StatisticsGeneralView(players, match_counts_cache)
            
            message = await ctx.interaction.original_response()
            await message.edit(embed=embed, view=view)
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while displaying general statistics.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @statistics.command(
        name="teamates_enemies",
        description=f"Displays wr & matches with different teamates and enemies.",
    )
    async def teamates_enemies(
        self, ctx: commands.Context, target_player: Optional[discord.Member] = None
    ):
        try:
            await ctx.interaction.response.send_message(
                "League player teamates statistics loading", ephemeral=True
            )
            if target_player is None:
                target_player = ctx.author

            logger.info(
                f"Generating teammates/enemies statistics for {target_player.name}"
            )
            matches: list[Match] = self.db.get_matches(target_player.id)
            teamates = {}
            enemies = {}
            for match in matches:
                team = 1
                if target_player.id in [p.discord_id for p in match.team2]:
                    team = 2
                for player in match.team1:
                    if not player.user_exists:
                        continue
                    if player.discord_name not in teamates.keys():
                        teamates[player.discord_name] = {"wins": 0, "losses": 0}
                        enemies[player.discord_name] = {"wins": 0, "losses": 0}

                    if match.winner == 1:
                        if team == 1:
                            teamates[player.discord_name]["wins"] += 1
                        else:
                            enemies[player.discord_name]["wins"] += 1

                    elif match.winner == 2:
                        if team == 1:
                            teamates[player.discord_name]["losses"] += 1
                        else:
                            enemies[player.discord_name]["losses"] += 1

                for player in match.team2:
                    if not player.user_exists:
                        continue
                    if player.discord_name not in teamates.keys():
                        teamates[player.discord_name] = {"wins": 0, "losses": 0}
                        enemies[player.discord_name] = {"wins": 0, "losses": 0}

                    if match.winner == 1:
                        if team == 2:
                            enemies[player.discord_name]["losses"] += 1
                        else:
                            teamates[player.discord_name]["losses"] += 1

                    elif match.winner == 2:
                        if team == 2:
                            enemies[player.discord_name]["wins"] += 1
                        else:
                            teamates[player.discord_name]["wins"] += 1

            teamates = [
                {"name": key, "wins": p["wins"], "losses": p["losses"]}
                for key, p in teamates.items()
            ]
            teamates = sorted(teamates, key=lambda p: -p["wins"] - p["losses"])
            enemies = [
                {"name": key, "wins": p["wins"], "losses": p["losses"]}
                for key, p in enemies.items()
            ]
            enemies = sorted(enemies, key=lambda p: -p["wins"] - p["losses"])

            player = Player(self.bot, target_player.id)
            embed = StatisticsTeamatesEnemiesEmbed(
                player.win_rate,
                target_player.display_name
                + " Teammates statistics",  # Added space for better readability
                teamates,
            )
            view = StatisticsTeamatesEnemiesView(
                player.win_rate, teamates, enemies, target_player.display_name
            )
            message = await ctx.interaction.original_response()
            await message.edit(embed=embed, view=view)
            logger.debug(f"Successfully displayed statistics for {target_player.name}")
        except Exception as e:
            logger.error(
                f"Error displaying teammates statistics: {str(e)}", exc_info=True
            )
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while displaying teamates and enemies statistics.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @league.group(name="remove", description=f"Remove commands")
    async def remove(self, ctx: commands.Context):
        pass

    @remove.command(
        name="player", description=f"Removes a player record from the database."
    )
    @permissions.admin()
    async def player(self, ctx: commands.Context, member: discord.Member):
        try:
            self.db.remove_player(member)
            await ctx.reply(
                embed=discord.Embed(
                    title=f"{member.name}'s record has been removed from the database",
                    color=0x00FF42,
                )
            )
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while removing the player.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @remove.command(
        name="match", description=f"Removes a match record from the database."
    )
    @permissions.admin()
    async def match(self, ctx: commands.Context, match_id: int):
        try:
            logger.info(f"Admin {ctx.author.name} removing match {match_id}")
            self.db.remove_match(match_id)
            await ctx.reply(
                embed=discord.Embed(
                    title=f"Match {match_id} has been removed from the database",
                    color=0x00FF42,
                )
            )
        except Exception as e:
            logger.error(f"Error removing match {match_id}: {str(e)}", exc_info=True)
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while removing the match.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @league.command(name="matches", description=f"Displays a players matches")
    async def matches(
        self, ctx: commands.Context, member: Optional[discord.Member] = None
    ):
        try:
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
                embed.add_field(
                    name=f"Date", value=f"{str(match.timestamp)[:10]}", inline=False
                )
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
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while displaying matches.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @commands.hybrid_group(description="ingame role manage commands")
    async def ingame_role_manage(self, ctx: commands.Context):
        pass

    @ingame_role_manage.command(description="Show the ingame_role for the server.")
    @permissions.admin()
    async def show_ingame_role(self, ctx: commands.Context):
        try:
            await show_roles(self.bot, ctx, ConfigTables.INGAMEROLE, ctx.guild.id)
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while showing the ingame role.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @ingame_role_manage.command(description="Set a ingame_role for the server.")
    @permissions.admin()
    async def set_ingame_role(self, ctx: commands.Context, role: Role):
        try:
            await set_value(
                self.bot, ctx, ConfigTables.INGAMEROLE, ctx.guild.id, role.id
            )
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while setting the ingame role.",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @ingame_role_manage.command(description="Remove a ingame_role for the server.")
    @permissions.admin()
    async def remove_ingame_role(self, ctx: commands.Context, role: Role):
        try:
            await remove_value(
                self.bot, ctx, ConfigTables.INGAMEROLE, ctx.guild.id, role.id
            )
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while removing the ingame role.",
                    description=str(e),
                    color=0xFF0000,
                )
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(league_cog(bot))
    logger.info("League cog loaded")
