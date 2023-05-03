from discord.ext import commands
import discord
import sqlite3
import datetime
import os
import matplotlib.pyplot as plt
import numpy as np
import json


ranks_mmr = {
    "i4": 500,
    "i3": 550,
    "i2": 600,
    "i1": 650,
    "b4": 700,
    "b3": 750,
    "b2": 800,
    "b1": 850, 
    "s4": 900,
    "s3": 950,
    "s2": 1000,
    "s1": 1050,
    "g4": 1100,
    "g3": 1150,
    "g2": 1200,
    "g1": 1250,
    "p4": 1300,
    "p3": 1350,
    "p2": 1400,
    "p1": 1450,
    "d4": 1500,
    "d3": 1550,
    "d2": 1600,
    "d1": 1650,
    "master": 1700,
    "grandmaster": 1850,
    "challenger": 2300 
}


class leagueCustoms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def wl(self, ctx):
        if 802299956299169845 not in [role.id for role  in ctx.author.roles]:
            #print("Not an admin")
            return
        
        dbcon = sqlite3.connect(os.getenv("DB"))
        dbcur = dbcon.cursor()
        res = dbcur.execute(f"SELECT discord_id, rating, timestamp FROM players ORDER BY timestamp DESC")
        res = res.fetchall()

        ratings = {i[0]: [] for i in res}

        players = {i[0]: {
            "wins": 0,
            "losses": 0,
            "wl": 0.0,
            "ratings": [],
            "total_games": 0
        } for i in res}

        for i in res:
            players[i[0]]["ratings"].append(float(i[1]))
        
        #print(json.dumps(players, indent=4))
        

        for player_id in players.keys():
            for i in range(1, len(players[player_id]["ratings"])):
                if players[player_id]["ratings"][i - 1] < players[player_id]["ratings"][i]:
                    players[player_id]["losses"] += 1
                else:
                    players[player_id]["wins"] += 1
                players[player_id]["total_games"] += 1
            

            if players[player_id]['total_games'] > 0:
                players[player_id]['wl'] = int(players[player_id]['wins']/players[player_id]['total_games']*100)

        #print(json.dumps(players, indent=4))

        stats = ""
        for player_id in players.keys():
            stats += f"{self.bot.get_user(int(player_id))}\nWins: {players[player_id]['wins']}\nLosses: {players[player_id]['losses']}\nWin/loss: {players[player_id]['wl']}%\n\n\n"

        await ctx.send(stats)
        
        


        '''
        # Saves peak rating on that date
        timestamps = {i[1].split(" ")[0]: [] for i in res}
        for i in res:
            timestamps[i[1].split(" ")[0]].append(float(i[0]))
        for i, j in timestamps.items():
            timestamps[i] = max(j)
        
        

        plt.figure(dpi=100,
            figsize=(10, 5))

        plt.scatter(
            x=timestamps.keys(), 
            y=timestamps.values(), 
        )

        #plt.xticks(rotation="vertical")
        

        plt.savefig("./figure.png")
        with open('figure.png', 'rb') as f:
            picture = discord.File(f)
            await ctx.send(file=picture)
        '''
        

    @commands.command()
    async def set_mmr(self, ctx, player: discord.Member, rank:str):
        if 802299956299169845 not in [role.id for role  in ctx.author.roles]:
            #print("Not an admin")
            return
        
        if rank not in ranks_mmr.keys() or not rank:
            await ctx.send(f"Invalid rank! Available ranks: {', '.join(ranks_mmr.keys())}")
            return
        
        dbcon = sqlite3.connect(os.getenv("DB"))
        dbcur = dbcon.cursor()
        dbcur.execute(f"INSERT INTO players (discord_id, rating, timestamp) VALUES ('{player.id}', {str(ranks_mmr[rank])}, '{datetime.datetime.now()}')")
        dbcon.commit()
        dbcon.close()
        await ctx.send(f"{player.name} has been set to {rank} ({ranks_mmr[rank]} mmr)")

    

    @commands.command()
    async def get_mmr(self, ctx, player: discord.Member):
        if 802299956299169845 not in [role.id for role  in ctx.author.roles]:
            #print("Not an admin")
            return
        
        dbcon = sqlite3.connect(os.getenv("DB"))
        dbcur = dbcon.cursor()
        res = dbcur.execute(f"SELECT rating FROM players WHERE discord_id = '{player.id}' ORDER BY timestamp DESC LIMIT 1")
        res = res.fetchone()

        if res is None:
            await ctx.send(f"{player.name} has no mmr")
        else:
            await ctx.send(f"{player.name} has {res[0]} mmr")
    

    @commands.command()
    async def get_ratings(self, ctx, player: discord.Member):
        if 802299956299169845 not in [role.id for role  in ctx.author.roles]:
            print("Not an admin")
            return
        
        dbcon = sqlite3.connect(os.getenv("DB"))
        dbcur = dbcon.cursor()
        res = dbcur.execute(f"SELECT rating FROM players WHERE discord_id = '{player.id}' ORDER BY timestamp DESC")
        res = res.fetchall()
        print(res)

        if res is None:
            await ctx.send(f"{player.name} has no mmr")
        else:
            await ctx.send(f"{player.name} has {res[0]} mmr")


    @commands.command()
    async def leagueCustoms(self, ctx, *additional_players: discord.Member):
        # admin role id 802299956299169845
        if 802299956299169845 not in [role.id for role  in ctx.author.roles]:
            #print("Not an admin")
            return
        
        players = ctx.author.voice.channel.members
        for player in additional_players:
            if player not in players:
                # print("added pale", player.name)
                players.append(player)
            elif player in players:
                players.remove(player)
            
        # print("players:")
        # for player in players:
        #     print(player, player.name)
        #print("in custom teams")

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
            #print("pla  res:",pla)
            if not pla:
                pla = (str(player.id), str(1000),datetime.datetime.now() )
                new_players.append(pla)
            formatted_players.append(pla)
        #print("new pla", new_players)
        dbcur.executemany('INSERT  INTO players VALUES(?, ?, ?) ',new_players)
        dbcon.commit()
        dbcon.close()
        #print("updateed")
        
        formatted_players.sort(key=lambda a:float(a[1]))
        #print("formatted.players", formatted_players)
        team_left = []
        team_right = []
        while len(formatted_players) != 0:
            if sum([float(p[1]) for p in team_left]) > sum([float(p[1]) for p in team_right]):
                #print("add team righ", formatted_players[-1])
                team_right.append(formatted_players.pop())
            else:
                #print("add team left", formatted_players[-1])
                team_left.append(formatted_players.pop())
        
        embed = discord.Embed(
            title="Teams",  color=0x00FF42
        )
        
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
                #print("mmr diff scaled", mmr_diff_scaled)
            
                #print("PHASE 1 DONE")
                    
                    
                
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
                    #print("new palyer mmr", player)
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
    
        


async def setup(bot):
    await bot.add_cog(leagueCustoms(bot))
