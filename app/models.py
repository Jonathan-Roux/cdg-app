from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


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
    created_at = Column(DateTime, default=func.now())

    devis = relationship("Devis", back_populates="client")


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


class LigneDevis(Base):
    __tablename__ = "lignes_devis"

    id = Column(Integer, primary_key=True, index=True)
    devis_id = Column(Integer, ForeignKey("devis.id"), nullable=False)
    designation = Column(String, nullable=False)
    quantite = Column(Float, default=1)
    prix_unitaire_ht = Column(Float, nullable=False)
    tva = Column(Float, default=20.0)

    devis = relationship("Devis", back_populates="lignes")