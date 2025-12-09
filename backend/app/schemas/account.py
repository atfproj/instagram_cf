from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.account import AccountStatus


class AccountBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    language: str = Field(default="en", max_length=10)
    group_id: Optional[UUID] = None
    proxy_id: Optional[UUID] = None


class AccountCreate(AccountBase):
    password: str = Field(..., min_length=1)


class AccountUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = None
    language: Optional[str] = Field(None, max_length=10)
    group_id: Optional[UUID] = None
    proxy_id: Optional[UUID] = None
    status: Optional[AccountStatus] = None


class AccountResponse(AccountBase):
    id: UUID
    status: AccountStatus
    last_post_at: Optional[datetime]
    last_login_at: Optional[datetime]
    posts_count_today: int
    failed_attempts: int
    account_age_days: int
    warmup_stage: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

