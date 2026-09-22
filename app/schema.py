from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class CreateUrl(BaseModel):
    url: HttpUrl
    custom_alias: Optional[str] = Field(None, min_length=3, max_length=10, pattern=r'^[a-zA-Z0-9_-]+$', description="Custom alias for the shortened URL. Must be 3-10 characters long and can only contain letters, numbers, underscores, and hyphens")


class UrlResponse(BaseModel):
    short_url: str
    target_url: str
    short_code: str

    class Config:
        from_attributes = True

class UrlStatsResponse(BaseModel):
    target_url: str
    short_code: str
    clicks: int
    created_at: datetime
    class Config:
        from_attributes = True
