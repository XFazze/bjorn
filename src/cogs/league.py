from discord.ext import commands
import discord

import lib.persmissions as permissions
from lib.league import Database, Player, CustomMatch, Tournament, CustomMatch, generate_teams, MatchEmbed, MatchView, ranks_mmr


class league(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(bot, "data/data.sqlite")

    @commands.group(invoke_without_command=True)
    async def league(self, ctx: commands.Context):
        await ctx.reply(embed=discord.Embed(title=f"Invalid league command! Try '{ctx.prefix}help league'", color=0xFF0000))

    @league.command(description="Creates a league custom match instance with teams from the current voice channel.")
    @permissions.admin()
    @permissions.voice()
    async def customs(self, ctx: commands.Context, *additional_players: discord.Member):
        member_players = ctx.author.voice.channel.members

        if len(member_players) < 2:
            await ctx.reply(embed=discord.Embed(title=f"Not enough players in voice channel!", color=0xFF0000))
            return

        for player in additional_players:
            if player not in member_players:
                member_players.append(player)
            elif player in players:
                member_players.remove(player)

        players = [Player(self.bot, i.id)
                   for i in member_players]
        team1, team2 = generate_teams(players)
        custom_match = CustomMatch(self.bot, ctx.author, team1, team2)

        embed = MatchEmbed(team1, team2)
        view = MatchView(custom_match, embed)

        await ctx.reply(embed=embed, view=view)

    @league.command(description=f"Sets a player's mmr to a given value.")
    @permissions.admin()
    async def setmmr(self, ctx: commands.Context, member: discord.Member, mmr: int):
        player = Player(self.bot, member.id)
        player.mmr = mmr
        player.update()
        await ctx.reply(embed=discord.Embed(title=f"{member.name}'s mmr has been set to {mmr}", color=0x00FF42))

    @league.command(description=f"Sets a player's rank to a given rank. Available ranks: {ranks_mmr.keys()}.")
    @permissions.admin()
    async def setrank(self, ctx: commands.Context, member: discord.Member, rank: str):
        if rank not in ranks_mmr.keys():
            embed = discord.Embed(title=f"Invalid rank!", color=0xFF0000)
            embed.add_field(name="Available ranks:",
                            value="\n".join(ranks_mmr.keys()))
            await ctx.reply(embed=embed)
            return

        player = Player(self.bot, member.id)
        player.mmr = ranks_mmr[rank]
        player.update()

        await ctx.reply(embed=discord.Embed(title=f"{member.name}'s mmr has been set to {rank}: {ranks_mmr[rank]}", color=0x00FF42))

    @league.command(description=f"Displays all players.")
    async def players(self, ctx: commands.Context):
        players = self.db.get_all_players()

        embed = discord.Embed(title=f"Players", color=0x00FF42)
        embed.add_field(name="Name", value="\n".join(
            [p.discord_name for p in players]))
        embed.add_field(name="Win rate", value="\n".join(
            [f"{p.win_rate:.1f}%" for p in players]))
        embed.add_field(name="Matches", value="\n".join(
            [f"{len(p.matches)}" for p in players]))

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(league(bot))
