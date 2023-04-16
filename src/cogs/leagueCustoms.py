from discord.ext import commands
import discord
import sqlite3
from numpy import log
import datetime


class leagueCustoms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def customTeams(self, ctx, *additional_players: discord.Member):
        if ctx.author.id != 243022798543519745:
            return
        players = ctx.author.voice.channel.members
        for player in additional_players:
            if player not in players:
                # print("added pale", player.name)
                players.append(player)

        # print("players:")
        # for player in players:
        #     print(player, player.name)
        print("in custom teams")

        dbcon = sqlite3.connect("data.db")
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
        
        team_left_Display = '\n'.join([self.bot.get_user(int(p[0])).name for p in  team_left])
        embed.add_field(name=f"LEFT TEAM", value=team_left_Display)
        
        team_right_Display = '\n'.join([self.bot.get_user(int(p[0])).name for p in  team_right])
        embed.add_field(name=f"RIGTH TEAM", value=team_right_Display)
        
        

        game_result = discord.ui.View(timeout=None)
        
        async def win_callback(interaction):
            if interaction.user == ctx.author:
                if(interaction.data['custom_id']=="discard"):
                    embed.title = "Teams discarded"
                    await interaction.response.edit_message(embed=embed, view=None)
                    return
                try:
                    #print("p", team_right)
                    mmr_diff=abs(sum([int(p[1]) for p in team_left]) -sum([int(p[1]) for p in team_right]))
                    mmr_diff_maxed = max(min(abs(mmr_diff), 100)/100,10)  # 0 to 1
                    mmr_diff_powed = mmr_diff_maxed**2     
                    mmr_diff_scaled = 1+ mmr_diff_powed * 1 if mmr_diff == 0 else mmr_diff/abs(mmr_diff) # 0 to 2. over 1 when left is higher mmr
                    print("mmr diff scaled")
                except Exception as e:
                    print("error", e)
                print("PHASE 1 DONE")
                    
                    
                try:
                    dbcon = sqlite3.connect("data.db")
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
                        
                except Exception as e:
                    print("error", e)
                print("PHASE 2 DONE")
                
                try:
                    for player in updated_players:
                        print("new palyer mmr", player)
                        player.append( datetime.datetime.now())
                        
                    dbcur.executemany('INSERT INTO players VALUES(?, ?, ?)',updated_players)
                    dbcon.commit()            
                    dbcon.close()
                    embed.title = f"{interaction.data['custom_id']} Team Winner & mmr updtaed"
                    await interaction.response.edit_message(embed=embed, view=None)
                    
                except Exception as e:
                    print("error", e)
                print("PHASE 3 DONE")
                    

        
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
