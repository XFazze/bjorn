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
                inviters[i.inviter.name] = []
            
            if len(inviters[i.inviter.name]) < i.uses:
                inviters[i.inviter.name].append(member.name)

                os.remove('invites.json')
                with open('invites.json', "w+") as f:
                    f.write(json.dumps(inviters))
            

    @commands.command()
    async def friend(self, ctx):
        with open('invites.json', "r") as f:
            inviters =  json.loads(f.read())
        
        await ctx.reply(
            embed=discord.Embed(
                title=f"{inviters}", color=0x00FF42
            )
        )
async def setup(bot):
    await bot.add_cog(friend(bot))