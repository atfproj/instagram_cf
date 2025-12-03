from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base


class MediaType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    CAROUSEL = "carousel"
    REEL = "reel"


class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    POSTING = "posting"
    COMPLETED = "completed"
    FAILED = "failed"


class PostExecutionStatus(str, enum.Enum):
    QUEUED = "queued"
    POSTING = "posting"
    SUCCESS = "success"
    FAILED = "failed"


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    media_paths = Column(JSON, nullable=False)  # массив путей к медиа
    media_type = Column(Enum(MediaType), nullable=False)
    caption_original = Column(Text, nullable=False)
    original_language = Column(String(10), nullable=False)
    target_groups = Column(JSON, nullable=False)  # массив group_id
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT, nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime, nullable=True)

    # Relationships
    executions = relationship("PostExecution", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post(id={self.id}, status={self.status})>"


class PostExecution(Base):
    __tablename__ = "post_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    caption_translated = Column(Text, nullable=False)
    instagram_media_id = Column(String(100), nullable=True)
    status = Column(Enum(PostExecutionStatus), default=PostExecutionStatus.QUEUED, nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="executions")
    account = relationship("Account", back_populates="post_executions")

    def __repr__(self):
        return f"<PostExecution(id={self.id}, status={self.status})>"

