from email import message
from discord.ext import commands
from discord import Role
from lib.config import (
    ConfigDatabase,
    ConfigTables,
)


class reaction_roles(commands.Cog):
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        db = ConfigDatabase(self)
        roles = db.get_items_by(
            ConfigTables.REACTIONROLES,
            str(payload.message_id)[6:] + str(ord(payload.emoji.name)),
        )

        for role in roles:
            role_obj = payload.member.guild.get_role(int(role))
            await payload.member.add_roles(role_obj)

    @commands.hybrid_command(
        name="add_reaction_role",
        description="When a user reacts with the emoji the role will get added.",
    )
    async def add_reaction_role(self, ctx: commands.Context, role: Role, emoji):
        if ctx.message.reference is None:
            await ctx.reply(
                "You need to reply to a message. This message will delete in 20 seconds.",
                delete_after=20.0,
            )
            await ctx.message.delete()
            return
        col1 = str(ctx.message.reference.message_id)[6:] + str(
            ord(emoji)
        )  # Integer to large for sqlite
        db = ConfigDatabase(self)
        db.insert_item(ConfigTables.REACTIONROLES, col1, str(role.id))

        await ctx.message.delete()
        await ctx.send(
            f"Added role {str(role.name)} to emoji {emoji} on message {str(ctx.message.reference.message_id)}. This message will delete in 20 seconds.",
            delete_after=20.0,
        )

    @commands.hybrid_command(
        name="remove_reaction_role",
        description="Removes a reaction role",
    )
    async def remove_reaction_role(self, ctx: commands.Context, role: Role, emoji):
        if ctx.message.reference is None:
            await ctx.reply(
                "You need to reply to a message. This message will delete in 20 seconds.",
                delete_after=20.0,
            )
            await ctx.message.delete()
            return
        col1 = str(ctx.message.reference.message_id)[6:] + str(
            ord(emoji)
        )  # Integer to large for sqlite
        db = ConfigDatabase(self)
        db.delete_item(ConfigTables.REACTIONROLES, col1, str(role.id))

        await ctx.message.delete()
        await ctx.send(
            f"Removed role {str(role.name)} to emoji {emoji} on message {str(ctx.message.reference.message_id)}. This message will delete in 20 seconds.",
            delete_after=20.0,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(reaction_roles(bot))
