"""Chat router for RAG-based Q&A."""
import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from ..models.schemas import ChatRequest
from ..services.retrieval import hybrid_search
from ..services.llm import generate_answer_stream
from ..utils.sanitize import validate_session_id, sanitize_query
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat(request: Request, chat_request: ChatRequest):
    """Chat endpoint with streaming response."""
    session_id = chat_request.session_id
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")

    # Validate session ID format
    if not validate_session_id(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    question = sanitize_query(chat_request.question)
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    logger.info(f"Chat request from session {session_id[:8]}...: {question[:50]}...")

    # Retrieve relevant chunks using hybrid search
    chunks = hybrid_search(session_id, question, top_k=5)

    # Build citations from retrieved chunks
    citations = []
    seen_sources = set()
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        source_key = (
            metadata.get("filename", ""),
            metadata.get("page_number"),
            metadata.get("section_number"),
        )
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            citations.append({
                "filename": metadata.get("filename", "unknown"),
                "page_number": metadata.get("page_number"),
                "section_number": metadata.get("section_number"),
                "paragraph_range": metadata.get("paragraph_range"),
                "relevance_score": chunk.get("score", 0),
            })

    # Stream response
    async def event_stream():
        # First send citations
        yield f"data: {json.dumps({'type': 'citations', 'data': citations})}\n\n"

        # Then stream the answer
        try:
            for token in generate_answer_stream(question, chunks):
                yield f"data: {json.dumps({'type': 'token', 'data': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

        # Signal end
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
