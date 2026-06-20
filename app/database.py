from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL sur Railway, SQLite en local
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cdg.db")

# Railway fournit postgresql:// mais SQLAlchemy 2.x exige postgresql+psycopg2://
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_