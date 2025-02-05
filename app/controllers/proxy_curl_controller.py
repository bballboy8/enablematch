from fastapi import APIRouter
import services 
from logging_module import logger
from utils.dependencies import get_current_user_id
from fastapi.responses import JSONResponse
from fastapi.background import BackgroundTasks

router = APIRouter()


@router.get('/get_linkedin_person')
async def get_linkedin_person(url: str):
    logger.debug("Inside get linkedin person controller")
    response = await services.get_linkedin_person(url)
    logger.debug("Response from get linkedin person service")
    return JSONResponse(content=response["data"], status_code=response["status_code"])


@router.put("/fetch-and-assign-linkedin-data-to-users")
async def fetch_and_assign_linkedin_data_to_users(background_tasks: BackgroundTasks):
    logger.debug("Inside fetch and assign linkedin data to users controller")
    background_tasks.add_task(services.fetch_and_assign_linkedin_data_to_users)
    logger.debug("Response from fetch and assign linkedin data to users service")
    return JSONResponse(content={"message": "Task added to background tasks"}, status_code=200)