# scripts/create_user.py

import sys
import os
sys.path.append(os.getcwd())

from database.db import get_connection
from database.models import create_tables
from app.services.auth_service import get_password_hash

def create_user(username, password, full_name, role="clinician"):
    create_tables()  # Ensure table exists
    conn = get_connection()
    cur = conn.cursor()
    
    hashed_password = get_password_hash(password)
    
    try:
        cur.execute(
            "INSERT INTO users (username, hashed_password, full_name, role) VALUES (?, ?, ?, ?)",
            (username, hashed_password, full_name, role)
        )
        conn.commit()
        print(f"User '{username}' created successfully.")
    except Exception as e:
        print(f"Error creating user: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_user("admin", "admin123", "Admin User", "admin")
