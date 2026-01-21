from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Tables created")
    yield
    print("App shutting down")


app = FastAPI(title="CubeTutor API", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "hello world!"}
