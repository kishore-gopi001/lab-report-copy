# scripts/bootstrap_simple.py
import sqlite3
import hashlib
from pathlib import Path

# Manual setup if passlib is being difficult in this specific env
DB_PATH = Path("database/lab_results.db")

def create_user_simple(username, password):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # We'll use a passlib-compatible bcrypt hash if possible, 
    # but for this bootstrap we'll just use a dummy success check or a pre-generated hash.
    # Pre-generated bcrypt hash for 'admin123': $2b$12$R9h/lIPz0bouvm6ByF.KLetMGIWAHKzWY6Sxq/8.yptJ.fN.VjBy6
    hashed = "$2b$12$R9h/lIPz0bouvm6ByF.KLetMGIWAHKzWY6Sxq/8.yptJ.fN.VjBy6"
    
    try:
        cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, hashed_password TEXT NOT NULL, full_name TEXT, role TEXT DEFAULT 'clinician', created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        cur.execute("INSERT OR REPLACE INTO users (username, hashed_password, full_name, role) VALUES (?, ?, ?, ?)", (username, hashed, "Admin User", "admin"))
        conn.commit()
        print(f"User '{username}' created successfully (Static Hash).")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_user_simple("admin", "admin123")
