"""V1 API router aggregation."""

from fastapi import APIRouter

from app.api.v1.repositories import router as repositories_router

api_v1_router = APIRouter()
api_v1_router.include_router(repositories_router)
