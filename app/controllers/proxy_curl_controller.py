from fastapi import APIRouter
import services 
from logging_module import logger
from utils.dependencies import get_current_user_id
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get('/get_linkedin_person')
async def get_linkedin_person(url: str):
    logger.debug("Inside get linkedin person controller")
    response = await services.get_linkedin_person(url)
    logger.debug("Response from get linkedin person service")
    return JSONResponse(content=response["data"], status_code=response["status_code"])