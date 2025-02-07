from utils.thirdparty.proxy_curl_service import ProxyCurlApiService
from logging_module import logger
from config.db_connection import db
from config import constants
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from bson import ObjectId 

RATE_LIMIT = 5  # Max 5 requests per second
MAX_WORKERS = 8  # Adjust based on system capability

async def get_linkedin_person(url, user_id=None):
    try:
        logger.debug(f"Inside get linkedin person service for url: {url}")
        await asyncio.sleep(0.2)
        user_linkedin_profile_collection = db[constants.USERS_LINKEDIN_PROFILE_COLLECTION]
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]

        if not url.endswith("/"):
            url = url + "/"

        person = await user_linkedin_profile_collection.find_one({"search_url": url})
        if person:
            person["_id"] = str(person["_id"])
            await salesforce_users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"linkedin_profile": str(person["_id"])}}
            )
            return {"status_code": 200, "data": person}

        proxycurl_client = ProxyCurlApiService()
        response = await proxycurl_client.get_linkedin_person(url)
        if response["status_code"] != 200:
            await salesforce_users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"linkedin_profile": 'NA'}}
            ) 
            return response
        person = response["data"]
        person["search_url"] = url
        await user_linkedin_profile_collection.insert_one(person)
        person["id"] = str(person["_id"])
        person.pop("_id")

        await salesforce_users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"linkedin_profile": str(person["id"])}}
        )

        return {"status_code": 200, "data": person}
    except Exception as e:
        logger.error(f"Error in get_linkedin_person: {e}")
        return {"status_code": 500, "data": f"Error in get_linkedin_person: {e}"}

async def get_key_value_concatenation(data):
    # List of expected keys
    keys = [
        "public_identifier",
        "first_name", "last_name", "full_name", "follower_count", "occupation",
        "headline", "summary", "country", "country_full_name", "city", "state",
        "experiences", "education", "languages", "languages_and_proficiencies",
        "accomplishment_organisations", "accomplishment_publications",
        "accomplishment_honors_awards", "accomplishment_patents",
        "accomplishment_courses", "accomplishment_projects",
        "accomplishment_test_scores", "volunteer_work", "recommendations", "skills",
    ]
    
    key_value_pairs = []
    
    for key in keys:
        if key in data and data[key]:
            if key in {"education", "experiences", "volunteer_work"} and isinstance(data[key], list):  
                # Remove keys that contain "url" (case-insensitive)
                filtered_entries = [
                    {k: v for k, v in entry.items() if "url" not in k.lower()}  
                    for entry in data[key]
                ]
                key_value_pairs.append(f"{key} - {filtered_entries}")
            else:
                key_value_pairs.append(f"{key} - {data[key]}")
    
    return " ".join(key_value_pairs)

import asyncio
async def fetch_and_assign_linkedin_data_to_users():
    try:
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]

        # Get all users from salesforce_users_collection
        users = await salesforce_users_collection.find(
            {"linkedin_url": {"$exists": True}, "linkedin_profile": {"$exists": False}, "gong_call_ids": {"$exists": True}}
        ).to_list(None)

        print("Processing users:", len(users))
        time.sleep(5)
        semaphore = asyncio.Semaphore(RATE_LIMIT)

        async def limited_fetch(user):
            async with semaphore:
                if "linkedin" not in user["linkedin_url"]:
                    await salesforce_users_collection.update_one(
                        {"linkedin_url": user["linkedin_url"]},
                        {"$set": {"linkedin_profile": 'NA'}}
                    )
                    return None
                return await get_linkedin_person(user["linkedin_url"], str(user["_id"]))

        tasks = [limited_fetch(user) for user in users]
        results = await asyncio.gather(*tasks)
        
        return {"status_code": 200, "data": results}
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error in fetch_and_assign_linkedin_data_to_users: {e}")
        return {"status_code": 500, "data": f"Error in fetch_and_assign_linkedin_data_to_users: {e}"}