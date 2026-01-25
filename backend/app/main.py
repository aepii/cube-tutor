from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.db import init_db
from app.api.routes import auth, algs


# Startup and shutdown logic of the application
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Tables created")
    yield
    print("App shutting down")


# FastAPI application
app = FastAPI(title="CubeTutor API", lifespan=lifespan)

# Add routers
app.include_router(auth.router)
app.include_router(algs.router)
