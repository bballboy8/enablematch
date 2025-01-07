from config import constants
from logging_module import logger
import requests
from proxycurl.asyncio import Proxycurl
import asyncio


api_key = constants.PROXY_CURL_API_KEY


class ProxyCurlApiService:
    def __init__(self):
        self.proxycurl_client = Proxycurl(api_key)

    async def get_linkedin_person(self, url):
        try:
            person = await self.proxycurl_client.linkedin.person.get(linkedin_profile_url=url)
            return {"status_code": 200, "data": person}
        except Exception as e:
            logger.error(f"Error in get: {e}")
            return {"status_code": 500, "data": f"Error in get: {e}"}
