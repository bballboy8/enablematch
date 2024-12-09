from fastapi import APIRouter, Request, Depends
from blueprints import  UserSignIn, UserSignUp,  Token
import services 
from logging_module import logger
from fastapi.security import OAuth2PasswordRequestForm
from utils.dependencies import get_current_user_id

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """Generates an access token given email and password."""
    logger.info("Login for access token entry point")
    response = await services.login_for_access_token_service(form_data)
    logger.info("Login for access token exit point")
    return response

@router.get('/get_user_details')
async def get_user_details(user_id=Depends(get_current_user_id)):
    logger.debug("Inside get user details controller")
    response = await services.get_user_via_token_service(user_id)
    logger.debug("Response from get user details service")
    return response


@router.post("/signin")
async def signin(user_data: UserSignIn):
    logger.info("Signin entry point")
    response = await services.signin_service(user_data)
    logger.info("Signin exit point")
    return response

@router.post("/signup")
async def signup(user_data: UserSignUp):
    logger.info("Signup entry point")
    response = await services.signup_service(user_data)
    logger.info("Signup exit point")
    return response
