from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class FileStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class DocumentMetadata(BaseModel):
    filename: str
    page_number: Optional[int] = None
    section_number: Optional[int] = None
    paragraph_range: Optional[str] = None
    upload_date: str
    chunk_index: int = 0


class UploadedFile(BaseModel):
    filename: str
    file_type: str
    status: FileStatus
    upload_date: str
    num_chunks: int = 0
    error_message: Optional[str] = None


class UploadResponse(BaseModel):
    success: bool
    files: List[UploadedFile]
    message: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str
    selected_files: Optional[List[str]] = None  # Filter retrieval to these files only


class Citation(BaseModel):
    filename: str
    page_number: Optional[int] = None
    section_number: Optional[int] = None
    paragraph_range: Optional[str] = None
    relevance_score: float = 0.0


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    session_id: str


class SessionInfo(BaseModel):
    session_id: str
    files: List[UploadedFile]
    created_at: str


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
