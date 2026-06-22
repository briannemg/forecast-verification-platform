"""Database utilities for the weather verification platform."""

import sqlite3
from pathlib import Path

from src.config import BASE_DIR, DATABASE_PATH

def get_connection() -> sqlite3.Connection:
    """Create a SQLite database connection.

    Returns
    -------
    sqlite3.Connection
        Active connection to the project database.
        
    Raises
    ------
    sqlite3.Error
        Raised if the database connection cannot be established.
    """
    connection = sqlite3.connect(DATABASE_PATH)
    
    if connection is None:
        raise sqlite3.Error("Unable to establish database connection.")
    
    return connection
    
def initialize_database() -> None:
    """Initialize database tables from schema.sql.
    
    Reads the SQL schema file and creates all required database tables.
    
    Raises
    ------
    FileNotFoundError
        Raised if the schema file cannot be located.
    sqlite3.Error
        Raised if SQL execution fails.
    """
    schema_path: Path = BASE_DIR / "sql" / "schema.sql"
    
    with open(schema_path, "r", encoding="utf-8") as file:
        schema = file.read()
        
    with get_connection() as connection:
        connection.execute("PRAGMA foreign_keys = ON;")
        connection.executescript(schema)
        
        
if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized: {DATABASE_PATH}")