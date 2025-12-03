from sqlalchemy import Column, String, Enum, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum
from app.core.database import Base


class ProxyType(str, enum.Enum):
    HTTP = "http"
    SOCKS5 = "socks5"


class ProxyStatus(str, enum.Enum):
    ACTIVE = "active"
    FAILED = "failed"
    CHECKING = "checking"


class Proxy(Base):
    __tablename__ = "proxies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(500), nullable=False)
    type = Column(Enum(ProxyType), nullable=False)
    country = Column(String(50), nullable=True)
    status = Column(Enum(ProxyStatus), default=ProxyStatus.ACTIVE, nullable=False)
    last_check_at = Column(DateTime, nullable=True)
    success_rate = Column(Float, default=1.0)
    assigned_accounts = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Proxy(id={self.id}, url={self.url}, status={self.status})>"

