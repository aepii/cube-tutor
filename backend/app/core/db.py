from contextlib import contextmanager

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401  (registers the tables on SQLModel.metadata)
from app.core.settings import settings

load_dotenv()

# Initializes the engine object which manages the connection pool
engine = create_engine(settings.DATABASE_URL, echo=True)


# Create all table defined in the models module
def init_db():
    SQLModel.metadata.create_all(engine)


# Returns database session
def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


# Session for use outside of FastAPI
db_context = contextmanager(get_session)
