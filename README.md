# Secure Multi-Modal Insurance Assistant

A RAG-based (Retrieval-Augmented Generation) chatbot that allows users to upload insurance documents (PDF, DOCX, images) and ask questions about them. The system extracts text, indexes it using hybrid search, and generates accurate answers with source citations.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14)                  │
│  - Upload UI (PDF, DOCX, Image)                         │
│  - Chat Interface (streaming responses via SSE)          │
│  - Mobile-responsive layout                             │
│  - Session management (localStorage + UUID)             │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API / SSE (streaming)
┌─────────────────────▼───────────────────────────────────┐
│                  Backend (Python FastAPI)                 │
│  - Document ingestion pipeline                          │
│  - OCR processing (EasyOCR: English + Vietnamese)       │
│  - Text chunking (500 tokens, 50 overlap)               │
│  - Hybrid search: BM25 + Semantic + Cohere Rerank       │
│  - Session isolation (per-session namespace)            │
│  - LLM integration (Azure OpenAI GPT-4o, streaming)    │
│  - Input sanitization & validation                      │
│  - Retry logic with exponential backoff                 │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              Vector DB (ChromaDB)                         │
│  - Per-session collections (cosine similarity)          │
│  - Metadata: filename, page, section, upload_date       │
│  - Persistent storage on disk                           │
└─────────────────────────────────────────────────────────┘
```

## Features

- **Multi-modal document support**: PDF, DOCX, and images (PNG/JPG)
- **OCR**: EasyOCR with English and Vietnamese language support
- **Hybrid search**: Combines BM25 (keyword) + semantic (embedding) search with RRF fusion
- **Reranking**: Cohere Rerank v4 via Azure AI for improved precision
- **Streaming responses**: Real-time token-by-token answer generation via SSE
- **Source citations**: Every answer includes references to source document, page, and section
- **Session isolation**: Each user session has its own document collection
- **"I don't know" handling**: LLM refuses to answer when context is insufficient
- **Mobile-responsive UI**: Works on desktop, tablet, and mobile
- **Input validation**: File type, size, and content validation on both client and server
- **Security**: Filename sanitization, session ID validation, CORS protection

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 14 (App Router) | React framework with SSR support |
| Styling | Tailwind CSS | Responsive utility-first CSS |
| Backend | Python FastAPI | Async API framework |
| Vector DB | ChromaDB | Lightweight vector storage |
| OCR | EasyOCR | Open-source OCR (EN + VI) |
| PDF Parsing | PyMuPDF (fitz) | Fast PDF text extraction |
| DOCX Parsing | python-docx | Word document parsing |
| Embeddings | OpenAI text-embedding-3-small | Text vectorization |
| LLM | Azure OpenAI (GPT-4o) | Answer generation |
| BM25 | rank_bm25 | Keyword-based retrieval |
| Reranker | Cohere Rerank v4 (Azure AI) | Result reranking |

## Prerequisites

- Python 3.10+
- Node.js 18+
- Azure OpenAI API access (for embeddings and LLM)
- Azure AI access with Cohere Rerank model (optional, for reranking)

## Setup

### 1. Clone and configure environment

```bash
# Copy environment template
cp .env.example backend/.env

# Edit backend/.env with your API keys
```

### 2. Backend setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Start the backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Run from the `backend/` directory, or use:
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## Environment Variables

Create `backend/.env` with the following:

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Yes |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Yes |
| `AZURE_OPENAI_DEPLOYMENT` | LLM model deployment name | Yes |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding model deployment | Yes |
| `RERANKER_API_KEY` | Cohere Rerank API key (Azure AI) | No (fallback to RRF) |
| `RERANKER_ENDPOINT` | Cohere Rerank endpoint URL | No |
| `RERANKER_MODEL` | Reranker model name | No |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | No (default: `./chroma_data`) |
| `MAX_FILE_SIZE_MB` | Max upload file size in MB | No (default: 5) |
| `MAX_FILES_PER_SESSION` | Max files per upload | No (default: 2) |
| `MAX_PDF_PAGES` | Max PDF pages to process | No (default: 20) |
| `FRONTEND_URL` | Frontend URL for CORS | No (default: `http://localhost:3000`) |

Frontend `.env.local`:
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL (default: `http://localhost:8000`) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/session/create` | Create new session |
| GET | `/api/session/{id}/info` | Get session info and files |
| DELETE | `/api/session/{id}` | Delete session and data |
| POST | `/api/upload` | Upload documents (multipart) |
| POST | `/api/chat` | Chat with streaming response (SSE) |

## How It Works

### Document Ingestion Pipeline

1. **Upload**: User uploads PDF/DOCX/Image (max 5MB, max 2 files)
2. **Parse**: Extract text using appropriate parser (PyMuPDF, python-docx, or EasyOCR)
3. **Chunk**: Split text into ~500-token chunks with 50-token overlap
4. **Embed**: Generate embeddings using OpenAI text-embedding-3-small
5. **Index**: Store in ChromaDB with metadata (filename, page, section, date)
6. **BM25**: Build in-memory BM25 index for keyword search

### RAG Query Pipeline

1. **Query**: User asks a question
2. **Semantic Search**: Query ChromaDB with embedded question (top-10)
3. **BM25 Search**: Query in-memory BM25 index (top-10)
4. **RRF Fusion**: Merge results using Reciprocal Rank Fusion
5. **Rerank**: Cohere Rerank v4 reranks top-10 candidates → top-5
6. **Generate**: LLM generates answer from top-5 chunks with citations
7. **Stream**: Response streamed token-by-token via SSE

## Design Decisions & Tradeoffs

| Decision | Rationale | Tradeoff |
|----------|-----------|----------|
| ChromaDB (local) | No external infra needed, simple setup | Not horizontally scalable |
| Per-session collections | Strong isolation, fast queries | Many collections with many users |
| Hybrid search + Rerank | Better precision than single method | Higher latency (~200ms for rerank) |
| EasyOCR | Free, supports Vietnamese | Lower accuracy than cloud OCR |
| SSE streaming | Simpler than WebSocket, sufficient for chat | Server→client only |
| 500-token chunks | Balance between context and precision | May miss very long context spans |
| localStorage sessions | Simple, no server-side session store | Lost on browser clear |
| Azure OpenAI | Enterprise-grade, supports Vietnamese well | Requires Azure subscription |

## Project Structure

```
aia-chatbot/
├── frontend/                     # Next.js 14 app
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── page.tsx         # Main page (upload + chat)
│   │   │   └── globals.css      # Tailwind styles
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx # Chat UI with streaming
│   │   │   ├── MessageBubble.tsx # Individual message component
│   │   │   ├── FileUpload.tsx    # Drag-and-drop upload
│   │   │   ├── DocumentList.tsx  # Uploaded files list
│   │   │   └── LoadingIndicator.tsx # Reusable loading states
│   │   └── lib/
│   │       ├── api.ts           # Backend API client
│   │       └── session.ts       # Session management
│   ├── package.json
│   └── tailwind.config.ts
│
├── backend/                      # Python FastAPI
│   ├── app/
│   │   ├── main.py             # App entry + CORS + logging
│   │   ├── config.py           # Pydantic settings
│   │   ├── routers/
│   │   │   ├── upload.py       # POST /api/upload
│   │   │   ├── chat.py         # POST /api/chat (SSE)
│   │   │   └── session.py      # Session CRUD
│   │   ├── services/
│   │   │   ├── ingestion.py    # Document processing pipeline
│   │   │   ├── chunking.py     # Text chunking with overlap
│   │   │   ├── vectorstore.py  # ChromaDB + embeddings
│   │   │   ├── bm25.py         # BM25 keyword search
│   │   │   ├── retrieval.py    # Hybrid search + RRF + rerank
│   │   │   ├── reranker.py     # Cohere Rerank v4 (Azure AI)
│   │   │   └── llm.py          # LLM prompt + streaming
│   │   ├── models/
│   │   │   └── schemas.py      # Pydantic request/response models
│   │   └── utils/
│   │       ├── pdf_parser.py   # PyMuPDF text extraction
│   │       ├── docx_parser.py  # python-docx extraction
│   │       ├── image_parser.py # EasyOCR processing
│   │       ├── retry.py        # Exponential backoff retry
│   │       └── sanitize.py     # Input sanitization
│   └── requirements.txt
│
├── chroma_data/                  # ChromaDB persistent storage
├── .env.example                  # Environment template
├── plan.md                       # Implementation plan
└── README.md                     # This file
```

## Security Features

- **Session isolation**: Each session has its own ChromaDB collection; users cannot access other sessions' data
- **Input sanitization**: Filenames are sanitized to prevent path traversal attacks
- **Session ID validation**: UUIDs are validated before processing
- **File validation**: Type checking (extension + MIME type), size limits
- **CORS**: Restricted to configured frontend origin
- **Query sanitization**: User queries are cleaned before processing
- **No secrets in responses**: API keys and internal errors are never exposed to clients

## Known Limitations

- No persistent session store (sessions are lost if BM25 in-memory index is cleared on restart)
- No rate limiting implemented (recommended for production)
- No authentication system (relies on session isolation only)
- OCR accuracy may vary for low-quality scanned documents
- ChromaDB is single-node (not suitable for high-traffic production)
- No automatic session cleanup (expired sessions persist in ChromaDB)
- Maximum 2 files per upload, 5MB per file, 20 pages per PDF

## Future Improvements

- Add Redis-based rate limiting
- Implement session expiry with background cleanup task
- Add authentication (OAuth2 / API keys)
- Support more file formats (TXT, HTML, Excel)
- Add conversation history / multi-turn context
- Implement document deletion per file
- Add WebSocket support for bidirectional communication
- Deploy with Docker Compose for easier setup
- Add comprehensive test suite (pytest + Jest)
- Implement caching for repeated queries
