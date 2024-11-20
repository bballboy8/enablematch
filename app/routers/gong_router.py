from fastapi import APIRouter
from controllers.gong_controller import router as gong_router

router = APIRouter()

router.include_router(gong_router, prefix="/gong", tags=["Gong"])
