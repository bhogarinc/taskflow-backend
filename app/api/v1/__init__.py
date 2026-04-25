"""API v1 routes."""
from fastapi import APIRouter

from app.api.v1 import auth, users, tasks, boards, teams

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(boards.router, prefix="/boards", tags=["Boards"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])