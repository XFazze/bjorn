from discord.ext import commands
import discord
import sqlite3
import datetime
import os
import matplotlib.pyplot as plt
import numpy as np
import random

import lib.persmissions as permissions
from lib.league import Database, Player, CustomMatch, Tournament, CustomMatch, generate_teams, MatchEmbed, MatchView


class leagueCustoms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(bot, "data/data.sqlite")

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


async def setup(bot):
    await bot.add_cog(leagueCustoms(bot))
