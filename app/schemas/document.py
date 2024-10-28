from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional, Dict, Any

class DocumentBase(BaseModel):
    filename: str

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(DocumentBase):
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DocumentInDB(DocumentBase):
    id: int
    file_path: str
    extracted_text_path: str
    uploaded_at: datetime
    file_size: int
    status: str
    content_hash: str
    mime_type: str
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True