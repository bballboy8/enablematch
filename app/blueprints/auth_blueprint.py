from pydantic import BaseModel
from typing import Optional



class UserSignIn(BaseModel):
    email:  str
    password: str 


class UserDeleteAccount(BaseModel):
    user_id: str


class UserSignUp(BaseModel):
    fullname: str
    email: str
    password: str
    company_name: Optional[str] = None
    job_title: Optional[str] = None


class Token(BaseModel):

    access_token: str
    token_type: str
    user_id: str
