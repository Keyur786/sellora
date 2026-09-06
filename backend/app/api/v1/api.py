from fastapi import APIRouter
from app.api.v1 import health, dashboard, products, orders, profit, marketplaces, imports, returns, expenses, tax, ai, organization

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(organization.router, prefix="/organization", tags=["Organization"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(profit.router, prefix="/profit", tags=["Profit Analytics"])
api_router.include_router(marketplaces.router, prefix="/marketplaces", tags=["Marketplaces"])
api_router.include_router(imports.router, prefix="/import", tags=["Data Import"])
api_router.include_router(returns.router, prefix="/returns", tags=["Returns & RTO"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["Operational Expenses"])
api_router.include_router(tax.router, prefix="/tax", tags=["GST & Tax Reconciliation"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Copilot & Intelligence"])

