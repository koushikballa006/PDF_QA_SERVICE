# app/api/websockets/qa.py
from fastapi import APIRouter, WebSocket, Depends, HTTPException, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.message import QuestionMessage, AnswerMessage
from app.services.qa import QAService
from app.core.rate_limiter import RateLimiter
import json
from typing import Dict, Set
import asyncio

router = APIRouter()
qa_service = QAService()
rate_limiter = RateLimiter()

# Store active connections and their rate limits
active_connections: Dict[str, WebSocket] = {}
client_message_counts: Dict[str, int] = {}
RATE_LIMIT_WINDOW = 60  # seconds
MAX_MESSAGES = 30  # messages per minute

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_message_counts: Dict[str, int] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_message_counts[client_id] = 0
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_message_counts:
            del self.client_message_counts[client_id]
            
    async def check_rate_limit(self, client_id: str) -> bool:
        current_count = self.client_message_counts.get(client_id, 0)
        if current_count >= MAX_MESSAGES:
            return False
        self.client_message_counts[client_id] = current_count + 1
        return True
        
    async def reset_rate_limits(self):
        """Reset rate limits every minute"""
        while True:
            await asyncio.sleep(RATE_LIMIT_WINDOW)
            self.client_message_counts.clear()
            
    async def send_personal_message(self, message: dict, client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/qa/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    db: Session = Depends(get_db)
):
    await manager.connect(websocket, client_id)
    
    # Start rate limit reset task
    reset_task = asyncio.create_task(manager.reset_rate_limits())
    
    try:
        while True:
            # Check rate limit
            if not await manager.check_rate_limit(client_id):
                await websocket.send_json({
                    "error": "Rate limit exceeded. Please wait before sending more messages.",
                    "code": "RATE_LIMIT_EXCEEDED"
                })
                continue

            try:
                # Receive message
                data = await websocket.receive_text()
                message = QuestionMessage.parse_raw(data)
                
                # Process question and get answer
                try:
                    answer = await qa_service.get_answer(
                        db,
                        message.document_id,
                        message.question,
                        message.conversation_id
                    )
                    
                    # Send response
                    response = AnswerMessage(
                        answer=answer.answer,
                        confidence=answer.confidence,
                        context=answer.context,
                        conversation_id=answer.conversation_id
                    )
                    
                    await websocket.send_json(response.dict())
                    
                except Exception as e:
                    # Handle QA service errors
                    await websocket.send_json({
                        "error": "Failed to process question",
                        "detail": str(e),
                        "code": "QA_PROCESSING_ERROR"
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "error": "Invalid message format",
                    "code": "INVALID_MESSAGE_FORMAT"
                })
                
            except Exception as e:
                await websocket.send_json({
                    "error": "Internal server error",
                    "detail": str(e),
                    "code": "INTERNAL_SERVER_ERROR"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        
    except Exception as e:
        manager.disconnect(client_id)
        # Log the error here
        print(f"Error in websocket connection: {str(e)}")
        
    finally:
        # Clean up
        reset_task.cancel()
        try:
            await reset_task
        except asyncio.CancelledError:
            pass
        manager.disconnect(client_id)

# Helper function to broadcast messages to all connected clients
async def broadcast_message(message: dict):
    """Broadcast a message to all connected clients"""
    for client_id, connection in manager.active_connections.items():
        try:
            await connection.send_json(message)
        except Exception as e:
            print(f"Error sending message to client {client_id}: {str(e)}")
            manager.disconnect(client_id)