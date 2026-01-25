from fastapi import APIRouter
from app.api import investments, emails, documents, trigger, status

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(investments.router, prefix="/investments", tags=["investments"])
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(trigger.router, prefix="/trigger", tags=["trigger"])
api_router.include_router(status.router, tags=["status"])
