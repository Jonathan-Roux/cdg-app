from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app import models
from app.auth import hasher_mot_de_passe, verifier_mot_de_passe, creer_token, decoder_token, UTILISATEUR

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterSchema(BaseModel):
    email: str
    password: str
    nom: str
    prenom: Optional[str] = None
    telephone: Optional[str] = None


class LoginSchema(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email deja utilise")
    user = models.User(
        email=data.email,
        password_hash=hasher_mot_de_passe(data.password),
        role="client",
        nom=data.nom,
        prenom=data.prenom,
        telephone=data.telephone
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    client = models.Client(
        nom=data.nom, prenom=data.prenom, email=data.email,
        telephone=data.telephone, user_id=user.id
    )
    db.add(client)
    db.commit()
    token = creer_token({"sub": data.email, "role": "client", "user_id": user.id})
    return {"token": token, "role": "client", "nom": user.nom, "email": user.email}


@router.post("/login")
def login(data: LoginSchema, response: Response, db: Session = Depends(get_db)):
    admin_user = UTILISATEUR["username"]
    if data.email == admin_user or data.email == f"{admin_user}@cdgserrurerie.fr":
        if verifier_mot_de_passe(data.password, UTILISATEUR["password"]):
            token = creer_token({"sub": admin_user, "role": "admin", "user_id": 0})
            response.set_cookie(key="token", value=token, httponly=True, samesite="lax", max_age=60*60*8)
            return {"token": token, "role": "admin", "nom": "Jonathan", "email": data.email}
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not verifier_mot_de_passe(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    if not user.actif:
        raise HTTPException(status_code=403, detail="Compte desactive")
    token = creer_token({"sub": user.email, "role": user.role, "user_id": user.id})
    response.set_cookie(key="token", value=token, httponly=True, samesite="lax", max_age=60*60*8)
    return {"token": token, "role": user.role, "nom": user.nom, "email": user.email}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("token")
    return {"message": "Deconnecte"}


@router.get("/me")
def get_me(token: Optional[str] = Cookie(default=None), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifie")
    payload = decoder_token(token)
    role = payload.get("role")
    email = payload.get("sub")
    user_id = payload.get("user_id")
    if role == "admin":
        return {"email": email, "role": "admin", "nom": "Jonathan", "prenom": ""}
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return {"id": user.id, "email": user.email, "role": user.role,
            "nom": user.nom, "prenom": user.prenom or "", "telephone": user.telephone or ""}
