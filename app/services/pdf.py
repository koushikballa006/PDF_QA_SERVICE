import fitz
import os
from typing import Tuple
from fastapi import UploadFile
from app.core.config import get_settings
import asyncio
from concurrent.futures import ThreadPoolExecutor

settings = get_settings()
executor = ThreadPoolExecutor()

class PDFService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.extracted_text_dir = settings.EXTRACTED_TEXT_DIR
        
        # Ensure directories exist
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.extracted_text_dir, exist_ok=True)

    async def save_uploaded_file(self, file: UploadFile) -> Tuple[str, int]:
        """Save the uploaded PDF file and return its path and size."""
        file_path = os.path.join(self.upload_dir, file.filename)
        
        size = 0
        with open(file_path, "wb") as buffer:
            while content := await file.read(1024 * 1024):  # Read in 1MB chunks
                size += len(content)
                buffer.write(content)
        
        return file_path, size

    async def extract_text(self, file_path: str, document_id: int) -> str:
        """Extract text from PDF and save it to a file."""
        try:
            # Run PDF processing in thread pool
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                executor,
                self._extract_text_sync,
                file_path
            )
            
            # Save extracted text
            text_path = os.path.join(self.extracted_text_dir, f"{document_id}.txt")
            await loop.run_in_executor(
                executor,
                self._save_text,
                text_path,
                text
            )
            
            return text_path
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")

    def _extract_text_sync(self, file_path: str) -> str:
        """Synchronous PDF text extraction."""
        pdf_document = fitz.open(file_path)
        text = ""
        for page in pdf_document:
            text += page.get_text()
        return text

    def _save_text(self, text_path: str, text: str):
        """Synchronous text saving."""
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)