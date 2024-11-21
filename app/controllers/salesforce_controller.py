from fastapi import APIRouter, Depends
from logging_module import logger
from utils.dependencies import get_current_user_id
from services import salesforce_service
from fastapi.responses import JSONResponse
from typing import Optional

router = APIRouter()




@router.get("/get-salesforce-data")
async def get_salesforce_data(query: str, user_id: str = Depends(get_current_user_id)):
    """Get data from Salesforce."""
    logger.info("Get Salesforce Data entry point")
    response = await salesforce_service.get_salesforce_data(query)
    logger.info("Get Salesforce Data exit point")
    return JSONResponse(content=response, status_code=response["status_code"])