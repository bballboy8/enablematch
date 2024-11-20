from fastapi import APIRouter, Request, Depends
import services
from logging_module import logger
from fastapi.security import OAuth2PasswordRequestForm
from utils.dependencies import get_current_user_id
from services import gong_service
from fastapi.responses import JSONResponse
from typing import Optional

router = APIRouter()


@router.get("/get-gong-users")
async def get_gong_users(user_id: str = Depends(get_current_user_id)):
    """Get users from Gong."""
    logger.info("Get Gong Users entry point")
    response = await gong_service.get_gong_users()
    logger.info("Get Gong Users exit point")
    return JSONResponse(content=response, status_code=response["status_code"])


@router.get("/get-calls-by-date-range")
async def get_calls_by_date_range(
    start_date: str,
    end_date: Optional[str] = "",
    user_id: str = Depends(get_current_user_id),
):
    """Get calls by date range from Gong."""
    logger.info("Get Calls by Date Range entry point")
    response = await gong_service.get_calls_by_date_range(start_date, end_date)
    logger.info("Get Calls by Date Range exit point")
    return JSONResponse(content=response, status_code=response["status_code"])


@router.get("/get-call-transcript-by-call-id")
async def get_call_transcript_by_call_id(
    call_id: str, user_id: str = Depends(get_current_user_id)
):
    """Get call transcript by call id from Gong."""
    logger.info("Get Call Transcript by Call ID entry point")
    response = await gong_service.get_call_transcript_by_call_id(call_id)
    logger.info("Get Call Transcript by Call ID exit point")
    return JSONResponse(content=response, status_code=response["status_code"])