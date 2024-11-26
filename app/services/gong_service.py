from utils.thirdparty import gong_api_service
from logging_module import logger
from models.gong import CallDetailModel
from config.db_connection import db
from config import constants

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

async def gong_data_loader():
    """Load data from Gong."""
    try:
        gong_data = await gong_api_service.get_gong_extensive_call_data()
        cursor = ""
        if gong_data["status_code"] == 200:
            cursor = gong_data["response"]["records"]["cursor"]
            await save_gong_record_in_db(gong_data["response"]["calls"])

        while True:
            gong_data = await gong_api_service.get_gong_extensive_call_data(cursor)
            await save_gong_record_in_db(gong_data["response"]["calls"])
            if "cursor" not in gong_data["response"]["records"]:
                break
            cursor = gong_data["response"]["records"]["cursor"]

        return {"response": "Loaded", "status_code": 200}
    except Exception as e:
        logger.error(f"Error while loading data from Gong: {e}")
        return {
            "response": f"An error occurred while loading data from Gong.{e}",
            "status_code": 500,
        }
    
async def save_gong_record_in_db(records):
    """Save Gong records in database."""
    try:
        call_details_collection = db[constants.CALL_DETAILS_COLLECTION]
        all_records = [CallDetailModel(**record["metaData"]) for record in records]
        call_details_collection.insert_many([record.model_dump() for record in all_records])
        return {"response": "Records saved successfully", "status_code": 200}
    except Exception as e:
        logger.error(f"Error while saving records in database: {e}")
        return {
            "response": f"An error occurred while saving records in database.{e}",
            "status_code": 500,
        }