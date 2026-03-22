from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import init_db
from app.models.models import User, Product, StockItem, ExpiryDate, Location  # noqa: F401
from app.routes.stock import router as stock_router
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.locations import router as locations_router


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

app.include_router(auth_router,      prefix="/api/v1", tags=["auth"])
app.include_router(stock_router,     prefix="/api/v1", tags=["stock"])
app.include_router(users_router,     prefix="/api/v1", tags=["users"])
app.include_router(locations_router, prefix="/api/v1", tags=["locations"])


@app.get("/health")
async def health():
    return {"status": "ok"}
