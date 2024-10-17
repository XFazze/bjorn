from enum import Enum
import os

from discord.ext import commands
from discord import Embed

from lib.general import Database


class ConfigTables(Enum):
    ROLEONJOIN = "roleonjoin", "guild_id", "role_id"
    ADMIN = "admin", "guild_id", "role_id"
    BETTERVC = "bettervc", "guild_id", "category_id"
    INGAMEROLE = "ingame_role", "guild_id", "role_id"
    STRIKEPERMISSIONS = "strike_permissions", "guild_id", "role_id"
    REACTIONROLES = (
        "reaction_roles_message_id",
        "message_idaemoji_id",
        "role_id",
    )  # Column 1 is combined message_id and emoji_id with a "a" in between ex "1271497554378358929a802299956299169845"

    def __init__(self, table, col1, col2):
        self.table = table
        self.col1 = col1
        self.col2 = col2


class ConfigDatabase(Database):
    def __init__(self, bot: commands.Bot):
        super().__init__(os.environ["CONFIG_DB_NAME"])
        self.bot = bot
        tables = {}
        for table in ConfigTables:
            tables[table.table] = [table.col1, table.col2]
        self.create_tables(tables)

        self.tables = ConfigTables

    def get_items(self, table: ConfigTables) -> list[(str, str)]:
        return self.cursor.execute(
            f"SELECT {table.col1}, {table.col2} FROM {table.table}"
        ).fetchall()

    def get_items_by(self, table: ConfigTables, col1: str) -> list[str]:
        items = self.cursor.execute(
            f"SELECT {table.col1}, {table.col2} FROM {table.table} WHERE {table.col1} = {col1}"
        ).fetchall()
        return [i[1] for i in items]

    def insert_item(self, table: ConfigTables, col1: str, col2: str) -> None:
        self.cursor.execute(
            f"INSERT INTO {table.table} ({table.col1}, {table.col2}) VALUES ({col1}, {col2})"
        )
        self.connection.commit()

    def delete_item(
        self, table: ConfigTables, col1: str = None, col2: str = None
    ) -> None:
        if col1 is not None and col2 is not None:
            self.cursor.execute(
                f"DELETE FROM {table.table} WHERE {table.col1} = {col1} AND {table.col2} = {col2} "
            )
        elif col2 is not None:
            self.cursor.execute(
                f"DELETE FROM {table.table} WHERE {table.col2} = {col2} "
            )
        elif col1 is not None:
            self.cursor.execute(
                f"DELETE FROM {table.table} WHERE {table.col1} = {col1}"
            )

        result = self.connection.commit()


async def show_roles(
    bot: commands.Bot, ctx: commands.Context, table: ConfigTables, key
):
    db = ConfigDatabase(bot)
    roles = db.get_items_by(table, key)
    embed = Embed(title=f"Role on join", color=0x00FF42)
    embed.add_field(
        name="Roles",
        value="\n".join([ctx.guild.get_role(int(r)).name for r in roles]),
    )
    await ctx.send(
        embed=embed,
        ephemeral=True,
    )


async def show_channel(
    bot: commands.Bot, ctx: commands.Context, table: ConfigTables, key
):
    db = ConfigDatabase(bot)
    channels = db.get_items_by(table, key)
    embed = Embed(title=f"Role on join", color=0x00FF42)
    embed.add_field(
        name="Channels",
        value="\n".join([ctx.guild.get_channel(int(c)).name for c in channels]),
    )
    await ctx.send(
        embed=embed,
        ephemeral=True,
    )


async def set_value(
    bot: commands.Bot, ctx: commands.Context, table: ConfigTables, key, value
):
    db = ConfigDatabase(bot)
    roles = db.get_items_by(table, key)
    if value in roles:
        await ctx.send(
            embed=Embed(title=f"id: {value} already set", color=0xFF0000),
            ephemeral=True,
        )
        return

    db.insert_item(table, key, value)
    await ctx.send(
        embed=Embed(title=f"id: {value} set", color=0x00FF42),
        ephemeral=True,
    )


async def remove_value(bot: commands.Bot, ctx: commands.Context, table, key, value):
    db = ConfigDatabase(bot)
    roles = db.get_items_by(table, key)
    if value not in roles:
        await ctx.send(
            embed=Embed(title=f"id: {value} not added", color=0xFF0000),
            ephemeral=True,
        )
        return
    db.delete_item(table, key, value)
    await ctx.send(
        embed=Embed(title=f"Removed id: {value} ", color=0x00FF42),
        ephemeral=True,
    )


async def remove_all_values(bot: commands.Bot, ctx: commands.Context, table, key):
    db = ConfigDatabase(bot)
    roles = db.get_items_by(table, key)
    if len(roles) == 0:
        await ctx.send(
            embed=Embed(title=f"Is already empty", color=0xFF0000),
            ephemeral=True,
        )
        return
    db.delete_item(table, key)
    await ctx.send(
        embed=Embed(title=f"Removed everything", color=0x00FF42),
        ephemeral=True,
    )
