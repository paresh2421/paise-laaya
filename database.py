from sqlmodel import SQLModel, create_engine
import os

# Paste your exact Neon URL here!
DATABASE_URL = "postgresql://neondb_owner:npg_EPDu9mrITeo5@ep-proud-silence-aoklkqh4.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# Notice we removed connect_args={"check_same_thread": False} because Postgres doesn't need it!
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)