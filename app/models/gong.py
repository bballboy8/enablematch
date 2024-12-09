from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from dateutil import parser
from pytz import UTC

class CallDetailModel(BaseModel):
    gong_id: str
    url: str
    title: str
    scheduled: datetime = Field(..., description="Datetime when the call was scheduled, in UTC.")
    started: datetime = Field(..., description="Datetime when the call started, in UTC.")
    duration: int
    primaryUserId: str
    direction: str
    system: str
    scope: str
    media: str
    language: str
    workspaceId: str
    sdrDisposition: Optional[str]
    clientUniqueId: Optional[str]
    customData: Optional[str]
    purpose: Optional[str]
    meetingUrl: str
    isPrivate: bool
    calendarEventId: Optional[str]

    @field_validator("scheduled", "started", mode="before")
    def convert_to_utc(cls, value):
        if isinstance(value, str):
            dt = parser.isoparse(value)
            return dt.astimezone(UTC)
        return value
    
    @model_validator(mode="before")
    def map_id_to_gong_id(cls, values):
        values['gong_id'] = values.get('id')
        return values