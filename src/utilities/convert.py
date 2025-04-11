#!/usr/bin/env python3
import sqlite3
import os
import logging
import shutil
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database paths
OLD_DB_PATH = 'data/league(OLD).sqlite'
NEW_DB_PATH = 'data/league(NEW).sqlite'
REFERENCE_DB_PATH = 'data/league.sqlite'
BACKUP_PATH = f'data/old_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sqlite'

def backup_original():
    """Create a backup of the old database before conversion"""
    if os.path.exists(OLD_DB_PATH):
        logger.info(f"Creating backup of original old database at {BACKUP_PATH}")
        shutil.copy2(OLD_DB_PATH, BACKUP_PATH)
        return True
    else:
        logger.warning(f"Old database not found at {OLD_DB_PATH}")
        return False

def get_schema_from_reference():
    """Extract schema from the reference database"""
    if not os.path.exists(REFERENCE_DB_PATH):
        logger.error(f"Reference database not found at {REFERENCE_DB_PATH}")
        return None
    
    try:
        # Connect to the reference database
        ref_conn = sqlite3.connect(REFERENCE_DB_PATH)
        ref_cursor = ref_conn.cursor()
        
        # Get all table names
        ref_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = ref_cursor.fetchall()
        table_schemas = {}
        
        # Get schema for each table
        for table in tables:
            table_name = table[0]
            # Skip SQLite internal tables
            if table_name.startswith('sqlite_'):
                logger.info(f"Skipping SQLite internal table: {table_name}")
                continue
                
            ref_cursor.execute(f"PRAGMA table_info({table_name});")
            columns = ref_cursor.fetchall()
            
            create_statement = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            column_defs = []
            
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, is_pk = col
                column_def = f"{col_name} {col_type}"
                
                if not_null:
                    column_def += " NOT NULL"
                if default_val is not None:
                    column_def += f" DEFAULT {default_val}"
                if is_pk:
                    column_def += " PRIMARY KEY"
                    
                column_defs.append(column_def)
                
            create_statement += ", ".join(column_defs) + ");"
            table_schemas[table_name] = {
                'create_sql': create_statement,
                'columns': [col[1] for col in columns]
            }
        
        ref_cursor.close()
        ref_conn.close()
        return table_schemas
    
    except Exception as e:
        logger.error(f"Error getting schema from reference database: {e}")
        return None

def convert_database():
    """Copy data from the old database to a new one with the reference schema"""
    # Verify old database exists
    if not os.path.exists(OLD_DB_PATH):
        logger.error(f"Old database file not found at {OLD_DB_PATH}")
        return False
    
    # Get schema from reference database
    schema = get_schema_from_reference()
    if not schema:
        logger.error("Failed to get schema from reference database")
        return False
    
    # Create backup
    backup_original()
    
    # Remove new database if it exists
    if os.path.exists(NEW_DB_PATH):
        logger.info(f"Removing existing new database at {NEW_DB_PATH}")
        os.remove(NEW_DB_PATH)
    
    try:
        # Connect to databases
        old_conn = sqlite3.connect(OLD_DB_PATH)
        old_cursor = old_conn.cursor()
        
        new_conn = sqlite3.connect(NEW_DB_PATH)
        new_cursor = new_conn.cursor()
        
        # Enable foreign keys in the new database
        new_cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Create tables in the new database based on reference schema
        logger.info("Creating tables in new database based on reference schema")
        for table_name, table_info in schema.items():
            # Skip any internal SQLite tables (extra check)
            if table_name.startswith('sqlite_'):
                logger.info(f"Skipping SQLite internal table: {table_name}")
                continue
                
            new_cursor.execute(table_info['create_sql'])
            logger.info(f"Created table {table_name} in new database")
        
        # Check which tables exist in the old database
        old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        old_tables = [row[0] for row in old_cursor.fetchall()]
        
        # Copy data from old database to new database
        logger.info("Copying data from old database to new database")
        for table_name, table_info in schema.items():
            # Skip any internal SQLite tables (extra check)
            if table_name.startswith('sqlite_'):
                continue
                
            if table_name in old_tables:
                # Get column names that exist in both databases
                old_cursor.execute(f"PRAGMA table_info({table_name});")
                old_columns = [row[1] for row in old_cursor.fetchall()]
                
                # Find common columns
                common_columns = [col for col in old_columns if col in table_info['columns']]
                
                if common_columns:
                    # Select data from old table
                    columns_str = ', '.join(common_columns)
                    old_cursor.execute(f"SELECT {columns_str} FROM {table_name};")
                    rows = old_cursor.fetchall()
                    
                    if rows:
                        # Prepare INSERT statement with placeholders
                        placeholders = ', '.join(['?' for _ in common_columns])
                        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders});"
                        
                        # Insert data into new table
                        new_cursor.executemany(insert_sql, rows)
                        logger.info(f"Copied {len(rows)} rows from {table_name}")
                    else:
                        logger.info(f"No data found in table {table_name}")
                else:
                    logger.warning(f"No common columns found for table {table_name}")
            else:
                logger.warning(f"Table {table_name} not found in old database")
        
        # Commit changes and close connections
        new_conn.commit()
        logger.info("Database conversion completed successfully")
        
        old_cursor.close()
        old_conn.close()
        new_cursor.close()
        new_conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error during database conversion: {e}")
        if 'new_conn' in locals():
            new_conn.rollback()
        return False

if __name__ == "__main__":
    logger.info("Starting database conversion")
    result = convert_database()
    
    if result:
        logger.info("Database conversion completed successfully")
        logger.info(f"New database created at {NEW_DB_PATH}")
        logger.info(f"Backup of original database created at {BACKUP_PATH}")
    else:
        logger.error("Database conversion failed")