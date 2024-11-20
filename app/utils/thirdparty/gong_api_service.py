import requests
import base64
from config import constants


def get_api_token():
    username = constants.GONG_USERNAME
    password = constants.GONG_PASSWORD
    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
    return f"Basic {auth_base64}"


def get_users():
    try:
        endpoint = f"{constants.GONG_BASE_URL}/v2/users"
        api_token = get_api_token()
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
