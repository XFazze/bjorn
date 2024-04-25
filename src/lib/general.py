from typing import Dict, List
from discord.ext import commands
import sqlite3
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
