from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
load_dotenv()


db_username = os.getenv('DB_USER_NAME')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')


def get_mongodb_connection_string():
    return f"mongodb+srv://{db_username}:{db_password}@enablematch.ub0ym.mongodb.net/{db_name}"


client = AsyncIOMotorClient(get_mongodb_connection_string())
db = client[db_name]
