from fastapi import APIRouter, Depends
import services 
from logging_module import logger
from utils.dependencies import get_current_user_id

router = APIRouter()


@router.get("/get-pinecone-indexes")
async def get_pinecone_indexes(user_id: str = Depends(get_current_user_id)):
    logger.debug("Inside get pinecone indexes controller")
    response = await services.get_pinecone_indexes_service()
    logger.debug("Response from get pinecone indexes service")
    return response
