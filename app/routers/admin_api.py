from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app import models
from app.auth import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])

STATUTS_DEVIS = ["brouillon", "envoye", "accepte", "refuse", "facture"]
STATUTS_INTERVENTION = ["planifiee", "en_cours", "terminee", "annulee"]
STATUTS_FACTURE = ["en_attente", "payee", "annulee"]


@router.get("/clients")
def liste_clients(db: Session = Depends(get_db), _=Depends(require_admin)):
    clients = db.query(models.Client).all()
    return [{
        "id": c.id, "nom": c.nom, "prenom": c.prenom or "",
        "email": c.email or "", "telephone": c.telephone or "",
        "adresse": c.adresse or "", "ville": c.ville or "",
        "code_postal": c.code_postal or "",
        "a_compte": c.user_id is not None,
        "created_at": c.created_at.strftime("%d/%m/%Y") if c.created_at else ""
    } for c in clients]


@router.get("/clients/{client_id}")
def get_client(client_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    c = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client introuvable")
    devis = db.query(models.Devis).filter(models.Devis.client_id == client_id).all()
    interventions = db.query(models.Intervention).filter(models.Intervention.client_id == client_id).all()
    return {
        "id": c.id, "nom": c.nom, "prenom": c.prenom or "",
        "email": c.email or "", "telephone": c.telephone or "",
        "adresse": c.adresse or "", "ville": c.ville or "",
        "notes": c.notes or "", "a_compte": c.user_id is not None,
        "nb_devis": len(devis), "nb_interventions": len(interventions)
    }


@router.get("/devis")
def liste_devis(db: Session = Depends(get_db), _=Depends(require_admin)):
    devis_list = db.query(models.Devis).order_by(models.Devis.created_at.desc()).all()
    result = []
    for d in devis_list:
        lignes = db.query(models.LigneDevis).filter(models.LigneDevis.devis_id == d.id).all()
        total_ttc = sum(l.quantite * l.prix_unitaire_ht * (1 + l.tva / 100) for l in lignes)
        client = db.query(models.Client).filter(models.Client.id == d.client_id).first()
        result.append({
            "id": d.id, "numero": d.numero,
            "client": f"{client.nom} {client.prenom or ''}" if client else "-",
            "client_id": d.client_id, "statut": d.statut,
            "total_ttc": round(total_ttc, 2),
            "created_at": d.created_at.strftime("%d/%m/%Y") if d.created_at else ""
        })
    return result


class StatutDevisSchema(BaseModel):
    statut: str

@router.put("/devis/{devis_id}/statut")
def changer_statut_devis(devis_id: int, data: StatutDevisSchema,
                          db: Session = Depends(get_db), _=Depends(require_admin)):
    if data.statut not in STATUTS_DEVIS:
        raise HTTPException(status_code=400, detail=f"Statut invalide")
    d = db.query(models.Devis).filter(models.Devis.id == devis_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    d.statut = data.statut
    db.commit()
    return {"id": d.id, "statut": d.statut}


class InterventionSchema(BaseModel):
    client_id: int
    description: str
    statut: Optional[str] = "planifiee"
    date_intervention: Optional[str] = None
    technicien: Optional[str] = None
    notes: Optional[str] = None

@router.get("/interventions")
def liste_interventions(db: Session = Depends(get_db), _=Depends(require_admin)):
    interventions = db.query(models.Intervention).order_by(models.Intervention.created_at.desc()).all()
    result = []
    for i in interventions:
        client = db.query(models.Client).filter(models.Client.id == i.client_id).first()
        result.append({
            "id": i.id,
            "client": f"{client.nom} {client.prenom or ''}" if client else "-",
            "client_id": i.client_id, "description": i.description, "statut": i.statut,
            "date_intervention": i.date_intervention.strftime("%d/%m/%Y %H:%M") if i.date_intervention else "A planifier",
            "technicien": i.technicien or "CDG Serrurerie",
            "created_at": i.created_at.strftime("%d/%m/%Y") if i.created_at else ""
        })
    return result

@router.post("/interventions")
def creer_intervention(data: InterventionSchema, db: Session = Depends(get_db), _=Depends(require_admin)):
    client = db.query(models.Client).filter(models.Client.id == data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    intervention = models.Intervention(
        client_id=data.client_id, description=data.description,
        statut=data.statut, technicien=data.technicien, notes=data.notes
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    return {"id": intervention.id, "statut": intervention.statut}

class StatutInterventionSchema(BaseModel):
    statut: str

@router.put("/interventions/{intervention_id}/statut")
def changer_statut_intervention(intervention_id: int, data: StatutInterventionSchema,
                                 db: Session = Depends(get_db), _=Depends(require_admin)):
    if data.statut not in STATUTS_INTERVENTION:
        raise HTTPException(status_code=400, detail="Statut invalide")
    i = db.query(models.Intervention).filter(models.Intervention.id == intervention_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Intervention introuvable")
    i.statut = data.statut
    db.commit()
    return {"id": i.id, "statut": i.statut}


class FactureSchema(BaseModel):
    client_id: int
    devis_id: Optional[int] = None
    numero: str
    montant_ht: float
    montant_ttc: float
    notes: Optional[str] = None

@router.get("/factures")
def liste_factures(db: Session = Depends(get_db), _=Depends(require_admin)):
    factures = db.query(models.Facture).order_by(models.Facture.created_at.desc()).all()
    result = []
    for f in factures:
        client = db.query(models.Client).filter(models.Client.id == f.client_id).first()
        result.append({
            "id": f.id, "numero": f.numero,
            "client": f"{client.nom} {client.prenom or ''}" if client else "-",
            "client_id": f.client_id, "statut": f.statut,
            "montant_ht": f.montant_ht, "montant_ttc": f.montant_ttc,
            "created_at": f.created_at.strftime("%d/%m/%Y") if f.created_at else ""
        })
    return result

@router.post("/factures")
def creer_facture(data: FactureSchema, db: Session = Depends(get_db), _=Depends(require_admin)):
    client = db.query(models.Client).filter(models.Client.id == data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    facture = models.Facture(
        numero=data.numero, client_id=data.client_id, devis_id=data.devis_id,
        montant_ht=data.montant_ht, montant_ttc=data.montant_ttc,
        notes=data.notes, user_id=client.user_id
    )
    db.add(facture)
    db.commit()
    db.refresh(facture)
    return {"id": facture.id, "numero": facture.numero}

class StatutFactureSchema(BaseModel):
    statut: str

@router.put("/factures/{facture_id}/statut")
def changer_statut_facture(facture_id: int, data: StatutFactureSchema,
                            db: Session = Depends(get_db), _=Depends(require_admin)):
    if data.statut not in STATUTS_FACTURE:
        raise HTTPException(status_code=400, detail="Statut invalide")
    f = db.query(models.Facture).filter(models.Facture.id == facture_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    f.statut = data.statut
    db.commit()
    return {"id": f.id, "statut": f.statut}


@router.get("/stats")
def stats(db: Session = Depends(get_db), _=Depends(require_admin)):
    ca_result = db.query(func.sum(models.Facture.montant_ht)).filter(
        models.Facture.statut == "payee"
    ).scalar()
    return {
        "clients": db.query(models.Client).count(),
        "devis": db.query(models.Devis).count(),
        "devis_acceptes": db.query(models.Devis).filter(models.Devis.statut == "accepte").count(),
        "interventions": db.query(models.Intervention).count(),
        "interventions_en_cours": db.query(models.Intervention).filter(models.Intervention.statut == "en_cours").count(),
        "factures": db.query(models.Facture).count(),
        "factures_en_attente": db.query(models.Facture).filter(models.Facture.statut == "en_attente").count(),
        "ca_ht": round(ca_result or 0, 2)
    }
