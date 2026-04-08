from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from connect4.api.rate_limit import limiter
from connect4.api.sse import GameEventBroker
from connect4.config import get_settings
from connect4.db.connection import close_pool, create_pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.db_pool = await create_pool()
    broker = GameEventBroker()
    await broker.start(str(get_settings().database_url))
    app.state.event_broker = broker
    yield
    await broker.stop()
    await close_pool(app.state.db_pool)


app = FastAPI(title="Connect 4", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_settings().cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from connect4.api.auth import router as auth_router  # noqa: E402
from connect4.api.games import router as games_router  # noqa: E402

app.include_router(auth_router, prefix="/api")
app.include_router(games_router, prefix="/api")
