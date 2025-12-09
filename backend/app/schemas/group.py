from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class GroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class GroupResponse(GroupBase):
    id: UUID
    accounts_count: int
    created_at: datetime

    class Config:
        orm_mode = True

