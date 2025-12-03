from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.core.database import Base


class TranslationCache(Base):
    __tablename__ = "translations_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text_original = Column(Text, nullable=False, index=True)
    language_from = Column(String(10), nullable=False, index=True)
    language_to = Column(String(10), nullable=False, index=True)
    text_translated = Column(Text, nullable=False)
    service = Column(String(20), nullable=False)  # deepl, google
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TranslationCache(id={self.id}, {self.language_from}->{self.language_to})>"

