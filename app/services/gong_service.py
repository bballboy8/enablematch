from utils.thirdparty import gong_api_service
from logging_module import logger
from models.gong import CallDetailModel
from config.db_connection import db
from config import constants
from utils import helper_functions
from bson import ObjectId

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
        all_records = []
        for record in records:
            if len(record.get("parties", [])) == 2:
                all_records.append(CallDetailModel(**record["metaData"], party_one=record.get("parties")[0], party_two=record.get("parties")[1]))
            else:
                if len(record.get("parties", [])) == 1:
                    all_records.append(CallDetailModel(**record["metaData"], party_one=record.get("parties")[0], party_two={}))
                else:
                    all_records.append(CallDetailModel(**record["metaData"], party_one={}, party_two={}))

        call_details_collection.insert_many([record.model_dump() for record in all_records])
        return {"response": "Records saved successfully", "status_code": 200}
    except Exception as e:
        logger.error(f"Error while saving records in database: {e}")
        return {
            "response": f"An error occurred while saving records in database.{e}",
            "status_code": 500,
        }

async def get_matching_records_with_title(title):
    """Get matching records with title from database."""
    try:
        call_details_collection = db[constants.CALL_DETAILS_COLLECTION]
        records = await call_details_collection.find({"title": {"$regex": title, "$options": "i"}}).to_list(length=None)
        return {"response": [{
                record["gong_id"] : record["title"]
            }
            for record in records], "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching records from database: {e}")
        return {
            "response": f"An error occurred while fetching records from database.{e}",
            "status_code": 500,
        }

import time
async def collect_caIl_transcripts():
    try:
        logger.info("Collecting Call Transcripts for Salesforce User")
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]
        users_gong_transcript_collection = db[
            constants.USERS_GONG_TRANSCRIPT_COLLECTION
        ]

        salesforce_users = await salesforce_users_collection.find(
            {'gong_call_ids': {'$exists':True}, 'linkedin_profile':{'$exists':True}}
        ).to_list(length=None)

        logger.info(f"Total Salesforce Users: {len(salesforce_users)}")

        total_count = 0
        for user in salesforce_users:
            if "NA" == user.get("linkedin_profile", ""):
                continue
            salesforce_user_id = user["Id"]
            call_ids = user.get("gong_call_ids", [])

            transcript = await gong_api_service.get_call_transcript_by_call_id(call_ids)
            if transcript.get("status_code") == 500:
                return transcript
            call_transcripts = transcript["response"]["callTranscripts"]
            logger.info(f"Total call transcripts: {len(call_transcripts)}")
            for i in range(len(call_transcripts)):
                transcript = call_transcripts[i]
                formatted_transcript_response = helper_functions.parse_transcript(
                    transcript
                )
                if formatted_transcript_response.get("status_code") == 500:
                    continue
                inserted = await users_gong_transcript_collection.insert_one(
                    {
                        "user_id": salesforce_user_id,
                        "call_id": transcript["callId"],
                        "transcript": formatted_transcript_response["transcript"],
                    }
                )
                inserted_id = str(inserted.inserted_id)
                logger.debug(f"Inserted transcript with id: {inserted_id}")
                await salesforce_users_collection.update_one(
                    {"Id": salesforce_user_id},
                    {"$push": {"gong_transcript_ids": inserted_id}},
                )
                total_count += 1
                time.sleep(1)
                logger.debug(f"Current count: {total_count}")
        logger.info(f"Total call transcripts inserted: {total_count}")
        logger.info("Call Transcripts collected successfully")
        return {"response": "Transcripts collected successfully", "status_code": 200}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "response": f"An error occurred while collecting call transcripts.{e}",
            "status_code": 500,
        }
