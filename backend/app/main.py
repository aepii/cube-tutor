import fastapi
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import algs, auth, health
from app.core.settings import Settings, settings
from app.core.telemetry import configure_telemetry


# FastAPI application. The schema is migrated before startup (the one-shot
# `migrate` job runs `alembic upgrade head`), not by the app.
def create_app(s: Settings) -> fastapi.FastAPI:
    # `fastapi.FastAPI`, looked up at call time: the telemetry instrumentation
    # replaces that attribute with a traced subclass (app/core/telemetry.py).
    app = fastapi.FastAPI(title="CubeTutor API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.CORS_ORIGINS,
        allow_origin_regex=s.CORS_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(algs.router)
    return app


# Telemetry is set up here, once per process, and never in create_app (tests
# build many apps). It must run before the app is built: the FastAPI
# instrumentation patches the FastAPI class.
configure_telemetry(settings)
app = create_app(settings)
