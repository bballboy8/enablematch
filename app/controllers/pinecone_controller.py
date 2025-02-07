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


@router.post("/create-pinecone-index")
async def create_pinecone_index(index_name: str, user_id: str = Depends(get_current_user_id)):
    logger.debug("Inside create pinecone index controller")
    response = await services.create_pinecone_index_service(index_name)
    logger.debug("Response from create pinecone index service")
    return response

@router.delete("/delete-pinecone-index")
async def delete_pinecone_index(index_name: str, user_id: str = Depends(get_current_user_id)):
    logger.debug("Inside delete pinecone index controller")
    response = await services.delete_index_service(index_name)
    logger.debug("Response from delete pinecone index service")
    return response

@router.get("/query-pinecone-index")
async def query_pinecone_index(query: str, user_id: str = Depends(get_current_user_id)):
    logger.debug("Inside query pinecone index controller")
    response = await services.query_pinecone_index_service(query)
    logger.debug("Response from query pinecone index service")
    return response