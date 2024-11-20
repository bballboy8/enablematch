from utils.thirdparty import gong_api_service
from logging_module import logger


async def get_gong_users():
    """Get users from Gong."""
    try:
        users = gong_api_service.get_users()
        if users:
            return {"response": users, "status_code": 200}
        else:
            return {
                "response": "An error occurred while fetching users from Gong.",
                "status_code": 500,
            }

    except Exception as e:
        logger.error(f"Error while fetching gong users: {e}")
        return {
            "response": f"An error occurred while fetching the gong users.{e}",
            "status_code": 500,
        }
