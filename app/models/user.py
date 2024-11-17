from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class User(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
