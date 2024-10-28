from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.storage import StorageService
from app.schemas.document import DocumentCreate, DocumentInDB, DocumentUpdate
from app.core.rate_limiter import RateLimiter
from typing import List
import hashlib

router = APIRouter()
storage_service = StorageService()
rate_limiter = RateLimiter()

@router.post("/upload", response_model=DocumentInDB)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a PDF document."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are allowed")
        
    # Generate content hash
    content = await file.read()
    content_hash = hashlib.sha256(content).hexdigest()
    await file.seek(0)
    
    # Check if document already exists
    existing_doc = storage_service.get_by_hash(db, content_hash)
    if existing_doc:
        raise HTTPException(400, "Document already exists")
    
    document_in = DocumentCreate(filename=file.filename)
    return await storage_service.store_document(db, file, document_in, content_hash)

@router.get("/", response_model=List[DocumentInDB])
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all uploaded documents."""
    return storage_service.get_documents(db, skip=skip, limit=limit)

@router.get("/{document_id}", response_model=DocumentInDB)
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific document by ID."""
    document = storage_service.get_document(db, document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    return document

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific document."""
    return storage_service.delete_document(db, document_id)