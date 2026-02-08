import sqlite3
from pathlib import Path

# Database file path
DB_PATH = Path("database/lab_results.db")

# Ensure database directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """
    Returns a SQLite database connection.

    - check_same_thread=False is required for FastAPI background tasks
    - row_factory allows dict-like access to rows
    """

    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
        isolation_level=None  # autocommit mode (safer for concurrent reads)
    )
    conn.row_factory = sqlite3.Row
    return conn
