"""Probes for Container Apps, the Compose healthcheck and the deploy smoke test.

Unversioned and unauthenticated. `live` says the process is serving requests;
`ready` says it can also reach the database.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from app.core.settings import settings

router = APIRouter(prefix="/health", tags=["health"])

# Separate from the app's pooled engine: NullPool opens a fresh connection per
# probe (so it really proves the DB is reachable, and never holds an app pool
# slot), and the connect timeout keeps a dead DB from hanging the probe.
_probe_engine = create_engine(
    settings.DATABASE_URL, poolclass=NullPool, connect_args={"connect_timeout": 2}
)


def get_probe_engine() -> Engine:
    return _probe_engine


@router.get("/live")
def live():
    return {"status": "ok"}


@router.get("/ready")
def ready(engine: Engine = Depends(get_probe_engine)):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ok"}
