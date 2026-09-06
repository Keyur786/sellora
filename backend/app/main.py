from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.api.v1.api import api_router
from app.services.seed_data import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if not present (convenient for local dev & testing)
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed demo store data if in development mode
    if settings.ENVIRONMENT == "development":
        db = SessionLocal()
        try:
            seed_demo_data(db)
        finally:
            db.close()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title=f"{settings.PROJECT_NAME} API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API. Real profitability for Indian online sellers.",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
