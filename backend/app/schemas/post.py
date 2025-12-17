from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.models.post import MediaType, PostStatus, PostExecutionStatus


class PostBase(BaseModel):
    caption_original: str = Field(..., min_length=1)
    original_language: str = Field(..., max_length=10)
    target_groups: List[UUID] = Field(..., min_items=1)


class PostCreate(PostBase):
    media_paths: List[str] = Field(..., min_items=1)
    media_type: MediaType
    scheduled_at: Optional[datetime] = None


class PostUpdate(BaseModel):
    caption_original: Optional[str] = None
    target_groups: Optional[List[UUID]] = None
    scheduled_at: Optional[datetime] = None


class PostExecutionResponse(BaseModel):
    id: UUID
    account_id: UUID
    account_username: Optional[str] = None
    caption_translated: str
    instagram_media_id: Optional[str]
    status: PostExecutionStatus
    error_message: Optional[str]
    retry_count: int
    posted_at: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True


class PostResponse(PostBase):
    id: UUID
    media_paths: List[str]
    media_type: MediaType
    status: PostStatus
    scheduled_at: Optional[datetime]
    created_at: datetime
    posted_at: Optional[datetime]
    executions: Optional[List[PostExecutionResponse]] = None

    class Config:
        orm_mode = True

