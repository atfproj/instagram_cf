from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base


class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    BANNED = "banned"
    COOLDOWN = "cooldown"
    LOGIN_REQUIRED = "login_required"
    PROXY_ERROR = "proxy_error"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(500), nullable=False)  # encrypted
    session_data = Column(JSON, nullable=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=True)
    language = Column(String(10), nullable=False, default="en")
    proxy_id = Column(UUID(as_uuid=True), ForeignKey("proxies.id"), nullable=True)
    proxy_url = Column(String(500), nullable=True)  # Deprecated, используем proxy_id
    proxy_type = Column(String(20), nullable=True)  # Deprecated, используем proxy_id
    status = Column(Enum(AccountStatus), default=AccountStatus.LOGIN_REQUIRED, nullable=False)
    last_post_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    posts_count_today = Column(Integer, default=0)
    failed_attempts = Column(Integer, default=0)
    device_id = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    posts_limit_per_day = Column(Integer, default=10)
    warmup_stage = Column(Integer, default=0)  # 0-3, где 3 = полный прогрев
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    group = relationship("Group", back_populates="accounts")
    proxy = relationship("Proxy", foreign_keys=[proxy_id])
    post_executions = relationship("PostExecution", back_populates="account", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="account", cascade="all, delete-orphan")

    @property
    def account_age_days(self) -> int:
        """Вычисляемое поле: возраст аккаунта в днях"""
        if self.created_at:
            return (datetime.utcnow() - self.created_at).days
        return 0

    def __repr__(self):
        return f"<Account(id={self.id}, username={self.username}, status={self.status})>"

