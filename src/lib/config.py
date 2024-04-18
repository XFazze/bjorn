from enum import Enum
import os

from discord.ext import commands
from discord import Member, Role, Embed

from lib.general import Database


class ConfigTables(Enum):
    ROLEONJOIN = "roleonjoin", "guild_id", "role_id"
    ADMIN = "admin", "guild_id", "role_id"

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

    def get_items(self, table: ConfigTables):
        return self.cursor.execute(
            f"SELECT {table.col1}, {table.col2} FROM {table.table}"
        ).fetchall()

    def get_items_by(self, table: ConfigTables, col1: str):
        return self.cursor.execute(
            f"SELECT {table.col1}, {table.col2} FROM {table.table} WHERE {table.col1} = {col1}"
        ).fetchall()

    def insert_item(self, table: ConfigTables, col1: str, col2: str):
        self.cursor.execute(
            f"INSERT INTO {table.table} ({table.col1}, {table.col2}) VALUES ({col1}, {col2})"
        )
        self.connection.commit()

    def delete_item(self, table: ConfigTables, col1: str = None, col2: str = None):
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


async def show_values(
    bot: commands.Bot, ctx: commands.Context, table: ConfigTables, key
):
    db = ConfigDatabase(bot)
    roles = db.get_items_by(table, key)
    embed = Embed(title=f"Role on join", color=0x00FF42)
    embed.add_field(
        name="Roles",
        value="\n".join([ctx.guild.get_role(int(r[1])).name for r in roles]),
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
    if value in [r[1] for r in roles]:
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
    if value not in [r[1] for r in roles]:
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
