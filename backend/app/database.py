from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Create a new database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
