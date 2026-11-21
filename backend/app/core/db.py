from contextlib import contextmanager

from sqlmodel import Session, create_engine

from app import models  # noqa: F401  (registers the tables on SQLModel.metadata)
from app.core.settings import settings

# Initializes the engine object which manages the connection pool
engine = create_engine(settings.DATABASE_URL, echo=settings.SQL_ECHO)

# Tables are created by Alembic (`alembic upgrade head`), never by the app.


# Returns database session
def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


# Session for use outside of FastAPI
db_context = contextmanager(get_session)
