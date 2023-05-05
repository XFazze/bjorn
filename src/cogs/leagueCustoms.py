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
<<<<<<< HEAD
    @commands.command()
    async def chance(self, ctx, *additional_players: discord.Member):
        # admin role id 802299956299169845
        if 802299956299169845 not in [role.id for role  in ctx.author.roles]:
            return
        
        players = ctx.author.voice.channel.members
        for player in additional_players:
            if player not in players:
                # print("added pale", player.name)
                players.append(player)
            elif player in players:
                players.remove(player)

        dbcon = sqlite3.connect(os.getenv("DB"))
        dbcur = dbcon.cursor()
        res = dbcur.execute("CREATE TABLE IF NOT EXISTS players(discord_id, rating, timestamp)")
        
        # Create players if not existsing
        formatted_players = []
        new_players = []
        for player in players:
            res = dbcur.execute(f"SELECT discord_id, rating FROM players WHERE discord_id='{player.id}' ORDER BY timestamp DESC LIMIT 1")
            pla = res.fetchone()
            if not pla:
                pla = (str(player.id), str(1000),datetime.datetime.now() )
                new_players.append(pla)
            formatted_players.append(pla)
        dbcur.executemany('INSERT  INTO players VALUES(?, ?, ?) ',new_players)
        dbcon.commit()
        dbcon.close()
        
        formatted_players.sort(key=lambda a:float(a[1]))
        team_left = []
        team_right = []
        while len(formatted_players) != 0:
            if sum([float(p[1]) for p in team_left]) > sum([float(p[1]) for p in team_right]):
                team_right.append(formatted_players.pop())
            else:
                team_left.append(formatted_players.pop())
        embed = discord.Embed(
            title="",  color=0x00FF42
        )
        winrate = int(( max((sum([float(p[1]) for p in team_left])),sum([float(p[1]) for p in team_right])) / (sum([float(p[1]) for p in team_left]) + sum([float(p[1]) for p in team_right])))*100)+1
        if winrate > 100:
            winrate = 99
        embed.add_field(name=f"LEFT TEAM {100-winrate}%", value="")
        embed.add_field(name=f"RIGTH TEAM {winrate}%", value="")
        
        await ctx.reply(embed=embed)
=======
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
>>>>>>> main

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

<<<<<<< HEAD
        dbcon = sqlite3.connect(os.getenv("DB"))
        dbcur = dbcon.cursor()
        res = dbcur.execute("CREATE TABLE IF NOT EXISTS players(discord_id, rating, timestamp)")
        # print("res of creatint", res.fetchone())
        # tables = dbcur.execute("SELECT name FROM sqlite_master")
        # print("after crea",tables.fetchone())
        
        # Create players if not existsing
        formatted_players = []
        new_players = []
        for player in players:
            res = dbcur.execute(f"SELECT discord_id, rating FROM players WHERE discord_id='{player.id}' ORDER BY timestamp DESC LIMIT 1")
            pla = res.fetchone()
            print("pla  res:",pla)
            if not pla:
                pla = (str(player.id), str(1000),datetime.datetime.now() )
                new_players.append(pla)
            formatted_players.append(pla)
        print("new pla", new_players)
        dbcur.executemany('INSERT  INTO players VALUES(?, ?, ?) ',new_players)
        dbcon.commit()
        dbcon.close()
        print("updateed")
        
        formatted_players.sort(key=lambda a:float(a[1]))
        print("formatted.players", formatted_players)
        team_left = []
        team_right = []
        while len(formatted_players) != 0:
            if sum([float(p[1]) for p in team_left]) > sum([float(p[1]) for p in team_right]):
                print("add team righ", formatted_players[-1])
                team_right.append(formatted_players.pop())
            else:
                print("add team left", formatted_players[-1])
                team_left.append(formatted_players.pop())
        
        embed = discord.Embed(
            title="Teams",  color=0x00FF42
        )
        random.shuffle(team_left)
        random.shuffle(team_right)
        winrate = int(( max((sum([float(p[1]) for p in team_left])),sum([float(p[1]) for p in team_right])) / (sum([float(p[1]) for p in team_left]) + sum([float(p[1]) for p in team_right])))*100)+1
        if winrate > 100:
            winrate = 99
        team_left_Display = '\n'.join([self.bot.get_user(int(p[0])).name for p in  team_left])
        embed.add_field(name=f"LEFT TEAM", value=team_left_Display)
        
        team_right_Display = '\n'.join([self.bot.get_user(int(p[0])).name for p in  team_right])
        embed.add_field(name=f"RIGTH TEAM", value=team_right_Display)
        
        

        game_result = discord.ui.View(timeout=7200) # 2 hours
        
        async def win_callback(interaction):
            if interaction.user == ctx.author:
                if(interaction.data['custom_id']=="discard"):
                    embed.title = "Teams discarded"
                    await interaction.response.edit_message(embed=embed, view=None)
                    return
                
                #print("p", team_right)
                mmr_diff=abs(sum([int(float(p[1])) for p in team_left]) - sum([int(float(p[1])) for p in team_right]))
                mmr_diff_maxed = max(min(abs(mmr_diff), 100),10)/100  # 0.1 to 1
                mmr_diff_powed = mmr_diff_maxed**2                   # 0.01 to 1 
                mmr_diff_scaled = 1+(0 if mmr_diff == 0 else (mmr_diff/abs(mmr_diff))*mmr_diff_powed) # 0 to 2. over 1 when left is higher mmr
                print("mmr diff scaled", mmr_diff_scaled)
            
                print("PHASE 1 DONE")
                    
                    
                
                dbcon = sqlite3.connect(os.getenv("DB"))
                dbcur = dbcon.cursor()
                
                updated_players = []
                for left_player in team_left:
                    res = dbcur.execute(f"SELECT discord_id, rating FROM players WHERE discord_id='{left_player[0]}' ORDER BY timestamp DESC LIMIT 1")
                    player =list( res.fetchone())
                    player[1] = float(player[1])
                    player[1] +=  10*(2-mmr_diff_scaled) if interaction.data['custom_id']== "Left" else -10*mmr_diff_scaled
                    player[1] = str(player[1])
                    
                    updated_players.append(player)
                
                for right_player in team_right:
                    res = dbcur.execute(f"SELECT discord_id, rating FROM players WHERE discord_id='{right_player[0]}' ORDER BY timestamp DESC LIMIT 1")
                    player =list( res.fetchone())

                    
                    player[1] = float(player[1])
                    player[1] +=  -10 * (2-mmr_diff_scaled) if interaction.data['custom_id']== "Left" else 10*mmr_diff_scaled
                    player[1] = str(player[1])
                    updated_players.append(player)
                    
            
                for player in updated_players:
                    print("new palyer mmr", player)
                    player.append( datetime.datetime.now())
                    
                dbcur.executemany('INSERT INTO players VALUES(?, ?, ?)',updated_players)
                dbcon.commit()            
                dbcon.close()
                embed.title = f"{interaction.data['custom_id']} Team Winner & mmr updtaed"
                await interaction.response.edit_message(embed=embed, view=None)
                
            
                

        
        left_win = discord.ui.Button(label="Left Win", style=discord.ButtonStyle.green,custom_id="Left" )
        left_win.callback = win_callback
        game_result.add_item(left_win)
                
        right_win = discord.ui.Button(label="Right Win", style=discord.ButtonStyle.green,custom_id="Rigth" )
        right_win.callback = win_callback
        game_result.add_item(right_win)
        
        discard = discord.ui.Button(label="Discard", style=discord.ButtonStyle.red,custom_id="discard", row=1)
        discard.callback = win_callback
        game_result.add_item(discard)
        
        await ctx.reply(embed=embed, view=game_result)
    
        
=======
        player = Player(self.bot, member.id)
        player.mmr = ranks_mmr[rank]
        player.update()
        await ctx.reply(f"{member.mention}'s mmr has been set to {rank}: {ranks_mmr[rank]}")
>>>>>>> main


async def setup(bot):
    await bot.add_cog(leagueCustoms(bot))
