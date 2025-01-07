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
        return {"status_code": 200, "data": person}
    except Exception as e:
        import traceback

        traceback.print_exc()
        logger.error(f"Error in get_linkedin_person: {e}")
        return {"status_code": 500, "data": f"Error in get_linkedin_person: {e}"}
