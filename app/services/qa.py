# app/services/qa.py
from typing import Optional, Dict, Any
from langchain import hub
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from sqlalchemy.orm import Session
from app.models.document import Document
from app.schemas.message import AnswerMessage
import os
import json

class QAService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-3.5-turbo"
        )
        self.conversations: Dict[str, list] = {}
        
    async def get_answer(
        self,
        db: Session,
        document_id: int,
        question: str,
        conversation_id: Optional[str] = None
    ) -> AnswerMessage:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")
            
        # Load document text
        with open(document.extracted_text_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        # Split text and create/get vectorstore
        texts = self.text_splitter.split_text(text)
        vectorstore = await self._get_or_create_vectorstore(
            texts,
            document_id
        )
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            self.llm,
            retriever=vectorstore.as_retriever(
                search_kwargs={"k": 3}
            )
        )
        
        # Get context from conversation history
        context = self._get_conversation_context(conversation_id)
        
        # Prepare the question with context
        full_question = self._prepare_question_with_context(
            question,
            context
        )
        
        # Get answer
        result = await qa_chain.ainvoke({"query": full_question})
        
        # Update conversation history
        self._update_conversation_history(
            conversation_id,
            question,
            result["result"]
        )
        
        return AnswerMessage(
            answer=result["result"],
            confidence=self._calculate_confidence(result),
            context=self._format_context(result.get("source_documents", [])),
            conversation_id=conversation_id or self._generate_conversation_id()
        )
        
    async def _get_or_create_vectorstore(
        self,
        texts: list,
        document_id: int
    ) -> Chroma:
        """Get existing vectorstore or create new one."""
        persist_directory = f"storage/vectorstore/{document_id}"
        
        if os.path.exists(persist_directory):
            return Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings
            )
            
        vectorstore = Chroma.from_texts(
            texts,
            self.embeddings,
            persist_directory=persist_directory
        )
        vectorstore.persist()
        return vectorstore
        
    def _get_conversation_context(
        self,
        conversation_id: Optional[str]
    ) -> list:
        """Get conversation history for context."""
        if not conversation_id:
            return []
        return self.conversations.get(conversation_id, [])
        
    def _prepare_question_with_context(
        self,
        question: str,
        context: list
    ) -> str:
        """Prepare question with conversation context."""
        if not context:
            return question
            
        context_str = "\n".join([
            f"Q: {q}\nA: {a}"
            for q, a in context[-3:]  # Use last 3 exchanges
        ])
        
        return f"""
        Previous conversation:
        {context_str}
        
        Current question: {question}
        """
        
    def _update_conversation_history(
        self,
        conversation_id: Optional[str],
        question: str,
        answer: str
    ):
        """Update conversation history."""
        if not conversation_id:
            return
            
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            
        self.conversations[conversation_id].append((question, answer))
        
        # Keep only last 10 exchanges
        self.conversations[conversation_id] = \
            self.conversations[conversation_id][-10:]
            
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score for the answer."""
        # Implement your confidence calculation logic here
        return 0.9  # Placeholder
        
    def _format_context(self, source_documents: list) -> str:
        """Format source documents into readable context."""
        if not source_documents:
            return ""
            
        context_parts = []
        for doc in source_documents:
            page_content = doc.page_content[:200] + "..."  # Truncate long content
            context_parts.append(page_content)
            
        return "\n\n".join(context_parts)
        
    def _generate_conversation_id(self) -> str:
        """Generate a new conversation ID."""
        import uuid
        return str(uuid.uuid4())