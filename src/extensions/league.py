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
                    ),
                    ephemeral=True  # Make the message visible only to the command user
                )
                logger.debug(
                    f"User {ctx.author.name} tried to use queue without being in a voice channel"
                )
                return

            # Look for existing queue in last 50 messages
            existing_queue_message = None
            existing_players = []
            
            async for message in ctx.channel.history(limit=50):
                if message.author == self.bot.user and message.embeds:
                    for embed in message.embeds:
                        if embed.title and embed.title.startswith("Queue "):
                            existing_queue_message = message
                            
                            # Extract players from the existing queue
                            if len(embed.fields) > 0 and embed.fields[0].name == "Players":
                                player_names = embed.fields[0].value.split("\n")
                                for name in player_names:
                                    if name and name != "No players in queue":
                                        clean_name = name.replace(" [BOT]", "")
                                        member = discord.utils.get(ctx.guild.members, name=clean_name)
                                        if member:
                                            existing_players.append(member)
                                        else:
                                            fake_player = self._create_fake_queue_member(clean_name)
                                            if fake_player:
                                                existing_players.append(fake_player)
                            break
                    
                    if existing_queue_message:
                        break
            
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
            
            # Add existing players to the new queue
            for player in existing_players:
                view.queue.append(player)
            
            message = await ctx.reply(embed=embed, view=view)
            
            # Delete old queue message if one was found
            if existing_queue_message:
                try:
                    await existing_queue_message.delete()
                    logger.info(f"Deleted old queue message in {ctx.guild.name}")
                except Exception as e:
                    logger.error(f"Error deleting old queue message: {e}")
            
            # Update the embed to show the transferred players
            if existing_players:
                queue_players = []
                for member in view.queue:
                    if hasattr(member, "is_fake") and hasattr(member, "_player"):
                        queue_players.append(member._player)
                    else:
                        try:
                            queue_players.append(Player(self.bot, member.id))
                        except:
                            continue
                
                updated_embed = QueueEmbed(queue_players, vc_members_names, ctx.author)
                await message.edit(embed=updated_embed, view=view)
                logger.info(f"Transferred {len(existing_players)} players from old queue to new queue")

            # Pass the creator parameter explicitly
            view = QueueControlView(self.bot, message, view, voice=voice, creator=ctx.author)
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

    @league.command(
        name="force_start",
        description="Admin command to force start a match from an existing queue",
    )
    @permissions.admin()
    async def force_start(self, ctx: commands.Context):
        try:
            # Defer response if this is an interaction
            if hasattr(ctx, "interaction") and ctx.interaction:
                await ctx.interaction.response.defer()

            # Find the active queue message in the channel
            queue_message = None
            async for message in ctx.channel.history(limit=50):
                if message.author == self.bot.user and message.embeds:
                    for embed in message.embeds:
                        if embed.title and embed.title.startswith("Queue "):
                            queue_message = message
                            break
                    if queue_message:
                        break

            if not queue_message:
                if hasattr(ctx, "interaction") and ctx.interaction:
                    await ctx.followup.send(
                        embed=discord.Embed(
                            title="No Active Queue Found",
                            description="Could not find an active queue in this channel.",
                            color=0xFF0000,
                        )
                    )
                else:
                    await ctx.reply(
                        embed=discord.Embed(
                            title="No Active Queue Found",
                            description="Could not find an active queue in this channel.",
                            color=0xFF0000,
                        )
                    )
                return

            queue_embed = queue_message.embeds[0]

            # Extract players from the embed
            player_names = []
            if len(queue_embed.fields) > 0 and queue_embed.fields[0].name == "Players":
                player_list = queue_embed.fields[0].value
                if player_list != "No players in queue":
                    player_names = player_list.split("\n")

            if not player_names:
                if hasattr(ctx, "interaction") and ctx.interaction:
                    await ctx.followup.send(
                        embed=discord.Embed(
                            title="Empty Queue",
                            description="The queue doesn't have any players.",
                            color=0xFF0000,
                        )
                    )
                else:
                    await ctx.reply(
                        embed=discord.Embed(
                            title="Empty Queue",
                            description="The queue doesn't have any players.",
                            color=0xFF0000,
                        )
                    )
                return

            if len(player_names) < 2:
                if hasattr(ctx, "interaction") and ctx.interaction:
                    await ctx.followup.send(
                        embed=discord.Embed(
                            title="Not Enough Players",
                            description="The queue must have at least 2 players to start a match.",
                            color=0xFF0000,
                        )
                    )
                else:
                    await ctx.reply(
                        embed=discord.Embed(
                            title="Not Enough Players",
                            description="The queue must have at least 2 players to start a match.",
                            color=0xFF0000,
                        )
                    )
                return

            # Convert names to Player objects
            queue_players = []
            for player_name in player_names:
                if "[BOT]" in player_name:
                    # This is a fake player
                    clean_name = player_name.replace(" [BOT]", "")
                    db = Database(self.bot)
                    fake_player = db.cursor.execute(
                        "SELECT * FROM fake_player WHERE discord_name = ?",
                        (clean_name,),
                    ).fetchone()
                    if fake_player:
                        queue_players.append(Player(self.bot, fake_player[1]))
                else:
                    # This is a real player
                    member = discord.utils.get(ctx.guild.members, name=player_name)
                    if member:
                        queue_players.append(Player(self.bot, member.id, False))

            if len(queue_players) < 2:
                if hasattr(ctx, "interaction") and ctx.interaction:
                    await ctx.followup.send(
                        embed=discord.Embed(
                            title="Not Enough Valid Players",
                            description="Could not find at least 2 valid players in the queue.",
                            color=0xFF0000,
                        )
                    )
                else:
                    await ctx.reply(
                        embed=discord.Embed(
                            title="Not Enough Valid Players",
                            description="Could not find at least 2 valid players in the queue.",
                            color=0xFF0000,
                        )
                    )
                return

            # Generate teams and start match
            team1, team2 = generate_teams(queue_players)

            # Get creator from the embed footer
            creator_name = queue_embed.footer.text[9:]  # Remove "Creator: " prefix
            creator = (
                discord.utils.get(ctx.guild.members, name=creator_name) or ctx.author
            )

            # Create a fake interaction if needed
            if not hasattr(ctx, "interaction") or not ctx.interaction:

                class FakeInteraction:
                    def __init__(self, author, guild, channel):
                        self.user = author
                        self.guild = guild
                        self.channel = channel

                    async def followup_send(self, *args, **kwargs):
                        return await self.channel.send(*args, **kwargs)

                interaction = FakeInteraction(ctx.author, ctx.guild, ctx.channel)
            else:
                interaction = ctx.interaction

            await start_match(
                team1,
                team2,
                self.bot,
                ctx.guild,
                creator,  # Use the original queue creator
                ctx.channel,
                interaction,
            )

            # Delete the queue message
            await queue_message.delete()

            # Send confirmation
            success_embed = discord.Embed(
                title="Match Started",
                description=f"Admin {ctx.author.name} force-started a match with {len(queue_players)} players from the queue.",
                color=0x00FF42,
            )

            if hasattr(ctx, "interaction") and ctx.interaction:
                await ctx.followup.send(embed=success_embed)
            else:
                await ctx.send(embed=success_embed)

            logger.info(
                f"Admin {ctx.author.name} force-started a match with {len(queue_players)} players"
            )

        except Exception as e:
            logger.error(f"Error in force_start command: {str(e)}", exc_info=True)
            error_embed = discord.Embed(
                title="An error occurred while force starting the match",
                description=str(e),
                color=0xFF0000,
            )

            if hasattr(ctx, "interaction") and ctx.interaction:
                try:
                    await ctx.followup.send(embed=error_embed)
                except:
                    await ctx.channel.send(embed=error_embed)
            else:
                await ctx.reply(embed=error_embed)

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
                target_player.display_name + " Teammates statistics",
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
    async def match(self, ctx: commands.Context, match_id: int, is_fake: bool = False):
        try:
            logger.info(
                f"Admin {ctx.author.name} removing match {match_id} (fake: {is_fake})"
            )
            self.db.remove_match(match_id, is_fake=is_fake)
            table_type = "test" if is_fake else "regular"
            await ctx.reply(
                embed=discord.Embed(
                    title=f"Match {match_id} has been removed from the {table_type} database",
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
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None,
        include_fake: bool = False,
    ):
        try:
            await ctx.interaction.response.send_message(
                "League matches loading", ephemeral=True
            )
            if member is None:
                member = ctx.author
            player = Player(self.bot, member.id) if member else None
            embeds = []

            is_fake_player = player and hasattr(player, "is_fake") and player.is_fake
            if player:
                matches = player.get_matches(
                    include_fake=include_fake or is_fake_player
                )
            else:
                matches = self.db.get_all_matches(include_fake=include_fake)

            if len(matches) == 0:
                message = await ctx.interaction.original_response()
                await message.edit(
                    embed=discord.Embed(title=f"No matches found", color=0xFF0000)
                )
                return

            for i, match in enumerate(matches):
                match: Match
                color = 0x00FF42
                if match.is_fake:
                    color = 0xFFAA00

                embed = discord.Embed(
                    title=f"{match.match_id}\t({i+1}/{len(matches)})", color=color
                )

                if match.is_fake:
                    embed.description = "*This is a test match with fake players*"

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

    @league.group(name="fake", description="Commands for managing fake players")
    @permissions.admin()
    async def fake(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @fake.command(name="add", description="Add a fake player for testing")
    async def fake_add(
        self,
        ctx: commands.Context,
        name: str,
        mmr: Optional[int] = 1000,
        wins: Optional[int] = 0,
        losses: Optional[int] = 0,
    ):
        try:
            db = Database(self.bot)
            fake_id = db.add_fake_player(name, mmr, wins, losses)

            if fake_id:
                win_rate = round(
                    (wins / (wins + losses) * 100) if wins + losses > 0 else 0, 1
                )

                embed = discord.Embed(
                    title="Fake Player Added",
                    description=f"Created fake player '{name}' with ID {fake_id}",
                    color=0x00FF42,
                )
                embed.add_field(name="MMR", value=str(mmr))
                embed.add_field(
                    name="Record", value=f"{wins}W - {losses}L ({win_rate}%)"
                )

                await ctx.reply(embed=embed)
            else:
                await ctx.reply("Failed to add fake player.")
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while adding a fake player",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @fake.command(name="list", description="List all fake players")
    async def fake_list(self, ctx: commands.Context):
        try:
            db = Database(self.bot)
            fake_players = db.get_fake_players()

            if not fake_players:
                await ctx.reply("No fake players found in the system.")
                return

            embed = discord.Embed(
                title="Fake Players",
                description=f"Found {len(fake_players)} fake players",
                color=0x00FF42,
            )

            names = []
            ids = []
            mmrs = []
            records = []

            for player in fake_players:
                names.append(player[2])
                ids.append(str(player[1]))
                mmrs.append(str(player[3]))

                wins = player[4]
                losses = player[5]
                win_rate = round(
                    (wins / (wins + losses) * 100) if wins + losses > 0 else 0, 1
                )
                records.append(f"{wins}W - {losses}L ({win_rate}%)")

            embed.add_field(name="Name", value="\n".join(names))
            embed.add_field(name="ID", value="\n".join(ids))
            embed.add_field(name="MMR", value="\n".join(mmrs))
            embed.add_field(name="Record", value="\n".join(records))

            await ctx.reply(embed=embed)
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while listing fake players",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @fake.command(name="remove", description="Remove a fake player")
    async def fake_remove(self, ctx: commands.Context, discord_id: int):
        try:
            db = Database(self.bot)
            if db.remove_fake_player(discord_id):
                await ctx.reply(
                    f"Fake player with ID {discord_id} removed successfully."
                )
            else:
                await ctx.reply(f"Could not find fake player with ID {discord_id}.")
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while removing a fake player",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @fake.command(name="generate", description="Generate multiple fake players")
    async def fake_generate(
        self,
        ctx: commands.Context,
        count: int = 5,
        base_mmr: int = 1000,
        mmr_variance: int = 200,
    ):
        try:
            if count > 20:
                await ctx.reply("Cannot generate more than 20 players at once.")
                return

            db = Database(self.bot)
            names = ["FakePlayer", "TestUser", "DummyPlayer", "BotUser", "SimPlayer"]
            adjectives = [
                "Cool",
                "Super",
                "Pro",
                "Mega",
                "Ultra",
                "Epic",
                "Amazing",
                "Skilled",
            ]

            success_count = 0
            for i in range(count):
                if random.random() > 0.5:
                    name = f"{random.choice(adjectives)}{random.choice(names)}{random.randint(1, 999)}"
                else:
                    name = f"{random.choice(names)}{random.randint(1, 999)}"

                mmr = base_mmr + random.randint(-mmr_variance, mmr_variance)
                mmr = max(500, mmr)

                total_games = random.randint(10, 50)
                win_rate = random.uniform(0.4, 0.6)
                wins = int(total_games * win_rate)
                losses = total_games - wins

                fake_id = db.add_fake_player(name, mmr, wins, losses)
                if fake_id:
                    success_count += 1

            if success_count > 0:
                await ctx.reply(f"Successfully generated {success_count} fake players.")
            else:
                await ctx.reply("Failed to generate any fake players.")

        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while generating fake players",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @fake.command(
        name="queue_multi", description="Add multiple fake players to an existing queue"
    )
    async def fake_queue_multi(self, ctx: commands.Context, count: int = 2):
        try:
            if count > 9:
                await ctx.reply("Cannot add more than 9 fake players to a queue.")
                return

            queue_message = None

            async for message in ctx.channel.history(limit=50):
                if message.author == self.bot.user and message.embeds:
                    for embed in message.embeds:
                        if embed.title and embed.title.startswith("Queue "):
                            queue_message = message
                            break

                    if queue_message:
                        break

            if not queue_message:
                await ctx.reply(
                    embed=discord.Embed(
                        title="No Active Queue Found",
                        description="Could not find an active queue in this channel. Start a queue first with `/league queue`.",
                        color=0xFF0000,
                    )
                )
                return

            queue_embed = queue_message.embeds[0]

            creator_name = queue_embed.footer.text[9:]
            creator = (
                discord.utils.get(ctx.guild.members, name=creator_name) or ctx.author
            )

            voice_channel = ctx.author.voice.channel if ctx.author.voice else None

            new_queue_view = QueueView(self.bot, voice_channel)

            existing_players = []
            if len(queue_embed.fields) > 0 and queue_embed.fields[0].name == "Players":
                player_names = queue_embed.fields[0].value.split("\n")
                for name in player_names:
                    if name and name != "No players in queue":
                        clean_name = name.replace(" [BOT]", "")
                        member = discord.utils.get(ctx.guild.members, name=clean_name)
                        if member:
                            new_queue_view.queue.append(member)
                        else:
                            fake_player = self._create_fake_queue_member(clean_name)
                            if fake_player:
                                new_queue_view.queue.append(fake_player)

            db = Database(self.bot)
            fake_players = db.get_fake_players()

            if not fake_players:
                await ctx.reply(
                    "No fake players found in the system. Create some first."
                )
                return

            if len(fake_players) < count:
                count = len(fake_players)

            selected_players = random.sample(fake_players, count)
            players = [Player(self.bot, player[1]) for player in selected_players]

            added_players = []
            for player in players:
                fake_member = self._create_fake_queue_member(player)
                if not any(
                    getattr(p, "id", None) == fake_member.id
                    for p in new_queue_view.queue
                ):
                    new_queue_view.queue.append(fake_member)
                    added_players.append(player)

            vc_members_names = []
            if voice_channel:
                vc_members_names = [m.name for m in voice_channel.members]

            queue_players = []
            for member in new_queue_view.queue:
                if hasattr(member, "is_fake") and hasattr(member, "_player"):
                    queue_players.append(member._player)
                else:
                    try:
                        queue_players.append(Player(self.bot, member.id))
                    except:
                        continue

            updated_embed = QueueEmbed(queue_players, vc_members_names, creator)
            await queue_message.edit(embed=updated_embed, view=new_queue_view)

            control_view = QueueControlView(
                self.bot, queue_message, new_queue_view, voice=voice_channel
            )

            if added_players:
                embed = discord.Embed(
                    title="Fake Players Added to Queue",
                    description=f"Added {len(added_players)} fake players to the queue",
                    color=0x00FF42,
                )

                names_list = [player.discord_name for player in added_players]
                mmr_list = [str(player.mmr) for player in added_players]

                embed.add_field(name="Players", value="\n".join(names_list))
                embed.add_field(name="MMR", value="\n".join(mmr_list))

                result_message = await ctx.reply(embed=embed)

                await ctx.interaction.followup.send(
                    "Queue Control", view=control_view, ephemeral=True
                )
            else:
                await ctx.reply("No new fake players were added to the queue.")

        except Exception as e:
            logger.error(f"Error adding fake players to queue: {str(e)}", exc_info=True)
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while adding fake players to the queue",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @fake.command(
        name="queue", description="Add a specific fake player to an existing queue"
    )
    async def fake_queue(self, ctx: commands.Context, player_identifier: str):
        try:
            queue_message = None

            async for message in ctx.channel.history(limit=50):
                if message.author == self.bot.user and message.embeds:
                    for embed in message.embeds:
                        if embed.title and embed.title.startswith("Queue "):
                            queue_message = message
                            break

                    if queue_message:
                        break

            if not queue_message:
                await ctx.reply(
                    embed=discord.Embed(
                        title="No Active Queue Found",
                        description="Could not find an active queue in this channel. Start a queue first with `/league queue`.",
                        color=0xFF0000,
                    )
                )
                return

            queue_embed = queue_message.embeds[0]

            creator_name = queue_embed.footer.text[9:]
            creator = (
                discord.utils.get(ctx.guild.members, name=creator_name) or ctx.author
            )

            voice_channel = ctx.author.voice.channel if ctx.author.voice else None

            new_queue_view = QueueView(self.bot, voice_channel)

            if len(queue_embed.fields) > 0 and queue_embed.fields[0].name == "Players":
                player_names = queue_embed.fields[0].value.split("\n")
                for name in player_names:
                    if name and name != "No players in queue":
                        clean_name = name.replace(" [BOT]", "")
                        member = discord.utils.get(ctx.guild.members, name=clean_name)
                        if member:
                            new_queue_view.queue.append(member)
                        else:
                            fake_player = self._create_fake_queue_member(clean_name)
                            if fake_player:
                                new_queue_view.queue.append(fake_player)

            db = Database(self.bot)

            try:
                player_id = int(player_identifier)
                fake_player = db.cursor.execute(
                    "SELECT * FROM fake_player WHERE discord_id = ?", (player_id,)
                ).fetchone()
            except ValueError:
                fake_player = db.cursor.execute(
                    "SELECT * FROM fake_player WHERE discord_name = ?",
                    (player_identifier,),
                ).fetchone()

            if not fake_player:
                await ctx.reply(
                    f"Could not find fake player with ID or name '{player_identifier}'. "
                    f"Use `/league fake list` to see available fake players."
                )
                return

            player = Player(self.bot, fake_player[1])

            fake_member = self._create_fake_queue_member(player)

            if any(
                getattr(p, "id", None) == fake_member.id for p in new_queue_view.queue
            ):
                await ctx.reply(
                    f"Player '{player.discord_name}' is already in the queue."
                )
                return

            new_queue_view.queue.append(fake_member)

            vc_members_names = []
            if voice_channel:
                vc_members_names = [m.name for m in voice_channel.members]

            queue_players = []
            for member in new_queue_view.queue:
                if hasattr(member, "is_fake") and hasattr(member, "_player"):
                    queue_players.append(member._player)
                else:
                    try:
                        queue_players.append(Player(self.bot, member.id))
                    except:
                        continue

            updated_embed = QueueEmbed(queue_players, vc_members_names, creator)
            await queue_message.edit(embed=updated_embed, view=new_queue_view)

            control_view = QueueControlView(
                self.bot, queue_message, new_queue_view, voice=voice_channel
            )

            embed = discord.Embed(
                title="Fake Player Added to Queue",
                description=f"Added '{player.discord_name}' to the queue",
                color=0x00FF42,
            )

            embed.add_field(name="MMR", value=str(player.mmr))
            embed.add_field(
                name="Record",
                value=f"{player.wins}W - {player.losses}L ({player.win_rate:.1f}%)",
            )

            await ctx.reply(embed=embed)

            await ctx.interaction.followup.send(
                "Queue Control", view=control_view, ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error adding fake player to queue: {str(e)}", exc_info=True)
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while adding fake player to the queue",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @fake.command(name="set_rating", description="Change a fake player's MMR")
    async def fake_set_rating(
        self, ctx: commands.Context, player_identifier: str, mmr: int
    ):
        try:
            db = Database(self.bot)

            try:
                player_id = int(player_identifier)
                fake_player = db.cursor.execute(
                    "SELECT * FROM fake_player WHERE discord_id = ?", (player_id,)
                ).fetchone()
            except ValueError:
                fake_player = db.cursor.execute(
                    "SELECT * FROM fake_player WHERE discord_name = ?",
                    (player_identifier,),
                ).fetchone()

            if not fake_player:
                await ctx.reply(
                    f"Could not find fake player with ID or name '{player_identifier}'. "
                    f"Use `/league fake list` to see available fake players."
                )
                return

            player = Player(self.bot, fake_player[1])

            original_mmr = player.mmr

            player.mmr = mmr
            player.update()

            embed = discord.Embed(
                title="Fake Player MMR Updated",
                description=f"Updated '{player.discord_name}' MMR from {original_mmr} to {mmr}",
                color=0x00FF42,
            )

            await ctx.reply(embed=embed)

        except Exception as e:
            logger.error(f"Error setting fake player rating: {str(e)}", exc_info=True)
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while updating fake player MMR",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @fake.command(name="match", description="Start a test match with fake players")
    async def fake_match(self, ctx: commands.Context, players_per_team: int = 5):
        try:
            if hasattr(ctx, "interaction") and ctx.interaction:
                await ctx.interaction.response.defer()
                interaction_deferred = True
            else:
                interaction_deferred = False

            if players_per_team < 1 or players_per_team > 5:
                await ctx.reply("Players per team must be between 1 and 5.")
                return

            db = Database(self.bot)
            fake_players = db.get_fake_players()

            if len(fake_players) < players_per_team * 2:
                await ctx.reply(
                    f"Not enough fake players. Need at least {players_per_team * 2}."
                )
                return

            selected_players = random.sample(fake_players, players_per_team * 2)

            team1_players = [
                Player(self.bot, player[1])
                for player in selected_players[:players_per_team]
            ]
            team2_players = [
                Player(self.bot, player[1])
                for player in selected_players[players_per_team:]
            ]

            status_message = await ctx.reply(
                embed=discord.Embed(
                    title="Starting Test Match...",
                    description=f"Creating a match with {players_per_team} players per team",
                    color=0x00FF42,
                )
            )

            if not hasattr(ctx, "interaction") or not ctx.interaction:

                class FakeInteraction:
                    def __init__(self, author, guild, channel):
                        self.user = author
                        self.guild = guild
                        self.channel = channel

                    async def followup_send(self, *args, **kwargs):
                        return await self.channel.send(*args, **kwargs)

                interaction = FakeInteraction(ctx.author, ctx.guild, ctx.channel)
            else:
                interaction = ctx.interaction

            await start_match(
                team1_players,
                team2_players,
                self.bot,
                ctx.guild,
                ctx.author,
                ctx.channel,
                interaction,
                move_players_setting=False,
            )

            await status_message.edit(
                embed=discord.Embed(
                    title="Test Match Started",
                    description=f"Started a test match with {players_per_team} players per team",
                    color=0x00FF42,
                )
            )

        except Exception as e:
            logger.error(f"Error in fake_match command: {str(e)}", exc_info=True)
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while creating a test match",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    @fake.command(name="matches", description="List fake player matches")
    async def fake_matches(self, ctx: commands.Context):
        try:
            await ctx.interaction.response.send_message(
                "Fake matches loading", ephemeral=True
            )

            matches = self.db.get_fake_matches()

            logger.info(f"Found {len(matches)} fake matches in the fake_match table")

            if not matches:
                await ctx.interaction.followup.send(
                    embed=discord.Embed(
                        title="No fake matches found",
                        description="There are no test matches in the database.",
                        color=0xFF0000,
                    )
                )
                return

            embeds = []
            for i, match in enumerate(matches):
                embed = discord.Embed(
                    title=f"Fake Match {match.match_id}\t({i+1}/{len(matches)})",
                    description="*This is a test match with fake players*",
                    color=0xFFAA00,
                )

                embed.add_field(
                    name=f"Team 1 (Total MMR: {sum(p.mmr for p in match.team1)})",
                    value="\n".join(
                        [f"{p.discord_name} ({p.mmr} MMR)" for p in match.team1]
                    ),
                )
                embed.add_field(name=f"MMR Diff: {math.ceil(match.mmr_diff)}", value="")
                embed.add_field(
                    name=f"Team 2 (Total MMR: {sum(p.mmr for p in match.team2)})",
                    value="\n".join(
                        [f"{p.discord_name} ({p.mmr} MMR)" for p in match.team2]
                    ),
                )
                embed.add_field(
                    name=f"Date", value=f"{str(match.timestamp)[:19]}", inline=False
                )
                embed.add_field(name=f"Result", value=f"Team {match.winner} Won")
                embeds.append(embed)

            if embeds:
                view = PlayerMatchesView(embeds)
                message = await ctx.interaction.original_response()
                await message.edit(embed=embeds[0], view=view)
            else:
                await ctx.interaction.followup.send(
                    embed=discord.Embed(
                        title="No fake matches found",
                        description="There are no test matches in the database.",
                        color=0xFF0000,
                    )
                )

        except Exception as e:
            logger.error(f"Error listing fake matches: {str(e)}", exc_info=True)
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while listing fake matches",
                    description=str(e),
                    color=0xFF0000,
                )
            )

    def _create_fake_queue_member(self, player):
        bot = self.bot

        class FakeQueueMember:
            def __init__(self, player_obj=None, player_name=None):
                if player_obj:
                    self.id = player_obj.discord_id
                    self.name = f"{player_obj.discord_name} [BOT]"
                    self.display_name = f"{player_obj.discord_name} [BOT]"
                    self._player = player_obj
                elif player_name:
                    db = Database(bot)
                    fake_player = db.cursor.execute(
                        "SELECT * FROM fake_player WHERE discord_name = ?",
                        (player_name,),
                    ).fetchone()
                    if fake_player:
                        player_obj = Player(bot, fake_player[1])
                        self.id = player_obj.discord_id
                        self.name = f"{player_name} [BOT]"
                        self.display_name = f"{player_name} [BOT]"
                        self._player = player_obj
                    else:
                        self.id = -999999
                        self.name = f"{player_name} [BOT]"
                        self.display_name = f"{player_name} [BOT]"
                self.is_fake = True

            def __eq__(self, other):
                if hasattr(other, "id"):
                    return self.id == other.id
                return False

        if isinstance(player, str):
            return FakeQueueMember(player_name=player)
        else:
            return FakeQueueMember(player_obj=player)

    @league.command(
        name="admin_add_player",
        description="Add a specific player to an existing queue (Admin only)",
    )
    @permissions.admin()
    async def admin_add_player(self, ctx: commands.Context, player: discord.Member):
        try:
            queue_message = None

            async for message in ctx.channel.history(limit=50):
                if message.author == self.bot.user and message.embeds:
                    for embed in message.embeds:
                        if embed.title and embed.title.startswith("Queue "):
                            queue_message = message
                            break

                    if queue_message:
                        break

            if not queue_message:
                await ctx.reply(
                    embed=discord.Embed(
                        title="No Active Queue Found",
                        description="Could not find an active queue in this channel. Start a queue first with `/league queue`.",
                        color=0xFF0000,
                    )
                )
                return

            queue_embed = queue_message.embeds[0]

            creator_name = queue_embed.footer.text[9:]
            creator = (
                discord.utils.get(ctx.guild.members, name=creator_name) or ctx.author
            )

            voice_channel = ctx.author.voice.channel if ctx.author.voice else None

            new_queue_view = QueueView(self.bot, voice_channel)

            # Load existing players from the queue
            if len(queue_embed.fields) > 0 and queue_embed.fields[0].name == "Players":
                player_names = queue_embed.fields[0].value.split("\n")
                for name in player_names:
                    if name and name != "No players in queue":
                        clean_name = name.replace(" [BOT]", "")
                        member = discord.utils.get(ctx.guild.members, name=clean_name)
                        if member:
                            new_queue_view.queue.append(member)
                        else:
                            fake_player = self._create_fake_queue_member(clean_name)
                            if fake_player:
                                new_queue_view.queue.append(fake_player)

            # Check if player is already in the queue
            if any(p.id == player.id for p in new_queue_view.queue):
                await ctx.reply(f"Player '{player.name}' is already in the queue.")
                return

            # Add the player to the queue
            new_queue_view.queue.append(player)

            # Update the queue display
            vc_members_names = []
            if voice_channel:
                vc_members_names = [m.name for m in voice_channel.members]

            queue_players = []
            for member in new_queue_view.queue:
                if hasattr(member, "is_fake") and hasattr(member, "_player"):
                    queue_players.append(member._player)
                else:
                    try:
                        queue_players.append(Player(self.bot, member.id))
                    except:
                        continue

            updated_embed = QueueEmbed(queue_players, vc_members_names, creator)
            await queue_message.edit(embed=updated_embed, view=new_queue_view)

            control_view = QueueControlView(
                self.bot, queue_message, new_queue_view, voice=voice_channel
            )

            # Display success message
            player_obj = Player(self.bot, player.id)
            embed = discord.Embed(
                title="Player Added to Queue",
                description=f"Added '{player.name}' to the queue",
                color=0x00FF42,
            )

            embed.add_field(name="MMR", value=str(player_obj.mmr))
            embed.add_field(
                name="Record",
                value=f"{player_obj.wins}W - {player_obj.losses}L ({player_obj.win_rate:.1f}%)",
            )

            await ctx.reply(embed=embed)

            await ctx.interaction.followup.send(
                "Queue Control", view=control_view, ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error adding player to queue: {str(e)}", exc_info=True)
            await ctx.reply(
                embed=discord.Embed(
                    title="An error occurred while adding player to the queue",
                    description=str(e),
                    color=0xFF0000,
                )
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(league_cog(bot))
    logger.info("League cog loaded")
