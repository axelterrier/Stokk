from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import init_db
from app.models.models import User, Product, StockItem, ExpiryDate  # noqa: F401 — needed for Base.metadata
from app.routes.stock import router as stock_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="FoodTracker API",
    version="0.1.0",
    description="Gestion de stock alimentaire pour foyer partagé",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stock_router, prefix="/api/v1", tags=["stock"])


@app.get("/health")
async def health():
    return {"status": "ok"}
