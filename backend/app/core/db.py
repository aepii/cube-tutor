from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
from app import models
from app.core.settings import settings

load_dotenv()


engine = create_engine(settings.DATABASE_URL, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
