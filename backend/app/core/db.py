from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
from contextlib import contextmanager
from app.core.settings import settings
from app import models

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
