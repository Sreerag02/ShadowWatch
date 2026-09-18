from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import database_url

DATABASE_URL = database_url()

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# Added by Deepa

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()