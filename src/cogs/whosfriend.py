from discord.ext import commands, tasks
import discord
import typing
import json
import os

class friend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != 802298523214938153:
            return
        guild_object = self.bot.get_guild(802298523214938153)
        invites = await guild_object.invites()
        
        with open('invites.json', "r") as f:
            inviters =  json.loads(f.read())
        
        for i in invites:

            if i.inviter.name not in inviters.keys():
                inviters[i.inviter.id] = []
            
            if len(inviters[i.inviter.id]) < i.uses:
                inviters[i.inviter.id].append(str(member.id))

                os.remove('invites.json')
                with open('invites.json', "w+") as f:
                    f.write(json.dumps(inviters))
            

    @commands.command()
    async def friend(self, ctx):
        with open('invites.json', "r") as f:
            inviters =  json.loads(f.read())
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