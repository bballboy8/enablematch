from fastapi import APIRouter, Request, Depends, Query
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
    start_date: str = Query(..., example="2024-11-08T13:00:00%2B00:00", description="Start date format"),
    end_date: Optional[str] = Query(None, example="2024-11-08T13:00:00%2B00:00", description="End date format (optional)"),
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

@router.get("/get-gong-extensive-call-data")
async def get_gong_extensive_call_data(
):
    """Get extensive call data from Gong."""
    logger.info("Get Gong Extensive Call Data entry point")
    response = await gong_service.gong_data_loader()
    logger.info("Get Gong Extensive Call Data exit point")
    return JSONResponse(content=response, status_code=response["status_code"])

@router.get("/get-matching-calls")
async def get_matching_calls(
    search_query: str = Query(..., example="Enablematch", description="Search query"),
):
    """Get matching calls with title from Gong."""
    logger.info("Get Matching Calls title entry point")
    response = await gong_service.get_matching_records_with_title(search_query)
    logger.info("Get Matching Calls title exit point")
    return JSONResponse(content=response, status_code=response["status_code"])