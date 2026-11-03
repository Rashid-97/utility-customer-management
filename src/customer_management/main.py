from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from customer_management.api.dependencies import dispose_engine
from customer_management.api.exception_handlers import register_exception_handlers
from customer_management.api.routers.subscriber_accounts import (
    router as subscriber_accounts_router,
)
from customer_management.api.routers.subscribers import router as subscribers_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    del app
    yield
    dispose_engine()


app = FastAPI(
    title="Utility Customer Management",
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(subscribers_router)
app.include_router(subscriber_accounts_router)

