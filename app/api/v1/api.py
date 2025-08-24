from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, transactions, webhooks, analytics

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])