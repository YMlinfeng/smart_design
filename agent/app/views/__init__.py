from fastapi import APIRouter

from app.views.view import router

api_router = APIRouter()

# 聚合路由
api_router.include_router(router, prefix="", tags=["process"])