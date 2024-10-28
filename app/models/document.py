from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.database.base import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    extracted_text_path = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    status = Column(String, default="pending")  # pending, processed, failed
    content_hash = Column(String, unique=True, index=True)
    mime_type = Column(String)
    metadata = Column(Text, nullable=True)  # JSON field for additional metadata

    