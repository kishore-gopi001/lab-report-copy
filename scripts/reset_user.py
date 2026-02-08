# scripts/reset_user.py
import sqlite3
from passlib.hash import pbkdf2_sha256
from pathlib import Path

DB_PATH = Path("database/lab_results.db")

def reset():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Generate PBKDF2 hash for 'admin123'
    hashed = pbkdf2_sha256.hash("admin123")
    print(f"New Hash: {hashed}")
    
    try:
        cur.execute("UPDATE users SET hashed_password = ? WHERE username = ?", (hashed, "admin"))
        if cur.rowcount == 0:
             cur.execute("INSERT INTO users (username, hashed_password, full_name, role) VALUES (?, ?, ?, ?)", ("admin", hashed, "Admin User", "admin"))
        conn.commit()
        print("User 'admin' updated/created successfully with pbkdf2_sha256.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset()
