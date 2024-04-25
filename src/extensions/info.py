from datetime import timedelta, datetime
from discord.ext import commands
import discord
import typing


class info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.start_time = datetime.now()

    @commands.hybrid_group(name="info", description="Information commands")
    async def info(self, ctx):
        pass

    @info.command(name="ping", description="Returns the latency of the bot")
    async def ping(self, ctx):
        await ctx.reply(
            embed=discord.Embed(
                title=f"Ping is {round(self.bot.latency*1000, 1)} ms", color=0x00FF42
            )
        )

    @info.command(name="uptime", description="Returns the uptime of the bot")
    async def uptime(self, ctx):
        time_difference = datetime.now() - self.start_time
        await ctx.reply(
            embed=discord.Embed(
                title=f"Uptime is {str(time_difference).split('.')[0]}", color=0x00FF42
            )
        )

    @info.command(name="bot", description="Returns information about the bot")
    async def bbot_info(self, ctx):
        bot = await self.bot.application_info()
        embed = discord.Embed(
            title=bot.name, description=self.bot.description, color=0x00FF42
        )

        embed.add_field(name="ID", value=bot.id)
        embed.add_field(name="Guilds", value=len(self.bot.guilds))
        embed.add_field(name="Users", value=len(self.bot.users))
        embed.add_field(name="Commands", value=len(self.bot.commands))
        embed.add_field(name="Emojis", value=len(self.bot.emojis))
        embed.add_field(name="Latency", value=round(self.bot.latency * 1000, 1))
        embed.add_field(
            name="Source code", value="https://github.com/XFazze/bjorn", inline=False
        )
        embed.set_author(name=bot.name, icon_url=bot.icon)
        embed.set_image(url=bot.icon)

        await ctx.reply(embed=embed)

    @info.command(name="invites", description="Returns all server invites")
    async def invites(self, ctx):
        invites = await ctx.guild.invites()
        await ctx.reply(
            embed=discord.Embed(
                title="Invites in this server:\n"
                + "".join(f"{i.url}\n" for i in invites),
                color=0x00FF42,
            )
        )

    @info.command(name="server", description="Returns information about the server")
    async def server(self, ctx: commands.Context):
        assert ctx.guild is not None
        embed = discord.Embed(
            title=ctx.guild.name, description=ctx.guild.description, color=0x00FF42
        )

        embed.add_field(name="Owner", value=ctx.guild.owner)
        embed.add_field(name="ID", value=ctx.guild.id)
        embed.add_field(name="Member count", value=ctx.guild.member_count)
        embed.add_field(name="Creation Date", value=ctx.guild.created_at)
        embed.add_field(name="Text channels", value=len(ctx.guild.text_channels))
        embed.add_field(name="Voice channels", value=len(ctx.guild.voice_channels))
        embed.add_field(name="Number of categories", value=len(ctx.guild.categories))
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        embed.set_image(url=ctx.guild.icon)

        await ctx.reply(embed=embed)

    @info.command(name="user", description="Returns information about the user")
    async def user(self, ctx: commands.Context, user: discord.Member | None = None):
        assert ctx.message.author is discord.Member
        if user is None:
            user = ctx.message.author
        embed = discord.Embed(title=user.name + user.discriminator, color=user.color)

        embed.add_field(name="ID", value=user.id)
        embed.add_field(name="Nickname", value=user.nick)
        embed.add_field(name="Creation Date", value=str(user.created_at)[:10])
        embed.add_field(name="Join Date", value=str(user.joined_at)[:10])
        embed.add_field(
            name="Roles",
            value="".join(f"{i.name}    " for i in user.roles),
            inline=False,
        )
        embed.set_author(name=user.name, icon_url=user.avatar)
        embed.set_image(url=user.avatar)

        await ctx.reply(embed=embed)

    @info.command(name="avatar", description="Returns user profile picture")
    async def avatar(self, ctx: commands.Context, user: discord.Member | None = None):
        assert ctx.message.author is discord.Member
        if user is None:
            user = ctx.message.author
        embed = discord.Embed(
            title=f"Avatar for {user.nick}",
            color=0x00FF42,
        )
        embed.set_image(url=user.avatar)
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(info(bot))
