from utils.thirdparty.proxy_curl_service import ProxyCurlApiService
from logging_module import logger
from config.db_connection import db
from config import constants


async def get_linkedin_person(url):
    try:
        user_profile_collection = db[constants.USERS_PROFILE_COLLECTION]

        if not url.endswith("/"):
            url = url + "/"

        person = await user_profile_collection.find_one({"search_url": url})
        if person:
            person["_id"] = str(person["_id"])
            return {"status_code": 200, "data": person}

        proxycurl_client = ProxyCurlApiService()
        response = await proxycurl_client.get_linkedin_person(url)
        if response["status_code"] != 200:
            return response
        person = response["data"]
        person["search_url"] = url
        await user_profile_collection.insert_one(person)
        person["_id"] = str(person["_id"])
        person.pop("_id")
        return {"status_code": 200, "data": person}
    except Exception as e:
        import traceback

        traceback.print_exc()
        logger.error(f"Error in get_linkedin_person: {e}")
        return {"status_code": 500, "data": f"Error in get_linkedin_person: {e}"}

async def get_key_value_concatenation(data):
    # List of expected keys
    keys = [
        "public_identifier", "profile_pic_url", "background_cover_image_url",
        "first_name", "last_name", "full_name", "follower_count", "occupation",
        "headline", "summary", "country", "country_full_name", "city", "state",
        "experiences", "education", "languages", "languages_and_proficiencies",
        "accomplishment_organisations", "accomplishment_publications",
        "accomplishment_honors_awards", "accomplishment_patents",
        "accomplishment_courses", "accomplishment_projects",
        "accomplishment_test_scores", "volunteer_work"
    ]
    
    # Collect "key: value" pairs for the keys that exist in the dictionary
    key_value_pairs = [f"{key}: {data[key]}" for key in keys if key in data and data[key]]
    
    # Join and return the concatenated string
    return "".join(key_value_pairs)
