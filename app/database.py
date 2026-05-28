from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

engine = None
SessionLocal = None

class Base(DeclarativeBase):
    pass

def init_db(database_url: str):
    global engine, SessionLocal
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(engine)   # swap for Alembic in prod

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()