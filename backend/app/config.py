from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_endpoint: str = "https://aia-tiennbn.openai.azure.com/openai/v1"
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-5.4-mini"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"

    # Reranker (Azure AI - Cohere)
    reranker_api_key: str = ""
    reranker_endpoint: str = "https://pj001.services.ai.azure.com/providers/cohere/v2/rerank"
    reranker_model: str = "Cohere-rerank-v4.0-fast"

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    chroma_persist_dir: str = "./chroma_data"
    max_file_size_mb: int = 5
    max_files_per_session: int = 2
    max_pdf_pages: int = 20

    # OCR
    ocr_languages: str = "en,vi"

    # Session
    session_expiry_hours: int = 24

    # CORS
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = (".env", "backend/.env")
        extra = "ignore"
        env_file_encoding = "utf-8"


settings = Settings()
