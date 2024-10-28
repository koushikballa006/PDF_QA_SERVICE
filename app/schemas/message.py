# app/schemas/message.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class QuestionMessage(BaseModel):
    document_id: int
    question: str
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AnswerMessage(BaseModel):
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    context: Optional[str] = None
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ErrorMessage(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None