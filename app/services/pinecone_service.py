from utils.thirdparty.pinecone_service import PineConeDBService
from logging_module import logger
from config.db_connection import db
from config import constants
from bson import ObjectId


async def get_pinecone_indexes_service():
    """
    Get the existing indexes in Pinecone asynchronously.

    Returns:
        dict: A dictionary containing the status code and the response.
        Keys:
            - status_code (int): HTTP-like status code (200 for success, 500 for error).
            - response (list): A list of existing indexes in Pinecone.
    """
    try:
        pinecone_client = PineConeDBService()
        response = await pinecone_client.get_existing_indexes()
        return response
    except Exception as e:
        logger.error(f"Failed to get Pinecone indexes: {e}")
        return {"status_code": 500, "response": str(e)}
    

async def create_pinecone_index_service(index_name: str):
    """
    Create a new Pinecone index asynchronously.

    Args:
        index_name (str): The name of the new index to be created.

    Returns:
        dict: A dictionary containing the status code and the response.
        Keys:
            - status_code (int): HTTP-like status code (200 for success, 500 for error).
            - response (str): A message indicating the status of the index creation.
    """
    try:
        pinecone_client = PineConeDBService()
        response = await pinecone_client.create_index(index_name)
        return response
    except Exception as e:
        logger.error(f"Failed to create Pinecone index: {e}")
        return {"status_code": 500, "response": str(e)}
    
async def delete_index_service(index_name: str):
    """
    Delete a Pinecone index asynchronously.

    Args:
        index_name (str): The name of the index to be deleted.

    Returns:
        dict: A dictionary containing the status code and the response.
        Keys:
            - status_code (int): HTTP-like status code (200 for success, 500 for error).
            - response (str): A message indicating the status of the index deletion.
    """
    try:
        pinecone_client = PineConeDBService()
        response = await pinecone_client.delete_index(index_name)
        return response
    except Exception as e:
        logger.error(f"Failed to delete Pinecone index: {e}")
        return {"status_code": 500, "response": str(e)}
    

async def query_pinecone_index_service(query:str):
    """
    Query a Pinecone index asynchronously.

    Args:
        index_name (str): The name of the index to query.
        query_vector (list): The query vector to search for similar records.
        top_k (int): The number of similar records to retrieve.

    Returns:
        dict: A dictionary containing the status code and the response.
        Keys:
            - status_code (int): HTTP-like status code (200 for success, 500 for error).
            - response (list): A list of similar records retrieved from the index.
    """
    try:
        targeted_candidates_collection = db[constants.TARGET_CANDIDATE_COLLECTION]
        pinecone_client = PineConeDBService()
        response = await pinecone_client.query_data(query, 3)
        if response["status_code"] != 200:
            return response
        records = [ record for record in response["response"]["matches"]]
        query_result = []
        for record in records:
            record_id = record["id"]
            query_result.append(await targeted_candidates_collection.find_one({"user_id": record_id}, {"_id": 0}))
        return {"status_code": 200, "response": query_result}
    except Exception as e:
        logger.error(f"Failed to query Pinecone index: {e}")
        return {"status_code": 500, "response": str(e)}