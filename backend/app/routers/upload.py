"""Upload router for document ingestion."""
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from typing import List
from ..models.schemas import UploadResponse, UploadedFile, FileStatus
from ..services.ingestion import validate_file, process_document
from ..utils.sanitize import sanitize_filename, validate_session_id
from ..config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    request: Request,
    files: List[UploadFile] = File(...)
):
    """Upload and process documents."""
    # Get session ID from header or cookie
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")

    # Validate session ID format
    if not validate_session_id(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    # Validate number of files
    if len(files) > settings.max_files_per_session:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.max_files_per_session} files allowed per upload"
        )

    processed_files: List[UploadedFile] = []

    for file in files:
        # Read file content
        content = await file.read()
        filename = sanitize_filename(file.filename or "unknown")
        content_type = file.content_type or "application/octet-stream"
        logger.info(f"Processing file: {filename} ({content_type}, {len(content)} bytes)")

        # Validate
        is_valid, error_msg = validate_file(filename, content_type, len(content))
        if not is_valid:
            processed_files.append(UploadedFile(
                filename=filename,
                file_type=content_type,
                status=FileStatus.ERROR,
                upload_date=datetime.now().isoformat(),
                error_message=error_msg,
            ))
            continue

        # Process document
        try:
            result = await process_document(
                file_bytes=content,
                filename=filename,
                content_type=content_type,
                session_id=session_id,
            )

            if result["success"]:
                processed_files.append(UploadedFile(
                    filename=filename,
                    file_type=result.get("file_type", content_type),
                    status=FileStatus.READY,
                    upload_date=datetime.now().isoformat(),
                    num_chunks=result["num_chunks"],
                ))
            else:
                processed_files.append(UploadedFile(
                    filename=filename,
                    file_type=content_type,
                    status=FileStatus.ERROR,
                    upload_date=datetime.now().isoformat(),
                    error_message=result.get("error", "Processing failed"),
                ))
        except Exception as e:
            processed_files.append(UploadedFile(
                filename=filename,
                file_type=content_type,
                status=FileStatus.ERROR,
                upload_date=datetime.now().isoformat(),
                error_message=f"Unexpected error: {str(e)}",
            ))

    success_count = sum(1 for f in processed_files if f.status == FileStatus.READY)
    return UploadResponse(
        success=success_count > 0,
        files=processed_files,
        message=f"Processed {success_count}/{len(files)} files successfully",
    )
