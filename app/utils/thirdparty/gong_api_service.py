import requests
import base64
from config import constants
from typing import Optional
import json


async def get_api_token():
    username = constants.GONG_USERNAME
    password = constants.GONG_PASSWORD
    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
    return f"Basic {auth_base64}"


async def get_users():
    try:
        endpoint = f"{constants.GONG_BASE_URL}/v2/users"
        api_token = await get_api_token()
        headers = {"Authorization": api_token, "Content-Type": "application/json"}
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


async def get_calls_by_date_range(start_date: str, end_date: Optional[str] = None):
    try:
        endpoint = f"{constants.GONG_BASE_URL}/v2/calls?fromDateTime={start_date}"
        if end_date:
            endpoint += f"&toDateTime={end_date}"
        api_token = await get_api_token()
        headers = {"Authorization": api_token, "Content-Type": "application/json"}
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


async def get_call_transcript_by_call_id(call_id):
    try:
        endpoint = f"{constants.GONG_BASE_URL}/v2/calls/transcript"
        api_token = await get_api_token()
        headers = {"Authorization": api_token, "Content-Type": "application/json"}
        payload = json.dumps({"filter": {"callIds": call_id}})
        response = requests.post( endpoint, headers=headers, data=payload)
        if response.status_code == 200:
            return {"response": response.json(), "status_code": 200}
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return {"error": response.text, "status_code": 500, "status": response.status_code}
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e), "status_code": 500}


async def get_gong_extensive_call_data(cursor: Optional[str] = None):
    try:
        endpoint = f"{constants.GONG_BASE_URL}/v2/calls/extensive"
        api_token = await get_api_token()
        headers = {"Authorization": api_token, "Content-Type": "application/json"}

        payload = {
            "contentSelector": {"exposedFields": {"parties": True}},
            "filter": {},
        }
        if cursor:
            payload["cursor"] = cursor

        response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            return {"response": response.json(), "status_code": 200}
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return {
                "error": response.text,
                "status_code": 500,
                "status": response.status_code,
            }
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e), "status_code": 500}
