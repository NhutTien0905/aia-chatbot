"""Session management router."""
import logging
from fastapi import APIRouter, Request, HTTPException
from ..models.schemas import SessionInfo, UploadedFile, HealthResponse
from ..services.vectorstore import delete_collection, delete_document_by_filename, get_chroma_client, get_collection_name
from ..utils.sanitize import validate_session_id
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["session"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="1.0.0")


@router.post("/session/create")
async def create_session():
    """Create a new session and return session ID."""
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}


@router.get("/session/{session_id}/info")
async def get_session_info(session_id: str):
    """Get session information including uploaded files."""
    if not validate_session_id(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    try:
        client = get_chroma_client()
        collection_name = get_collection_name(session_id)
        collection = client.get_collection(name=collection_name)

        # Get unique filenames from metadata
        results = collection.get(include=["metadatas"])
        files_map = {}
        if results["metadatas"]:
            for meta in results["metadatas"]:
                fname = meta.get("filename", "unknown")
                if fname not in files_map:
                    files_map[fname] = {
                        "filename": fname,
                        "file_type": meta.get("source_type", "unknown"),
                        "status": "ready",
                        "upload_date": meta.get("upload_date", ""),
                        "num_chunks": 0,
                    }
                files_map[fname]["num_chunks"] += 1

        return {
            "session_id": session_id,
            "files": list(files_map.values()),
        }
    except Exception:
        return {
            "session_id": session_id,
            "files": [],
        }


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its data."""
    if not validate_session_id(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    success = delete_collection(session_id)
    logger.info(f"Session {session_id[:8]}... deleted: {success}")
    return {"success": success, "message": "Session deleted" if success else "Session not found"}


@router.delete("/session/{session_id}/document/{filename:path}")
async def delete_document(session_id: str, filename: str):
    """Delete a specific document from a session."""
    if not validate_session_id(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    if not filename or len(filename) > 255:
        raise HTTPException(status_code=400, detail="Invalid filename")

    deleted_count = delete_document_by_filename(session_id, filename)
    if deleted_count > 0:
        return {
            "success": True,
            "message": f"Deleted {deleted_count} chunks for '{filename}'",
        }
    else:
        return {
            "success": False,
            "message": f"No chunks found for '{filename}'",
        }
