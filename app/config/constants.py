import os
from fastapi.security import OAuth2PasswordBearer


ALGORITHM = "HS256"
SECRET_KEY = "secret"
DEFAULT_TOKEN_EXPIRY_HOURS = 3600
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

USERS_COLLECTION = "users"

# keys
USER_ID_FIELD = "user_id"
ID_FIELD = "id"
MONGO_INDEX_FIELD = "_id"
UPDATED_AT_FIELD = "updated_at"

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
