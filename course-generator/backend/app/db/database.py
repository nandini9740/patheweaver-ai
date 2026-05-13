from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Uses SQLite for MVP local development, easily switch to PostgreSQL via .env DATABASE_URL
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# app/db/database.py -> BASE_DIR is app/db
# courses.db should be in the backend root
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "..", "..", "courses.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
