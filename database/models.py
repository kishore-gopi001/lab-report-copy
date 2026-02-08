from database.db import get_connection


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Main table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lab_interpretations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        hadm_id INTEGER,
        test_name TEXT NOT NULL,
        value REAL,
        unit TEXT,
        gender TEXT,
        status TEXT,
        reason TEXT,
        processed_time TEXT,
        reviewed INTEGER DEFAULT 0
    )
    """)

    # Indexes for performance (VERY IMPORTANT)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_lab_subject
    ON lab_interpretations (subject_id)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_lab_status
    ON lab_interpretations (status)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_lab_subject_status
    ON lab_interpretations (subject_id, status)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_lab_time
    ON lab_interpretations (processed_time)
    """)

    # User table for authentication
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT,
        role TEXT DEFAULT 'clinician',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
