from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from fastapi import HTTPException, Cookie
from typing import Optional

import os

SECRET_KEY = os.getenv("SECRET_KEY", "cdg-serrurerie-secret-key-2026")
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60 * 8  # 8 heures

_mdp = os.getenv("APP_PASSWORD", "cdg2026").encode()
_username = os.getenv("APP_USERNAME", "jonathan")

# Utilisateur unique
UTILISATEUR = {
    "username": _username,
    "password": bcrypt.hashpw(_mdp, bcrypt.gensalt())
}

def verifier_mot_de_passe(mdp_brut: str, mdp_hash: bytes):
    return bcrypt.checkpw(mdp_brut.encode(), mdp_hash)

def creer_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_utilisateur_actuel(token: Optional[str] = Cookie(default=None)):
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, deta