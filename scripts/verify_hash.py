# scripts/verify_hash.py
from passlib.hash import pbkdf2_sha256
import sqlite3
from pathlib import Path

DB_PATH = Path("database/lab_results.db")

def verify():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT hashed_password FROM users WHERE username = 'admin'")
    row = cur.fetchone()
    conn.close()
    
    if not row:
        print("Error: 'admin' user not found in DB")
        return
        
    hashed = row[0]
    print(f"Stored Hash: {hashed}")
    
    # Test common combinations
    test_pwd = "admin123"
    try:
        match = pbkdf2_sha256.verify(test_pwd, hashed)
        print(f"Password 'admin123' match: {match}")
    except Exception as e:
        print(f"Verification Error: {e}")

if __name__ == "__main__":
    verify()
