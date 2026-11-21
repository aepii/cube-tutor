from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import algs, auth, images

# FastAPI application. The schema is migrated before startup (`alembic upgrade
# head` in the container command), not by the app.
app = FastAPI(title="CubeTutor API")

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
