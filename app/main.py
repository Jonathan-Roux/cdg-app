from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import engine, get_db, Base
from app import models
from app.auth import verifier_mot_de_passe, creer_token, get_utilisateur_actuel, UTILISATEUR
from app.pdf import generer_devis_pdf
from app.routers import auth_api, client_api, admin_api
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CDG Serrurerie", version="2.0")
templates = Jinja2Templates(directory="app/templates")

# CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://cdgserrurerie.fr,https://www.cdgserrurerie.fr,http://localhost:3000,http://localhost:5500,http://localhost:8080,http://127.0.0.1:5500").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers API
app.include_router(auth_api.router)
app.include_router(client_api.router)
app.include_router(admin_api.router)

STATUTS_VALIDES = ["brouillon", "envoye", "accepte", "refuse", "facture"]

@app.get("/")
def accueil():
    return {"message": "API CDG Serrurerie v2.0 operationnelle"}

# --- AUTH DASHBOARD ---

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)
    try:
        get_utilisateur_actuel(token)
    except:
        return RedirectResponse(url="/login", status_code=302)
    clients = db.query(models.Client).all()
    devis = db.query(models.Devis).all()
    return templates.TemplateResponse(request=request, name="index.html", context={
        "clients": clients,
        "devis": devis
    })

@app.get("/login", response_class=HTMLResponse)
def page_login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username != UTILISATEUR["username"] or not verifier_mot_de_passe(password, UTILISATEUR["password"]):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    token = creer_token({"sub": username})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="token", value=token, httponly=True)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("token")
    return response

# --- CLIENTS ---

@app.post("/clients")
def creer_client(nom: str, prenom: str = None, email: str = None, telephone: str = None,
                  adresse: str = None, ville: str = None, code_postal: str = None,
                  contact: str = None, notes: str = None, db: Session = Depends(get_db)):
    client = models.Client(nom=nom, prenom=prenom, email=email, telephone=telephone,
        adresse=adresse, ville=ville, code_postal=code_postal, contact=contact, notes=notes)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@app.get("/clients")
def liste_clients(db: Session = Depends(get_db)):
    return db.query(models.Client).all()

@app.get("/clients/{client_id}")
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    return client

@app.put("/clients/{client_id}")
def modifier_client(client_id: int, nom: str = None, prenom: str = None,
                     email: str = None, telephone: str = None, adresse: str = None,
                     ville: str = None, code_postal: str = None, contact: str = None,
                     notes: str = None, db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    if nom: client.nom = nom
    if prenom: client.prenom = prenom
    if email: client.email = email
    if telephone: client.telephone = telephone
    if adresse: client.adresse = adresse
    if ville: client.ville = ville
    if code_postal: client.code_postal = code_postal
    if contact: client.contact = contact
    if notes: client.notes = notes
    db.commit()
    db.refresh(client)
    return client

@app.delete("/clients/{client_id}")
def supprimer_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    db.delete(client)
    db.commit()
    return {"message": f"Client {client.nom} supprime"}

# --- DEVIS ---

@app.post("/devis")
def creer_devis(numero: str, client_id: int, adresse_intervention: str = None,
                notes: str = None, db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    devis = models.Devis(numero=numero, client_id=client_id,
        adresse_intervention=adresse_intervention, notes=notes)
    db.add(devis)
    db.commit()
    db.refresh(devis)
    return devis

@app.get("/devis")
def liste_devis(db: Session = Depends(get_db)):
    return db.query(models.Devis).all()

@app.get("/devis/{devis_id}")
def get_devis(devis_id: int, db: Session = Depends(get_db)):
    devis = db.query(models.Devis).filter(models.Devis.id == devis_id).first()
    if not devis:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    return devis

@app.get("/devis/{devis_id}/total")
def total_devis(devis_id: int, db: Session = Depends(get_db)):
    devis = db.query(models.Devis).filter(models.Devis.id == devis_id).first()
    if not devis:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    lignes = db.query(models.LigneDevis).filter(models.LigneDevis.devis_id == devis_id).all()
    total_ht = sum(l.quantite * l.prix_unitaire_ht for l in lignes)
    tva = sum(l.quantite * l.prix_unitaire_ht * l.tva / 100 for l in lignes)
    return {"devis": devis.numero, "statut": devis.statut,
            "total_ht": round(total_ht, 2), "tva": round(tva, 2),
            "total_ttc": round(total_ht + tva, 2)}

@app.post("/devis/{devis_id}/lignes")
def ajouter_ligne(devis_id: int, designation: str, prix_unitaire_ht: float,
                  quantite: float = 1, tva: float = 20.0, db: Session = Depends(get_db)):
    devis = db.query(models.Devis).filter(models.Devis.id == devis_id).first()
    if not devis:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    ligne = models.LigneDevis(devis_id=devis_id, designation=designation,
        quantite=quantite, prix_unitaire_ht=prix_unitaire_ht, tva=tva)
    db.add(ligne)
    db.commit()
    db.refresh(ligne)
    return ligne

@app.put("/devis/{devis_id}/statut")
def changer_statut(devis_id: int, statut: str, db: Session = Depends(get_db)):
    if statut not in STATUTS_VALIDES:
        raise HTTPException(status_code=400, detail=f"Statut invalide: {STATUTS_VALIDES}")
    devis = db.query(models.Devis).filter(models.Devis.id == devis_id).first()
    if not devis:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    devis.statut = statut
    db.commit()
    return {"devis_id": devis_id, "statut": devis.statut}

@app.delete("/devis/{devis_id}")
def supprimer_devis(devis_id: int, db: Session = Depends(get_db)):
    devis = db.query(models.Devis).filter(models.Devis.id == devis_id).first()
    if not devis:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    db.delete(devis)
    db.commit()
    return {"message": f"Devis {devis.numero} supprime"}

# --- PDF ---

@app.get("/devis/{devis_id}/pdf")
def telecharger_pdf(devis_id: int, db: Session = Depends(get_db),
                    utilisateur: str = Depends(get_utilisateur_actuel)):
    devis = db.query(models.Devis).filter(models.Devis.id == devis_id).first()
    if not devis:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    pdf_bytes = generer_devis_pdf(devis, db)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=devis-{devis.numero}.pdf"}
    )
