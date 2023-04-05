from discord.ext import commands
import discord
import sqlite3
from numpy import log


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
        res = dbcur.execute("CREATE TABLE IF NOT EXISTS players(discord_id UNIQUE, rating, timestamp DEFAULT CURRENT_TIMESTAMP)")
        # print("res of creatint", res.fetchone())
        # tables = dbcur.execute("SELECT name FROM sqlite_master")
        # print("after crea",tables.fetchone())
        
        # Create players if not existsing
        formatted_players = [(str(player.id), str(1000)) for player in players]
        dbcur.executemany('INSERT OR IGNORE INTO players VALUES(?, ?)',formatted_players)
        dbcon.commit()
        dbcon.close()
        
        formatted_players.sort(key=lambda a:int(a[1]))
        team_left = []
        team_right = []
        while len(formatted_players) != 0:
            if sum([int(p[1]) for p in team_left]) > sum([int(p[1]) for p in team_right]):
                team_right.append(formatted_players.pop())
            else:
                team_left.append(formatted_players.pop())
        
        embed = discord.Embed(
            title="Teams",  color=0x00FF42
        )
        
        team_left_Display = '\n'.join([self.bot.get_user(int(p[0])).name for p in  team_left])
        embed.add_field(name=f"LEFT TEAM", value=team_left_Display)
        
        team_right_Display = '\n'.join([self.bot.get_user(int(p[0])).name for p in  team_right])
        embed.add_field(name=f"RIGTH TEAM", value=team_right_Display)
        
        

        game_result = discord.ui.View()
        
        async def win_callback(interaction):
            if interaction.user == ctx.author:
                if(interaction.data['custom_id']=="discard"):
                    embed.title = "Teams discarded"
                    await interaction.response.edit_message(embed=embed, view=None)
                    return
                try:
                    embed.title = f"{interaction.data['custom_id']} Team Winner"
                    await interaction.response.edit_message(embed=embed, view=None)
                    mmr_diff=abs([int(p[1]) for p in team_left] -[int(p[1]) for p in team_right])
                    mmr_diff_maxed = max(abs(mmr_diff), 100)/100  # 0 to 1
                    mmr_diff_powed = mmr_diff_maxed**2       
                    mmr_diff_scaled = 1+ mmr_diff_powed * mmr_diff/abs(mmr_diff) # 0 to 2. over 1 when left is higher mmr
                    
                    
                    dbcon = sqlite3.connect("data.db")
                    dbcur = dbcon.cursor()
                    
                    updated_players = []
                    for left_player in team_left:
                        res = dbcur.execute(f"SELECT discord_id, rating FROM players WHERE discord_id='{left_player[0]}' ORDER BY timestamp DESC LIMIT 1")
                        player = res.fetchone()[0]
                        
                        player[1] +=  10*(2-mmr_diff_scaled) if interaction.data['custom_id']== "Left" else -10*mmr_diff_scaled
                        
                        updated_players.append(player)
                    
                    for right_player in team_right:
                        res = dbcur.execute(f"SELECT discord_id, rating FROM players WHERE discord_id='{right_player[0]}' ORDER BY timestamp DESC LIMIT 1")
                        player = res.fetchone()[0]
                        
                        player[1] +=  -10 * (2-mmr_diff_scaled) if interaction.data['custom_id']== "Left" else 10*mmr_diff_scaled
                        updated_players.append(player)
                        
                    dbcur.executemany('INSERT OR IGNORE INTO players VALUES(?, ?)',updated_players)
                    dbcur.commit()            
                    dbcon.close()
                except Exception as e:
                    print("error", e)
                    

        
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
