from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import algs, auth, health
from app.core.settings import Settings, settings


# FastAPI application. The schema is migrated before startup (the one-shot
# `migrate` job runs `alembic upgrade head`), not by the app.
def create_app(s: Settings) -> FastAPI:
    app = FastAPI(title="CubeTutor API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(algs.router)
    return app


app = create_app(settings)
