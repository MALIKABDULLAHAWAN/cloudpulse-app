import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Default to SQLite for local dev; set DB_URL env var for PostgreSQL in production
DB_URL = os.getenv("DB_URL", "sqlite:///./cloudpulse.db")

_engine = None
_SessionLocal = None

def get_engine():
    global _engine
    if _engine is not None:
        return _engine
    connect_args = {"check_same_thread": False} if "sqlite" in DB_URL else {}
    retries = 10
    delay = 3
    while retries > 0:
        try:
            engine = create_engine(DB_URL, connect_args=connect_args, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"Database connected: {DB_URL}")
            _engine = engine
            return _engine
        except Exception as e:
            retries -= 1
            print(f"Database connection failed ({e}), retrying in {delay}s... ({retries} left)")
            time.sleep(delay)
    raise Exception("Database connection failed after multiple retries")

def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

def get_db():
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()
