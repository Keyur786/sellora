from fastapi import APIRouter
from app.api.v1 import health, dashboard, products, orders, profit, marketplaces

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(profit.router, prefix="/profit", tags=["Profit Analytics"])
api_router.include_router(marketplaces.router, prefix="/marketplaces", tags=["Marketplaces"])
