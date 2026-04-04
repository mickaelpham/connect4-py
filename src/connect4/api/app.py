from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from connect4.db.connection import close_pool, create_pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.db_pool = await create_pool()
    yield
    await close_pool(app.state.db_pool)


app = FastAPI(title="Connect 4", lifespan=lifespan)

from connect4.api.auth import router as auth_router  # noqa: E402

app.include_router(auth_router)
