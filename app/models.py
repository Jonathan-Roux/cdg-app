from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="client")  # "admin" ou "client"
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=True)
    telephone = Column(String, nullable=True)
    actif = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    interventions = relationship("Intervention", back_populates="user")
    factures = relationship("Facture", back_populates="user")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=True)
    email = Column(String, nullable=True)
    telephone = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    ville = Column(String, nullable=True)
    code_postal = Column(String, nullable=True)
    contact = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    devis = relationship("Devis", back_populates="client")
    interventions = relationship("Intervention", back_populates="client")
    factures_client = relationship("Facture", back_populates="client")


class Devis(Base):
    __tablename__ = "devis"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    statut = Column(String, default="brouillon")
    adresse_intervention = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    client = relationship("Client", back_populates="devis")
    lignes = relationship("LigneDevis", back_populates="devis")
    facture = relationship("Facture", back_populates="devis", uselist=False)


class LigneDevis(Base):
    __tablename__ = "lignes_devis"

    id = Column(Integer, primary_key=True, index=True)
    devis_id = Column(Integer, ForeignKey("devis.id"), nullable=False)
    designation = Column(String, nullable=False)
    quantite = Column(Float, default=1)
    prix_unitaire_ht = Column(Float, nullable=False)
    tva = Column(Float, default=20.0)

    devis = relationship("Devis", back_populates="lignes")


class Facture(Base):
    __tablename__ = "factures"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, nullable=False)
    devis_id = Column(Integer, ForeignKey("devis.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    statut = Column(String, default="en_attente")  # en_attente, payee, annulee
    montant_ht = Column(Float, default=0.0)
    montant_ttc = Column(Float, default=0.0)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    devis = relationship("Devis", back_populates="facture")
    user = relationship("User", back_populates="factures")
    client = relationship("Client", back_populates="factures_client")


class Intervention(Base):
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(String, nullable=False)
    statut = Column(String, default="planifiee")  # planifiee, en_cours, terminee, annulee
    date_intervention = Column(DateTime, nullable=True)
    technicien = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="interventions")
    client = relationship("Client", back_populates="interventions")
