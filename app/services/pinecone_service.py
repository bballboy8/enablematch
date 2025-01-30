from utils.thirdparty.pinecone_service import PineConeDBService
from logging_module import logger


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