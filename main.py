from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.init import init_database


settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_database()
    yield


app = FastAPI(
    title="Autonomous Multi-Agent Research Lab",
    version="0.1.0",
    description="Hermes Agent and GBrain-ready autonomous AI research organization.",
    lifespan=lifespan,
)
app.include_router(router)
