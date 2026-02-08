# app/services/auth_service.py

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from database.db import get_connection

# --- Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def verify_password(plain_password, hashed_password):
    print(f"AUTH_DEBUG: Comparing Plain (len={len(plain_password)}) with Hash ('{hashed_password[:10]}...')")
    try:
        match = pwd_context.verify(plain_password, hashed_password)
        print(f"AUTH_DEBUG: Result = {match}")
        return match
    except Exception as e:
        print(f"AUTH_DEBUG: Error during verify = {e}")
        return False

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    print(f"AUTH_DEBUG: get_current_user - token received: {token[:10] if token else 'NONE'}... (len: {len(token) if token else 0})")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print(f"AUTH_DEBUG: Decoding token with SECRET_KEY='{SECRET_KEY[:5]}...'")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        print(f"AUTH_DEBUG: Token decoded. Username = {username}")
        if username is None:
            print("AUTH_DEBUG: Username is None in payload")
            raise credentials_exception
    except JWTError as e:
        print(f"AUTH_DEBUG: JWT Decode Error: {e}")
        raise credentials_exception
        
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()
    
    if user is None:
        print(f"AUTH_DEBUG: User {username} not found in DB during token validation")
        raise credentials_exception
    print(f"AUTH_DEBUG: get_current_user success for {username}")
    return dict(user)
