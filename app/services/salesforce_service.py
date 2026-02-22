from utils.thirdparty.salesforce_api_service import SalesforceApiService
from logging_module import logger
from config.db_connection import db
from config import constants
from bson import ObjectId
from datetime import datetime, timezone
from pymongo import UpdateOne, InsertOne
from utils import helper_functions
from utils.thirdparty import gong_api_service
import services

users_gong_transcript_collection = db[constants.USERS_GONG_TRANSCRIPT_COLLECTION]
salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]
scraped_linkedin_profiles_collection = db[constants.SCRAPED_LINKEDIN_PROFILES_COLLECTION]
salesforce_instance = SalesforceApiService()

async def get_salesforce_data(query):
    """Get data from Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        data = salesforce_instance.get_salesforce_data(query)
        if data:
            return {"response": data, "status_code": 200}
        else:
            return {
                "response": f"An error occurred while fetching data from Salesforce.{data}",
                "status_code": 500,
            }

    except Exception as e:
        logger.error(f"Error while fetching Salesforce data: {e}")
        return {
            "response": f"An error occurred while fetching the Salesforce data.{e}",
            "status_code": 500,
        }

async def create_salesforce_contact(full_name,email):
    """Create a contact in Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        data = salesforce_instance.create_salesforce_contact(full_name,email)
        if data:
            return {"response": data, "status_code": 200}
        else:
            return {
                "response": f"An error occurred while creating a contact in Salesforce.{full_name} {email}",
                "status_code": 500,
            }

    except Exception as e:
        logger.error(f"Error while creating Salesforce contact: {e}")
        return {
            "response": f"An error occurred while creating the Salesforce contact.{e}",
            "status_code": 500,
        }

async def get_salesforce_contacts():
    """Get contacts from Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        contacts = salesforce_instance.get_salesforce_contacts()
        return {"response": contacts, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching Salesforce contacts: {e}")
        return {
            "response": f"An error occurred while fetching the Salesforce contacts: {e}",
            "status_code": 500,
        }

async def get_salesforce_contacts():
    """Get contacts from Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        contacts = salesforce_instance.get_salesforce_contacts()
        return {"response": contacts, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching Salesforce contacts: {e}")
        return {
            "response": f"An error occurred while fetching the Salesforce contacts: {e}",
            "status_code": 500,
        }


async def upload_resume_to_a_user(record_id, file):
    """Upload a file to Salesforce and link it to a record."""
    try:
        salesforce_instance = SalesforceApiService()

        file_contents = await file.read()
        file_name = file.filename

        content_document_id = salesforce_instance.upload_file_to_salesforce(
            file_name=file_name, file_content=file_contents, linked_entity_id=record_id
        )
        return {
            "message": "File uploaded successfully",
            "content_document_id": content_document_id,
        }
    except Exception as e:
        logger.error(f"Error while uploading file to Salesforce: {e}")
        return {
            "message": f"An error occurred while uploading the file to Salesforce: {e}"
        }

async def get_linked_files_from_salesforce(linked_entity_id):
    """Get files linked to a specific record in Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        files = salesforce_instance.get_linked_files(linked_entity_id)
        return {"response": files, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching linked files from Salesforce: {e}")
        return {
            "response": f"An error occurred while fetching linked files from Salesforce: {e}",
            "status_code": 500,
        }

async def download_file_from_salesforce(content_document_id):
    """Download a file from Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        file_content = salesforce_instance.download_file_from_salesforce(content_document_id)
        if file_content:
            with open("downloaded_file.pdf", "wb") as file:
                file.write(file_content["file_content"])

        return {"response": "Downloaded", "status_code": 200}
    except Exception as e:
        logger.error(f"Error while downloading file from Salesforce: {e}")
        return {
            "response": f"An error occurred while downloading the file from Salesforce: {e}",
            "status_code": 500,
        }

async def get_salesforce_user_first_document(salesforce_user_id):
    """Get the first document linked to a user in Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        document = salesforce_instance.get_salesforce_user_first_document(salesforce_user_id)
        if document["status_code"] == 500:
            return document
        return {"response": document, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching the first document linked to the user: {e}")
        return {
            "response": f"An error occurred while fetching the first document linked to the user: {e}",
            "status_code": 500,
        }

async def attach_note_to_salesforce_user(note_title, note_body, linked_entity_id):
    """Attach a note to a resume in Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        response = salesforce_instance.attach_note_to_salesforce_user(note_title, note_body, linked_entity_id)
        return {"response": response, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while attaching a note to the resume: {e}")
        return {
            "response": f"An error occurred while attaching a note to the resume: {e}",
            "status_code": 500,
        }


async def get_salesforce_user_notes(linked_entity_id):
    """Get notes attached to a specific record in Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        notes = salesforce_instance.get_salesforce_user_notes(linked_entity_id)
        if notes["status_code"] == 500:
            return notes
        return {"response": notes["notes"], "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching notes from Salesforce: {e}")
        return {
            "response": f"An error occurred while fetching notes from Salesforce: {e}",
            "status_code": 500,
        }

async def get_salesforce_users():
    """Get users from Salesforce and insert only new users."""
    try:
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]
        salesforce_instance = SalesforceApiService()
        
        users = salesforce_instance.get_salesforce_users()
        users = users['users']

        print(users[0])

        # # Extract Salesforce user IDs from the fetched users
        # fetched_user_ids = {user['Id'] for user in users}

        # print(len(users), "Fetched users")

        
        # # Find existing user IDs in the database
        # existing_users = await salesforce_users_collection.find(
        #     {"Id": {"$in": list(fetched_user_ids)}},
        #     {"Id": 1}
        # ).to_list(length=None)
        # existing_user_ids = {user['Id'] for user in existing_users}
        
        # # Filter out users that already exist in the database
        # new_users = [
        #     user
        #     for user in users if user['Id'] not in existing_user_ids
        # ]
        
        # # Insert only new users
        # if new_users:
        #     await salesforce_users_collection.insert_many(new_users)
        
        return {"response": "Synced succesfully", "status_code": 200}
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error while fetching Salesforce users: {e}")
        return {
            "response": f"An error occurred while fetching the Salesforce users: {e}",
            "status_code": 500,
        }
    


async def assign_current_ote_from_salesforce_to_db_salesforce_user():
    """Assign current OTE from Salesforce to DB Salesforce user."""
    try:
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]
        salesforce_instance = SalesforceApiService()
        
        users = salesforce_instance.get_salesforce_users()
        users = users['users']

        for user in users:
            try:
                await salesforce_users_collection.update_one(
                    {"Id": user["Id"]},
                    {"$set": {"Current_OTE__c": user["Current_OTE__c"]}}
                )
                logger.info(f"Updated current OTE for {user['Id']}")
            except Exception as e:
                logger.error(f"Error while updating current OTE for {user['Id']}: {e}")
                continue

        return {"response": "Current OTE updated successfully", "status_code": 200}
    except Exception as e:
        logger.error(f"Error while assigning current OTE from Salesforce to DB: {e}")
        return {
            "response": f"An error occurred while assigning current OTE from Salesforce to DB: {e}",
            "status_code": 500,
        }
    


async def fetch_gong_record_by_email(email:str):
    """Fetch Gong record by email."""
    try:
        salesforce_instance = SalesforceApiService()
        gong_record = salesforce_instance.fetch_gong_records_by_salesforce_user_email(email)
        return {"response": gong_record, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching Gong record by email: {e}")
        return {
            "response": f"An error occurred while fetching Gong record by email: {e}",
            "status_code": 500,
        }


async def get_each_table_count():
    """Get count of each table."""
    try:
        salesforce_instance = SalesforceApiService()
        count = salesforce_instance.get_each_table_count()
        return {"response": count, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching count of each table: {e}")
        return {
            "response": f"An error occurred while fetching count of each table: {e}",
            "status_code": 500,
        }


async def assign_gong_conversaation_ids_to_the_candidates():
    """Assign Gong conversation IDs to the candidates."""
    try:
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]

        # Fetch all Salesforce users
        salesforce_users = await salesforce_users_collection.find().to_list(length=None)
        print(len(salesforce_users), "users to be processed")
        gong_record = salesforce_instance.fetch_gong_records_by_salesforce_user_email("")

        if gong_record["status_code"] != 200:
            logger.error(f"Error while fetching Gong record by email: {gong_record['response']}")
            return gong_record
        gong_record = gong_record["gong_records"]

        for i, user in enumerate(salesforce_users):
            try:
                logger.info(f"Processing user {i+1} of {len(salesforce_users)} with email {user['PersonEmail']}")
                gong_ids, gong_participants_emails = [], []
                for record in gong_record:
                    if record.get("Gong__Primary_Account__c") and user['Id'] == record.get("Gong__Primary_Account__c",""):
                        gong_ids.append(record.get("Gong__Call_ID__c"))
                        gong_participants_emails.append(record.get("Gong__Participants_Emails__c"))

                if gong_ids:
                    await salesforce_users_collection.update_one(
                        {"Id": user["Id"]},
                        {"$set": {"gong_call_ids": gong_ids, "gong_participants_emails": gong_participants_emails}}
                    )
                    logger.info(f"Gong conversation IDs assigned to the candidate with email {user['PersonEmail']}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.error(f"Error while assigning Gong conversation IDs to the candidates: {e}")
                continue

        response = "Gong conversation IDs assigned to the candidates."

        return {"response": response, "status_code": 200}
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error while assigning Gong conversation IDs to the candidates: {e}")
        return {
            "response": f"An error occurred while assigning Gong conversation IDs to the candidates: {e}",
            "status_code": 500,
        }   


async def run_raw_saleforce_query_for_test():
    """Run raw Salesforce query for testing."""
    try:
        salesforce_instance = SalesforceApiService()
        response = salesforce_instance.run_raw_saleforce_query_for_test()
        return {"response": response, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while running raw Salesforce query for testing: {e}")
        return {
            "response": f"An error occurred while running raw Salesforce query for testing: {e}",
            "status_code": 500,
        }

import requests
import aiohttp
import asyncio

async def fetch_linkedin_url(session, user):
    try:
        url = user.get("LinkedIn_Profile__c")
        if not url:
            return False

        if "linkedin" in url:
            await salesforce_users_collection.update_one(
                {"Id": user["Id"]},
                {"$set": {"linkedin_url": url}}
            )
            logger.info(
                f"Stored direct LinkedIn URL for {user.get('PersonEmail')}"
            )
            return True

        async with session.get(url, allow_redirects=True, timeout=10) as response:
            linkedin_url = str(response.url)
            if "linkedin" not in linkedin_url:
                logger.warning(
                    f"Resolved URL is not LinkedIn: {linkedin_url}"
                )
                return False
            await salesforce_users_collection.update_one(
                {"Id": user["Id"]},
                {"$set": {"linkedin_url": linkedin_url}}
            )
            logger.info(
                f"Resolved & stored LinkedIn URL for {user.get('PersonEmail')}"
            )
            return True

    except Exception:
        logger.exception(f"Failed for user {user.get('Id')}")
        return False


async def sync_linkedin_urls():
    """Sync LinkedIn URLs for users with tinyurl links."""
    try:
        salesforce_users_collection = db["salesforce_users"]
        salesforce_users = await salesforce_users_collection.find(
            {
                "linkedin_url": {"$exists": False},
            }
        ).to_list(length=None)
        logger.info(f"Processing {len(salesforce_users)} users")

        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_linkedin_url(session, user)
                for user in salesforce_users
            ]
            await asyncio.gather(*tasks)

        return {"response": "LinkedIn URLs synced.", "status_code": 200}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"response": f"Error: {e}", "status_code": 500}


async def convert_tinyurl_to_linkedin():
    """Convert tinyurl to LinkedIn using async requests."""
    try:
        salesforce_users_collection = db["salesforce_users"]
        salesforce_users = await salesforce_users_collection.find(
            {
                "linkedin_url": {"$exists": False},
                "gong_call_ids": {"$exists": True},
                "LinkedIn_Profile__c": {"$regex": "rb.gy", "$options": "i"},
            }
        ).to_list(length=None)
        logger.info(f"Processing {len(salesforce_users)} users")

        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_linkedin_url(session, user, salesforce_users_collection)
                for user in salesforce_users
            ]
            await asyncio.gather(*tasks)

        return {"response": "Tinyurl converted to LinkedIn.", "status_code": 200}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"response": f"Error: {e}", "status_code": 500}
    

async def add_current_ote_in_candidate_blob():
    """Add current OTE in candidate blob."""
    try:
        candidates_blob_collection = db[constants.CANDIDATES_BLOB_COLLECTION]
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]

        candidates_blobs = await candidates_blob_collection.find().to_list(length=None)

        print(len(candidates_blobs), "candidates blobs to be processed")

        for candidate_blob in candidates_blobs:
            salesforce_user = await salesforce_users_collection.find_one(
                {"_id": ObjectId(candidate_blob["user_id"])}
            )
            if salesforce_user:
                current_ote = salesforce_user.get("Current_OTE__c")
                await candidates_blob_collection.update_one(
                    {"_id": candidate_blob["_id"]},
                    {"$set": {"current_ote": current_ote}}
                )
                logger.info(f"Updated current OTE for candidate blob {candidate_blob['_id']}")

        return {"response": "Current OTE updated successfully", "status_code": 200}
    except Exception as e:
        logger.error(f"Error while adding current OTE in candidate blob: {e}")
        return {
            "response": f"An error occurred while adding current OTE in candidate blob: {e}",
            "status_code": 500,
        }    

async def sync_gong_ids_for_salesforce_users(salesforce_user_ids):
    """
    Sync Gong call transcripts for Salesforce users.
    """
    try:
        logger.info(f"Starting Gong sync for {len(salesforce_user_ids)} users")
        # Step 1: Fetch all Gong records
        gong_response = salesforce_instance.fetch_gong_records_by_salesforce_user_email("")
        if gong_response.get("status_code") != 200:
            logger.error(f"Failed to fetch Gong records: {gong_response.get('response')}")
            return gong_response

        gong_records = gong_response.get("gong_records", [])
        if not gong_records:
            logger.info("No Gong records fetched.")
            return {"status_code": 200, "response": "No Gong records to process."}

        # Step 2: Fetch Salesforce users
        salesforce_users = await salesforce_users_collection.find(
            {"Id": {"$in": salesforce_user_ids}}
        ).to_list(length=None)

        # Step 3: Group Gong records by Salesforce user
        gong_records_by_user = {}
        for record in gong_records:
            user_id = record.get("Gong__Primary_Account__c")
            call_id = record.get("Gong__Call_ID__c")
            if user_id and call_id:
                gong_records_by_user.setdefault(user_id, []).append(record)

        # Step 4: Process each user
        for idx, user in enumerate(salesforce_users):
            user_id = user["Id"]
            email = user.get("PersonEmail")
            logger.info(f"[{idx + 1}/{len(salesforce_users)}] Processing {email}")

            try:
                user_gong_records = gong_records_by_user.get(user_id, [])
                if not user_gong_records:
                    continue

                incoming_call_ids = {r["Gong__Call_ID__c"] for r in user_gong_records}
                existing_call_ids = set(user.get("gong_call_ids", []))
                new_call_ids = incoming_call_ids - existing_call_ids
                if not new_call_ids:
                    logger.info(f"No new Gong calls for {email}")
                    continue

                successful_call_ids = set()
                failed_call_ids = set()
                inserted_transcript_ids = []

                # Step 4a: Fetch and process transcripts
                for call_id in new_call_ids:
                    # Skip if transcript already exists
                    exists = await users_gong_transcript_collection.find_one(
                        {"user_id": user_id, "call_id": call_id}, {"_id": 1}
                    )
                    if exists:
                        logger.info(f"Transcript already exists for call_id={call_id}")
                        successful_call_ids.add(call_id)
                        continue

                    # Fetch transcript
                    transcript_response = await gong_api_service.get_call_transcript_by_call_id([call_id])
                    if transcript_response.get("status_code") != 200:
                        logger.error(f"Failed to fetch transcript for call_id={call_id}")
                        failed_call_ids.add(call_id)
                        continue

                    transcript = transcript_response["response"]["callTranscripts"][0]
                    parsed = helper_functions.parse_transcript(transcript)
                    if parsed.get("status_code") == 500:
                        logger.error(f"Failed to parse transcript for call_id={call_id}")
                        failed_call_ids.add(call_id)
                        continue

                    # Insert transcript
                    result = await users_gong_transcript_collection.insert_one({
                        "user_id": user_id,
                        "call_id": call_id,
                        "transcript": parsed["transcript"],
                        "created_at": datetime.now(timezone.utc),
                    })
                    inserted_transcript_ids.append(str(result.inserted_id))
                    successful_call_ids.add(call_id)

                # Step 4b: Update Salesforce user document
                participants_emails = list({
                    r.get("Gong__Participants_Emails__c")
                    for r in user_gong_records if r.get("Gong__Participants_Emails__c")
                })

                update_doc = {
                    "$addToSet": {
                        "gong_call_ids": {"$each": list(successful_call_ids)},
                        "gong_transcript_ids": {"$each": inserted_transcript_ids},
                        "gong_participants_emails": {"$each": participants_emails},
                    },
                    "$set": {"gong_ids_update_required": False},
                }
                await salesforce_users_collection.update_one({"Id": user_id}, update_doc)
                logger.info(f"User {email}: {len(successful_call_ids)} calls synced, {len(failed_call_ids)} failed.")

            except Exception as user_err:
                logger.exception(f"Error processing user {email}: {user_err}")
                continue

        return {"status_code": 200, "response": "Gong conversation IDs synced successfully"}

    except Exception as e:
        logger.exception(f"Critical error in Gong sync: {e}")
        return {"status_code": 500, "response": str(e)}

async def fetch_and_assign_linkedin_data_to_users(
        session, user
):
    try:
        response = await fetch_linkedin_url(session, user)
        if response:
            response = await services.proxy_curl_service.get_linkedin_person(user["LinkedIn_Profile__c"], str(user["_id"]))
            if response["status_code"] == 200:
                await salesforce_users_collection.update_one(
                    {"_id": ObjectId(user["_id"])},
                    {"$set": {"linkedin_update_required": False}}
                )
            logger.info(f"Fetched and assigned LinkedIn data for {user.get('PersonEmail')}")
    except Exception as e:
        logger.error(f"Error processing {user['PersonEmail']}: {e}")

    
async def sync_linkedin_profiles_for_salesforce_users(salesforce_user_ids):
    try:
        logger.info(f"Syncing LinkedIn profiles for {len(salesforce_user_ids)} Salesforce users")
        salesforce_users = await salesforce_users_collection.find(
            {"Id": {"$in": salesforce_user_ids}}
        ).to_list(length=None)


        for user in salesforce_users:
            linkedin_url = user.get("linkedin_url")
            try:
                if linkedin_url:
                    scraped_profile = await scraped_linkedin_profiles_collection.find_one({"linkedinUrl": {"$regex": linkedin_url, "$options": "i"}}, {"_id": 1})
                    if scraped_profile:
                        logger.info(f"Found scraped LinkedIn profile for {user.get('PersonEmail')}, updating user document")
                        await salesforce_users_collection.update_one(
                            {"Id": user["Id"]},
                            {"$set": {
                                "linkedin_update_required": False,
                                "linkedin_profile": str(scraped_profile.get("_id"))
                            }}
                        )
                        logger.info(f"LinkedIn profile data updated from cache for {user.get('PersonEmail')}")
                    else:
                        logger.info(f"No cached profile found for {user.get('PersonEmail')}")
            except Exception as e:
                continue

        logger.info("Sync Completed")
        return {"response": "LinkedIn profiles synced successfully.", "status_code": 200}
    except Exception as e:
        print(e)
        return {
            "response": f"An error occurred while syncing LinkedIn profiles for Salesforce users: {e}",
            "status_code": 500,
        }

async def sync_salesforce_users():
    try:
        sf = SalesforceApiService()
        users = sf.get_salesforce_users()["users"]
        existing_users = await salesforce_users_collection.find(
            {},
            {"Id": 1, "Name": 1, "LinkedIn_Profile__c": 1, "PersonEmail": 1,
             "Summary_of_Candidate__c": 1, "Current_OTE__c": 1, "Gong__Gong_Count__c": 1, "Consulting_Status__c": 1, "Status__c": 1}
        ).to_list(length=None)

        existing_map = {u["Id"]: u for u in existing_users}


        ids_to_delete = [user["Id"] for user in users if user.get("IsDeleted")]

        if ids_to_delete:
            await salesforce_users_collection.update_many(
                {"Id": {"$in": list(ids_to_delete)}, "is_deleted": {"$ne": True}},
                {
                    "$set": {
                        "is_deleted": True,
                        "deleted_at": now,
                        "updated_at": now
                    }
                }
            )
            logger.info(f"Soft-deleted {len(ids_to_delete)} users not found in Salesforce")

        # skip the deleted users in the next steps
        users = [user for user in users if not user.get("IsDeleted")]

        ops = []
        now = datetime.now(timezone.utc)

        fields = [
            "Name",
            "LinkedIn_Profile__c",
            "PersonEmail",
            "Summary_of_Candidate__c",
            "Current_OTE__c",
            "Gong__Gong_Count__c",
            "Consulting_Status__c",
            "Status__c"
        ]

        for user in users:
            user_id = user["Id"]

            if user_id in existing_map:
                updates = {
                    f: user.get(f)
                    for f in fields
                    if user.get(f) != existing_map[user_id].get(f)
                }

                if updates:
                    if "LinkedIn_Profile__c" in updates:
                        updates["linkedin_update_required"] = True
                    if "Gong__Gong_Count__c" in updates:
                        updates["gong_ids_update_required"] = True
                    updates["updated_at"] = now
                    ops.append(
                        UpdateOne(
                            {"Id": user_id},
                            {"$set": updates}
                        )
                    )
            else:
                print("Inserting new user", user_id)
                user["linkedin_update_required"] = True
                user["gong_ids_update_required"] = True
                user["created_at"] = now
                user["updated_at"] = now
                ops.append(InsertOne(user))

        if ops:
            result = await salesforce_users_collection.bulk_write(ops)
            logger.info(
                f"Salesforce sync completed | "
                f"Inserted: {result.inserted_count}, "
                f"Modified: {result.modified_count}"
            )

        # pull the ids from database where gong_ids_update_required is True
        update_gong_ids_for_users = []
        async for user in salesforce_users_collection.find(
            {"gong_ids_update_required": True, "is_deleted": {"$ne": True}},
            {"Id": 1}
        ):
            update_gong_ids_for_users.append(user["Id"])

        # pull the ids from database where linkedin_update_required is True
        await sync_linkedin_urls()
        update_linkedin_for_users = []
        async for user in salesforce_users_collection.find(
            {"linkedin_update_required": True, "is_deleted": {"$ne": True}},
            {"Id": 1}
        ):
            update_linkedin_for_users.append(user["Id"])

        if update_gong_ids_for_users:
            response = await sync_gong_ids_for_salesforce_users(update_gong_ids_for_users)
            if response.get("status_code") != 200:
                logger.error("Error updating gong IDs for users")
            logger.info("Gong IDs sync completed")

        # AI Pipeline for conversating summary in gong transcripts collection
        conversation_summary_for_ids =  []
        async for user in users_gong_transcript_collection.find(
            {"conversation_summary": {"$exists": False}},
            {"_id": 1}):
            conversation_summary_for_ids.append(user["_id"])
        for transcript_id in conversation_summary_for_ids:
            await services.candidate_analysis_service.process_transcript_by_id(transcript_id)

        if update_linkedin_for_users:
            response = await sync_linkedin_profiles_for_salesforce_users(update_linkedin_for_users)
            if response.get("status_code") != 200:
                logger.error("Error updating LinkedIn profiles for users")
            logger.info("LinkedIn profiles sync completed")

    except Exception as e:
        logger.exception("Error syncing Salesforce users")
        return {"response": str(e), "status_code": 500}