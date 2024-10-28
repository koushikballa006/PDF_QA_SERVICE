from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.services.pdf import PDFService
from fastapi import UploadFile, HTTPException
import os
import json

class StorageService:
    def __init__(self):
        self.pdf_service = PDFService()

    async def store_document(
        self,
        db: Session,
        file: UploadFile,
        document_in: DocumentCreate,
        content_hash: str
    ) -> Document:
        """Store document and its metadata in database."""
        # Save file and get path
        file_path, file_size = await self.pdf_service.save_uploaded_file(file)

        # Create document record
        db_document = Document(
            filename=document_in.filename,
            file_path=file_path,
            file_size=file_size,
            status="pending",
            content_hash=content_hash,
            mime_type="application/pdf",
            metadata=json.dumps({"original_filename": file.filename})
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        try:
            # Extract text
            extracted_text_path = await self.pdf_service.extract_text(
                file_path, db_document.id
            )
            
            # Update document with extracted text path
            db_document.extracted_text_path = extracted_text_path
            db_document.status = "processed"
            db.commit()
            db.refresh(db_document)

        except Exception as e:
            db_document.status = "failed"
            db.commit()
            raise HTTPException(500, f"Failed to process document: {str(e)}")

        return db_document

    def get_by_hash(self, db: Session, content_hash: str) -> Optional[Document]:
        """Get document by content hash."""
        return db.query(Document).filter(Document.content_hash == content_hash).first()

    def get_documents(
        self, db: Session, skip: int = 0, limit: int = 10
    ) -> List[Document]:
        """Get all documents with pagination."""
        return db.query(Document).offset(skip).limit(limit).all()

    def get_document(self, db: Session, document_id: int) -> Optional[Document]:
        """Get specific document by ID."""
        return db.query(Document).filter(Document.id == document_id).first()

    def delete_document(self, db: Session, document_id: int) -> bool:
        """Delete a document and its associated files."""
        document = self.get_document(db, document_id)
        if not document:
            raise HTTPException(404, "Document not found")

        # Delete files
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        if os.path.exists(document.extracted_text_path):
            os.remove(document.extracted_text_path)

        # Delete from database
        db.delete(document)
        db.commit()
        return True