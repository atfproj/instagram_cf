from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.proxy import ProxyType, ProxyStatus


class ProxyBase(BaseModel):
    url: str = Field(..., min_length=1, max_length=500)
    type: ProxyType
    country: Optional[str] = Field(None, max_length=50)
    
    @validator('url')
    def validate_proxy_url(cls, v):
        """Валидация формата URL прокси"""
        if not (v.startswith("http://") or v.startswith("https://") or v.startswith("socks5://")):
            raise ValueError("URL прокси должен начинаться с http://, https:// или socks5://")
        return v


class ProxyCreate(ProxyBase):
    pass


class ProxyUpdate(BaseModel):
    url: Optional[str] = Field(None, min_length=1, max_length=500)
    type: Optional[ProxyType] = None
    country: Optional[str] = Field(None, max_length=50)
    status: Optional[ProxyStatus] = None


class ProxyResponse(ProxyBase):
    id: UUID
    status: ProxyStatus
    last_check_at: Optional[datetime]
    success_rate: float
    assigned_accounts: list
    created_at: datetime

    class Config:
        from_attributes = True


class ProxyCheckResponse(BaseModel):
    success: bool
    message: str
    response_time_ms: Optional[int] = None
    error: Optional[str] = None

