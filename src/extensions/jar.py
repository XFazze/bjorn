from discord.ext import commands
import discord
import time

#import lib.persmissions as permissions
from lib.jar import Database
allowed_user_id = 220607888459038721

class jar(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database(bot, "jar.sqlite")
    
    @commands.hybrid_group(
            name="jar", description="A pot of money for the server"
            )
    async def jar(self, ctx: commands.Context):
        pass
    
    @jar.command(
            name="pot",description="Says how much in total there is in the pot",
            )
    async def pot(self, ctx: commands.Context):
        pot = self.db.pot_value()
        total = 0
        for value in pot:
            total += int(value[0])
        await ctx.reply(
            embed = discord.Embed(title=f"The total pot right now is {total}kr"))

    @jar.command(
            name="how_flamed",description="Shows how much a certain person has flamed",
            )
    async def how_flamed(self, ctx: commands.Context, user: discord.Member | None = None):
        if user is None:
            user = ctx.message.author
        flamed = self.db.how_flamed(user.id)
        await ctx.reply(
            embed = discord.Embed(title=f"The person needs to pay {flamed}kr")
            )

    @jar.command(
            name="someone_flamed",description="Adds so that specifik person flamed",
            )
    async def add_tilt(self, ctx: commands.Context, user: discord.Member | None = None):
        if user is None:
            user = ctx.message.author
        if ctx.author.id == allowed_user_id:
            flamed = self.db.add_tilt(user.id)
            await ctx.reply(
                embed = discord.Embed(title=f"{user.name} has contributed to the pot")
                )
        else:
            await ctx.reply(
                embed = discord.Embed(title=f"U don't have permission for this")
                )
    
async def setup(bot: commands.Bot):
    await bot.add_cog(jar(bot))
    
    
    
    
    
    
    
    
    '''
    @jar.command(name="Remove flame",description="The flame that was addes was not right",)
    async def remove_tilt(self, ctx: commands.Context, time: str):
        remove = self.db.remove_tilt(time)
        await ctx.reply(
            embed = discord.Embed(title=f"The flame was succsecfully removed")
            )
    '''
    