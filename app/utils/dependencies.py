from config.constants import  SECRET_KEY, oauth2_scheme
from fastapi import Depends, HTTPException, status, Request, Response
from jose import jwt
from config.db_connection import db
from config import constants
from bson import ObjectId
from logging_module import logger
import requests
import services
from mimetypes import guess_type
from os.path import isfile
import asyncio


def get_current_user_id(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.debug("Inside get current user id")
        users_collection = db["users"]
        heisman_token_data = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"],
        )
        user_id = heisman_token_data.get("_id") or heisman_token_data.get("id")
        user = users_collection.find_one({"_id": ObjectId(user_id), "is_active": True})
        if not user:
            raise credentials_exception
        return user_id
    except Exception as e:
        logger.error(f"Error in get current user id: {e}")
        raise credentials_exception