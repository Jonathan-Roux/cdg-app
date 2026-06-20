from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import models
from app.auth import decoder_token

router = APIRouter(prefix="/api/client", tags=["client"])


def get_client_from_token(token: Optional[str] = Cookie(default=None), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifie")
    payload = decoder_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalide")
    client = db.query(models.Client).filter(models.Client.user_id == user_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Profil client introuvable")
    return client


@router.get("/devis")
def mes_devis(client: models.Client = Depends(get_client_from_token), db: Session = Depends(get_db)):
    devis_list = db.query(models.Devis).filter(models.Devis.client_id == client.id).all()
    result = []
    for d in devis_list:
        lignes = db.query(models.LigneDevis).filter(models.LigneDevis.devis_id == d.id).all()
        total_ht = sum(l.quantite * l.prix_unitaire_ht for l in lignes)
        total_ttc = sum(l.quantite * l.prix_unitaire_ht * (1 + l.tva / 100) for l in lignes)
        result.append({
            "id": d.id, "numero": d.numero, "statut": d.statut,
            "adresse_intervention": d.adresse_intervention or "",
            "notes": d.notes or "",
            "total_ht": round(total_ht, 2), "total_ttc": round(total_ttc, 2),
            "created_at": d.created_at.strftime("%d/%m/%Y") if d.created_at else ""
        })
    return result


@router.get("/interventions")
def mes_interventions(client: models.Client = Depends(get_client_from_token), db: Session = Depends(get_db)):
    interventions = db.query(models.Intervention).filter(
        models.Intervention.client_id == client.id
    ).order_by(models.Intervention.created_at.desc()).all()
    return [{
        "id": i.id, "description": i.description, "statut": i.statut,
        "date_intervention": i.date_intervention.strftime("%d/%m/%Y %H:%M") if i.date_intervention else "A planifier",
        "technicien": i.technicien or "CDG Serrurerie",
        "notes": i.notes or "",
        "created_at": i.created_at.strftime("%d/%m/%Y") if i.created_at else ""
    } for i in interventions]


@router.get("/factures")
def mes_factures(client: models.Client = Depends(get_client_from_token), db: Session = Depends(get_db)):
    factures = db.query(models.Facture).filter(
        models.Facture.client_id == client.id
    ).order_by(models.Facture.created_at.desc()).all()
    return [{
        "id": f.id, "numero": f.numero, "statut": f.statut,
        "montant_ht": f.montant_ht, "montant_ttc": f.montant_ttc,
        "notes": f.notes or "",
        "created_at": f.created_at.strftime("%d/%m/%Y") if f.created_at else ""
    } for f in factures]


@router.get("/profil")
def mon_profil(token: Optional[str] = Cookie(default=None), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifie")
    payload = decoder_token(token)
    user_id = payload.get("user_id")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    client = db.query(models.Client).filter(models.Client.user_id == user_id).first()
    return {
        "nom": user.nom, "prenom": user.prenom or "",
        "email": user.email, "telephone": user.telephone or "",
        "adresse": client.adresse if client else "",
        "ville": client.ville if client else "",
        "code_postal": client.code_postal if client else ""
    }
