import sqlite3
from typing import Dict, List
from discord.ext import commands
import os

class Database:
    def __init__(self, db_path):
        self.connection = sqlite3.connect(db_path)
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

class Bjorn_cog(commands.Cog):
    def __init__(self, bot):
        self.loading_id = int(os.getenv("LOADING_ID"))
        