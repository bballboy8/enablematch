from fastapi import APIRouter, Request, Depends
import services
from logging_module import logger
from fastapi.security import OAuth2PasswordRequestForm
from utils.dependencies import get_current_user_id
from services import gong_service
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/get-gong-users")
async def get_gong_users(user_id: str = Depends(get_current_user_id)):
    """Get users from Gong."""
    logger.info("Get Gong Users entry point")
    response = await gong_service.get_gong_users()
    logger.info("Get Gong Users exit point")
    return JSONResponse(content=response, status_code=response["status_code"])
