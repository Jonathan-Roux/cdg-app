from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from fastapi import HTTPException, Cookie, Depends
from typing import Optional
import os

SECRET_KEY = os.getenv("SECRET_KEY", "cdg-serrurerie-secret-key-2026")
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60 * 8  # 8 heures

# Compte admin legacy (compatibilité dashboard existant)
_admin_mdp = os.getenv("APP_PASSWORD", "cdg2026").encode()
_admin_username = os.getenv("APP_USERNAME", "jonathan")

UTILISATEUR = {
    "username": _admin_username,
    "password": bcrypt.hashpw(_admin_mdp, bcrypt.gensalt()),
    "role": "admin"
}


def hasher_mot_de_passe(mdp: str) -> str:
    return bcrypt.hashpw(mdp.encode(), bcrypt.gensalt()).decode()


def verifier_mot_de_passe(mdp_brut: str, mdp_hash: str) -> bool:
    if isinstance(mdp_hash, bytes):
        return bcrypt.checkpw(mdp_brut.encode(), mdp_hash)
    return bcrypt.checkpw(mdp_brut.encode(), mdp_hash.encode())


def creer_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decoder_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")


def get_utilisateur_actuel(token: Optional[str] = Cookie(default=None)):
    """Compatibilité dashboard admin existant"""
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    payload = decoder_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Token invalide")
    return username


def get_current_payload(token: Optional[str] = Cookie(default=None)) -> dict:
    """Retourne le payload complet JWT (sub, role, user_id)"""
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    return decoder_token(token)


def require_admin(payload: dict = Depends(get_current_payload)) -> dict:
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    return payload


def require_client_or_admin(payload: dict = Depends(get_current_payload)) -> dict:
    if payload.get("role") not in ("client", "admin"):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    return payload
