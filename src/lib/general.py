from typing import Dict, List
from discord.ext import commands
import sqlite3
from enum import Enum
import os


class Database:
    def __init__(self, db_path):
        self.connection = sqlite3.connect(os.environ["DATA_DIR"] + db_path + ".sqlite")
        self.cursor = self.connection.cursor()

    def create_tables(self, tables: Dict[str, List[str]]):
        for table_name, columns in tables.items():
            self.cursor.execute(
                f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {", ".join(columns)}
                    )
                """
            )


class ConfigTables(Enum):
    ROLEONJOIN = "roleonjoin", "guild_id", "role_id"

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


class Bjorn_cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.loading_id = int(os.environ["LOADING_ID"])
