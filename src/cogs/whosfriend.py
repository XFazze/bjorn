from discord.ext import commands, tasks
import discord
import typing
import json
import os
import lib.league as league
import sqlite3

def get_inviters(self):
            res = self.cursor.execute(
                f"SELECT discord_id, users FROM invite_history").fetchall()
            discord_id = []
            for j,i in enumerate(res):
                discord_id.append([])
                discord_id[j].append(int(i[0]))
                users = i[1].split(" ")

                for jj,ii in enumerate(users):
                    users[jj] = int(ii)

                discord_id[j].append(users)
            return discord_id


class Database_friend:
    def __init__(self):
        self.con = sqlite3.connect("friend.db")
        self.cur = self.con.cursor()
        self.cur.execute(
                "CREATE TABLE IF NOT EXISTS invite_history(inviter, users)"
            )

class friend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = league.Database(self.bot,"data/friends.sqlite")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != 802298523214938153:
            return
        guild_object = self.bot.get_guild(802298523214938153)
        invites = await guild_object.invites()

        #inviters = self.db.get_inviters()
        with open('invites.json', "r") as f:
            inviters =  json.loads(f.read()) 
        
        """
        dictonary = {}
        for ii,i in enumerate(inviters):
            dictonary[str(i)] = users[ii].split(" ")
        inviters = dictonary
        """
        
        for i in invites:

            if i.inviter.id not in inviters.keys():
                inviters[i.inviter.id] = []
            
            if len(inviters[i.inviter.id]) < i.uses:
                inviters[i.inviter.id].append(str(member.id))
                
                os.remove('invites.json')
                with open('invites.json', "w+") as f:
                    f.write(json.dumps(inviters))
                
                """
                temp = inviters.keys()
                temp_1 = []
                temp_2 = []

                for i in temp:
                    temp_1.append(inviters[i])
                
                for ii,i in enumerate(temp_1):
                    temp_2.append(str(temp_1[ii])+" ")
                """
                
            

    @commands.command()
    async def friend(self, ctx):
        with open('invites.json', "r") as f:
            inviters =  json.loads(f.read())
        
        """
        dictonary = {}
        for ii,i in enumerate(inviters):
            dictonary[str(i)] = users[ii].split(" ")
        inviters = dictonary
        """
        
        
        invites = await self.bot.get_guild(802298523214938153).invites()
        res = []
        tes = []
        ids = list(inviters.keys())
        for i in range(len(inviters)):
            idn = int(ids[i])
            print(idn)
            print(self.bot.get_user(idn))
            res.append(list(self.bot.get_user(idn)))
            tes.append(inviters[str(list(self.bot.get_user(idn)))])
        embed = discord.Embed(title=(f"Invites"), color=0x00FF42)
        for i in range(len(inviters.keys())):
            embed.add_field(name=f"{res[i]}", value='\n'.join(tes[i]))
        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(friend(bot))