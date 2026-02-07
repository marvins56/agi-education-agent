"""Document model for uploaded educational content."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.models.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    title = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=True)
    grade_level = Column(String(50), nullable=True)
    file_path = Column(String(500), nullable=True)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0)
    status = Column(String(50), default="pending")
    metadata_ = Column("metadata", JSONB, server_default=text("'{}'"))
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)
