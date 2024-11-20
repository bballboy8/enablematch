from utils.thirdparty import gong_api_service
from logging_module import logger


async def get_gong_users():
    """Get users from Gong."""
    try:
        users = await gong_api_service.get_users()
        if users:
            return {"response": users, "status_code": 200}
        else:
            return {
                "response": f"An error occurred while fetching users from Gong.{users}",
                "status_code": 500,
            }

    except Exception as e:
        logger.error(f"Error while fetching gong users: {e}")
        return {
            "response": f"An error occurred while fetching the gong users.{e}",
            "status_code": 500,
        }


async def get_calls_by_date_range(start_date, end_date):
    """Get calls by date range from Gong."""
    try:
        calls = await gong_api_service.get_calls_by_date_range(
            start_date=start_date, end_date=end_date
        )
        if calls:
            return {"response": calls, "status_code": 200}
        else:
            return {
                "response": f"An error occurred while fetching calls from Gong.{calls}",
                "status_code": 500,
            }

    except Exception as e:
        logger.error(f"Error while fetching gong calls: {e}")
        return {
            "response": f"An error occurred while fetching the gong calls.{e}",
            "status_code": 500,
        }


async def get_call_transcript_by_call_id(call_id):
    """Get call transcript by call id from Gong."""
    try:
        transcript = await gong_api_service.get_call_transcript_by_call_id(call_id)
        if transcript:
            return {"response": transcript, "status_code": 200}
        else:
            return {
                "response": f"An error occurred while fetching transcript from Gong.{transcript}",
                "status_code": 500,
            }
    except Exception as e:
        logger.error(f"Error while fetching gong transcript: {e}")
        return {
            "response": f"An error occurred while fetching the gong transcript.{e}",
            "status_code": 500,
        }
