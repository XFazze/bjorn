from discord.ext import commands
import discord
import sqlite3
import datetime
import os
import matplotlib.pyplot as plt
import numpy as np
import random

import lib.persmissions as permissions
from lib.league import Database, Player, CustomMatch, Tournament, CustomMatch, generate_teams, MatchEmbed, MatchView, ranks_mmr


class leagueCustoms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(bot, "data/data.sqlite")
    
    @commands.command(aliases=["ch"])
    @permissions.admin()
    async def chance(self, ctx: commands.Context, *additional_players: discord.Member):
        member_players = ctx.author.voice.channel.members
        for player in additional_players:
            if player not in member_players:
                member_players.append(player)
            elif player in players:
                member_players.remove(player)
        
        players = [Player(self.bot, i.id)
                   for i in member_players]
        team1, team2 = generate_teams(players)
        team_1_mmr,team_2_mmr = 0,0
        for i in team1:
            team_1_mmr += i.mmr
        for i in team2:
            team_2_mmr += i.mmr
        winrate = int((max(team_1_mmr,team_2_mmr) / (team_1_mmr+team_2_mmr))*100)+1
        embed = discord.Embed(title=f'Left Team {100-winrate}%         Right Team {winrate}%',  color=0x00FF42)
        await ctx.reply(embed=embed)


    @commands.command(aliases=["customs", "lc"])
    @permissions.admin()
    async def league_customs(self, ctx: commands.Context, *additional_players: discord.Member):
        member_players = ctx.author.voice.channel.members
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
        view = MatchView(custom_match)

        await ctx.reply(embed=embed, view=view)

    @commands.command()
    @permissions.admin()
    async def setmmr(self, ctx: commands.Context, member: discord.Member, mmr: int):
        player = Player(self.bot, member.id)
        player.mmr = mmr
        player.update()
        await ctx.reply(f"{member.mention}'s mmr has been set to {mmr}")

    @commands.command()
    @permissions.admin()
    async def setrank(self, ctx: commands.Context, member: discord.Member, rank: str):
        if rank not in ranks_mmr.keys():
            await ctx.reply(f"Invalid rank! Available ranks: {ranks_mmr.keys()}")
            return

        player = Player(self.bot, member.id)
        player.mmr = ranks_mmr[rank]
        player.update()
        await ctx.reply(f"{member.mention}'s mmr has been set to {rank}: {ranks_mmr[rank]}")


async def setup(bot):
    await bot.add_cog(leagueCustoms(bot))
