from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.db import init_db
from app.api.routes import auth, algs, images


# Startup and shutdown logic of the application
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Tables created")
    yield
    print("App shutting down")


# FastAPI application
app = FastAPI(title="CubeTutor API", lifespan=lifespan)

# CORS
origins = [
    "http://localhost:8081",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add routers
app.include_router(auth.router)
app.include_router(algs.router)
app.include_router(images.router)
