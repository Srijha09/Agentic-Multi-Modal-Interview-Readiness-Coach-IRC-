from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


# -------------------------
# Declarative Base (ONE ONLY)
# -------------------------
class Base(DeclarativeBase):
    pass


# -------------------------
# Engine
# -------------------------
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
    )


# -------------------------
# Session
# -------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db():
    """
    Dependency for getting database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




